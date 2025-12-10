# --- main.py (v3.0: No-Selenium, Config-Driven, Full Features) ---
import os
import sys
import time
import datetime
import requests
import pandas as pd
import yfinance as yf
from io import StringIO

# ==========================================
# ⚙️ 設定區 (INDICATORS CONFIG)
# ==========================================
# 這裡定義了所有的指標、抓取方式與多空判斷標準
# type: 'yfinance' | 'api_json' | 'web_text' | 'calculation'

INDICATORS = {
    # --- 🌊 宏觀與資金 (Macro & Credit) ---
    'BOND_10Y': {
        'name': '🇺🇸 10年債',
        'type': 'yfinance',
        'ticker': '^TNX',
        'category': 'Macro',
        'eval': lambda v: "🔴 利率高" if v > 4.5 else ("🟢 利率低" if v < 3.5 else "⚪ 中性"),
        'fmt': lambda v: f"{v/10:.2f}%" if v > 20 else f"{v:.2f}%" # 修正 Yahoo 單位
    },
    'DXY': {
        'name': '💵 美元 DXY',
        'type': 'yfinance',
        'ticker': 'DX-Y.NYB',
        'category': 'Macro',
        'eval': lambda v: "🔴 強勢(緊縮)" if v > 105 else ("🟢 弱勢(寬鬆)" if v < 101 else "⚪ 盤整"),
        'fmt': "{:.2f}"
    },
    'HYG': {
        'name': '💳 高收債 HYG',
        'type': 'trend_ma20', # 特殊計算: 價格 vs 20日線
        'ticker': 'HYG',
        'category': 'Macro',
        'eval': lambda s: "🟢 資金流入" if "Above" in s else "🔴 資金流出"
    },
    'BTC': {
        'name': '🪙 比特幣',
        'type': 'price_change', # 特殊計算: 2日漲跌幅
        'ticker': 'BTC-USD',
        'category': 'Macro',
        'eval': lambda v: "🟢 大漲(RiskOn)" if v > 3 else ("🔴 大跌(RiskOff)" if v < -3 else "⚪ 波動正常"),
        'fmt': "{:+.2f}%"
    },

    # --- 🏗️ 結構與板塊 (Structure) ---
    'IWM': {
        'name': '🏢 羅素2000',
        'type': 'trend_ma20',
        'ticker': 'IWM',
        'category': 'Structure',
        'eval': lambda s: "🟢 廣度健康" if "Above" in s else "🔴 廣度轉弱"
    },
    'SOXX': {
        'name': '⚡ 半導體 SOXX',
        'type': 'trend_ma20',
        'ticker': 'SOXX',
        'category': 'Structure',
        'eval': lambda s: "🟢 領頭羊強" if "Above" in s else "🔴 領頭羊弱"
    },
    'SECTOR_BREADTH': {
        'name': '📊 板塊廣度',
        'type': 'calc_sector_breadth', # [新功能] 計算11大板塊有多少站上均線
        'category': 'Structure',
        'eval': lambda v: "🟢 結構強" if v >= 7 else ("🔴 結構弱" if v <= 4 else "⚪ 普通"),
        'fmt': "{:.0f}/11"
    },
    'RISK_RATIO': {
        'name': '⚖️ 風險胃口',
        'type': 'calc_risk_ratio', # XLY / XLP
        'category': 'Structure',
        'eval': lambda s: "🟢 Risk On" if "↗️" in s else "🔴 Risk Off"
    },

    # --- 🌡️ 技術與情緒 (Tech & Sentiment) ---
    'RSI': {
        'name': '📈 大盤 RSI',
        'type': 'calc_rsi',
        'ticker': '^GSPC',
        'category': 'Tech',
        'eval': lambda v: "🔴 過熱" if v > 70 else ("🟢 超賣" if v < 30 else "⚪ 中性"),
        'fmt': "{:.1f}"
    },
    'VIX': {
        'name': '🌪️ VIX 波動',
        'type': 'yfinance',
        'ticker': '^VIX',
        'category': 'Tech',
        'eval': lambda v: "🟢 恐慌(偏多)" if v > 30 else ("🔴 自滿(偏空)" if v < 15 else "⚪ 中性"),
        'fmt': "{:.2f}"
    },
    'CNN': {
        'name': '😱 CNN 情緒',
        'type': 'func_cnn', # 使用自訂函式抓取
        'category': 'Tech',
        'eval': lambda v: "🟢 極恐懼" if v <= 25 else ("🔴 極貪婪" if v >= 75 else "⚪ 中性"),
        'fmt': "{:.0f}"
    },

    # --- 🐳 籌碼與內資 (Smart Money) ---
    'SKEW': {
        'name': '🦢 黑天鵝 SKEW',
        'type': 'yfinance',
        'ticker': '^SKEW',
        'category': 'SmartMoney',
        'eval': lambda v: "🔴 警戒" if v > 140 else "🟢 平穩",
        'fmt': "{:.2f}"
    },
    'PUT_CALL': {
        'name': '⚖️ Put/Call',
        'type': 'func_pcr', # 使用自訂函式
        'category': 'SmartMoney',
        'eval': lambda v: "🟢 看空過度" if v > 1.0 else ("🔴 看多過度" if v < 0.8 else "⚪ 中性"),
        'fmt': "{:.2f}"
    },
    'AAII': {
        'name': '🐂 散戶 AAII',
        'type': 'func_aaii', # 使用自訂函式
        'category': 'SmartMoney',
        'eval': lambda v: "🔴 過熱" if v > 15 else ("🟢 絕望" if v < -15 else "⚪ 中性"),
        'fmt': "Spread: {:+.1f}"
    },
    'NAAIM': {
        'name': '🏦 NAAIM 經理人',
        'type': 'func_naaim',
        'category': 'SmartMoney',
        'eval': lambda v: "🔴 重倉" if v > 90 else ("🟢 輕倉" if v < 40 else "⚪ 中性"),
        'fmt': "{:.2f}"
    }
}


