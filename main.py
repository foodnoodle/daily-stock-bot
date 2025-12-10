# --- main_v2.py (v2.2: 修正 SKEW 黑天鵝邏輯) ---
import os
import sys
import io
import requests
import time
import datetime
import yfinance as yf 

# 引入你的其他模組
from aaii_index import fetch_aaii_bull_bear_diff
from fear_greed_index import fetch_fear_greed_meter
from vix import fetch_vix_index
from put_call_ratio import fetch_total_put_call_ratio
from naaim_index import fetch_naaim_exposure_index
from skew_index import fetch_skew_index
from above_200_days_average import fetch_above_200_days_average

# 控制各指標是否執行
RUN_AAII = True
RUN_CNN = True
RUN_VIX = True
RUN_PUT_CALL = True
RUN_NAAIM = True
RUN_SKEW = True
RUN_ABOVE_200_DAYS = True

# 1. 抓取大盤行情 (指數版)
def fetch_market_data():
    try:
        tickers = ["^GSPC", "^NDX"]
        data = yf.download(tickers, period="2d", progress=False)['Close']
        name_map = {"^GSPC": "S&P 500", "^NDX": "Nasdaq 100"}
        
        market_info = []
        for symbol in tickers:
            try:
                if len(data) >= 2:
                    try:
                        current = data[symbol].iloc[-1]
                        prev = data[symbol].iloc[-2]
                    except:
                        current = data.iloc[-1]
                        prev = data.iloc[-2]

                    change_pct = ((current - prev) / prev) * 100
                    icon = "📈" if change_pct > 0 else "📉"
                    display_name = name_map.get(symbol, symbol)
                    market_info.append(f"{icon} **{display_name}**: {current:,.2f} ({change_pct:+.2f}%)")
                else:
                    market_info.append(f"❓ {symbol}: 數據不足")
            except Exception as e:
                market_info.append(f"❓ {symbol}: {e}")
        
        return "\n".join(market_info)
    except Exception as e:
        return f"無法取得大盤數據: {e}"

# 2. 抓取指標 (依序執行)
def fetch_all_indices():
    results = {}
    failed_keys = []
    print("🚀 開始依序抓取數據...")

    def run_fetcher(name, fetch_func):
        print(f"[{name}] 正在抓取...")
        try:
            return fetch_func()
        except Exception as e:
            return f"錯誤: {e}"

    if RUN_AAII: results['AAII'] = run_fetcher('AAII', fetch_aaii_bull_bear_diff)
    if RUN_PUT_CALL: results['PUT_CALL'] = run_fetcher('PUT_CALL', fetch_total_put_call_ratio)
    if RUN_VIX: results['VIX'] = run_fetcher('VIX', fetch_vix_index)
    if RUN_CNN: results['CNN'] = run_fetcher('CNN', fetch_fear_greed_meter)
    if RUN_NAAIM: results['NAAIM'] = run_fetcher('NAAIM', fetch_naaim_exposure_index)
    if RUN_SKEW: results['SKEW'] = run_fetcher('SKEW', fetch_skew_index)
    if RUN_ABOVE_200_DAYS: results['ABOVE_200_DAYS'] = run_fetcher('ABOVE_200_DAYS', fetch_above_200_days_average)

    for key, value in results.items():
        if (isinstance(value, str) and "錯誤" in value) or value is None:
            failed_keys.append(key)
    return results, failed_keys

