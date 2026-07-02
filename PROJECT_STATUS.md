# 项目状态与交接文档（PROJECT_STATUS）

> 本文件用于跨会话接续。新会话只需带上 `AGENTS.md`（工作手册）+ 本文件，即可无缝继续，不依赖历史对话记忆。
> 最后更新：2026-07-02（**增量更新：距上次(6/25)7天，走增量+窗口放宽到8天(N+1)，5个Sonnet子agent只抓6/24后新料。本轮新增16条/淘汰24条超期。硬料集中在pharma(和誉×礼来19亿BD、557医保初审、谈判药退保)与device(可孚增持、微泰618CGM+157%、三诺创新审查)；instant三平台反内卷共识+老百姓业绩会；nutri窗口内无合格新料如实留空不注水。淘汰偏多因7天未跑、一批6/2前老料集中过30天线**）

## 1. 这是什么项目

京东健康（JDH）每日竞争情报台。每天为 6 个业务部各产出一份"今日动态情报"，汇总写入 `data.json`，由 `index.html`（纯静态前端）读取展示。
- 角色与规则：见 `AGENTS.md`（权威工作手册，以它为准）。
- 核心铁律：**只报真实抓取到、有可点开 url 的内容；绝不编造、绝不杜撰链接。**

## 2. 文件清单

| 文件 | 作用 | 谁维护 |
|---|---|---|
| `README.md` | **唯一入口**：文件地图、快速进入状态、日常SOP摘要 | 结构变更时改 |
| `AGENTS.md` | 工作手册：部门配置、数据契约、质量护栏 | 人工（口径变更时改） |
| `SOURCES.md` | 信源地图：有效/失效源、工具坑、绕过技巧（信源唯一权威） | 每轮重抓后回填实测标记 |
| `SEARCH_GUIDE.md` | 检索手册：各部门必查信源、检索象限、品牌哨兵、筛选要点 | 业务口径/信源沉淀时更新 |
| `PLAYBOOK.md` | 执行剧本：子agent切分、prompt模板、SOP、harvest格式 | 流程优化时改 |
| `merge.py` | 增量合并：harvest新料并池+去重+滚动淘汰+标firstSeen+重排（增量模式核心） | 合并逻辑/淘汰窗口变更时改 |
| `validate.py` | data.json 结构自检脚本 | 契约变更时改 |
| `linkcheck.py` | 死链检测脚本（链接真实性护栏，需 requests） | 分级逻辑变更时改 |
| `archive.py` | 每日归档脚本：生成 archive/data-<日期>.json + 重建 manifest.json | 数据流变更时改 |
| `data.json` | 每日情报数据（前端默认数据源 = 最新一天副本） | 每天由 agent 抓取生成 |
| `newproducts.json` | 新品周报（5 部门新品），前端新品区读取；用户每周提供后整份替换，merge/archive 不碰 | 每周手动替换 |
| `profiles.json` | 连锁药房季度静态档案（省份/财报/战略），前端折叠对比表读取；merge.py 不碰、不归档 | 财报季手动更新 |
| `manifest.json` / `archive/` | 历史日历：日期清单（倒序）+ 各日归档文件 | archive.py 自动维护 |
| `index.html` | 前端展示（静态，`fetch('data.json')`） | 基本固定，少改 |
| `PROJECT_STATUS.md` | 本交接文档 | 每轮收尾时更新 |
| `.claude/launch.json` | 本地预览配置（node `npx serve` 起 8765 端口） | 固定 |

## 3. 数据契约要点（前端按此严格读取，字段/层级不能改）

