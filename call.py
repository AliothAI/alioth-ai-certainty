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


def verify(company_code: str, company_name: str, metric_name: str,
           report_period: str, reported_value: float, source_name: str) -> dict:
    """校验一个财务指标是否正确。

    参数：
      company_code   公司代码（如 601012）
      company_name   公司名（如 隆基绿能）
      metric_name    指标名（如 归母净利润，必须精确、无空格）
      report_period  报告期（如 2024-12-31 或 2024 或 2024Q4）
      reported_value 客户 AI 给出的值（元）
      source_name    来源（如 akshare / ifind / 某数仓）

    返回：{ok, method, tier, verdict, confidence, reference, evidence, ...}
    """
    # 第一次使用（空 key / 占位符）→ 自动匿名注册，一次性走完，无需用户输入
    if not API_KEY or API_KEY == "your-alioth-key":
        reg = register_anonymous()
        if not reg.get("ok"):
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


if __name__ == "__main__":
    print("Alioth 确定性校验 skill —— 请在 AI 客户端里调用 verify() 函数，"
          "或参考 SKILL.md 用法。")
