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
| **SEARCH_GUIDE.md** | 检索手册：各部门必查信源、检索象限、品牌哨兵、筛选要点 | 抓某部门前连同 AGENTS 一起读 |
| **PLAYBOOK.md** | 执行剧本：子 agent 切分、prompt 模板、SOP、harvest 格式 | 实际抓取时照着跑 |
| **merge.py** | 增量合并脚本：harvest 新料并池 + 去重 + 滚动淘汰 + 标 firstSeen（增量模式核心） | 增量模式写完 harvest.json 后跑 `python3 merge.py harvest.json` |
| **validate.py** | 自检脚本（结构契约） | 写完 data.json 跑 `python3 validate.py` |
| **linkcheck.py** | 死链检测（链接真实性，需 requests） | 提交前跑 `python3 linkcheck.py`，死链必处理 |
| **archive.py** | 每日归档：生成 archive/data-<日期>.json + 重建 manifest.json | 提交前跑 `python3 archive.py` |
| `data.json` | 前端读取的默认数据源（=最新一天副本） | 每日产出 |
| `manifest.json` / `archive/` | 历史日历：日期清单 + 各日归档文件 | archive.py 自动维护 |
| `index.html` | 静态前端 | 基本固定，少改 |

## 日常操作（每日更新 SOP 摘要）

> **默认走「🟢 增量滚动池」模式**（2026-06-25 起）：data.json 是持续滚动的池子，不是每天重抓的快照。每天只补近 2 天新料、自动淘汰超期旧料，token/耗时砍到约 1/5～1/10。全量重抓降级为兜底（首次建池/长期没跑/口径大改时才用）。详见 `PLAYBOOK.md` 第〇节。

完整步骤见 `PLAYBOOK.md`，速记（增量模式）：
1. 读 README + PROJECT_STATUS（带上下文）
2. 以上一版 data.json 为基础池，按 PLAYBOOK 派子 agent **只抓近 2 天新料**（带 AGENTS.md 铁律 + SOURCES.md 信源）
3. 把新料汇成 `harvest.json`（格式见 PLAYBOOK 第九节）→ `python3 merge.py harvest.json`（自动并池/去重/淘汰/标 firstSeen/重排）
4. `python3 validate.py` 自检全过 + `python3 linkcheck.py`（聚焦本轮新增链接）
5. `python3 archive.py` 归档当天数据 + 重建 manifest
6. 更新 PROJECT_STATUS.md 状态表 + SOURCES.md 实测标记
7. `git add -A && git commit && git push` → 自动部署

## 6 个部门（顺序固定，不可改）

`nutri 营养保健 / pharma 医药 / device 医疗器械 / consumer 消费器械 / instant 即时零售 / medical 消费医疗`

## 联系人

战略与综合支持部出品 / 咨询：wangchunhao.7、xiaoyuyan3

---

_注：除仓库文档外，Claude 在本项目目录下还有一份"记忆"（用户配置目录，不进 git），用于跨会话快速进入状态。即使记忆丢失，仅凭本仓库文档也能完全恢复工作。_
