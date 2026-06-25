#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日归档脚本（历史日历功能的数据侧）

把根目录 data.json 按其 generated 日期归档为 archive/data-<日期>.json，
并重建 manifest.json（前端日期选择器的数据源）。

用法：python3 archive.py        # 在 validate.py + linkcheck.py 全过后、git push 前跑
退出码：0=成功；1=data.json 日期非法/缺失（不归档脏数据）。

数据流：
  data.json (根, 当天工作文件 = 最新归档副本，前端默认&兜底都读它)
  archive/data-YYYY-MM-DD.json (每日一份历史)
  manifest.json: {"dates":[新→旧], "latest": dates[0]}
"""
import json
import os
import re
import glob
import shutil
import datetime
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data.json")
ARCHIVE_DIR = os.path.join(ROOT, "archive")
MANIFEST = os.path.join(ROOT, "manifest.json")
DATE_RE = re.compile(r"data-(\d{4}-\d{2}-\d{2})\.json$")


def valid_date(s):
    try:
        datetime.date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def main():
    # 1. 读 data.json 取日期
    try:
        with open(DATA, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        print(f"❌ 无法读取 data.json：{e}", file=sys.stderr)
        sys.exit(1)

    gen = d.get("generated", "")
    if not valid_date(gen):
        print(f"❌ data.json 的 generated 非法/缺失：{gen!r}（应为 YYYY-MM-DD），不归档。",
              file=sys.stderr)
        sys.exit(1)

    # 2. 复制为 archive/data-<日期>.json（覆盖，允许当天重跑）
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    dst = os.path.join(ARCHIVE_DIR, f"data-{gen}.json")
    shutil.copy2(DATA, dst)

    # 3. 扫描 archive/ 重建 manifest（倒序）
    dates = []
    for p in glob.glob(os.path.join(ARCHIVE_DIR, "data-*.json")):
        m = DATE_RE.search(os.path.basename(p))
        if m and valid_date(m.group(1)):
            dates.append(m.group(1))
    dates = sorted(set(dates), reverse=True)

    manifest = {"dates": dates, "latest": dates[0] if dates else None}
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 4. 小结
    print(f"=== 归档完成 ===")
    print(f"  归档文件：archive/data-{gen}.json")
    print(f"  manifest：共 {len(dates)} 天，最新 {manifest['latest']}")
    print(f"  日期列表：{', '.join(dates[:7])}" + (" ..." if len(dates) > 7 else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
