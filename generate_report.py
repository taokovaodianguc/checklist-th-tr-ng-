"""
generate_report.py — Ghép dữ liệu VN-Index (market_data.py) + tin tức
(kero_tin.py) thành 1 trang HTML tĩnh, style theo đúng bản brand bạn
đang dùng: header tối, nền kem, điểm nhấn cam.

Chạy: python3 generate_report.py --out reports/index.html
"""

import argparse
import html
from datetime import datetime

from kero_tin import FEEDS, pull
from market_data import get_vnindex_snapshot

CSS = """
:root {
  --bg: #f4efe4;
  --hero-bg: #211c17;
  --hero-text: #f4efe4;
  --accent: #d4772f;
  --up: #2f7a4f;
  --down: #b3452f;
  --card-bg: #fffdf8;
  --border: #e3dac8;
  --text: #2a251f;
  --muted: #7a7263;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Georgia, 'Times New Roman', serif;
}
.hero {
  background: var(--hero-bg);
  color: var(--hero-text);
  text-align: center;
  padding: 48px 24px 40px;
}
.hero .eyebrow {
  letter-spacing: 3px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--accent);
  font-family: Arial, sans-serif;
}
.hero h1 {
  font-size: clamp(28px, 4vw, 44px);
  margin: 12px 0 0;
  font-weight: 700;
  line-height: 1.25;
}
.hero .meta {
  margin-top: 18px;
  font-size: 13px;
  color: #c9c2b4;
  font-family: Arial, sans-serif;
  letter-spacing: 1px;
}
.disclaimer {
  background: #efe6d2;
  text-align: center;
  padding: 10px;
  font-size: 12px;
  color: var(--muted);
  font-family: Arial, sans-serif;
  border-bottom: 1px solid var(--border);
}
.wrap { max-width: 960px; margin: 0 auto; padding: 32px 24px 64px; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 40px;
}
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px;
  text-align: center;
}
.card .label {
  font-family: Arial, sans-serif;
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--muted);
}
.card .value { font-size: 26px; font-weight: 700; margin: 6px 0 4px; }
.card .delta { font-family: Arial, sans-serif; font-size: 13px; font-weight: 600; }
.up { color: var(--up); }
.down { color: var(--down); }
section { margin-bottom: 36px; }
h2 {
  font-family: Arial, sans-serif;
  font-size: 13px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}
.news-item {
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
  font-family: Arial, sans-serif;
  font-size: 14px;
}
.news-item a { color: var(--text); text-decoration: none; }
.news-item a:hover { color: var(--accent); }
.news-src { color: var(--accent); font-weight: 700; }
.news-time { color: var(--muted); font-size: 12px; }
.empty-note {
  font-family: Arial, sans-serif;
  font-size: 13px;
  color: var(--muted);
  background: var(--card-bg);
  border: 1px dashed var(--border);
  border-radius: 6px;
  padding: 14px;
}
"""


def render_vnindex_card(snap):
    if not snap:
        return '<div class="empty-note">Chưa lấy được dữ liệu VN-Index (xem log workflow).</div>'
    cls = "up" if snap["change"] >= 0 else "down"
    arrow = "▲" if snap["change"] >= 0 else "▼"
    return f"""
    <div class="cards">
      <div class="card">
        <div class="label">VN-Index</div>
        <div class="value">{snap['close']:,}</div>
        <div class="delta {cls}">{arrow} {abs(snap['change'])} ({snap['pct']}%)</div>
      </div>
    </div>
    """


def render_news(results, limit=15):
    if not results:
        return '<div class="empty-note">Không có tin nào trong khung giờ này.</div>'
    items = []
    for r in results[:limit]:
        t = r["time"].strftime("%H:%M") if r["time"] else "—"
        items.append(f"""
        <div class="news-item">
          <span class="news-src">[{html.escape(r['source'])}]</span>
          <a href="{html.escape(r['link'])}">{html.escape(r['title'])}</a>
          <span class="news-time"> · {t}</span>
        </div>""")
    return "".join(items)


def build_html(hours=15):
    snap = get_vnindex_snapshot()
    news = pull(FEEDS, hours=hours)
    today = datetime.now().strftime("%A, %d/%m/%Y")

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Bản tin thị trường {today}</title>
<style>{CSS}</style>
</head>
<body>
  <div class="hero">
    <div class="eyebrow">Bản tin thị trường chứng khoán</div>
    <h1>Tổng hợp thị trường sáng nay</h1>
    <div class="meta">{today} · Giờ Việt Nam</div>
  </div>
  <div class="disclaimer">⚠ Tài liệu thông tin tổng hợp tự động · KHÔNG phải khuyến nghị giao dịch hay đầu tư</div>
  <div class="wrap">
    {render_vnindex_card(snap)}
    <section>
      <h2>Tin thị trường & tín hiệu mở cửa</h2>
      {render_news(news)}
    </section>
  </div>
</body>
</html>"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=15)
    ap.add_argument("--out", default="reports/index.html")
    args = ap.parse_args()

    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_html(hours=args.hours))
    print(f"Da ghi report vao {args.out}")
