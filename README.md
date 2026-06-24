# 京东健康每日竞争情报台

> **新会话/新接手者从这里开始。** 这是项目的唯一入口，告诉你按什么顺序读哪些文件、各自干嘛、日常怎么操作。

## 这是什么

京东健康（JDH）每日竞争情报台。每天为 6 个业务部各产出"今日动态情报"，写入 `data.json`，由 `index.html`（纯静态前端）展示。
**核心铁律：只报真实抓取到、带可点开 url 的内容，绝不编造链接/数字/事件。**

- 线上地址：https://jdh-intel.netlify.app/
- 部署：push 到 GitHub `main` 分支 → Netlify 自动部署，约 1 分钟生效。

## 🚪 快速进入状态（新对话只需一句话）

在新对话里说：**「读 README.md 和 PROJECT_STATUS.md，我们继续」** 即可让我完整进入状态。

## 文件地图（按重要性排序）

| 文件 | 定位 | 什么时候读 |
|---|---|---|
| **README.md** | 🚪 唯一入口（本文件） | 第一个读 |
| **PROJECT_STATUS.md** | 当前进展 / data.json 状态 / 待办 | 第二个读，了解"现在到哪了" |
| **AGENTS.md** | 口径权威：6 部门配置、数据契约、质量铁律 | 抓取/改口径前必读 |
| **SOURCES.md** | 信源地图：哪个源出料、工具坑、绕过技巧（**信源唯一权威**） | 抓取前查，少走弯路 |
| **PLAYBOOK.md** | 执行剧本：子 agent 切分、prompt 模板、SOP | 实际抓取时照着跑 |
| **validate.py** | 自检脚本 | 写完 data.json 跑 `python3 validate.py` |
| `data.json` | 前端读取的唯一数据源 | 每日产出 |
| `index.html` | 静态前端 | 基本固定，少改 |

## 日常操作（每日更新 SOP 摘要）

完整步骤见 `PLAYBOOK.md`，速记：
1. 读 README + PROJECT_STATUS（带上下文）
2. 按 PLAYBOOK 派子 agent 抓取（带 AGENTS.md 全套铁律 + SOURCES.md 信源）
3. 汇总去重 → 按时效剔除超期 → 写入 data.json
4. `python3 validate.py` 自检全过
5. 更新 PROJECT_STATUS.md 状态表 + SOURCES.md 实测标记
6. `git add -A && git commit && git push` → 自动部署

## 6 个部门（顺序固定，不可改）

`nutri 营养保健 / pharma 医药 / device 医疗器械 / consumer 消费器械 / instant 即时零售 / medical 消费医疗`

## 联系人

战略与综合支持部出品 / 咨询：wangchunhao.7、xiaoyuyan3

---

_注：除仓库文档外，Claude 在本项目目录下还有一份"记忆"（用户配置目录，不进 git），用于跨会话快速进入状态。即使记忆丢失，仅凭本仓库文档也能完全恢复工作。_
