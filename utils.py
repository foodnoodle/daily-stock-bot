# --- utils.py (v6.0: 支援 AI 訓練數據格式) ---
import os
import requests
import datetime
import csv
import re
from config import INDICATORS, IMAGES
import data_fetchers as df    

def extract_numeric_value(text):
    if not isinstance(text, str): return ""
    clean_text = text.replace('%', '').replace('+', '').replace(',', '')
    match = re.search(r"[-+]?\d*\.\d+|\d+", clean_text)
    if match: return match.group()
    return ""

def get_indicator_status(key, value_in):
    # AAII 特殊處理
    value_str = value_in
    if key == 'AAII' and isinstance(value_in, tuple) and len(value_in) >= 3:
        value_str = value_in[2]

    if not value_str or "Error" in str(value_str) or "N/A" in str(value_str):
        return "⚠️ 無法判讀"
    
    cfg = INDICATORS.get(key)
    if not cfg: return "⚪ 中性"

    try:
        clean_val = str(value_str).replace('%','').replace('+','').replace(',','').split()[0]
        val = float(clean_val)
        thresholds = cfg['thresholds']
        
        if thresholds == 'ma_trend':
            if "(Above)" in str(value_str): return "🟢 多頭排列" if key != 'HYG' else "🟢 資金流入"
            if "(Below)" in str(value_str): return "🔴 轉弱/空頭" if key != 'HYG' else "🔴 資金流出"
            return "⚪ 中性"
            
        if thresholds == 'arrow_trend':
            if "↗️" in str(value_str): return "🟢 Risk On"
            if "↘️" in str(value_str): return "🔴 Risk Off"
            return "⚪ 中性"

        g_limit, r_limit = thresholds
        
        if key == 'BTC':
            if val > g_limit: return "🟢 大漲 (Risk On)"
            if val < r_limit: return "🔴 大跌 (Risk Off)"
            return "⚪ 波動正常"
        
        if key == 'PUT_CALL':
            if val > g_limit: return "🟢 看空過度 (偏多)"
            if val < r_limit: return "🔴 看多過度 (偏空)"
            return "⚪ 中性"
            
        if key == 'VIX':
            if val > g_limit: return "🟢 市場恐慌 (偏多)"
            if val < r_limit: return "🔴 市場自滿 (偏空)"
            return "⚪ 中性"

        if cfg.get('inverse'):
            if val <= g_limit: return "🟢 偏多 (超賣/恐懼)"
            if val >= r_limit: return "🔴 偏空 (過熱/貪婪)"
        else:
            if val >= g_limit: return "🟢 偏多"
            if val <= r_limit: return "🔴 偏空"

        return "⚪ 中性"
    except: return "⚪ 中性"

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
    return f"**🟢 多方**: {bulls} | **🔴 空方**: {bears}\n👉 {concl}"

def send_discord(results, market_text, summary):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url: return

    bulls = 0
    bears = 0
    for key, val in results.items():
        status = get_indicator_status(key, val)
        if "🟢" in status: bulls += 1
        if "🔴" in status: bears += 1
    
    embed_color = 0x95a5a6 
    thumbnail_url = IMAGES['NEUTRAL']

    if bulls > bears: 
        embed_color = 0x2ecc71 
        thumbnail_url = IMAGES['BULL']
    elif bears > bulls: 
        embed_color = 0xe74c3c 
        thumbnail_url = IMAGES['BEAR']

    categories = {
        'macro': '🌊 宏觀與資金 (Macro)',
        'struct': '🏗️ 結構與板塊 (Struct)',
        'tech': '🌡️ 技術與情緒 (Tech)',
        'fund': '🐳 籌碼與內資 (Fund)'
    }
    
    fields = []
    fields.append({"name": "🔮 市場情緒總結", "value": summary, "inline": False})
    fields.append({"name": "📊 美股大盤指數", "value": market_text, "inline": False})
    fields.append({"name": "\u200b", "value": "\u200b", "inline": False})

    cat_items = list(categories.items())
    for i, (cat_key, cat_name) in enumerate(cat_items):
        content = ""
        cat_indicators = {k: v for k, v in INDICATORS.items() if v['category'] == cat_key}
        for key, cfg in cat_indicators.items():
            val = results.get(key, "N/A")
            display_val = val
            if key == 'AAII' and isinstance(val, tuple) and len(val) >= 3:
                display_val = f"多{val[0]}% | 空{val[1]}%"
            status = get_indicator_status(key, val)
            content += f"> {cfg['name']}: **{display_val}** ({status})\n"
            
        fields.append({"name": cat_name, "value": content, "inline": False})
        if i < len(cat_items) - 1:
            fields.append({"name": "\u200b", "value": "\u200b", "inline": False})

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({datetime.datetime.now().strftime('%Y-%m-%d')})",
            "color": embed_color,
            "fields": fields,
            "image": {"url": thumbnail_url}, 
            "footer": {"text": "Bot v6.0 (AI Data Ready)"},
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    try: requests.post(url, json=data)
    except Exception as e: print(f"Discord Error: {e}")

