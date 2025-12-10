# --- dev_main.py (v2.5: 新增美元指數 + 風險胃口指標) ---
import os
import sys
import requests
import time
import datetime
import yfinance as yf 

# 引入你的其他模組 (部分爬蟲仍保留)
from aaii_index import fetch_aaii_bull_bear_diff
from fear_greed_index import fetch_fear_greed_meter
from put_call_ratio import fetch_total_put_call_ratio
from naaim_index import fetch_naaim_exposure_index
from skew_index import fetch_skew_index
from above_200_days_average import fetch_above_200_days_average

# --- [設定開關] ---
RUN_AAII = True
RUN_CNN = True
RUN_PUT_CALL = True
RUN_NAAIM = True
RUN_SKEW = True
RUN_ABOVE_200_DAYS = True

# API 指標開關
RUN_VIX = True
RUN_BOND_YIELD = True
RUN_DXY = True          # [新增] 美元指數
RUN_RISK_RATIO = True   # [新增] 風險胃口 (XLY/XLP)


# --- [API 抓取區] 使用 yfinance (穩定、快速) ---

def fetch_vix_index():
    """抓取 VIX 恐慌指數"""
    try:
        ticker = yf.Ticker("^VIX")
        data = ticker.history(period="1d")
        if not data.empty:
            return f"{data['Close'].iloc[-1]:.2f}"
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_10y_treasury_yield():
    """抓取 10 年期公債殖利率"""
    try:
        ticker = yf.Ticker("^TNX")
        data = ticker.history(period="1d")
        if not data.empty:
            val = data['Close'].iloc[-1]
            if val > 20: val = val / 10 # 修正 Yahoo 數據單位的潛在問題
            return f"{val:.2f}%"
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_dxy_index():
    """[新增] 抓取美元指數 (DXY)"""
    try:
        # Yahoo Finance 代號為 DX-Y.NYB
        ticker = yf.Ticker("DX-Y.NYB")
        data = ticker.history(period="1d")
        if not data.empty:
            return f"{data['Close'].iloc[-1]:.2f}"
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_risk_on_off_ratio():
    """[新增] 計算 XLY/XLP 風險胃口比率"""
    try:
        # 一次抓取兩檔 ETF
        tickers = ["XLY", "XLP"]
        # 抓 5 天以確保有足夠資料計算漲跌
        data = yf.download(tickers, period="5d", progress=False)['Close']
        
        if len(data) >= 2:
            # 取得最新與前一天的收盤價
            xly_now = data['XLY'].iloc[-1]
            xlp_now = data['XLP'].iloc[-1]
            xly_prev = data['XLY'].iloc[-2]
            xlp_prev = data['XLP'].iloc[-2]
            
            # 計算比率
            ratio_now = xly_now / xlp_now
            ratio_prev = xly_prev / xlp_prev
            
            # 判斷趨勢
            change = ratio_now - ratio_prev
            icon = "↗️" if change > 0 else "↘️"
            
            return f"{ratio_now:.2f} ({icon})"
        return "數據不足"
    except Exception as e:
        return f"錯誤: {e}"


# --- [主程式區] ---

def fetch_market_data():
    """抓取大盤行情"""
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

def fetch_all_indices():
    """抓取所有指標 (依序執行，含重試機制)"""
    results = {}
    failed_keys = []
    print("🚀 開始依序抓取數據...")

    def run_fetcher(name, fetch_func):
        max_retries = 3
        for i in range(max_retries):
            attempt = i + 1
            if attempt > 1:
                print(f"[{name}] ⚠️ 抓取失敗，重試中 ({attempt}/{max_retries})...")
            else:
                print(f"[{name}] 正在抓取...")
            
            try:
                result = fetch_func()
                
                # 錯誤檢查
                is_error = False
                error_msg = ""
                if isinstance(result, str) and "錯誤" in result:
                    is_error = True
                    error_msg = result
                elif isinstance(result, tuple) and result[0] is None:
                    is_error = True
                    error_msg = result[2] if len(result) > 2 else "失敗"

                if not is_error:
                    return result
                
                if attempt == max_retries:
                    print(f"   ❌ [{name}] 最終失敗: {error_msg}")
                    return error_msg
                else:
                    time.sleep(2)

            except Exception as e:
                if attempt == max_retries:
                    return f"錯誤: {e}"
                time.sleep(2)
        return "錯誤: 未知原因"

    # 執行所有抓取任務
    if RUN_BOND_YIELD: results['BOND_10Y'] = run_fetcher('BOND_10Y', fetch_10y_treasury_yield)
    if RUN_DXY: results['DXY'] = run_fetcher('DXY', fetch_dxy_index)
    if RUN_RISK_RATIO: results['RISK_RATIO'] = run_fetcher('RISK_RATIO', fetch_risk_on_off_ratio)
    
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

