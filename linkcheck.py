#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data.json 死链检测脚本（情报台真实性护栏）

用途：防住"看起来像真的、点开却是 404"的链接，是核心铁律
"绝不编造链接"的程序化兜底。与 validate.py 分工：
  - validate.py = 纯结构校验，零依赖、秒级、每次必跑、必须全过。
  - linkcheck.py = 网络真实性校验，慢、需 requests、收尾时单独跑，给人决策。
二者不可合并：网络抖动会让"必过的结构校验"变得不稳定。

分级（关键：宁可漏判，不可误杀真链接）：
  ☠️ 死链 DEAD（退出码 1，必须处理）：
     404 / 410 / DNS 解析失败 / 连接被拒绝。这些是确定性失效。
  ⚠️ 待人工复核 WARN（退出码 0，仅打印）：
     403 / 405 / 5xx / 超时 / SSL 错误 / 其它异常。
     中文媒体、公众号、政府站对爬虫常返回这些，多为反爬而非真失效，
     交给人 fetch 一眼确认，不自动拦截以免误删真实好料。

用法：
  python3 linkcheck.py [data.json] [--timeout 8] [--workers 10] [--strict]
  --strict：把 WARN 也算失败（退出码 1）。默认 WARN 不阻断。
退出码：0=无死链（可能有待核警告）；1=有死链 或 --strict 下有警告。
"""
import json
import sys
import argparse
import concurrent.futures as cf

try:
    import requests
    from requests.exceptions import (
        ConnectionError as ReqConnErr, Timeout, SSLError, TooManyRedirects,
    )
except ImportError:
    print("缺少依赖：pip3 install requests", file=sys.stderr)
    sys.exit(2)

import urllib3
urllib3.disable_warnings()  # 静音 LibreSSL/InsecureRequest 噪声

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def collect_urls(d):
    """遍历 data.json，返回 {url: [引用位置标签, ...]}。同一 url 合并。"""
    refs = {}

    def add(url, where):
        if not url or not isinstance(url, str):
            return
        refs.setdefault(url, []).append(where)

    for dept in d.get("depts", []):
        did = dept.get("id", "?")
        brief = dept.get("brief")
        if not brief:
            continue
        for i, m in enumerate(brief.get("musts", []) or []):
            add(m.get("url"), f"{did}/必读[{i}]")
        for s in brief.get("sections", []) or []:
            dim = s.get("dim", "?")
            # 普通 items
            for j, it in enumerate(s.get("items", []) or []):
                add(it.get("url"), f"{did}/{dim}[{j}] {it.get('title', '')[:14]}")
            # 卡片化 layers
            for layer in s.get("layers", []) or []:
                for c in layer.get("cards", []) or []:
                    nm = c.get("name", "?")
                    fin = c.get("financials")
                    if fin and fin.get("url"):
                        add(fin["url"], f"{did}/{dim}/{nm}/财报来源")
                    for k, it in enumerate(c.get("items", []) or []):
                        add(it.get("url"), f"{did}/{dim}/{nm}[{k}] {it.get('title', '')[:14]}")
    return refs


def classify(url, timeout):
    """请求一个 url，返回 (level, detail)。level ∈ {'ok','dead','warn'}。"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout,
                         allow_redirects=True, stream=True, verify=False)
        code = r.status_code
        r.close()
        if code in (404, 410):
            return "dead", f"HTTP {code}"
        if code in (403, 405) or code >= 500:
            return "warn", f"HTTP {code}（多为反爬/临时，人工确认）"
        if code >= 400:
            return "warn", f"HTTP {code}"
        return "ok", f"HTTP {code}"
    except ReqConnErr as e:
        # DNS 解析失败 / 拒绝连接 = 确定性死链；但读超时类不在这
        msg = str(e)
        if "NameResolutionError" in msg or "Name or service" in msg \
                or "getaddrinfo failed" in msg or "Failed to resolve" in msg:
            return "dead", "域名解析失败（DNS）"
        if "Connection refused" in msg:
            return "dead", "连接被拒绝"
        return "warn", f"连接异常：{type(e).__name__}"
    except Timeout:
        return "warn", f"超时（>{timeout}s，可能慢站）"
    except SSLError:
        return "warn", "SSL 证书错误"
    except TooManyRedirects:
        return "warn", "重定向过多"
    except Exception as e:
        return "warn", f"{type(e).__name__}: {str(e)[:50]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="data.json")
    ap.add_argument("--timeout", type=int, default=8)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--strict", action="store_true",
                    help="把待核警告也算失败")
    args = ap.parse_args()

    try:
        with open(args.path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        print(f"无法读取 {args.path}：{e}", file=sys.stderr)
        sys.exit(2)

    refs = collect_urls(d)
    urls = list(refs.keys())
    print(f"=== 死链检测：{args.path} ===")
    print(f"共 {len(urls)} 个唯一 url，并发 {args.workers}，超时 {args.timeout}s\n")

    results = {}
    is_tty = sys.stdout.isatty()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(classify, u, args.timeout): u for u in urls}
        done = 0
        for f in cf.as_completed(fut):
            u = fut[f]
            results[u] = f.result()
            done += 1
            if is_tty:
                print(f"\r  进度 {done}/{len(urls)}", end="", flush=True)
    if is_tty:
        print()

    dead, warn = [], []
    for u, (level, detail) in results.items():
        if level == "dead":
            dead.append((u, detail))
        elif level == "warn":
            warn.append((u, detail))

    if dead:
        print(f"\n☠️  死链 {len(dead)} 条（必须处理）：")
        for u, detail in dead:
            print(f"  - {detail}　{u}")
            for w in refs[u]:
                print(f"      ↳ {w}")
    if warn:
        print(f"\n⚠️  待人工复核 {len(warn)} 条（fetch 一眼确认，多为反爬）：")
        for u, detail in warn:
            print(f"  - {detail}　{u}")
            for w in refs[u]:
                print(f"      ↳ {w}")

    ok = len(urls) - len(dead) - len(warn)
    print(f"\n小结：✅ 正常 {ok}　⚠️ 待核 {len(warn)}　☠️ 死链 {len(dead)}")

    if dead or (args.strict and warn):
        print("\n检测未通过。" + ("（--strict：待核也算失败）" if args.strict and not dead else ""))
        sys.exit(1)
    print("\n✅ 无死链。" + ("（仍有待核项，请人工确认）" if warn else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
