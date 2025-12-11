# --- dev_main.py (v4.0: Config-Driven 重構版) ---
import os
import sys
import requests
import time
import datetime
import csv
import re
import yfinance as yf 
import pandas as pd

# 引入外部模組 (維持 Selenium 與特殊爬蟲)
from aaii_index import fetch_aaii_bull_bear_diff
from fear_greed_index import fetch_fear_greed_meter
from naaim_index import fetch_naaim_exposure_index
from skew_index import fetch_skew_index
from above_200_days_average import fetch_above_200_days_average
from put_call_ratio import fetch_put_call_ratio

# ==========================================
# ⚙️ 全局設定 (Configuration) - 這裡控制一切
# ==========================================
# 欄位說明:
#   name: 顯示名稱
#   category: 分類 (macro, struct, tech, fund)
#   type: 抓取類型 (price, trend, custom, external)
#   ticker: yfinance 代號 (如果是 yf 類型)
#   func: 對應的抓取函式 (如果是 custom/external)
#   thresholds: (偏多門檻, 偏空門檻) 或 特殊邏輯標籤
#   inverse: 是否反向指標 (True 代表數值越低越好，如 VIX)

INDICATORS = {
    # --- 1. 🌊 宏觀與資金 (Macro) ---
    'BOND_10Y': {
        'name': '🇺🇸 10年債', 'category': 'macro', 'type': 'price', 'ticker': '^TNX',
        'thresholds': (3.5, 4.5), 'inverse': True, 'correction': 0.1  # TNX 有時需除以10
    },
    'DXY': {
        'name': '💵 美元 DXY', 'category': 'macro', 'type': 'price', 'ticker': 'DX-Y.NYB',
        'thresholds': (101, 105), 'inverse': True
    },
    'HYG': {
        'name': '💳 高收債 HYG', 'category': 'macro', 'type': 'trend', 'ticker': 'HYG',
        'thresholds': 'ma_trend' # 特殊邏輯：均線之上(多)/之下(空)
    },
    'BTC': {
        'name': '🪙 比特幣', 'category': 'macro', 'type': 'custom', 'func': 'fetch_bitcoin_trend',
        'thresholds': (3.0, -3.0) # 漲跌幅 >3% 多, <-3% 空
    },

    # --- 2. 🏗️ 結構與板塊 (Structure) ---
    'IWM': {
        'name': '🏢 羅素2000', 'category': 'struct', 'type': 'trend', 'ticker': 'IWM',
        'thresholds': 'ma_trend'
    },
    'SOXX': {
        'name': '⚡ 半導體 SOXX', 'category': 'struct', 'type': 'trend', 'ticker': 'SOXX',
        'thresholds': 'ma_trend'
    },
    'RISK_RATIO': {
        'name': '⚖️ 風險胃口', 'category': 'struct', 'type': 'custom', 'func': 'fetch_risk_on_off_ratio',
        'thresholds': 'arrow_trend' # 特殊邏輯：看箭頭
    },

    # --- 3. 🌡️ 技術與情緒 (Tech) ---
    'RSI': {
        'name': '📈 大盤 RSI', 'category': 'tech', 'type': 'custom', 'func': 'fetch_rsi_index',
        'thresholds': (30, 70), 'inverse': True # <30 超賣(多), >70 過熱(空)
    },
    'VIX': {
        'name': '🌪️ VIX 波動', 'category': 'tech', 'type': 'price', 'ticker': '^VIX',
        'thresholds': (30, 15), # >30 恐慌(多), <15 自滿(空) (注意這裡是反向邏輯的寫法，但我會在程式統一處理)
        'inverse': False        # VIX 高是恐慌(通常視為買點?) 這裡定義：Panic=Green(Buy), Complacent=Red(Risk)
                                # 修正邏輯：我們統一定義 thresholds = (Green_Limit, Red_Limit)
                                # VIX: >30 is Green, <15 is Red.
    },
    'CNN': {
        'name': '😱 CNN 情緒', 'category': 'tech', 'type': 'external', 'func': fetch_fear_greed_meter,
        'thresholds': (45, 55), 'inverse': True # <45 恐懼(多), >55 貪婪(空)
    },
    'ABOVE_200_DAYS': {
        'name': '📊 >200日線', 'category': 'tech', 'type': 'external', 'func': fetch_above_200_days_average,
        'thresholds': (20, 80), 'inverse': True # <20 超賣, >80 過熱
    },

    # --- 4. 🐳 籌碼與內資 (Fund) ---
    'NAAIM': {
        'name': '🏦 機構持倉', 'category': 'fund', 'type': 'external', 'func': fetch_naaim_exposure_index,
        'thresholds': (40, 90), 'inverse': True
    },
    'SKEW': {
        'name': '🦢 黑天鵝 SKEW', 'category': 'fund', 'type': 'external', 'func': fetch_skew_index,
        'thresholds': (120, 140), 'inverse': True # <120 平穩, >140 警戒
    },
    'AAII': {
        'name': '🐂 散戶 AAII', 'category': 'fund', 'type': 'external', 'func': fetch_aaii_bull_bear_diff,
        'thresholds': (-15, 15), 'inverse': True # <-15 絕望(多), >15 過熱(空)
    },
    'PUT_CALL': {
        'name': '⚖️ Put/Call', 'category': 'fund', 'type': 'external', 'func': fetch_put_call_ratio,
        'thresholds': (1.0, 0.8), # >1.0 看空過度(多), <0.8 看多過度(空)
        'inverse': False # 這裡邏輯比較特別，直接用數值區間判斷
    }
}