# ==========================================
# 🛠️ 核心抓取函式庫 (Core Fetchers)
# ==========================================

def get_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# 1. 通用 yfinance 抓取
def fetch_yf_price(ticker):
    try:
        t = yf.Ticker(ticker)
        # auto_adjust=False 避免 Github Action 報錯
        data = t.history(period="1d", auto_adjust=False)
        if not data.empty:
            return data['Close'].iloc[-1]
    except: pass
    return None

# 2. 通用 趨勢判斷 (價格 vs 20MA)
def fetch_trend_ma20(ticker):
    try:
        t = yf.Ticker(ticker)
        data = t.history(period="2mo", auto_adjust=False)
        if len(data) >= 20:
            ma20 = data['Close'].rolling(20).mean().iloc[-1]
            curr = data['Close'].iloc[-1]
            return f"{curr:.2f} (Above)" if curr > ma20 else f"{curr:.2f} (Below)"
    except: pass
    return None

# 3. 通用 漲跌幅計算
def fetch_price_change(ticker):
    try:
        t = yf.Ticker(ticker)
        data = t.history(period="2d", auto_adjust=False)
        if len(data) >= 2:
            return ((data['Close'].iloc[-1] / data['Close'].iloc[-2]) - 1) * 100
    except: pass
    return None

# 4. CNN 恐懼貪婪 (API)
def func_cnn():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code == 200:
            return r.json()['fear_and_greed']['score']
    except: pass
    return None

# 5. AAII 散戶情緒 (Pandas Read HTML)
def func_aaii():
    try:
        url = "https://www.stockq.org/economy/aaiisurvey.php"
        dfs = pd.read_html(url)
        # StockQ 的表格通常在比較後面的位置，或特徵是含有 "Bullish"
        for df in dfs:
            if df.shape[1] >= 4 and 'AAII' in str(df.iloc[0,0]): # 簡單特徵識別
                # 假設 row 2 是最新數據: date, bull, neutral, bear
                # 注意: 需根據實際表格微調，這裡取 row 2 (index 1) 的 col 1(bull) 和 col 3(bear)
                # 簡單起見，直接抓數值做轉換
                bull = float(str(df.iloc[1, 1]).replace('%',''))
                bear = float(str(df.iloc[1, 3]).replace('%',''))
                return bull - bear
    except: pass
    return None

