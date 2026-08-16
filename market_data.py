"""
market_data.py — Kéo dữ liệu VN-Index thật (giá, biến động) qua vnstock.
Đây là phần "dữ liệu" đứng sau các con số lớn trên dashboard —
khác với kero_tin.py (chỉ lấy tiêu đề tin).

LƯU Ý: vnstock gọi API công khai của VCI/KBS — cần mạng ra ngoài internet
bình thường. Sandbox của Claude không có quyền này nên mình CHƯA chạy thử
được số liệu thật ở đây; sẽ chạy thật khi bạn đưa lên GitHub Actions.
"""

from datetime import datetime, timedelta


def get_vnindex_snapshot():
    """Trả về dict: giá đóng cửa gần nhất, % thay đổi so với phiên trước.
    Nếu lỗi (mất mạng, API đổi cấu trúc...), trả về None để phần HTML
    tự động ẩn khối này thay vì crash toàn bộ report.
    """
    try:
        from vnstock import Market
        market = Market()
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        df = market.index("VNINDEX").ohlcv(start=start, end=end)
        if df is None or len(df) < 2:
            return None
        last, prev = df.iloc[-1], df.iloc[-2]
        change = last["close"] - prev["close"]
        pct = change / prev["close"] * 100
        return {
            "close": round(float(last["close"]), 2),
            "change": round(float(change), 2),
            "pct": round(float(pct), 2),
            "date": str(last.get("time", ""))[:10],
        }
    except Exception as e:
        print(f"[!] Khong lay duoc VN-Index: {e}")
        return None


if __name__ == "__main__":
    print(get_vnindex_snapshot())
