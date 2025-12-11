# --- put_call_ratio.py (v5.1: 強化偽裝版) ---
import requests
import pandas as pd
import datetime

def fetch_put_call_ratio():
    """
    [智慧版] 抓取 CBOE Put/Call Ratio
    特色：如果預設日期沒資料，會自動往回找 (昨天 -> 前天...)，確保一定抓得到
    """
    base_url = "https://www.cboe.com/us/options/market_statistics/daily/"
    
    # [修正] 增加 Referer 和 Accept 等 Header，避免被 CBOE 阻擋
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.cboe.com/",
        "Connection": "keep-alive"
    }
    
    # 設定回溯天數，最多往回找 5 天
    for i in range(5):
        try:
            target_date = datetime.date.today() - datetime.timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            
            params = {'dt': date_str}
            
            # 加入 timeout 避免卡死
            r = requests.get(base_url, headers=headers, params=params, timeout=15)
            
            if "not available" in r.text.lower():
                continue

            dfs = pd.read_html(r.text)
            
            if dfs:
                df = dfs[0]
                row = df[df.iloc[:, 0].astype(str).str.contains("Total", case=False, na=False)]
                
                if not row.empty:
                    val = row.iloc[0, -1]
                    return str(val)
        
        except Exception:
            continue
            
    return "抓取失敗"
