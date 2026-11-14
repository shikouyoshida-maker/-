#!/usr/bin/env python3
"""吉田塾の予約をすばやく検索する。

使い方:
  python3 scripts/juku.py            → これからの開催と人数
  python3 scripts/juku.py 11/22      → その日の参加者
  python3 scripts/juku.py 山本        → その人の予約履歴
  python3 scripts/juku.py キャンセル  → キャンセル一覧
  python3 scripts/juku.py 福岡        → 福岡のこれからの開催
"""
import csv
import datetime as dt
import pathlib
import sys
from collections import OrderedDict

CSV = pathlib.Path(__file__).resolve().parent.parent / "data" / "吉田塾_予約一覧.csv"
rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
today = dt.date.today().isoformat()
q = sys.argv[1] if len(sys.argv) > 1 else ""


def by_session(rs):
    out = OrderedDict()
    for r in rs:
        out.setdefault((r["開催日"], r["会場"]), []).append(r)
    return out


def show_sessions(rs):
    for (d, v), xs in by_session(rs).items():
        names = OrderedDict()
        for x in xs:
            names.setdefault(x["氏名"], []).append(x["状態"])
        print(f"{d} {v}: {len(names)}名")


active = [r for r in rows if r["状態"] != "キャンセル"]

if not q:
    show_sessions([r for r in active if r["開催日"] >= today])
elif q in ("キャンセル", "cancel"):
    for r in sorted((r for r in rows if r["状態"] == "キャンセル"), key=lambda r: r["開催日"], reverse=True):
        print(f'{r["開催日"]} {r["会場"]} {r["氏名"]}')
elif q in ("大阪", "福岡", "徳島", "オンライン"):
    show_sessions([r for r in active if r["開催日"] >= today and r["会場"] == q])
elif "/" in q or "-" in q:
    parts = q.replace("-", "/").split("/")
    if len(parts) == 2:
        m, d = int(parts[0]), int(parts[1])
        y = int(today[:4])
        key = f"{y}-{m:02d}-{d:02d}"
        if not any(r["開催日"] == key for r in rows):
            key = f"{y + 1}-{m:02d}-{d:02d}"
    else:
        key = f"{int(parts[0])}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    hits = [r for r in rows if r["開催日"] == key]
    if not hits:
        print(f"{key} の予約はありません")
    for (d, v), xs in by_session(hits).items():
        print(f"■ {d} {v}")
        names = OrderedDict()
        for x in xs:
            names.setdefault(x["氏名"], []).append(x)
        n = 0
        for name, xx in names.items():
            sts = {x["状態"] for x in xx}
            if sts == {"キャンセル"}:
                continue
            n += 1
            tag = "（仮予約）" if "確定" not in sts else ""
            dup = f" ×{len(xx)}" if len(xx) > 1 else ""
            print(f"  {n:2d}. {name}{tag}{dup}  支払:{xx[0]['支払']}")
        canc = [name for name, xx in names.items() if {x['状態'] for x in xx} == {"キャンセル"}]
        if canc:
            print("  キャンセル: " + "、".join(canc))
else:
    hits = [r for r in rows if q in r["氏名"].replace(" ", "").replace("　", "") or q in r["氏名"]]
    for r in hits:
        print(f'{r["開催日"]} {r["会場"]} {r["状態"]} {r["氏名"]}')
    if not hits:
        print("該当なし")
