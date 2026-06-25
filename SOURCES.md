# 情报信源地图（SOURCES.md）

> 实测沉淀的"哪个源真出料"资产。与 `AGENTS.md`（工作手册）并列，抓取前先查这里少走弯路。
> 标记：★=实测出过料的优质源　✗=实测失效/不可用　⚠=可用但有坑
> 最后更新：2026-06-24（首版，consumer 6品类实抓验证）

---

## 一、通用工具行为与绕过技巧（所有部门通用）

- ⚠ **web_search 把"2026年X月"误判为未来而拒答** → 去掉年份，改用「近期 / 最新 / 618 / 一季报」等关键词重试。**最高频的坑**。
- ⚠ **web_search 有时只返回模型泛化话术、无真实链接** → 改用 WebFetch 抓 `html.duckduckgo.com/html/?q=关键词` 检索页，再逐条 fetch 原文核日期。更可靠。
- ✗ **Bing 新闻页 / 品牌官网新闻页（Alcon、Bausch 等）** → 常返回 JS 空壳或 404，抓不到正文。换垂直媒体或官方公告。
- ✗ **亿邦动力 618 频道页** → HTTP 403。
- ⚠ **含手机号的页面**（部分中华网/网易号）→ 触发敏感词拦截。`zqrb.cn / ce.cn` 偶发 504；`toutiao` 正文需 JS 渲染抓不到。
- 🆕 **WebFetch 抓某个具体 url 失败时的兜底：Jina Reader**。在原 url 前拼 `https://r.jina.ai/`（如 `https://r.jina.ai/https://www.toutiao.com/article/xxx`）再 WebFetch。它会**渲染 JS、绕过多数反爬，返回干净 Markdown 正文**，专治头条/JS 空壳/403 这类老大难。零成本、无需 key。**仅用于"我已知具体 url、但抓不到正文"的场景**，不替代 web_search 发现信源。抓到正文后日期/事实仍按铁律核验。
- 原则：任一源 fetch 失败 → 用其他独立源交叉核日期与事实；**核不到就丢弃，绝不用记忆补**。

---

## 一·五、RSS / 直连源清单（2026-06-24 实测，抓取时优先直连，跳过搜索引擎拒答坑）

> 用法：本站是静态站、无服务端订阅。RSS 的用法是**抓取时直接 fetch 这些 feed**，比 web_search 稳。
> fetch RSS 用带 UA 的请求（`Mozilla/5.0`），部分源裸连会 403。实测均为当日最新内容、新鲜度好。

**✅ 可用 RSS feed（已验证返回当日内容）**：
| 源 | feed 地址 | 服务维度 |
|---|---|---|
| FierceBiotech | `https://www.fiercebiotech.com/rss/xml` | 医药 新品/工业（约25条/次）|
| Endpoints News | `https://endpts.com/feed` | 医药 新品/BD（注意是 `/feed` 无斜杠，`/feed/` 会301）|
| BioPharma Dive | `https://www.biopharmadive.com/feeds/news/` | 医药 工业/融资 |
| MedTech Dive | `https://www.medtechdive.com/feeds/news/` | 医疗器械 工业/新品 |
| Crunchbase News | `https://news.crunchbase.com/feed/` | 跨部门 融资 |
| Sifted | `https://sifted.eu/feed` | 跨部门 欧洲融资 |
| 36氪 | `https://36kr.com/feed` | 即时零售/跨部门 行业·资本（约11条，当日刷新）|

**⚠ 无 RSS 但 HTTP200 可直接 fetch HTML 列表页解析**：
- 动脉网 `https://www.vbdata.cn/`（器械/消费医疗 新品·融资主力源）
- 36氪快讯 `https://36kr.com/information/web_news/`
- NMPA 要闻列表 `https://www.nmpa.gov.cn/yaowen/ypjgyw/index.html`（官方，无feed，直接抓列表页）
- CDE/各官方站：基本无 RSS，走列表页 fetch 或站内检索

**✗ feed 失效/反爬（别浪费时间试 RSS，改用搜索或列表页）**：
- MassDevice `/feed/` → 403　｜　MobiHealthNews `/rss.xml` → 403
- Medical Device Network `/feed/` → 连接失败　｜　虎嗅 `/rss/0.xml` → 失败
- NutraIngredients / Nutraceuticals World → 301/403（走站内或搜索）
- 晚点 LatePost → 无公开 RSS（走官网 `latepost.com` 列表页 fetch）
- 创业邦 `rss.cyzone.cn` → 返回非XML（走官网列表页）

> 维护：发现新可用 feed 或某 feed 失效，回填本表。RSS 不是必须，是"能省事就省事"的加速层；核心仍是 fetch 原文核日期。

---

## 二、通用权威源（跨部门，最高优先级）

| 源 | 用途 | 备注 |
|---|---|---|
| ★ NMPA 国家药监局 | 器械/药品注册、获批、飞检、通告 | 器械查询系统直接检索获批比搜索引擎靠谱 |
| ★ 国家医保局 | 医保政策、目录、个账白名单 | 2026-06 械字号面膜新政即出自此 |
| 市场监管总局 / 海关总署 | 监管整治、跨境、抽检 | 近视防控镜核查出自市监 |
| ★ 巨潮资讯 / 港交所 / 北交所 | 上市公司公告、财报、IR | 财报与重大事项第一手 |
| ★ 东方财富 / 证券时报 / 智通财经 / 中财网 / 证券之星 | 财报与公告转载 | 出料稳，日期可核 |
| 医药魔方 ByDrug / 药智网 | 新药/器械研发与获批 | 药智注册页偶发加载失败 |