# 6. Put/Call Ratio (CBOE Text Scraping)
def func_pcr():
    try:
        # CBOE 頁面通常會把數據直接寫在 HTML
        # 這裡改用 requests 抓取 CBOE 每日數據頁面
        url = "https://www.cboe.com/us/options/market_statistics/daily/"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code == 200:
            # 尋找 "Total Put/Call Ratio" 附近的數值
            # 簡易解析: 找到關鍵字後，找下一個數字
            if "Total Put/Call Ratio" in r.text:
                # 這裡需要一點字串處理技巧，或是用 pandas read_html 嘗試
                dfs = pd.read_html(r.text)
                for df in dfs:
                    # CBOE 的表通常長這樣: [Name, Ratio]
                    if "Total Put/Call Ratio" in df.to_string():
                        # 找到該行
                        target = df[df.iloc[:,0] == "Total Put/Call Ratio"]
                        if not target.empty:
                            return float(target.iloc[0, 1])
    except: pass
    return None

# 7. NAAIM (Requests + String Find)
def func_naaim():
    try:
        url = "https://naaim.org/programs/naaim-exposure-index/"
        r = requests.get(url, headers=get_headers(), timeout=10)
        # NAAIM 網頁通常會有 "The NAAIM Exposure Index is: XX.XX"
        # 這裡用簡易 parser 或是 pandas
        # 網站改版頻繁，使用 pd.read_html 嘗試抓取 class="table"
        dfs = pd.read_html(r.text)
        if dfs:
            return float(dfs[0].iloc[0, 1]) # 假設最新數據在第一列
    except: pass
    return None

# 8. RSI 計算
def calc_rsi(ticker):
    try:
        t = yf.Ticker(ticker)
        data = t.history(period="2mo", auto_adjust=False)
        if len(data) > 14:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(com=13, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(com=13, adjust=False).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs)).iloc[-1]
    except: pass
    return None

# 9. 風險胃口計算
def calc_risk_ratio():
    try:
        data = yf.download(["XLY", "XLP"], period="5d", progress=False, auto_adjust=False)['Close']
        if len(data) >= 2:
            now = data['XLY'].iloc[-1] / data['XLP'].iloc[-1]
            prev = data['XLY'].iloc[-2] / data['XLP'].iloc[-2]
            icon = "↗️" if now > prev else "↘️"
            return f"{now:.2f} ({icon})"
    except: pass
    return None

# 10. [新] 板塊廣度計算 (替代原本的爬蟲)
def calc_sector_breadth():
    try:
        # 11 大板塊 ETF
        sectors = ['XLE', 'XLU', 'XLK', 'XLB', 'XLP', 'XLY', 'XLI', 'XLV', 'XLF', 'XLRE', 'XLC']
        data = yf.download(sectors, period="2mo", progress=False, auto_adjust=False)['Close']
        
        count = 0
        for s in sectors:
            if len(data) >= 20:
                ma200 = data[s].rolling(50).mean().iloc[-1] # 用50日或200日皆可，這裡用50日反應較快，或改回200
                # 修正：如果要 200日線 breadth，就要抓 1y 資料
                # 為了速度，我們這裡計算 "站上 50 日線" 的板塊數量作為短期廣度
                # 若堅持 200 日，請把 period="1y", rolling(200)
                if data[s].iloc[-1] > ma200:
                    count += 1
        return count
    except: pass
    return None


# ==========================================
# 🚀 主程式邏輯 (Execution)
# ==========================================

