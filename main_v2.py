# --- main_v2.py (升級版：圖文卡片 + 大盤行情) ---
import os
import sys
import io
import requests
import time
# 新增：引入 yfinance 抓股價
import yfinance as yf 

# 引入你的其他模組 (這些都是共用的，不用重寫)
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

# 抓取大盤行情的函式
def fetch_market_data():
    try:
        tickers = ["SPY", "QQQ"]
        # 使用 yfinance 下載最近 2 天的數據
        data = yf.download(tickers, period="2d", progress=False)['Close']
        
        # 計算漲跌幅
        market_info = []
        for symbol in tickers:
            try:
                # 確保有兩天的數據來計算差異
                if len(data) >= 2:
                    current = data[symbol].iloc[-1]
                    prev = data[symbol].iloc[-2]
                    change_pct = ((current - prev) / prev) * 100
                    icon = "📈" if change_pct > 0 else "📉"
                    # 格式化文字
                    market_info.append(f"{icon} **{symbol}**: {current:.2f} ({change_pct:+.2f}%)")
                else:
                    market_info.append(f"❓ {symbol}: 數據不足")
            except Exception:
                market_info.append(f"❓ {symbol}: 讀取失敗")
        
        return "\n".join(market_info)
    except Exception as e:
        return f"無法取得大盤數據: {e}"

# 抓取所有指標的函式 (保持原本穩定的排隊執行邏輯)
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

# --- 升級版：發送 Discord Embed (卡片) ---
def send_discord_embed(results, market_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 未設定 Webhook URL")
        return

    # 1. 決定卡片顏色 (簡單邏輯：看 CNN 指數)
    color = 0x808080 # 預設灰色
    fear_greed_val = results.get('CNN', '50')
    try:
        # 嘗試取出數值部分 (例如 "35 (Fear)" -> 35)
        val = float(str(fear_greed_val).split()[0])
        if val <= 25: color = 0x00FF00 # 極度恐懼 -> 綠色 (機會?)
        elif 25 < val <= 45: color = 0x90EE90 # 恐懼 -> 淺綠
        elif 45 < val <= 55: color = 0x808080 # 中立 -> 灰色
        elif 55 < val <= 75: color = 0xFF6347 # 貪婪 -> 淺紅
        elif val > 75: color = 0xFF0000 # 極度貪婪 -> 紅色 (危險?)
    except:
        pass

    # 2. 建立 Fields (欄位)
    fields = []
    
    # 加入大盤行情
    fields.append({
        "name": "📊 美股大盤今日走勢",
        "value": market_text if market_text else "無法讀取",
        "inline": False
    })

    # 整理各個指標
    # CNN
    fields.append({
        "name": "😱 CNN 恐懼貪婪",
        "value": str(results.get('CNN', 'N/A')),
        "inline": True
    })
    
    # VIX
    fields.append({
        "name": "🌪️ VIX 波動率",
        "value": str(results.get('VIX', 'N/A')),
        "inline": True
    })
    
    # Put/Call
    fields.append({
        "name": "⚖️ Put/Call Ratio",
        "value": str(results.get('PUT_CALL', 'N/A')),
        "inline": True
    })

    # AAII (如果抓取成功，它是個 tuple)
    aaii = results.get('AAII')
    if isinstance(aaii, tuple):
        bull, bear, diff = aaii
        aaii_str = f"多: {bull}% | 空: {bear}% (差: {diff:.1f})"
    else:
        aaii_str = str(aaii)
    
    fields.append({
        "name": "🐂 AAII 散戶情緒",
        "value": aaii_str,
        "inline": False
    })

    # 其他指標...
    fields.append({
        "name": "🏦 NAAIM 經理人持倉",
        "value": str(results.get('NAAIM', 'N/A')),
        "inline": True
    })
    
    fields.append({
        "name": "🦢 SKEW 黑天鵝",
        "value": str(results.get('SKEW', 'N/A')),
        "inline": True
    })
    
    fields.append({
        "name": "📈 >200日線比例",
        "value": str(results.get('ABOVE_200_DAYS', 'N/A')),
        "inline": True
    })

    # 3. 組裝 JSONPayload
    data = {
        "embeds": [{
            "title": "📅 每日財經情緒日報",
            "description": "市場情緒指標與大盤概況彙整",
            "color": color,
            "fields": fields,
            "footer": {"text": "Github Actions Auto Bot • Generated by Python"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }]
    }

    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code in [200, 204]:
            print("✅ Discord Embed 發送成功！")
        else:
            print(f"❌ 發送失敗: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 發送錯誤: {e}")

# --- 智慧暫停 (防呆機制) ---
def pause_for_exit():
    # 檢查是否在 GitHub Actions 環境 (GITHUB_ACTIONS=true) 或 非互動模式
    if os.environ.get("GITHUB_ACTIONS") == "true" or not sys.stdin.isatty():
        print("(雲端執行模式：跳過暫停，直接結束程式)")
        return
    try:
        input("\n所有數據已顯示完畢，請按 Enter 鍵關閉視窗...")
    except EOFError:
        pass

if __name__ == "__main__":
    # 使用 StringIO 攔截 print (這樣 Log 才會乾淨，也可以選擇不攔截直接印)
    # 為了簡單，我們這裡直接讓它印出 Log，因為結果是用 Embed 發送的，不需要攔截文字
    
    # 1. 抓指標
    results, failed = fetch_all_indices()
    
    # 2. 抓大盤
    print("\n[Market] 正在抓取大盤資訊...")
    market_text = fetch_market_data()
    print(market_text)
    
    # 3. 發送漂亮的 Embed
    print("\n正在發送 Discord 通知...")
    send_discord_embed(results, market_text)
    
    pause_for_exit()
