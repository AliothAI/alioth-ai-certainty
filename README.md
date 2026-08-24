# Alioth AI Certainty Skill

以巨潮财报原文为唯一基准，校验财务数据「对不对」——确定对/错 + 溯源到年报原文 + 100% 置信。

> **all in one for AI certainty**（当前聚焦金融数据）

## 安装

把本目录复制到 AI 客户端的 skills 目录：

**Claude Code**
```bash
cp -r alioth-ai-certainty ~/.claude/skills/
```

**Cursor**：复制到 Cursor 的 skill 目录（或直接导入本文件夹）。

## 使用

第一次使用会**自动匿名注册**（零输入），之后直接在 Claude Code / Cursor 里问：

> 「隆基绿能 2024 归母净利润 -85.92亿 对不对」

返回确定性判定表格（对/错 + 正确值 + 溯源），不写分析文字。

## 文件说明

| 文件 | 说明 |
|---|---|
| `SKILL.md` | skill 定义（触发词、用法） |
| `call.py` | Python 客户端 |
| `call-node.js` | Node.js 客户端（零依赖，推荐） |
| `mcp_config.json` | 配置（首次使用自动填充 key） |

## 服务地址

默认 `https://alioth-api.titanplus.cn`。本地调试可在 `mcp_config.json` 覆盖 `base_url`。

## 覆盖指标

当前聚焦「归母净利润」，支持常见财务指标（营收 / ROE / 每股收益 / 现金流等陆续扩展）。

## 免费

研究员免费看全量（正确值 + 溯源 + 多源交叉），无需付费。付费点在机构版（团队数据质量管控），与 CLI 无关。
