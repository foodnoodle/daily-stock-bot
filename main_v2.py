# --- main_v2.py (終極版 v2.1：日期 + 個別情緒解讀 + 真實指數) ---
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

# 1. 抓取大盤行情的函式 (修改為真實指數)
def fetch_market_data():
    try:
        # ^GSPC = S&P 500, ^NDX = Nasdaq 100
        tickers = ["^GSPC", "^NDX"]
        data = yf.download(tickers, period="2d", progress=False)['Close']
        
        # 對應的顯示名稱
        name_map = {"^GSPC": "S&P 500", "^NDX": "Nasdaq 100"}
        
        market_info = []
        for symbol in tickers:
            try:
                # yfinance 有時返回的順序不固定，確保安全讀取
                if len(data) >= 2:
                    # 處理多層索引或單層索引的情況
                    try:
                        current = data[symbol].iloc[-1]
                        prev = data[symbol].iloc[-2]
                    except:
                        # 如果只有一檔股票或格式不同，嘗試直接讀取
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

# 2. 抓取所有指標 (依序執行)
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

# 3. 輔助函式：判斷個別指標的情緒狀態
def get_indicator_status(key, value):
    """
    根據指標數值回傳：(數值字串, 情緒狀態字串)
    """
    try:
        val_str = str(value).strip()
        status = "⚪ 中性" # 預設

        if key == 'CNN':
            # CNN 通常格式 "35 (Fear)"，我們取數字
            val = float(val_str.split()[0])
            if val <= 25: status = "🟢 極度恐懼 (悲觀)"
            elif val <= 45: status = "🟢 恐懼 (偏悲觀)"
            elif val >= 75: status = "🔴 極度貪婪 (樂觀)"
            elif val >= 55: status = "🔴 貪婪 (偏樂觀)"
            
        elif key == 'VIX':
            val = float(val_str.replace(',',''))
            if val > 30: status = "🟢 市場恐慌 (悲觀)"
            elif val < 15: status = "🔴 市場自滿 (樂觀)"
            
        elif key == 'PUT_CALL':
            val = float(val_str)
            if val > 1.0: status = "🟢 過度看空 (悲觀)"
            elif val < 0.8: status = "🔴 過度看多 (樂觀)"
            
        elif key == 'AAII':
            # AAII 是個 tuple (bull, bear, diff)
            if isinstance(value, tuple):
                bull, bear, diff = value
                val_str = f"多{bull}% | 空{bear}%"
                if diff > 15: status = "🔴 散戶極度樂觀"
                elif diff < -15: status = "🟢 散戶極度悲觀"
            else:
                return val_str, "❓ 格式錯誤"

        elif key == 'NAAIM':
            val = float(val_str)
            if val > 80: status = "🔴 經理人樂觀 (高持倉)"
            elif val < 20: status = "🟢 經理人悲觀 (低持倉)"
            
        elif key == 'SKEW':
            val = float(val_str.replace(',',''))
            if val > 140: status = "🟢 黑天鵝風險高 (避險情緒)"
            else: status = "🔴 風險情緒平穩" # SKEW 低通常代表市場不擔心崩盤
            
        elif key == 'ABOVE_200_DAYS':
            val = float(val_str.replace('%',''))
            if val > 80: status = "🔴 市場過熱 (極度樂觀)"
            elif val < 20: status = "🟢 市場超賣 (極度悲觀)"

        return val_str, status

    except Exception:
        return str(value), "⚠️ 無法判讀"

# 4. 計算市場情緒總結 (簡易版)
def calculate_sentiment_summary(results):
    # 這裡只做簡單的多空計數
    bull_signals = 0
    bear_signals = 0
    
    # 遍歷結果來統計
    for key, val in results.items():
        _, status = get_indicator_status(key, val)
        if "🟢" in status: bull_signals += 1 # 恐懼/悲觀往往是買點 (偏多訊號)
        if "🔴" in status: bear_signals += 1 # 貪婪/樂觀往往是賣點 (偏空訊號)

    conclusion = "⚪ 市場情緒分歧，建議觀望"
    if bull_signals > bear_signals:
        conclusion = "🟢 市場偏向恐懼 (可能存在反彈機會)"
    elif bear_signals > bull_signals:
        conclusion = "🔴 市場偏向貪婪 (追高風險增加)"
        
    return f"**多方訊號(恐懼)**: {bull_signals} | **空方訊號(貪婪)**: {bear_signals}\n👉 {conclusion}"

# 5. 發送 Discord Embed (終極卡片)
def send_discord_embed(results, market_text, summary_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 未設定 Webhook URL")
        return

    # 取得今天的日期字串
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # 決定卡片顏色 (依據 CNN)
    color = 0x808080 
    try:
        val = float(str(results.get('CNN', '50')).split()[0])
        if val <= 45: color = 0x00FF00 # 綠色 (恐懼/機會)
        elif val >= 55: color = 0xFF0000 # 紅色 (貪婪/風險)
    except: pass

    fields = []
    
    # [區塊 1] 總結摘要
    fields.append({
        "name": "🔮 市場情緒總結",
        "value": summary_text,
        "inline": False
    })

    # [區塊 2] 大盤行情
    fields.append({
        "name": "📊 美股大盤指數",
        "value": market_text if market_text else "無法讀取",
        "inline": False
    })

    # [區塊 3] 各項指標詳細解讀
    # 定義顯示順序
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
            # 組合數值與狀態，例如: "35\n🟢 極度恐懼"
            fields.append({
                "name": names[key],
                "value": f"{val_str}\n{status}",
                "inline": True
            })

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({today_date})", # 標題加入日期
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

# 防呆暫停
def pause_for_exit():
    if os.environ.get("GITHUB_ACTIONS") == "true" or not sys.stdin.isatty():
        return
    try:
        input("按 Enter 結束...")
    except: pass

if __name__ == "__main__":
    # 1. 抓指標
    results, failed = fetch_all_indices()
    
    # 2. 抓大盤
    print("\n[Market] 正在抓取大盤資訊...")
    market_text = fetch_market_data()
    
    # 3. 計算總結
    print("[Analysis] 正在分析市場情緒...")
    summary_text = calculate_sentiment_summary(results)
    
    # 4. 發送
    print("\n正在發送 Discord 通知...")
    send_discord_embed(results, market_text, summary_text)
    
    pause_for_exit()
