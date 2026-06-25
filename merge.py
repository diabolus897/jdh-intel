#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量合并脚本（「增量滚动池」模式的数据侧核心）

把当日「新料」(harvest) 合并进「基础池」(上一版 data.json)，产出新的 data.json：
  - 新料并入对应部门/维度（含卡片化部门的卡内动态流）
  - 跨池去重（url 同 / 标题高度重合 → 留新料内容、保留原 firstSeen）
  - 按时效滚动淘汰超期旧料（新品 7 天、其余维度 30 天，待核日期保留）
  - 给每条标注 firstSeen（本轮首次入池=今天 → 前端"🆕今日新增"高亮）
  - 维度/卡内 items 重排：本轮新增置顶，其余按日期倒序

用法：
  python3 merge.py harvest.json                 # 池=data.json，结果写回 data.json
  python3 merge.py harvest.json --pool X.json --out Y.json   # 自定义池/输出（测试用）
  python3 merge.py harvest.json --dry           # 只打印报告，不写文件

退出码：0=成功；1=harvest/pool 读取失败或 generated 非法。

—— harvest.json 的格式（**只写当日新料，不必复刻整份 data.json**）——
{
  "generated": "2026-06-26",                 # 必填：今天，决定 firstSeen 与淘汰基准
  "leads":  { "nutri": "今日一句话概览", ... },        # 可选：覆盖各部门 brief.lead
  "musts":  { "nutri": [ {dim,rel,title,note,url}, ... ], ... },  # 可选：覆盖各部门 musts(挑3条)
  "add": {                                    # 当日新增条目，按部门→维度
    "nutri":  { "竞对动态": [ item, ... ], "新品动态": [ item, ... ] },
    "instant":{ "竞对动态": { "美团买药":[item], "老百姓":[item] },   # 卡片化维度=按卡名分组
               "政策动态": [ item ] },         # 非卡片化维度=条目数组
    ...
  },
  "financials": { "instant": { "老百姓": { ...经营速览卡... } } }   # 可选：季度才更新
}
item 字段同数据契约：{title, rel, summary, source, date, url, takeaway}（卡内可省 rel/takeaway）。
没有新料的部门/维度可省略；某维度今日无新料就别写它——池里旧料会自动保留+老化。
"""
import json
import os
import sys
import re
import copy
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data.json")

# 滚动淘汰窗口（天）：新品守 7 天，其余维度放宽 30 天（与时效铁律一致）
EVICT_DAYS = {
    "新品动态": 7,
    "竞对动态": 30, "政策动态": 30, "工业动态": 30,
    "新技术·新模式": 30, "行业·资本": 30,
}
EVICT_DEFAULT = 30


def valid_date(s):
    if s == "待核":
        return True
    try:
        datetime.date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def parse_date(s):
    """返回 datetime.date 或 None（待核/非法）。"""
    try:
        return datetime.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def date_sort_key(s):
    d = parse_date(s)
    return d.toordinal() if d else 0


def norm_url(u):
    if not u:
        return ""
    u = str(u).strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#")[0]
    u = u.rstrip("/")
    return u


def norm_title(t):
    if not t:
        return ""
    # 去除标点/空白，仅留中英文数字，用于"同一件事换措辞"判重
    return re.sub(r"[\s\W_]+", "", str(t).lower())


def item_key(it):
    """判重键：优先归一化 url，无 url 用归一化标题。"""
    u = norm_url(it.get("url"))
    if u:
        return "u:" + u
    return "t:" + norm_title(it.get("title"))


def evict_days(dim):
    return EVICT_DAYS.get(dim, EVICT_DEFAULT)


def is_expired(it, today, dim):
    """超期判断：有合法日期且超过该维度窗口 → 淘汰；待核/无日期 → 保留。"""
    d = parse_date(it.get("date", ""))
    if d is None:
        return False  # 待核/非法日期：保守保留，报告里会计数
    return (today - d).days > evict_days(dim)


def merge_item_list(pool_items, new_items, dim, today_str):
    """合并单个维度（或单张卡）的条目列表。
    返回 (merged_list, n_new, n_evicted, n_pending)。"""
    today = datetime.date.fromisoformat(today_str)
    pool_items = pool_items or []
    new_items = new_items or []

    # 池中条目按 key 索引，取其已有 firstSeen
    pool_by_key = {}
    for it in pool_items:
        pool_by_key.setdefault(item_key(it), it)

    out, seen = [], set()
    n_new = 0

    # 1) 先放新料：池里已有→复用其 firstSeen(非真新增)；池里没有→今天首见(真新增)
    for it in new_items:
        k = item_key(it)
        if k in seen:
            continue  # harvest 内部重复
        seen.add(k)
        it = dict(it)
        prev = pool_by_key.get(k)
        if prev is not None:
            fs = prev.get("firstSeen") or (prev.get("date") if valid_date(prev.get("date", "")) and prev.get("date") != "待核" else today_str)
        else:
            fs = today_str
            n_new += 1
        it["firstSeen"] = fs
        out.append(it)

    # 2) 再放池中未被新料覆盖的旧条目（回填 firstSeen）
    for it in pool_items:
        k = item_key(it)
        if k in seen:
            continue
        seen.add(k)
        it = dict(it)
        if not it.get("firstSeen"):
            if valid_date(it.get("date", "")) and it.get("date") != "待核":
                it["firstSeen"] = it["date"]
            # 日期待核且无 firstSeen：不强标，前端按"非新"处理
        out.append(it)

    # 3) 滚动淘汰超期
    kept, n_evicted, n_pending = [], 0, 0
    for it in out:
        if it.get("date") == "待核" or parse_date(it.get("date", "")) is None:
            n_pending += 1
        if is_expired(it, today, dim):
            n_evicted += 1
            continue
        kept.append(it)

    # 4) 排序：本轮新增(firstSeen==today)置顶，其余按日期倒序
    kept.sort(key=lambda it: (1 if it.get("firstSeen") == today_str else 0,
                              date_sort_key(it.get("date", ""))), reverse=True)
    return kept, n_new, n_evicted, n_pending


def main():
    args = sys.argv[1:]
    if not args:
        print("用法：python3 merge.py harvest.json [--pool data.json] [--out data.json] [--dry]",
              file=sys.stderr)
        sys.exit(1)
    harvest_path = args[0]
    pool_path = DATA
    out_path = DATA
    dry = False
    i = 1
    while i < len(args):
        if args[i] == "--pool":
            pool_path = args[i + 1]; i += 2
        elif args[i] == "--out":
            out_path = args[i + 1]; i += 2
        elif args[i] == "--dry":
            dry = True; i += 1
        else:
            print(f"未知参数：{args[i]}", file=sys.stderr); sys.exit(1)

    try:
        with open(harvest_path, encoding="utf-8") as f:
            harvest = json.load(f)
    except Exception as e:
        print(f"❌ 无法读取 harvest：{e}", file=sys.stderr); sys.exit(1)
    try:
        with open(pool_path, encoding="utf-8") as f:
            pool = json.load(f)
    except Exception as e:
        print(f"❌ 无法读取池 {pool_path}：{e}", file=sys.stderr); sys.exit(1)

    today_str = harvest.get("generated", "")
    if not valid_date(today_str) or today_str == "待核":
        print(f"❌ harvest.generated 非法/缺失：{today_str!r}（应为 YYYY-MM-DD）", file=sys.stderr)
        sys.exit(1)

    add = harvest.get("add", {}) or {}
    leads = harvest.get("leads", {}) or {}
    musts = harvest.get("musts", {}) or {}
    fins = harvest.get("financials", {}) or {}

    merged = copy.deepcopy(pool)
    merged["generated"] = today_str

    report = []  # (dept, dim/card, new, evicted)
    tot_new = tot_eq = 0

    for dept in merged.get("depts", []):
        did = dept.get("id")
        brief = dept.get("brief")
        if brief is None:
            # 池里整部门无料；若 harvest 有该部门新料，仍需建壳——交由全量模式处理，增量跳过
            if did in add:
                report.append((did, "(brief=null,跳过;需全量建壳)", 0, 0))
            continue

        # 覆盖 lead / musts（有才覆盖）
        if leads.get(did):
            brief["lead"] = leads[did]
        if musts.get(did):
            brief["musts"] = musts[did]

        dept_add = add.get(did, {})
        dept_fin = fins.get(did, {})

        for sec in brief.get("sections", []):
            dim = sec.get("dim")
            if "layers" in sec:
                # 卡片化维度：add[did][dim] = {卡名: [items]}
                card_add = dept_add.get(dim, {}) if isinstance(dept_add.get(dim), dict) else {}
                for layer in sec["layers"]:
                    for card in layer.get("cards", []):
                        name = card.get("name")
                        # 季度财报更新（有才覆盖）
                        if name in dept_fin:
                            card["financials"] = dept_fin[name]
                        new_items = card_add.get(name, [])
                        kept, n_new, n_ev, n_pd = merge_item_list(
                            card.get("items", []), new_items, dim, today_str)
                        card["items"] = kept
                        if n_new or n_ev:
                            report.append((did, f"{dim}/{name}", n_new, n_ev))
                        tot_new += n_new; tot_eq += n_ev
            else:
                new_items = dept_add.get(dim, [])
                if isinstance(new_items, dict):
                    new_items = []  # 容错：非卡片化维度误填了 dict
                kept, n_new, n_ev, n_pd = merge_item_list(
                    sec.get("items", []), new_items, dim, today_str)
                sec["items"] = kept
                if n_new or n_ev:
                    report.append((did, dim, n_new, n_ev))
                tot_new += n_new; tot_eq += n_ev

    # 同源同步：pharma 美团买药卡 = instant 美团买药卡（PLAYBOOK 铁律，两处必须一致）
    def find_card(did, name):
        for dept in merged.get("depts", []):
            if dept.get("id") != did or not dept.get("brief"):
                continue
            for sec in dept["brief"].get("sections", []):
                for layer in sec.get("layers", []) or []:
                    for card in layer.get("cards", []):
                        if card.get("name") == name:
                            return card
        return None
    mt_instant = find_card("instant", "美团买药")
    mt_pharma = find_card("pharma", "美团买药")
    if mt_instant is not None and mt_pharma is not None:
        if mt_pharma.get("items") != mt_instant.get("items"):
            mt_pharma["items"] = copy.deepcopy(mt_instant.get("items", []))
            report.append(("pharma", "竞对动态/美团买药(同步instant)", 0, 0))

    # 报告
    print(f"=== 增量合并：{today_str} ===")
    print(f"  池：{os.path.basename(pool_path)}  新料：{os.path.basename(harvest_path)}")
    if report:
        for did, where, n_new, n_ev in report:
            seg = []
            if n_new: seg.append(f"+{n_new}新")
            if n_ev:  seg.append(f"-{n_ev}淘汰")
            print(f"  [{did}] {where}: {' '.join(seg)}")
    else:
        print("  （无变更）")
    print(f"  合计：本轮新增 {tot_new} 条，淘汰超期 {tot_eq} 条。")

    if dry:
        print("  --dry：未写文件。")
        sys.exit(0)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  ✅ 已写入 {os.path.basename(out_path)}（请接着跑 validate.py / linkcheck.py / archive.py）")
    sys.exit(0)


if __name__ == "__main__":
    main()