# ==========================================
# 🛠️ 核心功能區 (Fetchers)
# ==========================================

# 1. 通用 yfinance 抓取器 (解決重複程式碼)
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

# 2. 客製化計算函式 (Custom Fetchers)
def fetch_bitcoin_trend():
    try:
        d = yf.Ticker("BTC-USD").history(period="2d")
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

# ==========================================
# 🧠 邏輯處理區 (Logic)
# ==========================================

def fetch_all_indices():
    results = {}
    print("🚀 開始依序抓取數據...")
    
    for key, cfg in INDICATORS.items():
        print(f"[{key}] 正在抓取 ({cfg['name']})...")
        try:
            # 根據類型分派任務
            if cfg['type'] == 'price':
                val = fetch_yf_price(cfg['ticker'], cfg.get('correction', 1.0))
            elif cfg['type'] == 'trend':
                val = fetch_yf_trend(cfg['ticker'])
            elif cfg['type'] == 'custom':
                # 呼叫本檔案內的函式
                func = globals()[cfg['func']]
                val = func()
            elif cfg['type'] == 'external':
                # 呼叫外部匯入的函式
                val = cfg['func']()
            
            results[key] = val
            # 簡單防呆重試 (針對外部爬蟲)
            if "抓取失敗" in str(val) or "Error" in str(val):
                time.sleep(1) # 這裡可以加強重試邏輯，為求簡潔先略過
                
        except Exception as e:
            print(f"❌ {key} 發生例外: {e}")
            results[key] = "Error"
            
    return results

def get_indicator_status(key, value_str):
    """通用判讀邏輯：根據 CONFIG 門檻回傳狀態文字"""
    if not value_str or "Error" in str(value_str) or "N/A" in str(value_str):
        return "⚠️ 無法判讀"

    cfg = INDICATORS.get(key)
    if not cfg: return "⚪ 中性"

    try:
        # 1. 數值前處理 (移除 %, +)
        clean_val = str(value_str).replace('%','').replace('+','').replace(',','').split()[0]
        val = float(clean_val)
        
        # 2. 判斷邏輯
        thresholds = cfg['thresholds']
        
        # A. 趨勢型 (MA Trend)
        if thresholds == 'ma_trend':
            if "(Above)" in str(value_str): return "🟢 多頭排列"
            if "(Below)" in str(value_str): return "🔴 轉弱/空頭"
            return "⚪ 中性"
            
        # B. 箭頭型 (Risk Ratio)
        if thresholds == 'arrow_trend':
            if "↗️" in str(value_str): return "🟢 Risk On"
            if "↘️" in str(value_str): return "🔴 Risk Off"
            return "⚪ 中性"

        # C. 區間型 (Tuple)
        # 一般定義：(Green_Limit, Red_Limit)
        # Inverse=True (例如RSI): <30 Green, >70 Red
        # Inverse=False (例如VIX): >30 Green(恐慌買點), <15 Red(自滿)
        # 這裡為了簡化，我們依據「數值本身」來做通用判斷
        
        g_limit, r_limit = thresholds
        
        # 比特幣特殊處理 (-3, 3)
        if key == 'BTC':
            if val > g_limit: return "🟢 大漲 (Risk On)"
            if val < r_limit: return "🔴 大跌 (Risk Off)"
            return "⚪ 波動正常"

        # Put/Call 特殊處理
        if key == 'PUT_CALL':
            if val > g_limit: return "🟢 看空過度 (偏多)"
            if val < r_limit: return "🔴 看多過度 (偏空)"
            return "⚪ 中性"
            
        # VIX 特殊處理
        if key == 'VIX':
            if val > g_limit: return "🟢 市場恐慌 (偏多)"
            if val < r_limit: return "🔴 市場自滿 (偏空)"
            return "⚪ 中性"

        # 通用 Inverse 邏輯 (RSI, CNN, AAII...)
        # Green < Limit (超賣/恐懼), Red > Limit (過熱/貪婪)
        if cfg.get('inverse'):
            if val <= g_limit: return "🟢 偏多 (超賣/恐懼)"
            if val >= r_limit: return "🔴 偏空 (過熱/貪婪)"
        else:
            # 正常邏輯: Green > Limit, Red < Limit
            if val >= g_limit: return "🟢 偏多"
            if val <= r_limit: return "🔴 偏空"

        return "⚪ 中性"

    except:
        return "⚪ 中性"