- 顶层：`{ "generated": "YYYY-MM-DD", "depts": [...] }`
- **【2026-06-25 新增】历史日历归档**：根 `data.json` = 最新一天副本（前端默认&兜底都读它）；历史在 `archive/data-<日期>.json`；`manifest.json = {dates:[新→旧], latest}` 是前端日期选择器数据源。三者由 `python3 archive.py` 自动维护，**必须随每日 push 进 git**。前端 manifest 加载失败时自动回退读 data.json（老入口/旧缓存兼容）。
- `depts` 固定 6 个、顺序固定：`nutri / pharma / device / consumer / instant / medical`
- 每个 dept：`{id, name, dims[], brief}`；`brief = {lead, musts[], sections[]}` 或 `null`
- `musts`：跨维度挑 3 条最重要（优先 hi），字段 `{dim, rel, title, note, url}`
- `sections`：按维度顺序排（竞对动态在最前）；每个 `{dim, items[]}`
- `item` 字段：`{title, rel(hi/mid/lo), summary(≤60字), source, date, url, takeaway}`
- 维度内 `items` 按日期从新到旧排；无料维度 `items: []`（前端显示"今日暂无最新动态"）
- 6 部门维度集：前 5 个用「竞对动态/政策动态/工业动态/新品动态」；**即时零售 instant 用「竞对动态/政策动态/新技术·新模式/行业·资本」**
- **【2026-06-25 新增】增量滚动池（阶段B/C）**：① 每条 item 可带可选字段 `firstSeen`（首次入池日期，merge.py 自动维护，不手写）；② 前端据 `firstSeen===generated` 显示「🆕今日新增」徽标 + 置顶 + 卡片高亮，统计栏改为「滚动情报池 / 🆕今日新增置顶」，空维度文案改「今日无新动态」。全量模式产出无 firstSeen 也合法（当天不亮🆕）。merge.py/harvest 详见 PLAYBOOK 第九节。
- **【2026-06-24 新增】即时零售 instant 竞对动态已卡片化**：`brief.layout="instant"`，竞对 section 用 `layers`（O2O 2卡 + 连锁药店 3卡，连锁卡含财报小卡 `financials.periods`），不再用 `items`；其余 3 维度与其他 5 部门仍用普通 `items`。精确契约见 `AGENTS.md`「即时零售专属结构」段落。
- **【2026-06-25 新增】医药 pharma 竞对也卡片化**：`brief.layout="pharma"`，竞对 section 用 `layers`（单层、2 卡：阿里健康 + 美团买药，无财报小卡）。**美团买药卡与 instant 部门同源同数据**。政策口径扩为医保局+卫健委+药监局；工业按 26 品牌 watchlist 抓取、上限放宽到 ~5 条。layers 校验已通用化（任何部门有 layers 即走 check_layers）。
- **【2026-06-26 v2 改造】呈现优化 + 数据分层**：
  - **`lead` 字段废弃**：`brief` 不再写 lead，导读由「今日必读」承担（前端不渲染 lead，旧归档残留兼容）。
  - **今日必读判据明文化**：`rel=hi` 且满足（有行动窗口/竞对已落地/赛道结构变化）之一；`note` 写"对 JDH 的具体动作含义"。
  - **政策 `effective` 字段（可选）**：政策类 item 可带真实生效日，前端渲染"⏳距生效 N 天 / ✅已生效"徽标。**只在确有生效日时填，不编造**。
  - **连锁经营档案迁出到 `profiles.json`**：省份/财报/战略从 data.json 连锁卡的 `financials` 迁到独立季度档案 `profiles.json`（merge.py 永不碰、archive.py 不归档、历史日也读当前态）。前端在即时零售「今日必读」后渲染**可折叠三家对比表面板**。连锁竞对卡只剩动态流。`coverage` 统一为 `{count, advantage}`、`strategy` 标 `source`（MD&A/投资者交流）。
  - **归类去重护栏#12**：行业大盘/赛道数据只进「行业·资本」，竞对卡只放该对手自己的动作。
  - **连锁动态流去财务噪音**：派息/可转债/评级/权益分派不进 items（属档案财务面）。
- **【2026-06-26 新品改周报挂载】三层数据架构成型**：
  - 新品（具体新品/获批）**不再日抓**，改为接用户每周「新品周报」整份挂载到 `newproducts.json`，保持一周。
  - 5 部门（nutri/pharma/device/consumer/medical）新品区前端从 newproducts.json 读，显示"📅 新品周报·更新于X"徽标；data.json 新品 section 保留但 items 恒空。
  - merge.py 跳过新品维度、archive.py 不归档 newproducts、validate.py 加 check_products 校验。
  - 首期已迁现有 13 条（nutri 4/pharma 1/device 4/consumer 1/medical 3）。
  - **三层架构**：快流 data.json（日更，merge 滚动）/ 中流 newproducts.json（周更，整份替换）/ 慢流 profiles.json（季度，手动）——按更新频率分层，各走各的维护节奏。
