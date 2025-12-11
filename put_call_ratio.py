# --- put_call_ratio.py (智慧版：Requests + 自動回溯) ---
import requests
import pandas as pd
import datetime

def fetch_put_call_ratio():
    """
    [智慧版] 抓取 CBOE Put/Call Ratio
    特色：如果預設日期沒資料，會自動往回找 (昨天 -> 前天...)，確保一定抓得到
    """
    base_url = "https://www.cboe.com/us/options/market_statistics/daily/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # 設定回溯天數，最多往回找 5 天 (避免無窮迴圈)
    for i in range(5):
        try:
            # 計算要查詢的日期
            # i=0 (今天/預設), i=1 (昨天), i=2 (前天)...
            target_date = datetime.date.today() - datetime.timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            
            # 在網址後面加上 ?dt=YYYY-MM-DD 參數
            params = {'dt': date_str}
            
            # 發送請求
            r = requests.get(base_url, headers=headers, params=params, timeout=10)
            
            # 如果網頁內容包含 "Data not available" 或類似錯誤，直接跳過
            if "not available" in r.text.lower():
                continue

            # 解析表格
            dfs = pd.read_html(r.text)
            
            if dfs:
                df = dfs[0]
                # 尋找包含 "Total" 的那一行
                row = df[df.iloc[:, 0].astype(str).str.contains("Total", case=False, na=False)]
                
                if not row.empty:
                    val = row.iloc[0, -1]
                    # 回傳數值 (字串格式)
                    return str(val)
        
        except Exception:
            # 發生錯誤 (例如表格解析失敗)，就繼續試下一天
            continue
            
    return "抓取失敗"
