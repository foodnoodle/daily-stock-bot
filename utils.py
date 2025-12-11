# --- utils.py ---
import os
import requests
import datetime
import csv
import re
from config import INDICATORS # 匯入設定檔以取得門檻值
import data_fetchers as df    # 匯入抓取器以取得 SPX 價格

def extract_numeric_value(text):
    if not isinstance(text, str): return ""
    clean_text = text.replace('%', '').replace('+', '').replace(',', '')
    match = re.search(r"[-+]?\d*\.\d+|\d+", clean_text)
    if match: return match.group()
    return ""

def get_indicator_status(key, value_str):
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

    categories = {
        'macro': '🌊 宏觀與資金 (Macro)',
        'struct': '🏗️ 結構與板塊 (Struct)',
        'tech': '🌡️ 技術與情緒 (Tech)',
        'fund': '🐳 籌碼與內資 (Fund)'
    }
    
    fields = []
    fields.append({"name": "🔮 市場情緒總結", "value": summary, "inline": False})
    fields.append({"name": "📊 美股大盤指數", "value": market_text, "inline": False})

    for cat_key, cat_name in categories.items():
        content = ""
        cat_indicators = {k: v for k, v in INDICATORS.items() if v['category'] == cat_key}
        for key, cfg in cat_indicators.items():
            val = results.get(key, "N/A")
            status = get_indicator_status(key, val)
            content += f"> {cfg['name']}: **{val}** ({status})\n"
        fields.append({"name": cat_name, "value": content, "inline": False})

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({datetime.datetime.now().strftime('%Y-%m-%d')})",
            "color": 0x808080,
            "fields": fields,
            "footer": {"text": "Bot v5.0 (Modularized)"},
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    try: requests.post(url, json=data)
    except Exception as e: print(f"Discord Error: {e}")

def save_csv(results):
    try:
        if not os.path.exists("data"): os.makedirs("data")
        file = "data/history.csv"
        keys = list(INDICATORS.keys())
        fieldnames = ['Date', 'SPX_Price'] + keys
        
        row = {
            'Date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'SPX_Price': df.get_sp500_price_raw()
        }
        for k in keys:
            raw = results.get(k, "")
            # AAII 修正邏輯
            if k == 'AAII' and isinstance(raw, tuple):
                val = f"{raw[2]:.2f}"
            else:
                val = extract_numeric_value(str(raw))
            row[k] = val

        exists = os.path.isfile(file)
        with open(file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not exists: writer.writeheader()
            writer.writerow(row)
        print("💾 數據已儲存")
    except Exception as e: print(f"CSV Error: {e}")
