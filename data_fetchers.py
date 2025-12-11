# --- data_fetchers.py (v6.0: AI 數據增強版) ---
import yfinance as yf

# 1. [新增] 抓取完整大盤數據 (OHLCV) 供 AI 使用
def fetch_full_market_data():
    """
    一次抓取 SPX 與 NDX 的 開/高/低/收/量
    回傳 dict: {'SPX_Open': ..., 'SPX_High': ..., 'NDX_Volume': ...}
    """
    try:
        # ^GSPC = S&P 500, ^NDX = Nasdaq 100
        tickers = ["^GSPC", "^NDX"]
        # 抓取 1 天資料
        data = yf.download(tickers, period="1d", progress=False, auto_adjust=False)
        
        result = {}
        # yfinance 的多層索引格式處理
        for symbol in tickers:
            prefix = "SPX" if symbol == "^GSPC" else "NDX"
            try:
                # 提取該指數的最後一筆數據
                result[f'{prefix}_Open'] = f"{data['Open'][symbol].iloc[-1]:.2f}"
                result[f'{prefix}_High'] = f"{data['High'][symbol].iloc[-1]:.2f}"
                result[f'{prefix}_Low']  = f"{data['Low'][symbol].iloc[-1]:.2f}"
                result[f'{prefix}_Close'] = f"{data['Close'][symbol].iloc[-1]:.2f}"
                result[f'{prefix}_Volume'] = f"{data['Volume'][symbol].iloc[-1]:.0f}"
            except Exception:
                # 若抓取失敗填入空值
                result[f'{prefix}_Open'] = ""
                result[f'{prefix}_High'] = ""
                result[f'{prefix}_Low'] = ""
                result[f'{prefix}_Close'] = ""
                result[f'{prefix}_Volume'] = ""
                
        return result
    except Exception as e:
        print(f"Market Data Error: {e}")
        return {}

# 2. 通用 yfinance 抓取器 (單一價格)
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

# 3. 客製化計算函式
def fetch_bitcoin_trend():
    try:
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

# [新增] 抓取 3個月國庫券殖利率 (作為 2年期 的替代品，用於計算殖利率曲線)
def fetch_short_term_yield():
    return fetch_yf_price("^IRX")
