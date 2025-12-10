# --- main_v2.py (終極版：圖文卡片 + 大盤行情 + 情緒總結) ---
import os
import sys
import io
import requests
import time
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

# 1. 抓取大盤行情的函式
def fetch_market_data():
    try:
        tickers = ["SPY", "QQQ"]
        data = yf.download(tickers, period="2d", progress=False)['Close']
        
        market_info = []
        for symbol in tickers:
            try:
                if len(data) >= 2:
                    current = data[symbol].iloc[-1]
                    prev = data[symbol].iloc[-2]
                    change_pct = ((current - prev) / prev) * 100
                    icon = "📈" if change_pct > 0 else "📉"
                    market_info.append(f"{icon} **{symbol}**: {current:.2f} ({change_pct:+.2f}%)")
                else:
                    market_info.append(f"❓ {symbol}: 數據不足")
            except Exception:
                market_info.append(f"❓ {symbol}: 讀取失敗")
        
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

# 3. 計算市場情緒總結 (這就是你要找回的功能！)
def calculate_sentiment_summary(results):
    signals = []
    
    # 判斷邏輯 (依照原本 main.py 的標準)
    try:
        # AAII
        if 'AAII' in results and isinstance(results['AAII'], tuple):
            bull, bear, diff = results['AAII']
            if diff < -15: signals.append("偏多")
            elif diff > 15: signals.append("偏空")
        
        # Put/Call
        pc = float(results.get('PUT_CALL', 0))
        if pc > 1.0: signals.append("偏多")
        elif pc < 0.8: signals.append("偏空")
        
        # VIX
        vix = float(results.get('VIX', 0))
        if vix > 30: signals.append("偏多")
        elif vix < 15: signals.append("偏空")
        
        # CNN
        cnn_val = float(str(results.get('CNN', 0)).split()[0])
        if cnn_val <= 44: signals.append("偏多")
        elif cnn_val >= 56: signals.append("偏空")
        
        # NAAIM
        naaim = float(results.get('NAAIM', 0))
        if naaim < 20: signals.append("偏多")
        elif naaim > 80: signals.append("偏空")
        
        # SKEW
        skew = float(results.get('SKEW', 0))
        if skew > 140: signals.append("偏空")
        
        # Above 200
        above = float(str(results.get('ABOVE_200_DAYS', 0)).replace('%',''))
        if above < 20: signals.append("偏多")
        elif above > 80: signals.append("偏空")
        
    except Exception as e:
        print(f"計算情緒時發生部分錯誤 (可忽略): {e}")

    bull_count = signals.count("偏多")
    bear_count = signals.count("偏空")
    
    conclusion = "⚪ 市場情緒分歧，建議觀望"
    if bull_count > bear_count:
        conclusion = "🟢 市場偏向恐懼 (可能存在機會)"
    elif bear_count > bull_count:
        conclusion = "🔴 市場偏向貪婪 (建議謹慎)"
        
    return f"**多方訊號**: {bull_count} | **空方訊號**: {bear_count}\n👉 {conclusion}"

# 4. 發送 Discord Embed (卡片)
def send_discord_embed(results, market_text, summary_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 未設定 Webhook URL")
        return

    # 決定卡片顏色 (依據 CNN)
    color = 0x808080 
    try:
        val = float(str(results.get('CNN', '50')).split()[0])
        if val <= 25: color = 0x00FF00 
        elif 25 < val <= 45: color = 0x90EE90
        elif 55 < val <= 75: color = 0xFF6347
        elif val > 75: color = 0xFF0000 
    except: pass

    fields = []
    
    # [新增] 總結摘要放在最上面
    fields.append({
        "name": "🔮 市場情緒總結",
        "value": summary_text,
        "inline": False
    })

    # 大盤行情
    fields.append({
        "name": "📊 美股大盤走勢",
        "value": market_text if market_text else "無法讀取",
        "inline": False
    })

    # 各項指標
    fields.append({"name": "😱 CNN 恐懼貪婪", "value": str(results.get('CNN', 'N/A')), "inline": True})
    fields.append({"name": "🌪️ VIX 波動率", "value": str(results.get('VIX', 'N/A')), "inline": True})
    fields.append({"name": "⚖️ Put/Call Ratio", "value": str(results.get('PUT_CALL', 'N/A')), "inline": True})

    aaii = results.get('AAII')
    aaii_str = f"多: {aaii[0]}% | 空: {aaii[1]}%" if isinstance(aaii, tuple) else str(aaii)
    fields.append({"name": "🐂 AAII 散戶", "value": aaii_str, "inline": True})

    fields.append({"name": "🏦 NAAIM 經理人", "value": str(results.get('NAAIM', 'N/A')), "inline": True})
    fields.append({"name": "🦢 SKEW 黑天鵝", "value": str(results.get('SKEW', 'N/A')), "inline": True})
    fields.append({"name": "📈 >200日線%", "value": str(results.get('ABOVE_200_DAYS', 'N/A')), "inline": True})

    data = {
        "embeds": [{
            "title": "📅 每日財經情緒日報",
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