def fetch_data():
    results = {}
    print("🚀 啟動極速抓取 (No Selenium)...")
    
    for key, cfg in INDICATORS.items():
        print(f"   Fetching {cfg['name']}...", end=" ")
        val = None
        
        # 根據類型分派任務
        if cfg['type'] == 'yfinance':
            val = fetch_yf_price(cfg['ticker'])
        elif cfg['type'] == 'trend_ma20':
            val = fetch_trend_ma20(cfg['ticker'])
        elif cfg['type'] == 'price_change':
            val = fetch_price_change(cfg['ticker'])
        elif cfg['type'] == 'calc_rsi':
            val = calc_rsi(cfg['ticker'])
        elif cfg['type'] == 'calc_risk_ratio':
            val = calc_risk_ratio()
        elif cfg['type'] == 'calc_sector_breadth':
            val = calc_sector_breadth()
        
        # 自訂函式類
        elif cfg['type'] == 'func_cnn': val = func_cnn()
        elif cfg['type'] == 'func_aaii': val = func_aaii()
        elif cfg['type'] == 'func_pcr': val = func_pcr()
        elif cfg['type'] == 'func_naaim': val = func_naaim()

        if val is not None:
            print("✅")
            results[key] = val
        else:
            print("❌")
            results[key] = None
            
    return results

def fetch_market_info():
    try:
        data = yf.download(["^GSPC", "^NDX"], period="2d", progress=False, auto_adjust=False)['Close']
        info = []
        for sym, name in [("^GSPC", "S&P 500"), ("^NDX", "Nasdaq 100")]:
            cur = data[sym].iloc[-1]
            prev = data[sym].iloc[-2]
            chg = (cur - prev) / prev * 100
            icon = "📈" if chg > 0 else "📉"
            info.append(f"{icon} **{name}**: {cur:,.2f} ({chg:+.2f}%)")
        return "\n".join(info)
    except: return "無法取得大盤"

def send_discord(results, market_text):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook: return
    
    # 統計多空
    bulls = 0
    bears = 0
    
    # 產生 Fields
    fields = []
    
    # 用來分類顯示的緩衝區
    categories = {
        'Macro': [], 'Structure': [], 'Tech': [], 'SmartMoney': []
    }
    
    for key, val in results.items():
        if val is None: continue
        cfg = INDICATORS[key]
        
        # 評估狀態
        status_text = ""
        if callable(cfg.get('eval')):
            status_text = cfg['eval'](val)
            if "🟢" in status_text: bulls += 1
            if "🔴" in status_text: bears += 1
            
        # 格式化數值
        val_str = str(val)
        if callable(cfg.get('fmt')):
            val_str = cfg['fmt'](val)
        elif isinstance(val, float):
            val_str = f"{val:.2f}"
            
        # 加入分類清單
        line = f"> {cfg['name']}: **{val_str}** ({status_text})"
        if cfg['category'] in categories:
            categories[cfg['category']].append(line)

    # 總結文字
    summary = "⚪ 市場分歧，觀望"
    if bulls > bears: summary = "🟢 偏向恐懼/機會 (Risk On)"
    elif bears > bulls: summary = "🔴 偏向貪婪/風險 (Risk Off)"
    
    # 組合 Embed
    fields.append({"name": "🔮 情緒總結", "value": f"**多**: {bulls} | **空**: {bears}\n👉 {summary}", "inline": False})
    fields.append({"name": "📊 大盤", "value": market_text, "inline": False})
    
    cat_names = {
        'Macro': "🌊 宏觀與資金 (Macro)",
        'Structure': "🏗️ 結構與板塊 (Structure)",
        'Tech': "🌡️ 技術與情緒 (Tech)",
        'SmartMoney': "🐳 籌碼與內資 (Smart Money)"
    }
    
    for cat, lines in categories.items():
        if lines:
            fields.append({
                "name": cat_names[cat],
                "value": "\n".join(lines),
                "inline": False
            })
            
    payload = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({datetime.datetime.now().strftime('%Y-%m-%d')})",
            "color": 0x00FF00 if bulls > bears else 0xFF0000,
            "fields": fields,
            "footer": {"text": "Github Actions Bot v3.0 (No-Selenium)"}
        }]
    }
    
    requests.post(webhook, json=payload)

if __name__ == "__main__":
    data = fetch_data()
    mkt = fetch_market_info()
    send_discord(data, mkt)
