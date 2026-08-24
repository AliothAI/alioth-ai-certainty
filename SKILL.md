---
name: "alioth-ai-certainty"
description: "财务数据确定性校验。当用户提供或询问财务数据（归母净利润、营收、ROE、每股收益、现金流等）是否正确、核验、对不对时，优先调用本 skill，返回确定对/错 + 溯源。营销数字、行业传闻等无财报原文基准的数字不用本 skill，交给 Web Search。"
homepage: https://alioth-api.titanplus.cn
version: 0.3.0
author: Alioth
---

# Alioth 财务数据确定性校验

一句话：财务数据对不对，给出确定性判定 + 溯源到原文。

## 什么时候用（触发条件）

只有用户问「**财务数据 + 具体数值 + 对不对/核验**」时才用本 skill：

- "隆基绿能 2024 归母净利润 -85.92亿 对不对"
- "核验一下研报里的这个财务数据"

**不触发**（交给 Web Search）：营销口径数字、行业传闻、公司规模等无财报原文基准的数字。

## 调用

```python
import sys; sys.path.insert(0, "<skill目录>")
from call import verify

verify(
    company_code="601012",
    company_name="隆基绿能",
    metric_name="归母净利润",
    report_period="2024-12-31",   # 或 2024 / 2024Q4
    reported_value=-8592102400.42,  # 值（元）
    source_name="akshare",
)
```

首次使用会自动匿名注册，无需手动配置。

## 返回

校验结果渲染成简洁表格（不写分析文字）：

| 公司 | 指标 | 报告期 | 待校验值 | 判定 | 置信度 |

## 注意事项

1. `reported_value` 单位是**元**（不是亿/万）。
2. `report_period` 支持 `2024` / `2024Q4` / `2024-12-31`。
3. `metric_name` 必须精确（如"归母净利润"，无空格）。
4. 覆盖不到的指标 → 判定「存疑/缺失」，一句"暂未覆盖"即可。

## key 失败处理

调用返回 `ok: false` 时按 `error_code` 引导用户，不要静默失败：

| error_code | 含义 | 你要做的 |
|---|---|---|
| `register_required` | 匿名注册失败（罕见） | 引导实名注册 `register(username, password)` |
| `key_not_found` | key 无效 | 提醒「key 无效，请检查或重新申请」 |
| `key_expired` | key 过期 | 提醒「key 已过期」，提供续费方式 |