- **【2026-06-26 v3 呈现改造：竞对卡等高 + 连锁档案重构 + 全球新品雷达】**（纯前端+数据文件，不碰抓取链路）：
  - **竞对卡等高**：`.ccard` 改定高 330px 的 flex 列布局（header 固定、`.cc-feed` flex 撑满内部滚动），pharma/instant 所有竞对卡统一高度、溢出滚动。
  - **连锁经营档案重构**：从「今日必读后的横向三家对比表」改为「**连锁动态卡下方、每家一张可展开卡片**」。`renderChainPanel()`→`renderProfileCards(deptId)`（泛化读 `PROFILES[deptId].chains`，为其他部门建档铺路）。每卡含：两期财务小表（2025年报+2026Q1，**数字右对齐** `.pf-v text-align:right`）、覆盖省份（列具体省名+优势省绿底高亮）、战略详情（`strategyDetail` 分段可滚动 max-height:230px）、纪要。
  - **profiles.json 扩字段**：`coverage` 加 `provinces[]`/`advProvinces[]`（用户提供：老百姓18省/9优势、益丰10/6、大参林21/4；修正了用户名单两处笔误——老百姓"山西"重复→改"陕西"、大参林"附件"→"福建"）；新增 `strategyDetail:[{h,items[]}]` 承接三家大段战略（业绩说明会/投资者交流口径）。
  - **全球新品雷达**：新品维度前端展示名改「🛰️ 全球新品雷达」（数据契约 key 仍是「新品动态」不变）。新品卡升级为周报样式：京东/自营在售徽标（`jd`/`zy`=有绿/无红/待核灰）+ `tags[]` + `watch:true` 归到底部「⚠️ 提示关注」分组 + 部门 `deptSummary` 本周小结。
  - **newproducts.json 整份替换为周报第2期**（截至0618，22条）：nutri5/pharma3/device3/consumer1/medical10，扩 `week/deptSummary` + 每条 `jd/zy/tags/watch`。周报「整体Top5/一句话总览」按部门渲染下不展示（已与用户确认取舍）。
  - **validate.py 同步**：`check_products` 放宽 summary 长度（周报为原文概述）+ 校验 jd/zy/tags 可选字段；`check_profiles` 加 coverage.provinces/advProvinces + strategyDetail 校验。全过。

## 4. 时效口径（已固化，分级）

- **近 30 天**（≥抓取日前30天）：财报、重要政策法规/监管新规、重大 BD/收购，**以及竞对动态**（平台级动作不密集，卡7天会经常空）。
- **近 7 天**：新品、普通行业动态、营销活动等一般动态。
- 明显超期 → 直接删，不用"仅供参考"保留。
- hi/mid 重点条目必须再 fetch 原文确认确切日期，尽量消除"待核"。
- 新品维度只收"具体新品/新成分/新配方/新获批产品"；趋势/盘点/展会预告/榜单/指南一律不收；首轮空必须去垂直信源再深挖一轮才可留空。

## 5. 当前 data.json 状态（2026-07-02，增量滚动池；新增16淘汰24，现存约67条含卡内动态）

| 部门 | 竞对 | 政策 | 工业 | 新品 | 备注 |
|---|---|---|---|---|---|
| nutri 营养保健 | 5 | 1 | 5 | 0 | 窗口内无合格新料(硬料均在6/24前);淘汰2条超期政策 |
| pharma 医药 | 2卡(阿里健康+美团) | 4 | 4 | 0 | 🆕和誉×礼来19亿BD;🆕557医保初审;🆕8种谈判药退保;中成药再注册大限 |
| device 医疗器械 | 8 | 2 | 5 | 0 | 🆕可孚增持回购;🆕微泰618CGM+157%/线下试戴;🆕三诺血糖血酮创新审查;联影国债招标 |
| consumer 消费器械 | 4 | 2 | 7 | 0 | 🆕化妆品新原料新规(7/15);🆕敷尔佳增线上信息服务;🆕重组胶原赛道分化 |
| instant 即时零售 | 5卡(O2O 2+连锁 3) | 1 | 0(新技术) | 4(行业资本) | 🆕三平台反内卷五项共识;🆕老百姓业绩会四驾马车;🆕即时零售618增速10倍 |
| medical 消费医疗 | 2 | 1 | 3 | 0 | 🆕华熙二代娃娃针Q3获批指引;淘汰3条超期竞对 |

> **【2026-06-25 增量滚动池全落地】** 默认模式已从"每天全量重抓30天"改为"**增量滚动池**"(只抓近2天新料+merge并池+滚动淘汰),解决token高+单轮1.5h痛点(详见第7节+PLAYBOOK第〇节)。阶段A(流程)/B(`merge.py`自动并池去重淘汰标firstSeen)/C(前端🆕今日新增分层)全部落地。基础池已从24号归档回填27条真实料补全(~100条),为26号增量打更全底座。

> **【2026-06-25 新增铁律：不放京东健康自家动态】** 所有维度只报竞对/行业/上游/政策,绝不收以京东健康自己为主角的新闻(京东作为竞争格局被对比的一方提及可留;主角是京东自己→删)。已写入 AGENTS.md 护栏#9 + PLAYBOOK 两个prompt模板。本轮已删除1条(instant"京东AI药师99.6%")。

