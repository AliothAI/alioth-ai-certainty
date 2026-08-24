"""Alioth 确定性校验 skill —— 客户端调用脚本。

call.py 形态：读 mcp_config.json 的 key，调 verify_metric 服务。

两种模式：
  base_url 已配  → HTTP 远程服务（线上域名 / 本地 uvicorn）—— 安装到任何 CLI 都用这个
  base_url 未配  → 本地直接 import service 层（仅开发时 skill 在 alioth-engine 项目内）

第一次使用：无需注册，verify() 自动匿名注册拿免费 key（零输入，一次性走完）。
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
CONFIG = json.loads((_HERE / "mcp_config.json").read_text(encoding="utf-8"))
API_KEY = CONFIG.get("api_key", "")

# 标准服务地址（部署在阿里云，固定值；本地调试可临时在 mcp_config.json 覆盖）
DEFAULT_BASE_URL = "https://alioth-api.titanplus.cn"
BASE_URL = CONFIG.get("base_url", DEFAULT_BASE_URL)


def _write_key(api_key: str) -> None:
    """把 key 写回 skill 自己的 mcp_config.json（跟着 skill 走，与 CLI 目录无关）。"""
    global API_KEY
    API_KEY = api_key
    cfg = json.loads((_HERE / "mcp_config.json").read_text(encoding="utf-8"))
    cfg["api_key"] = api_key
    (_HERE / "mcp_config.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def register_anonymous() -> dict:
    """匿名注册：第一次使用自动调用，无需用户名密码。成功后自动写回 key。"""
    if BASE_URL:
        import requests
        resp = requests.post(f"{BASE_URL}/register/anonymous", json={}, timeout=30)
        resp.raise_for_status()
        result = resp.json()
    else:
        sys.path.insert(0, str(_HERE.parent))
        from service.auth import register_anonymous as _ra
        result = _ra()
    if result.get("ok"):
        _write_key(result["api_key"])
    return result


def register(username: str, password: str) -> dict:
    """实名注册（付费绑定时用）：创建账号 + 签发免费 key，自动写回 mcp_config.json。"""
    payload = {"username": username, "password": password}
    if BASE_URL:
        import requests
        resp = requests.post(f"{BASE_URL}/register", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
    else:
        sys.path.insert(0, str(_HERE.parent))
        from service.auth import register as _register
        result = _register(username, password)
    if result.get("ok"):
        _write_key(result["api_key"])
    return result


def verify(company_code: str = "", company_name: str = "", metric_name: str = "",
           report_period: str = "2024-12-31", reported_value: float = None,
           source_name: str = "", scope: str = "metric") -> dict:
    """统一入口：按参数自动分派（调用方不需要知道内部有几个引擎）。

    两种用法：
      1. 单指标校验（默认）：给出 metric_name + reported_value
         verify(company_code="601012", company_name="隆基绿能",
                metric_name="归母净利润", report_period="2024-12-31",
                reported_value=-8592102400.42, source_name="akshare")
      2. 三大报表勾稽复核：只给公司 + 报告期，不给指标
         verify(company_code="600519", company_name="贵州茅台",
                report_period="2024-12-31", scope="statements")
         （或省略 scope——不传 metric_name/reported_value 时自动进勾稽模式）

    返回：{ok, ...}，两种模式字段不同（metric: verdict/confidence/reference；
          statements: checks/all_pass/failed_count）。
    """
    # 自动分派：没给指标和数值 → 勾稽复核
    if scope == "metric" and not metric_name and reported_value is None:
        scope = "statements"

    if scope == "statements":
        return _verify_statements(company_code, company_name, report_period)
    return _verify_metric(company_code, company_name, metric_name,
                          report_period, reported_value, source_name)


def _ensure_key() -> str:
    """第一次使用（空 key / 占位符）→ 自动匿名注册，一次性走完，无需用户输入。"""
    global API_KEY
    if not API_KEY or API_KEY == "your-alioth-key":
        reg = register_anonymous()
        if not reg.get("ok"):
            return ""
        API_KEY = reg.get("api_key", API_KEY)
    return API_KEY


def _verify_metric(company_code: str, company_name: str, metric_name: str,
                   report_period: str, reported_value: float, source_name: str) -> dict:
    """校验一个财务指标是否正确（内部函数，外部走 verify() 统一入口）。"""
    if not _ensure_key():
        return {"ok": False, "error_code": "register_required",
                "error": "匿名注册失败，请手动调用 register(username, password)"}

    payload = {
        "api_key": API_KEY, "company_code": company_code,
        "company_name": company_name, "metric_name": metric_name,
        "report_period": report_period, "reported_value": reported_value,
        "source_name": source_name,
    }

    if BASE_URL:
        import requests
        resp = requests.post(f"{BASE_URL}/verify_metric", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    # 本地开发模式：skill 在 alioth-engine 项目内时，直接 import 引擎
    sys.path.insert(0, str(_HERE.parent))
    from service.server import verify_metric as _verify
    return _verify(API_KEY, company_code, company_name, metric_name,
                   report_period, reported_value, source_name)


def _verify_statements(company_code: str, company_name: str, report_period: str) -> dict:
    """三大报表勾稽复核（内部函数，外部走 verify() 统一入口）。

    不需要 api_key（勾稽是纯算术，100% 确定性，免费开放）。
    """
    payload = {"company_code": company_code, "company_name": company_name,
               "report_period": report_period}
    if BASE_URL:
        import requests
        resp = requests.post(f"{BASE_URL}/verify_statements", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()

    sys.path.insert(0, str(_HERE.parent))
    from service.server import verify_statements as _verify
    return _verify(company_name, company_code, report_period)


def verify_doc(report_text: str) -> dict:
    """文档核验：paste 一份研报/文档全文 → 抽取所有财务数字 → 值层核验 + 文档内部勾稽。

    两层结果：
      results          每个数字对不对（对基准，含正确值 + 溯源）
      doc_articulation 文档自述科目勾稽（文档自己跟自己对不对得上——
                       AI 生成文档常「每个数都对、拼在一起断裂」）
    """
    if not _ensure_key():
        return {"ok": False, "error_code": "register_required",
                "error": "匿名注册失败，请手动调用 register(username, password)"}
    payload = {"api_key": API_KEY, "report_text": report_text}
    if BASE_URL:
        import requests
        resp = requests.post(f"{BASE_URL}/verify_report", json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()
    sys.path.insert(0, str(_HERE.parent))
    from service.api import verify_report as _vr
    class _Req:  # 本地模式直接构造请求对象
        api_key = API_KEY
        report_text = report_text
    return _vr(_Req())


if __name__ == "__main__":
    print("Alioth 确定性校验 skill —— 请在 AI 客户端里调用 verify() 函数，"
          "或参考 SKILL.md 用法。")
