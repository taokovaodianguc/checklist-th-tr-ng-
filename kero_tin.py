#!/usr/bin/env python3
"""
kero_tin.py — Kéo tin nhanh từ CafeF & Vietstock (RSS) để chuẩn bị
bản tin thị trường buổi sáng.

CÁCH DÙNG:
    python3 kero_tin.py                # lấy tất cả nguồn, in ra màn hình
    python3 kero_tin.py --sector bds   # chỉ lọc theo 1-2 từ khóa ngành
    python3 kero_tin.py --hours 15     # chỉ lấy tin trong N giờ gần nhất
    python3 kero_tin.py --out brief.md # ghi ra file markdown thay vì in

GHI CHÚ:
- Đây là RSS feed công khai (không cần API key). CafeF/Vietstock không
  có API chính thức cho nhà phát triển ngoài, nên RSS là cách "kéo tin"
  ổn định và hợp lệ nhất — không phải scrape HTML dễ vỡ khi họ đổi giao diện.
- Sandbox của Claude không có quyền truy cập mạng ra ngoài whitelist,
  nên script này CHƯA được chạy thử với dữ liệu thật ở đây. Hãy chạy nó
  trên máy của bạn (có mạng bình thường) — mọi domain trong FEEDS đều
  là feed .rss thật, mình đã xác minh URL bằng web search/fetch.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser

# ── Danh sách nguồn RSS ──────────────────────────────────────────────
# Thêm/bớt tuỳ nhu cầu. "tags" dùng để lọc theo --sector.
FEEDS = [
    # --- CafeF ---
    {"name": "CafeF - Chứng khoán",      "url": "https://cafef.vn/thi-truong-chung-khoan.rss", "tags": ["chungkhoan"]},
    {"name": "CafeF - Bất động sản",     "url": "https://cafef.vn/bat-dong-san.rss",            "tags": ["bds"]},
    {"name": "CafeF - Tài chính ngân hàng", "url": "https://cafef.vn/tai-chinh-ngan-hang.rss",  "tags": ["nganhang"]},
    {"name": "CafeF - Vĩ mô đầu tư",     "url": "https://cafef.vn/vi-mo-dau-tu.rss",            "tags": ["vimo"]},
    {"name": "CafeF - Hàng hoá nguyên liệu", "url": "https://cafef.vn/hang-hoa-nguyen-lieu.rss","tags": ["dauka", "vatlieu"]},
    {"name": "CafeF - Tài chính quốc tế", "url": "https://cafef.vn/tai-chinh-quoc-te.rss",       "tags": ["quocte"]},
    {"name": "CafeF - Doanh nghiệp",     "url": "https://cafef.vn/doanh-nghiep.rss",            "tags": ["doanhnghiep"]},

    # --- Vietstock ---
    {"name": "Vietstock - Cổ phiếu",        "url": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",         "tags": ["chungkhoan"]},
    {"name": "Vietstock - Chính sách CK",   "url": "https://vietstock.vn/143/chung-khoan/chinh-sach.rss",       "tags": ["chungkhoan", "vimo"]},
    {"name": "Vietstock - Ngân hàng",       "url": "https://vietstock.vn/757/tai-chinh/ngan-hang.rss",          "tags": ["nganhang"]},
    {"name": "Vietstock - Bất động sản",    "url": "https://vietstock.vn/4220//bat-dong-san/thi-truong-nha-dat.rss", "tags": ["bds"]},
    {"name": "Vietstock - Vĩ mô",           "url": "https://vietstock.vn/761/kinh-te/vi-mo.rss",                "tags": ["vimo"]},
    {"name": "Vietstock - Nhiên liệu",      "url": "https://vietstock.vn/34/hang-hoa/nhien-lieu.rss",           "tags": ["dauka"]},
    {"name": "Vietstock - Kim loại",        "url": "https://vietstock.vn/742/hang-hoa/kim-loai.rss",            "tags": ["thep", "vatlieu"]},
    {"name": "Vietstock - Chứng khoán TG",  "url": "https://vietstock.vn/773/the-gioi/chung-khoan-the-gioi.rss","tags": ["quocte"]},
    {"name": "Vietstock - Nhận định TT",    "url": "https://vietstock.vn/1636/nhan-dinh-phan-tich/nhan-dinh-thi-truong.rss", "tags": ["chungkhoan"]},
]

SECTOR_MAP = {
    "bds": "Bất động sản",
    "dauka": "Dầu khí",
    "vatlieu": "Vật liệu xây dựng",
    "nganhang": "Ngân hàng",
    "chungkhoan": "Chứng khoán",
    "thep": "Thép",
    "vimo": "Vĩ mô",
    "quocte": "Quốc tế",
    "doanhnghiep": "Doanh nghiệp",
}


def parse_time(entry):
    """feedparser thường tự parse được published_parsed; fallback nếu không."""
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, "published", None):
        try:
            return parsedate_to_datetime(entry.published)
        except Exception:
            pass
    return None


def pull(feeds, hours=None, sector=None):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours else None
    results = []

    for src in feeds:
        if sector and sector not in src["tags"]:
            continue
        d = feedparser.parse(src["url"])
        if d.bozo and not d.entries:
            print(f"[!] Không đọc được: {src['name']} ({src['url']})", file=sys.stderr)
            continue
        for e in d.entries:
            t = parse_time(e)
            if cutoff and t and t < cutoff:
                continue
            results.append({
                "source": src["name"],
                "title": e.get("title", "").strip(),
                "link": e.get("link", ""),
                "summary": (e.get("summary", "") or "").strip(),
                "time": t,
            })

    results.sort(key=lambda x: x["time"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return results


def render(results, as_markdown=False):
    lines = []
    if as_markdown:
        lines.append(f"# Kéo tin thị trường — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    for r in results:
        t = r["time"].strftime("%H:%M %d/%m") if r["time"] else "—"
        if as_markdown:
            lines.append(f"- **[{r['source']}]** ({t}) [{r['title']}]({r['link']})")
        else:
            lines.append(f"[{t}] ({r['source']}) {r['title']}\n    {r['link']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Kéo tin CafeF/Vietstock qua RSS")
    ap.add_argument("--sector", choices=SECTOR_MAP.keys(), help="Lọc theo ngành")
    ap.add_argument("--hours", type=int, help="Chỉ lấy tin trong N giờ gần nhất")
    ap.add_argument("--out", help="Ghi ra file .md thay vì in ra màn hình")
    args = ap.parse_args()

    results = pull(FEEDS, hours=args.hours, sector=args.sector)
    text = render(results, as_markdown=bool(args.out))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Đã ghi {len(results)} tin vào {args.out}")
    else:
        print(text if results else "Không có tin nào khớp bộ lọc.")


if __name__ == "__main__":
    main()