# 3. 判斷個別指標情緒狀態
def get_indicator_status(key, value):
    try:
        val_str = str(value).strip()
        status = "⚪ 中性" 

        if key == 'CNN':
            val = float(val_str.split()[0])
            if val <= 25: status = "🟢 極度恐懼 (偏多)"
            elif val <= 45: status = "🟢 恐懼 (偏多)"
            elif val >= 75: status = "🔴 極度貪婪 (偏空)"
            elif val >= 55: status = "🔴 貪婪 (偏空)"
            
        elif key == 'VIX':
            val = float(val_str.replace(',',''))
            # VIX 高代表恐慌，通常視為底部機會(偏多)
            if val > 30: status = "🟢 市場恐慌 (偏多)"
            elif val < 15: status = "🔴 市場自滿 (偏空)"
            
        elif key == 'PUT_CALL':
            val = float(val_str)
            # PC Ratio 高代表大家在買保險，過度悲觀往往是反彈契機
            if val > 1.0: status = "🟢 過度看空 (偏多)"
            elif val < 0.8: status = "🔴 過度看多 (偏空)"
            
        elif key == 'AAII':
            if isinstance(value, tuple):
                bull, bear, diff = value
                val_str = f"多{bull}% | 空{bear}%"
                if diff > 15: status = "🔴 散戶過熱 (偏空)"
                elif diff < -15: status = "🟢 散戶絕望 (偏多)"
            else:
                return val_str, "❓ 格式錯誤"

        elif key == 'NAAIM':
            val = float(val_str)
            if val > 90: status = "🔴 經理人重倉 (偏空)"
            elif val < 40: status = "🟢 經理人輕倉 (偏多)"
            
        elif key == 'SKEW':
            # --- [修正重點] ---
            # SKEW 飆高代表機構在大買黑天鵝保險，暗示隨時可能崩盤 -> 視為風險警示 (偏空)
            val = float(val_str.replace(',',''))
            if val > 140: status = "🔴 黑天鵝警戒 (偏空)"
            elif val < 120: status = "🟢 風險情緒平穩 (偏多)"
            else: status = "⚪ 避險情緒略增 (中性)"
            
        elif key == 'ABOVE_200_DAYS':
            val = float(val_str.replace('%',''))
            if val > 80: status = "🔴 市場過熱 (偏空)"
            elif val < 20: status = "🟢 市場超賣 (偏多)"

        return val_str, status

    except Exception:
        return str(value), "⚠️ 無法判讀"

# 4. 計算總結 (修正 SKEW 納入空方計數)
def calculate_sentiment_summary(results):
    bull_signals = 0
    bear_signals = 0
    
    for key, val in results.items():
        _, status = get_indicator_status(key, val)
        if "🟢" in status: bull_signals += 1
        if "🔴" in status: bear_signals += 1

    conclusion = "⚪ 市場情緒分歧，建議觀望"
    # 當「恐懼/偏多」訊號較多時 -> 機會
    if bull_signals > bear_signals:
        conclusion = "🟢 市場偏向恐懼 (可能存在機會)"
    # 當「貪婪/偏空」訊號較多時 -> 風險
    elif bear_signals > bull_signals:
        conclusion = "🔴 市場偏向貪婪/風險高 (建議謹慎)"
        
    return f"**偏多訊號(綠)**: {bull_signals} | **偏空訊號(紅)**: {bear_signals}\n👉 {conclusion}"

# 5. 發送 Discord
def send_discord_embed(results, market_text, summary_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 未設定 Webhook URL")
        return

    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 卡片顏色依據 CNN
    color = 0x808080 
    try:
        val = float(str(results.get('CNN', '50')).split()[0])
        if val <= 45: color = 0x00FF00 
        elif val >= 55: color = 0xFF0000 
    except: pass

    fields = []
    
    fields.append({"name": "🔮 市場情緒總結", "value": summary_text, "inline": False})
    fields.append({"name": "📊 美股大盤指數", "value": market_text if market_text else "無法讀取", "inline": False})

    order = ['CNN', 'VIX', 'PUT_CALL', 'AAII', 'NAAIM', 'SKEW', 'ABOVE_200_DAYS']
    names = {
        'CNN': '😱 CNN 恐懼貪婪',
        'VIX': '🌪️ VIX 波動率',
        'PUT_CALL': '⚖️ Put/Call Ratio',
        'AAII': '🐂 AAII 散戶情緒',
        'NAAIM': '🏦 NAAIM 經理人',
        'SKEW': '🦢 SKEW 黑天鵝',
        'ABOVE_200_DAYS': '📈 >200日線比例'
    }

    for key in order:
        val = results.get(key)
        if val:
            val_str, status = get_indicator_status(key, val)
            fields.append({
                "name": names[key],
                "value": f"{val_str}\n{status}",
                "inline": True
            })

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({today_date})", 
            "color": color,
            "fields": fields,
            "footer": {"text": "Github Actions Auto Bot"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }]
    }

    try:
        requests.post(webhook_url, json=data)
        print("✅ Discord Embed 發送成功！")
    except Exception as e:
        print(f"❌ 發送錯誤: {e}")

def pause_for_exit():
    if os.environ.get("GITHUB_ACTIONS") == "true" or not sys.stdin.isatty():
        return
    try:
        input("按 Enter 結束...")
    except: pass

if __name__ == "__main__":
    results, failed = fetch_all_indices()
    print("\n[Market] 正在抓取大盤資訊...")
    market_text = fetch_market_data()
    print("[Analysis] 正在分析市場情緒...")
    summary_text = calculate_sentiment_summary(results)
    print("\n正在發送 Discord 通知...")
    send_discord_embed(results, market_text, summary_text)
    pause_for_exit()