> **历史遗留(下轮注意)**:卫健委处方流转/互联网诊疗近30天无独立新政;益丰/大参林2026问答纪要官方未公开(memo用业绩说明会通知替代);部分门店增量未逐项拆分。

> **【26号怎么跑】** 用增量模式(PLAYBOOK第〇节SOP+3.1增量prompt模板):以当前data.json为基础池,派子agent只抓近2天新料→汇成harvest.json→`python3 merge.py harvest.json`(先--dry)→validate→linkcheck→archive→push。

> **【2026-06-24 重要变更】消费器械（consumer）业务口径重订**：原口径误为"个护小家电（飞利浦/徕芬/SKG/电动牙刷/美容仪）"，与实际业务严重偏离。已据真实业务范围改写 `AGENTS.md` 第 4 部门段落，现覆盖 6 个品类：①视力辅助 ②隐形眼镜及护理（含美瞳）③康复理疗（护腰/护颈/矫姿）④中医保健器械（艾灸/拔罐/刮痧/足浴）⑤成人情趣（安全套/情趣玩具）⑥医美敷料/疤痕修复（可复美/敷尔佳/硅酮疤痕贴）。抓取按 GMV 体量侧重：隐形眼镜·美瞳 / 医美敷料 / 成人情趣 深抓，其余 3 类补充。

## 6. 抓取经验（踩过的坑，下次直接用）

- **web_search 常把"2026年X月"误判为未来而拒答** → 去掉年份、改用"近期/最新/618"等关键词重试即可绕过。
- **部分页面 fetch 失败**：含手机号的页面触发敏感词拦截（如部分中华网/网易号）；zqrb.cn、ce.cn 偶发超时/504；toutiao 正文需JS渲染抓不到。失败时用其他独立源交叉核验日期与事实，核不到就丢弃，**不要用记忆补**。
- **存疑即删**：无法独立佐证的数字（如曾出现的"Swisse营收49亿超越汤臣倍健"）整条丢弃。
- 优先垂直信源：NMPA、市场监管总局/海关总署、医保局、医药魔方ByDrug、NutraIngredients、各企业公告/IR；通用搜索仅作补充。

## 7. 每日更新流程（SOP）

> **【2026-06-25 重大流程升级：默认改为「增量滚动池」模式，降本增效】**
> data.json 不再是"每天从零重抓的 30 天快照"，而是"**持续滚动维护的池子**"。25 号全量结果=基础池。每天只做增量：继承昨天 → 只抓**近 2 天**新料 → 去重 merge 进池 → 自动淘汰超时效旧料。抓取量砍到约 1/5～1/10，解决 token 高、单轮 1.5h 的痛点；质量不降反升（老料是已核验存量）。**全量重抓降级为兜底**（首次建池/长期>1周没跑/口径大改/疑似池脏时才用）。完整两模式 SOP 见 `PLAYBOOK.md` 第〇节。

**增量模式日常流程**：
1. 新会话带上 `AGENTS.md` + 本文件 + `PLAYBOOK.md`。
2. 以上一版 data.json（archive/ 最新一天）为基础池起点。
3. 派子 agent **只抓近 2 天新料**（漏跑则窗口=间隔天数+1天 buffer），用 PLAYBOOK 3.1 增量 prompt 模板；hi/mid 逐条 fetch 核日期。
4. 新料汇成 `harvest.json`（格式见 PLAYBOOK 第九节）→ `python3 merge.py harvest.json`（自动并池/跨池去重/滚动淘汰超期/标 firstSeen/重排，先 `--dry` 看报告）。
5. `python3 validate.py` 全过 + `python3 linkcheck.py`（聚焦本轮新增链接）+ `python3 archive.py` 归档。
6. `git commit && push` → Netlify 自动部署。
7. 出自检报告：本轮新增 N 条 / 淘汰 M 条 / 各维度现存条数 / 空维度说明 / 失败信源。更新本文件第 5 节状态表。

**纪律**：某维度近 2 天无新料 = 正常，明说"今日无新动态"，绝不注水/扩窗口硬抓。

## 8. 部署信息

- 方式：GitHub 仓库 + Netlify 连接，**push 即自动部署**。
- 站点类型：静态站，无需构建（publish 目录 = 仓库根目录）。
- GitHub 仓库地址：https://github.com/diabolus897/jdh-intel.git （分支 main）
- Netlify 站点名：jdh-intel（原自动名 silly-pasca-14d103）
- **线上网址（发同事内测）：https://jdh-intel.netlify.app/**
- 更新网页 = 改完 data.json 后 git push 即可，约1分钟后线上自动生效。

## 9. 联系人

战略与综合支持部出品 / 咨询：wangchunhao.7、xiaoyuyan3
