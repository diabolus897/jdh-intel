#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data.json 结构自检脚本（情报台数据契约校验）
用法：python3 validate.py [data.json]
退出码：0=全部通过，1=有错误。警告不阻断但会打印。
契约依据：AGENTS.md「数据契约」+「质量护栏」。
"""
import json
import sys
import datetime

# ---- 契约常量 ----
DEPT_ORDER = ["nutri", "pharma", "device", "consumer", "instant", "medical"]
DEPT_NAMES = {
    "nutri": "营养保健", "pharma": "医药", "device": "医疗器械",
    "consumer": "消费器械", "instant": "即时零售", "medical": "消费医疗",
}
# 前5个部门维度集；instant 用不同维度集
DIMS_DEFAULT = ["竞对动态", "政策动态", "工业动态", "新品动态"]
DIMS_INSTANT = ["竞对动态", "政策动态", "新技术·新模式", "行业·资本"]
ITEM_FIELDS = {"title", "rel", "summary", "source", "date", "url", "takeaway"}
MUST_FIELDS = {"dim", "rel", "title", "note", "url"}
REL_VALUES = {"hi", "mid", "lo"}
SUMMARY_MAX = 60

errors = []
warnings = []
stats = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def valid_date(s):
    """接受 'YYYY-MM-DD' 或 '待核'。"""
    if s == "待核":
        return True
    try:
        datetime.date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


# instant 竞对卡片字段
CARD_FEED_FIELDS = {"title", "summary", "date", "source", "url"}
FIN_FIELDS = {"label"}  # periods 至少要有 label；其余指标可缺(留空表示未查到)


def check_layers(did, dim, layers):
    """校验即时零售竞对的卡片化布局。返回卡片总数。"""
    if not isinstance(layers, list):
        err(f"[{did}/{dim}] layers 不是数组")
        return 0
    total = 0
    for li, layer in enumerate(layers):
        if layer.get("type") not in ("o2o", "chain"):
            err(f"[{did}/{dim}] layers[{li}] type 应为 o2o/chain，实际 {layer.get('type')!r}")
        # title 可空（单层卡片如医药竞对不显示分层标签）；多层时建议给 title
        cards = layer.get("cards", [])
        if not isinstance(cards, list):
            err(f"[{did}/{dim}] layers[{li}] cards 不是数组")
            continue
        for ci, c in enumerate(cards):
            total += 1
            tag = f"[{did}/{dim}] {layer.get('type')}卡[{c.get('name','?')}]"
            if not c.get("name"):
                err(f"{tag} 缺 name")
            # 财报小卡（仅 chain 卡有；可选但若有则校验）
            fin = c.get("financials")
            if fin is not None:
                periods = fin.get("periods", [])
                if not periods:
                    err(f"{tag} financials 无 periods")
                for pi, p in enumerate(periods):
                    if not p.get("label"):
                        err(f"{tag} periods[{pi}] 缺 label")
                if fin.get("url") and not str(fin["url"]).startswith("http"):
                    err(f"{tag} financials.url 非法：{fin.get('url')!r}")
                # 经营速览扩展字段（全部可选，有才校验）
                cov = fin.get("coverage")
                if cov is not None and not isinstance(cov, dict):
                    err(f"{tag} financials.coverage 应为对象")
                strat = fin.get("strategy")
                if strat is not None and not isinstance(strat, list):
                    err(f"{tag} financials.strategy 应为数组")
                memo = fin.get("memo")
                if memo is not None:
                    if not isinstance(memo, dict):
                        err(f"{tag} financials.memo 应为对象")
                    elif not memo.get("title"):
                        err(f"{tag} financials.memo 缺 title")
                    elif memo.get("url") and not str(memo["url"]).startswith("http"):
                        err(f"{tag} financials.memo.url 非法：{memo.get('url')!r}")
            # 卡内动态流
            feed = c.get("items", [])
            if not isinstance(feed, list):
                err(f"{tag} items 不是数组")
                continue
            real_dates = []
            for fi, it in enumerate(feed):
                miss = CARD_FEED_FIELDS - set(it.keys())
                if miss:
                    err(f"{tag} items[{fi}] 缺字段 {miss}")
                if not str(it.get("url", "")).startswith("http"):
                    err(f"{tag} items[{fi}] url 非法：{it.get('url')!r}")
                if not valid_date(it.get("date", "")):
                    err(f"{tag} items[{fi}] date 格式错：{it.get('date')!r}")
                if it.get("date") != "待核":
                    real_dates.append(it.get("date"))
            if real_dates != sorted(real_dates, reverse=True):
                err(f"{tag} items 日期非倒序：{real_dates}")
    return total


def check(path="data.json"):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except json.JSONDecodeError as e:
        err(f"JSON 不合法：{e}")
        return
    except FileNotFoundError:
        err(f"文件不存在：{path}")
        return

    # 顶层
    if "generated" not in d or not valid_date(d.get("generated", "")):
        err(f"顶层 generated 缺失或格式错：{d.get('generated')!r}")
    if "depts" not in d or not isinstance(d["depts"], list):
        err("顶层缺 depts 数组")
        return

    ids = [x.get("id") for x in d["depts"]]
    if ids != DEPT_ORDER:
        err(f"部门顺序错误，应为 {DEPT_ORDER}，实际 {ids}")

    for dept in d["depts"]:
        did = dept.get("id", "?")
        # name
        if dept.get("name") != DEPT_NAMES.get(did):
            err(f"[{did}] name 应为 {DEPT_NAMES.get(did)!r}，实际 {dept.get('name')!r}")
        # dims
        expect_dims = DIMS_INSTANT if did == "instant" else DIMS_DEFAULT
        if dept.get("dims") != expect_dims:
            err(f"[{did}] dims 应为 {expect_dims}，实际 {dept.get('dims')}")

        brief = dept.get("brief")
        if brief is None:
            stats.append(f"[{did}] {DEPT_NAMES.get(did)}: brief=null（整部门无料）")
            continue

        # musts
        musts = brief.get("musts", [])
        if not isinstance(musts, list):
            err(f"[{did}] musts 不是数组")
        else:
            if len(musts) > 3:
                warn(f"[{did}] musts {len(musts)} 条，契约建议挑最重要 3 条")
            elif len(musts) < 3:
                warn(f"[{did}] musts 仅 {len(musts)} 条，契约要求挑最重要 3 条")
            for i, m in enumerate(musts):
                miss = MUST_FIELDS - set(m.keys())
                if miss:
                    err(f"[{did}] musts[{i}] 缺字段 {miss}")
                if m.get("rel") not in REL_VALUES:
                    err(f"[{did}] musts[{i}] rel 非法：{m.get('rel')!r}")
                if not str(m.get("url", "")).startswith("http"):
                    err(f"[{did}] musts[{i}] url 非法：{m.get('url')!r}")

        # sections
        sections = brief.get("sections", [])
        sec_dims = [s.get("dim") for s in sections]
        if sec_dims != expect_dims:
            err(f"[{did}] sections 维度顺序应为 {expect_dims}，实际 {sec_dims}")

        cnt = []
        for s in sections:
            dim = s.get("dim", "?")
            # 竞对动态卡片化布局（layers）：即时零售/医药等部门可用，单独校验
            if "layers" in s:
                n = check_layers(did, dim, s["layers"])
                cnt.append(f"{dim}:{n}卡")
                continue
            items = s.get("items", [])
            if not isinstance(items, list):
                err(f"[{did}/{dim}] items 不是数组")
                continue
            real_dates = []
            for j, it in enumerate(items):
                miss = ITEM_FIELDS - set(it.keys())
                if miss:
                    err(f"[{did}/{dim}] items[{j}] 缺字段 {miss}")
                if it.get("rel") not in REL_VALUES:
                    err(f"[{did}/{dim}] items[{j}] rel 非法：{it.get('rel')!r}")
                if not str(it.get("url", "")).startswith("http"):
                    err(f"[{did}/{dim}] items[{j}] url 非法：{it.get('url')!r}")
                if not valid_date(it.get("date", "")):
                    err(f"[{did}/{dim}] items[{j}] date 格式错：{it.get('date')!r}")
                slen = len(str(it.get("summary", "")))
                if slen > SUMMARY_MAX:
                    err(f"[{did}/{dim}] items[{j}] summary 超长({slen}>{SUMMARY_MAX})：{it.get('title')!r}")
                if it.get("date") != "待核":
                    real_dates.append(it.get("date"))
            # 日期倒序（待核不参与）
            if real_dates != sorted(real_dates, reverse=True):
                err(f"[{did}/{dim}] items 日期非倒序：{real_dates}")
            cnt.append(f"{dim}:{len(items)}")
        stats.append(f"[{did}] {DEPT_NAMES.get(did)}: " + " / ".join(cnt))


def check_profiles(path="profiles.json"):
    """校验 profiles.json（连锁药房季度档案）。文件不存在=跳过（前端面板自动不显示）。"""
    import os
    if not os.path.exists(path):
        stats.append("[profiles] profiles.json 不存在（跳过校验，前端面板不显示）")
        return
    try:
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
    except json.JSONDecodeError as e:
        err(f"[profiles] JSON 不合法：{e}")
        return
    chains = (p.get("instant", {}) or {}).get("chains", [])
    if not isinstance(chains, list) or not chains:
        err("[profiles] instant.chains 缺失或为空")
        return
    names = [c.get("name") for c in chains]
    for c in chains:
        nm = c.get("name", "?")
        tag = f"[profiles] {nm}"
        if not c.get("name"):
            err(f"{tag} 缺 name")
        periods = c.get("periods", [])
        if not isinstance(periods, list) or not periods:
            err(f"{tag} periods 缺失或为空")
        else:
            for pi, pr in enumerate(periods):
                if not pr.get("label"):
                    err(f"{tag} periods[{pi}] 缺 label")
        strat = c.get("strategy")
        if strat is not None:
            if not isinstance(strat, dict):
                err(f"{tag} strategy 应为对象 {{source, points}}")
            else:
                if strat.get("source") and strat["source"] not in ("MD&A", "投资者交流"):
                    warn(f"{tag} strategy.source 建议为 'MD&A' 或 '投资者交流'，实际 {strat.get('source')!r}")
                if not isinstance(strat.get("points", []), list):
                    err(f"{tag} strategy.points 应为数组")
        cov = c.get("coverage")
        if cov is not None:
            if not isinstance(cov, dict):
                err(f"{tag} coverage 应为对象 {{count, advantage, provinces, advProvinces}}")
            else:
                for k in ("provinces", "advProvinces"):
                    if k in cov and not isinstance(cov[k], list):
                        err(f"{tag} coverage.{k} 应为数组")
                # 优势省应是布局省的子集（有才校验）
                prov = cov.get("provinces")
                adv = cov.get("advProvinces")
                if isinstance(prov, list) and isinstance(adv, list):
                    extra = [x for x in adv if x not in prov]
                    if extra:
                        warn(f"{tag} advProvinces 含未在 provinces 列出的省：{extra}")
        sd = c.get("strategyDetail")
        if sd is not None and not isinstance(sd, list):
            err(f"{tag} strategyDetail 应为数组 [{{h, items[]}}]")
        memo = c.get("memo")
        if memo is not None:
            if not isinstance(memo, dict):
                err(f"{tag} memo 应为对象")
            elif memo.get("url") and not str(memo["url"]).startswith("http"):
                err(f"{tag} memo.url 非法：{memo.get('url')!r}")
    stats.append(f"[profiles] 连锁档案 {len(chains)} 家：{', '.join(names)}（口径 {p.get('updated','?')}）")


# 新品周报字段（与 data.json item 同；卡内不强制 takeaway，但周报建议带）
PRODUCT_FIELDS = {"title", "rel", "summary", "source", "date", "url"}
PRODUCT_DEPTS = {"nutri", "pharma", "device", "consumer", "medical"}


def check_products(path="newproducts.json"):
    """校验 newproducts.json（新品周报，中流数据）。文件不存在=跳过（前端降级显示占位）。"""
    import os
    if not os.path.exists(path):
        stats.append("[newproducts] newproducts.json 不存在（跳过校验，前端新品区显示占位）")
        return
    try:
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
    except json.JSONDecodeError as e:
        err(f"[newproducts] JSON 不合法：{e}")
        return
    depts = p.get("depts", {})
    if not isinstance(depts, dict):
        err("[newproducts] depts 应为对象 {部门id: [items]}")
        return
    cnt = []
    for did, items in depts.items():
        if did not in PRODUCT_DEPTS:
            err(f"[newproducts] 未知部门 id：{did!r}（应 ∈ {sorted(PRODUCT_DEPTS)}）")
        if not isinstance(items, list):
            err(f"[newproducts/{did}] items 不是数组")
            continue
        for j, it in enumerate(items):
            miss = PRODUCT_FIELDS - set(it.keys())
            if miss:
                err(f"[newproducts/{did}] items[{j}] 缺字段 {miss}")
            if it.get("rel") not in REL_VALUES:
                err(f"[newproducts/{did}] items[{j}] rel 非法：{it.get('rel')!r}")
            if not str(it.get("url", "")).startswith("http"):
                err(f"[newproducts/{did}] items[{j}] url 非法：{it.get('url')!r}")
            if not valid_date(it.get("date", "")):
                err(f"[newproducts/{did}] items[{j}] date 格式错：{it.get('date')!r}")
            # 周报 summary 为原文概述（不受日抓 60 字限制）；过长仅提示
            slen = len(str(it.get("summary", "")))
            if slen > 120:
                warn(f"[newproducts/{did}] items[{j}] summary 偏长({slen})：{it.get('title')!r}")
            # jd/zy 在售状态（可选，有才校验取值）
            for k in ("jd", "zy"):
                if k in it and it[k] not in ("有", "无", "待核"):
                    err(f"[newproducts/{did}] items[{j}] {k} 取值非法：{it.get(k)!r}（应为 有/无/待核）")
            if "tags" in it and not isinstance(it["tags"], list):
                err(f"[newproducts/{did}] items[{j}] tags 应为数组")
        cnt.append(f"{did}:{len(items)}")
    stats.append(f"[newproducts] 新品周报（{p.get('updated','?')} {p.get('week','')}）：" + " / ".join(cnt))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    check(path)
    check_profiles()
    check_products()

    print(f"=== 自检：{path} ===")
    for s in stats:
        print("  " + s)
    if warnings:
        print(f"\n⚠️  警告 {len(warnings)} 条：")
        for w in warnings:
            print("  - " + w)
    if errors:
        print(f"\n❌ 错误 {len(errors)} 条：")
        for e in errors:
            print("  - " + e)
        # 修正清单：按类型聚合，方便一次性批量改完
        buckets = {
            "summary 超长": 0, "缺字段": 0, "url 非法": 0,
            "date 格式": 0, "日期非倒序": 0, "rel 非法": 0,
            "维度/顺序/name": 0, "卡片(layers)": 0, "其它": 0,
        }
        for e in errors:
            if "summary 超长" in e:
                buckets["summary 超长"] += 1
            elif "缺字段" in e or "缺 name" in e or "缺 label" in e or "无 periods" in e:
                buckets["缺字段"] += 1
            elif "url" in e and "非法" in e:
                buckets["url 非法"] += 1
            elif "date 格式" in e:
                buckets["date 格式"] += 1
            elif "非倒序" in e:
                buckets["日期非倒序"] += 1
            elif "rel" in e and "非法" in e:
                buckets["rel 非法"] += 1
            elif ("dims" in e or "顺序" in e or "name 应为" in e):
                buckets["维度/顺序/name"] += 1
            elif ("layers" in e or "卡[" in e or "type 应为" in e):
                buckets["卡片(layers)"] += 1
            else:
                buckets["其它"] += 1
        summary = "　".join(f"{k}×{v}" for k, v in buckets.items() if v)
        print(f"\n📋 修正清单：{summary}")
        print("\n校验未通过。")
        sys.exit(1)
    print("\n✅ 全部校验通过。")
    sys.exit(0)


if __name__ == "__main__":
    main()