---

## 三、消费器械（consumer）6 品类信源（已实测）

### 隐形眼镜·美瞳（深抓）
- **品牌方**：海昌、博士伦(Bausch)、视康·强生 Acuvue、爱尔康 Alcon、Moody、可糖、可啦啦、4inLook
- ★ **前瞻产业研究院** `xw.qianzhan.com` —— 渠道格局/平台份额数据很硬（淘系/抖音/京东占比、美瞳增速均出自此）
- ★ **NMPA / 中国质量新闻网** —— 软性亲水接触镜三类注册证批准目录
- ⚠ 爱尔康/博士伦官网新闻页抓不到；财报走 investing.com 等转载纪要

### 医美敷料 / 疤痕修复（深抓）
- **品牌方**：巨子生物(可复美)、敷尔佳、创尔生物(创福康)、锦波生物(重组胶原蛋白原料龙头)、珀莱雅(械字号跨界)
- ★ **港交所/A股/北交所公告 + 东方财富/证券时报/智通财经/中财网** —— 财报、派息、经营范围变更、高管变动
- ★ **国家医保局** —— 械字号面膜医保个账新政（对本品类影响最大）
- 青眼 / 聚美丽 —— 美妆械字号行业动态
- ⏳ **618 医用敷料细分战报通常 7 月初**才由青眼/星图/蝉妈妈放出，届时补抓

### 成人情趣（深抓）
- **品牌方**：杜蕾斯(利洁时)、冈本、杰士邦(人福医药/现 ST 人福)、网易春风、大象、Svakom、春水堂
- ★ **人福医药公告** —— 杰士邦母公司财报与重大事项
- ★ **艾瑞网** —— 天猫 618 成人计生类目战报
- ★ **每经网 / 中华网** —— 安全套新品（如杰士邦仿生皮）
- 地方药监 —— 二类器械经营备案、抽检、国标修订(CNS/TBT 通报)
- ⚠ 抖音/拼多多/美团成人计生类目隐私品类**普遍不单列战报**，抓不到属正常；措辞专业克制
- ✗ 博禾医生 等源偶发 HTTP 521

### 康复理疗 / 中医器械 / 视力辅助（补充，料稀薄）
- **品牌方**：SKG/未来穿戴(港股冲刺中)、倍轻松、攀高、奥佳华、翔宇医疗(中医艾灸设备)
- 新浪科技 —— 未来穿戴 IPO 进展
- 市监总局 / 各地药监 —— 近视防控镜核查、视知觉训练软件无证查处
- ⚠ **教训**：这 3 类绝大多数搜索结果是选购指南/测评榜单/趋势盘点，按反软文铁律会大量丢弃。直接查 NMPA 器械查询系统获批更高效。本轮窗口内基本无合格硬料属正常。

---

## 四、其他 5 部门信源（来自业务周报 prompt，详细检索方法见 SEARCH_GUIDE.md）

> 下列为各业务人工沉淀的必查信源。完整检索象限/品牌哨兵/筛选要点见 `SEARCH_GUIDE.md`。实测标记（★出料/✗失效）待对应部门重抓后回填。

- **医药 pharma**：
  - 国内：医药魔方 ByDrug、丁香园 Insight、药智网、咸达数据、CDE/NMPA
  - 美国：Endpoints News、FierceBiotech、FDA、药明康德 PDUFA 汇总、BioPharma Dive
  - 辅助：港交所/SEC/上交所公告、医脉通、生物制品圈、E药经理人
- **医疗器械 device**：
  - 新品：NMPA/CMDE 公示、动脉网、医械之家、思宇MedTech、器械之家、健康界；FDA 510(k)/De Novo/PMA、MedTech Dive、MassDevice；Medical Device Network、MedTech Europe；日経メディカル；CMEF/Medica/Arab Health 展后
  - 融资：动脉网、亿欧大健康、36氪医疗、IT桔子、烯牛数据、鲸准、企查查/天眼查；Crunchbase News、MobiHealthNews、Sifted、日経STARTUP
- **营养保健 nutri**：
  - 成品先行：电商上新/DTC官网/社媒/iHerb·Amazon；再查 备案/媒体/原料商
  - 行业媒体：NutraIngredients、Nutraceuticals World；监管：市场监管总局/海关总署
  - 品牌哨兵 Top40 + 海外清单见 SEARCH_GUIDE.md
- **消费医疗 medical**：
  - 国内：NMPA/CMDE、上市公司公告、新氧/美团医美、爱康/美年体检套餐、医美行业媒体、融资新闻
  - 海外：FDA/CE、设备厂商官网、ASDS/AAD/IMCAS 会议、医疗科技融资
- **即时零售 instant**：亿邦动力、36氪、连锁药店公告、中康数据（该业务周报输入待补）
  - **连锁药店经营速览（季度更新）来源**：巨潮资讯 `cninfo.com.cn`（年报/季报/**投资者关系互动·业绩说明会·解读会纪要**）、公司 IR 页、财经媒体财报解读。覆盖/优势省份、门店增量、毛利率/经营现金流、战略举措多在「**管理层讨论与分析**」与**解读会纪要**里；逐项带 url，查不到不写。
    - 老百姓 603883.SH ｜ 益丰药房 603939.SH ｜ 大参林 603233.SH（**老百姓非 002424，那是贵州百灵**）

---

_维护说明：每轮重抓后，把新验证的"出料源"标 ★、失效源标 ✗ 回填本表。这是项目最值钱的复用资产。_
