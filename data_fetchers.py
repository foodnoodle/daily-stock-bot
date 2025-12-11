# --- data_fetchers.py (v5.1: 修復 BTC 資料長度不足問題) ---
import yfinance as yf

# 1. 通用 yfinance 抓取器
def fetch_yf_price(ticker, correction=1.0):
    try:
        t = yf.Ticker(ticker)
        d = t.history(period="1d")
        if not d.empty:
            val = d['Close'].iloc[-1]
            if correction != 1.0 and val > 20: val = val * correction
            return f"{val:.2f}"
        return "N/A"
    except: return "Error"

def fetch_yf_trend(ticker):
    try:
        t = yf.Ticker(ticker)
        d = t.history(period="2mo")
        if len(d) >= 20:
            ma20 = d['Close'].rolling(window=20).mean().iloc[-1]
            curr = d['Close'].iloc[-1]
            status = "Above" if curr > ma20 else "Below"
            return f"{curr:.2f} ({status})"
        return "N/A"
    except: return "Error"

# 2. 客製化計算函式
def fetch_bitcoin_trend():
    try:
        # [修正] 改為 5d，確保一定有足夠資料計算漲跌
        d = yf.Ticker("BTC-USD").history(period="5d")
        if len(d) >= 2:
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            return f"{chg:+.2f}%"
        return "N/A"
    except: return "Error"

def fetch_risk_on_off_ratio():
    try:
        d = yf.download(["XLY", "XLP"], period="5d", progress=False, auto_adjust=False)['Close']
        if len(d) >= 2:
            r_now = d['XLY'].iloc[-1] / d['XLP'].iloc[-1]
            r_prev = d['XLY'].iloc[-2] / d['XLP'].iloc[-2]
            icon = "↗️" if r_now > r_prev else "↘️"
            return f"{r_now:.2f} ({icon})"
        return "N/A"
    except: return "Error"

def fetch_rsi_index():
    try:
        d = yf.Ticker("^GSPC").history(period="2mo")
        if len(d) > 14:
            delta = d['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(com=13, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(com=13, adjust=False).mean()
            rsi = 100 - (100 / (1 + (gain / loss)))
            return f"{rsi.iloc[-1]:.1f}"
        return "N/A"
    except: return "Error"

def fetch_market_info():
    """抓取大盤漲跌資訊"""
    try:
        d = yf.download(["^GSPC", "^NDX"], period="2d", progress=False, auto_adjust=False)['Close']
        msg = []
        name_map = {"^GSPC": "S&P 500", "^NDX": "Nasdaq 100"}
        for sym in ["^GSPC", "^NDX"]:
            try:
                curr = d[sym].iloc[-1]
                prev = d[sym].iloc[-2]
                chg = (curr - prev) / prev * 100
                icon = "📈" if chg > 0 else "📉"
                display_name = name_map.get(sym, sym)
                msg.append(f"{icon} **{display_name}**: {curr:,.2f} ({chg:+.2f}%)")
            except: pass
        return "\n".join(msg)
    except: return "N/A"

def get_sp500_price_raw():
    """CSV 存檔用"""
    try:
        t = yf.Ticker("^GSPC")
        d = t.history(period="1d")
        if not d.empty: return f"{d['Close'].iloc[-1]:.2f}"
    except: pass
    return ""