def calculate_summary(results):
    bulls = 0
    bears = 0
    for key, val in results.items():
        status = get_indicator_status(key, val)
        if "🟢" in status: bulls += 1
        if "🔴" in status: bears += 1
    
    concl = "⚪ 市場分歧，建議觀望"
    if bulls > bears: concl = "🟢 市場偏向恐懼/機會 (Risk On)"
    elif bears > bulls: concl = "🔴 市場偏向貪婪/風險 (Risk Off)"
    
    return f"**🟢 多方訊號**: {bulls} | **🔴 空方訊號**: {bears}\n👉 {concl}"

# ==========================================
# 📤 輸出與存檔 (Discord & CSV)
# ==========================================

def send_discord(results, market_text, summary):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url: return

    # 建立分類顯示字串
    categories = {
        'macro': '🌊 宏觀與資金 (Macro)',
        'struct': '🏗️ 結構與板塊 (Struct)',
        'tech': '🌡️ 技術與情緒 (Tech)',
        'fund': '🐳 籌碼與內資 (Fund)'
    }
    
    fields = []
    fields.append({"name": "🔮 市場情緒總結", "value": summary, "inline": False})
    fields.append({"name": "📊 美股大盤指數", "value": market_text, "inline": False})

    # 依分類產生欄位
    for cat_key, cat_name in categories.items():
        content = ""
        # 篩選屬於此分類的指標
        cat_indicators = {k: v for k, v in INDICATORS.items() if v['category'] == cat_key}
        
        for key, cfg in cat_indicators.items():
            val = results.get(key, "N/A")
            status = get_indicator_status(key, val)
            content += f"> {cfg['name']}: **{val}** ({status})\n"
        
        fields.append({"name": cat_name, "value": content, "inline": False})

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({datetime.datetime.now().strftime('%Y-%m-%d')})",
            "color": 0x808080, # 這裡簡化顏色邏輯，統一灰，或可根據 Summary 變色
            "fields": fields,
            "footer": {"text": "Bot v4.0 (Config-Driven)"},
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    try: requests.post(url, json=data)
    except Exception as e: print(f"Discord Error: {e}")

def save_csv(results):
    try:
        if not os.path.exists("data"): os.makedirs("data")
        file = "data/history.csv"
        
        # 1. 準備欄位: Date, SPX_Price + 所有 INDICATORS keys
        keys = list(INDICATORS.keys())
        fieldnames = ['Date', 'SPX_Price'] + keys
        
        # 2. 準備數據
        row = {
            'Date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'SPX_Price': fetch_yf_price("^GSPC")
        }
        
        for k in keys:
            raw = str(results.get(k, ""))
            # 提取純數字 (AAII 特殊處理: 取最後差值 or Tuple第三個)
            if k == 'AAII' and isinstance(results.get(k), tuple):
                val = f"{results[k][2]:.2f}"
            else:
                match = re.search(r"[-+]?\d*\.\d+|\d+", raw.replace(',',''))
                val = match.group() if match else ""
            row[k] = val

        # 3. 寫入
        exists = os.path.isfile(file)
        with open(file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not exists: writer.writeheader()
            writer.writerow(row)
        print("💾 數據已儲存")
    except Exception as e: print(f"CSV Error: {e}")

def fetch_market_info():
    # 簡單的大盤顯示函式
    try:
        d = yf.download(["^GSPC", "^NDX"], period="2d", progress=False, auto_adjust=False)['Close']
        msg = []
        for sym, name in [("^GSPC","S&P 500"), ("^NDX","Nasdaq 100")]:
            try:
                curr = d[sym].iloc[-1]
                prev = d[sym].iloc[-2]
                chg = (curr - prev) / prev * 100
                icon = "📈" if chg > 0 else "📉"
                msg.append(f"{icon} **{name}**: {curr:,.2f} ({chg:+.2f}%)")
            except: pass
        return "\n".join(msg)
    except: return "N/A"

if __name__ == "__main__":
    res = fetch_all_indices()
    mkt = fetch_market_info()
    summ = calculate_summary(res)
    
    print("\n" + summ)
    send_discord(res, mkt, summ)
    save_csv(res)
