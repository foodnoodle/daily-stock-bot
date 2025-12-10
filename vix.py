# 引入必要的函式庫
import yfinance as yf

def fetch_vix_index():
    """使用 yfinance 抓取 VIX 恐慌指數"""
    try:
        # ^VIX 是 Yahoo Finance 的代號
        ticker = yf.Ticker("^VIX")
        # 抓取當日最新資料
        data = ticker.history(period="1d")
        
        if not data.empty:
            # 取得收盤價 (Close) 或最新價
            vix_val = data['Close'].iloc[-1]
            # 回傳格式化後的字串，保留兩位小數
            return f"{vix_val:.2f}"
            
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"