def get_indicator_status(key, value):
    """判讀數值多空情緒"""
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
            if val > 30: status = "🟢 市場恐慌 (偏多)"
            elif val < 15: status = "🔴 市場自滿 (偏空)"
            
        elif key == 'PUT_CALL':
            val = float(val_str)
            if val > 1.0: status = "🟢 過度看空 (偏多)"
            elif val < 0.8: status = "🔴 過度看多 (偏空)"

        elif key == 'BOND_10Y':
            val = float(val_str.replace('%',''))
            if val > 4.5: status = "🔴 利率過高 (承壓)"
            elif val < 3.5: status = "🟢 利率舒適 (寬鬆)"
        
        elif key == 'DXY':
            # 美元指數判讀
            val = float(val_str)
            if val > 105: status = "🔴 美元強勢 (資金緊縮)"
            elif val < 101: status = "🟢 美元弱勢 (資金寬鬆)"
            else: status = "⚪ 美元盤整"

        elif key == 'RISK_RATIO':
            # 風險胃口 (XLY/XLP)
            # 根據箭頭符號判斷趨勢
            if "↗️" in val_str:
                status = "🟢 風險偏好升 (Risk On)"
            elif "↘️" in val_str:
                status = "🔴 風險偏好降 (Risk Off)"

        elif key == 'AAII':
            if isinstance(value, tuple):
                bull, bear, diff = value
                val_str = f"多{bull}% | 空{bear}%"
                if diff > 15: status = "🔴 散戶過熱 (偏空)"
                elif diff < -15: status = "🟢 散戶絕望 (偏多)"
            else: return val_str, "❓ 格式錯誤"

        elif key == 'NAAIM':
            val = float(val_str)
            if val > 90: status = "🔴 經理人重倉 (偏空)"
            elif val < 40: status = "🟢 經理人輕倉 (偏多)"
            
        elif key == 'SKEW':
            val = float(val_str.replace(',',''))
            if val > 140: status = "🔴 黑天鵝警戒 (偏空)"
            elif val < 120: status = "🟢 情緒平穩 (偏多)"
            
        elif key == 'ABOVE_200_DAYS':
            val = float(val_str.replace('%',''))
            if val > 80: status = "🔴 市場過熱 (偏空)"
            elif val < 20: status = "🟢 市場超賣 (偏多)"

        return val_str, status

    except Exception:
        return str(value), "⚠️ 無法判讀"

def calculate_sentiment_summary(results):
    bull_signals = 0
    bear_signals = 0
    
    for key, val in results.items():
        _, status = get_indicator_status(key, val)
        if "🟢" in status: bull_signals += 1
        if "🔴" in status: bear_signals += 1

    conclusion = "⚪ 市場情緒分歧，建議觀望"
    if bull_signals > bear_signals:
        conclusion = "🟢 市場偏向恐懼/機會 (Risk On)"
    elif bear_signals > bull_signals:
        conclusion = "🔴 市場偏向貪婪/風險 (Risk Off)"
        
    return f"**多方訊號**: {bull_signals} | **空方訊號**: {bear_signals}\n👉 {conclusion}"

def send_discord_embed(results, market_text, summary_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 未設定 Webhook URL")
        return

    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 這裡依舊以 CNN 作為卡片主色調
    color = 0x808080 
    try:
        val = float(str(results.get('CNN', '50')).split()[0])
        if val <= 45: color = 0x00FF00 
        elif val >= 55: color = 0xFF0000 
    except: pass

    fields = []
    
    fields.append({"name": "🔮 市場情緒總結", "value": summary_text, "inline": False})
    fields.append({"name": "📊 美股大盤指數", "value": market_text if market_text else "無法讀取", "inline": False})

    # [調整] 顯示順序，把 總經指標 放在前面
    order = ['BOND_10Y', 'DXY', 'RISK_RATIO', 'CNN', 'VIX', 'PUT_CALL', 'AAII', 'NAAIM', 'SKEW', 'ABOVE_200_DAYS']
    
    names = {
        'BOND_10Y': '🇺🇸 10年債殖利率',
        'DXY': '💵 美元指數',
        'RISK_RATIO': '⚖️ 風險胃口 (XLY/XLP)',
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
                "name": names.get(key, key),
                "value": f"{val_str}\n{status}",
                "inline": True
            })

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({today_date})", 
            "color": color,
            "fields": fields,
            "footer": {"text": "Github Actions Auto Bot (API v2.5)"},
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