def save_csv(results):
    try:
        folder = "data"
        if not os.path.exists(folder): os.makedirs(folder)
        file = "data/history.csv"
        
        # [變更] 定義全新的 AI 友善欄位順序 (包含 SPX 和 NDX 的完整 OHLCV)
        fieldnames = [
            'Date', 
            # SPX 數據
            'SPX_Open', 'SPX_High', 'SPX_Low', 'SPX_Close', 'SPX_Volume',
            # NDX 數據
            'NDX_Open', 'NDX_High', 'NDX_Low', 'NDX_Close', 'NDX_Volume',
            # 宏觀利率
            '10Y_Yield', '3M_Yield',
            # 其他關鍵因子
            'RSI', 'VIX', 'CNN', 'Put_Call', 
            'DXY', 'BTC_Chg', 'HYG_Price', 
            'Risk_Ratio', 'IWM_Price', 'SOXX_Price', 
            'NAAIM', 'SKEW', 'AAII_Diff', 'Above_200MA'
        ]
        
        # 1. 抓取完整的 OHLCV 數據
        market_data = df.fetch_full_market_data()
        
        # 2. 抓取短債數據
        short_yield = df.fetch_short_term_yield()

        # 3. 準備 AAII 數值
        aaii_raw = results.get('AAII', "")
        aaii_val = ""
        if isinstance(aaii_raw, tuple) and len(aaii_raw) >= 3:
            aaii_val = f"{aaii_raw[2]:.1f}"
        else:
            aaii_val = extract_numeric_value(str(aaii_raw))

        # 4. 組裝資料列
        row = {
            'Date': datetime.datetime.now().strftime("%Y-%m-%d"),
            
            'SPX_Open': market_data.get('SPX_Open', ''),
            'SPX_High': market_data.get('SPX_High', ''),
            'SPX_Low':  market_data.get('SPX_Low', ''),
            'SPX_Close':market_data.get('SPX_Close', ''),
            'SPX_Volume':market_data.get('SPX_Volume', ''),
            
            'NDX_Open': market_data.get('NDX_Open', ''),
            'NDX_High': market_data.get('NDX_High', ''),
            'NDX_Low':  market_data.get('NDX_Low', ''),
            'NDX_Close':market_data.get('NDX_Close', ''),
            'NDX_Volume':market_data.get('NDX_Volume', ''),
            
            '10Y_Yield': extract_numeric_value(str(results.get('BOND_10Y', ''))),
            '3M_Yield':  extract_numeric_value(short_yield),
            
            'RSI': extract_numeric_value(str(results.get('RSI', ''))),
            'VIX': extract_numeric_value(str(results.get('VIX', ''))),
            'CNN': extract_numeric_value(str(results.get('CNN', ''))),
            'Put_Call': extract_numeric_value(str(results.get('PUT_CALL', ''))),
            'DXY': extract_numeric_value(str(results.get('DXY', ''))),
            'BTC_Chg': extract_numeric_value(str(results.get('BTC', ''))),
            'HYG_Price': extract_numeric_value(str(results.get('HYG', ''))),
            'Risk_Ratio': extract_numeric_value(str(results.get('RISK_RATIO', ''))),
            'IWM_Price': extract_numeric_value(str(results.get('IWM', ''))),
            'SOXX_Price': extract_numeric_value(str(results.get('SOXX', ''))),
            'NAAIM': extract_numeric_value(str(results.get('NAAIM', ''))),
            'SKEW': extract_numeric_value(str(results.get('SKEW', ''))),
            'AAII_Diff': aaii_val,
            'Above_200MA': extract_numeric_value(str(results.get('ABOVE_200_DAYS', '')))
        }

        exists = os.path.isfile(file)
        with open(file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not exists: writer.writeheader()
            writer.writerow(row)
            
        print(f"💾 數據已儲存至: {file}")

    except Exception as e: print(f"CSV Error: {e}")
