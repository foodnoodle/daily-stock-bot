# --- main.py (v5.0: 輕量模組化主程式) ---
import time
import data_fetchers as df
import utils
from config import INDICATORS

def fetch_all_indices():
    results = {}
    print("🚀 開始依序抓取數據...")
    
    for key, cfg in INDICATORS.items():
        print(f"[{key}] 正在抓取 ({cfg['name']})...")
        try:
            # 根據類型分派任務
            if cfg['type'] == 'price':
                val = df.fetch_yf_price(cfg['ticker'], cfg.get('correction', 1.0))
            elif cfg['type'] == 'trend':
                val = df.fetch_yf_trend(cfg['ticker'])
            elif cfg['type'] == 'custom':
                val = cfg['func']() # 呼叫 config 裡設定的函式
            elif cfg['type'] == 'external':
                val = cfg['func']() # 呼叫外部爬蟲
            
            results[key] = val
            
            # 簡單防呆等待
            if "Error" in str(val): time.sleep(1)
                
        except Exception as e:
            print(f"❌ {key} 發生例外: {e}")
            results[key] = "Error"
            
    return results

if __name__ == "__main__":
    # 1. 抓取所有指標
    results = fetch_all_indices()
    
    # 2. 抓取大盤資訊
    market_text = df.fetch_market_info()
    
    # 3. 計算總結
    summary = utils.calculate_summary(results)
    print("\n" + summary)
    
    # 4. 發送 Discord
    utils.send_discord(results, market_text, summary)
    
    # 5. 存檔 CSV
    utils.save_csv(results)
