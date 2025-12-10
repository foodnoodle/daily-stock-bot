# --- dev_main.py (v2.7: 排版大整形 + 修復 Warning) ---
import os
import sys
import requests
import time
import datetime
import yfinance as yf 
import pandas as pd

# 引入你的其他模組
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

RUN_VIX = True
RUN_BOND_YIELD = True
RUN_DXY = True          
RUN_RISK_RATIO = True   
RUN_BTC = True          
RUN_RSI = True          


# --- [API 抓取與計算區] ---

def fetch_vix_index():
    try:
        ticker = yf.Ticker("^VIX")
        data = ticker.history(period="1d")
        if not data.empty:
            return f"{data['Close'].iloc[-1]:.2f}"
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_10y_treasury_yield():
    try:
        ticker = yf.Ticker("^TNX")
        data = ticker.history(period="1d")
        if not data.empty:
            val = data['Close'].iloc[-1]
            if val > 20: val = val / 10
            return f"{val:.2f}%"
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_dxy_index():
    try:
        ticker = yf.Ticker("DX-Y.NYB")
        data = ticker.history(period="1d")
        if not data.empty:
            return f"{data['Close'].iloc[-1]:.2f}"
        return "抓取失敗"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_risk_on_off_ratio():
    try:
        tickers = ["XLY", "XLP"]
        # [修復 Warning] 加入 auto_adjust=False
        data = yf.download(tickers, period="5d", progress=False, auto_adjust=False)['Close']
        if len(data) >= 2:
            xly_now = data['XLY'].iloc[-1]
            xlp_now = data['XLP'].iloc[-1]
            ratio_now = xly_now / xlp_now
            
            xly_prev = data['XLY'].iloc[-2]
            xlp_prev = data['XLP'].iloc[-2]
            ratio_prev = xly_prev / xlp_prev
            
            change = ratio_now - ratio_prev
            icon = "↗️" if change > 0 else "↘️"
            return f"{ratio_now:.2f} ({icon})"
        return "數據不足"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_bitcoin_trend():
    try:
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="2d")
        if len(data) >= 2:
            now = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            pct_change = ((now - prev) / prev) * 100
            return f"{pct_change:+.2f}%"
        return "數據不足"
    except Exception as e:
        return f"錯誤: {e}"

def fetch_rsi_index():
    try:
        ticker = yf.Ticker("^GSPC")
        data = ticker.history(period="2mo")
        if len(data) > 14:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0))
            loss = (-delta.where(delta < 0, 0))
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return f"{rsi.iloc[-1]:.1f}"
        return "數據不足"
    except Exception as e:
        return f"錯誤: {e}"


# --- [主程式區] ---

def fetch_market_data():
    try:
        tickers = ["^GSPC", "^NDX"]
        # [修復 Warning] 加入 auto_adjust=False
        data = yf.download(tickers, period="2d", progress=False, auto_adjust=False)['Close']
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
    results = {}
    failed_keys = []
    print("🚀 開始依序抓取數據...")

    def run_fetcher(name, fetch_func):
        max_retries = 3
        for i in range(max_retries):
            try:
                # 簡單 log，不刷屏
                if i == 0: print(f"[{name}] 抓取中...")
                else: print(f"[{name}] 重試中 ({i+1})...")
                
                result = fetch_func()
                
                is_error = False
                error_msg = ""
                if isinstance(result, str) and "錯誤" in result:
                    is_error = True; error_msg = result
                elif isinstance(result, tuple) and result[0] is None:
                    is_error = True; error_msg = result[2] if len(result) > 2 else "失敗"

                if not is_error: return result
                if i == max_retries - 1: return error_msg
                time.sleep(2)
            except Exception as e:
                if i == max_retries - 1: return f"錯誤: {e}"
                time.sleep(2)
        return "錯誤"

    # API 類
    if RUN_BOND_YIELD: results['BOND_10Y'] = run_fetcher('BOND_10Y', fetch_10y_treasury_yield)
    if RUN_DXY: results['DXY'] = run_fetcher('DXY', fetch_dxy_index)
    if RUN_RISK_RATIO: results['RISK_RATIO'] = run_fetcher('RISK_RATIO', fetch_risk_on_off_ratio)
    if RUN_BTC: results['BTC'] = run_fetcher('BTC', fetch_bitcoin_trend)
    if RUN_RSI: results['RSI'] = run_fetcher('RSI', fetch_rsi_index)

    # 爬蟲類
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
    try:
        val_str = str(value).strip()
        status = "⚪ 中性" 
        
        # 為了排版整齊，簡化部分文字
        if key == 'CNN':
            val = float(val_str.split()[0])
            if val <= 25: status = "🟢 極恐懼"
            elif val <= 45: status = "🟢 恐懼"
            elif val >= 75: status = "🔴 極貪婪"
            elif val >= 55: status = "🔴 貪婪"
            
        elif key == 'VIX':
            val = float(val_str.replace(',',''))
            if val > 30: status = "🟢 恐慌"
            elif val < 15: status = "🔴 自滿"
            
        elif key == 'PUT_CALL':
            val = float(val_str)
            if val > 1.0: status = "🟢 看空過度"
            elif val < 0.8: status = "🔴 看多過度"

        elif key == 'BOND_10Y':
            val = float(val_str.replace('%',''))
            if val > 4.5: status = "🔴 利率高"
            elif val < 3.5: status = "🟢 利率低"
        
        elif key == 'DXY':
            val = float(val_str)
            if val > 105: status = "🔴 強勢 (緊縮)"
            elif val < 101: status = "🟢 弱勢 (寬鬆)"

        elif key == 'RISK_RATIO':
            if "↗️" in val_str: status = "🟢 Risk On"
            elif "↘️" in val_str: status = "🔴 Risk Off"

        elif key == 'BTC':
            val = float(val_str.replace('%','').replace('+',''))
            if val > 3.0: status = "🟢 大漲"
            elif val < -3.0: status = "🔴 大跌"

        elif key == 'RSI':
            val = float(val_str)
            if val > 70: status = "🔴 過熱"
            elif val < 30: status = "🟢 超賣"
            elif val > 60: status = "⚪ 強勢"
            elif val < 40: status = "⚪ 弱勢"

        elif key == 'AAII':
            if isinstance(value, tuple):
                bull, bear, diff = value
                val_str = f"多{bull}% | 空{bear}%"
                if diff > 15: status = "🔴 過熱"
                elif diff < -15: status = "🟢 絕望"
            else: return val_str, "❓ 錯誤"

        elif key == 'NAAIM':
            val = float(val_str)
            if val > 90: status = "🔴 重倉"
            elif val < 40: status = "🟢 輕倉"
            
        elif key == 'SKEW':
            val = float(val_str.replace(',',''))
            if val > 140: status = "🔴 警戒"
            elif val < 120: status = "🟢 平穩"
            
        elif key == 'ABOVE_200_DAYS':
            val = float(val_str.replace('%',''))
            if val > 80: status = "🔴 過熱"
            elif val < 20: status = "🟢 超賣"

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

    conclusion = "⚪ 市場分歧，觀望"
    if bull_signals > bear_signals: conclusion = "🟢 偏向恐懼/機會 (Risk On)"
    elif bear_signals > bull_signals: conclusion = "🔴 偏向貪婪/風險 (Risk Off)"
        
    return f"**🟢 多方**: {bull_signals} | **🔴 空方**: {bear_signals}\n👉 {conclusion}"

def send_discord_embed(results, market_text, summary_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url: return

    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 顏色邏輯
    color = 0x808080 
    try:
        val = float(str(results.get('CNN', '50')).split()[0])
        if val <= 45: color = 0x00FF00 
        elif val >= 55: color = 0xFF0000 
    except: pass

    fields = []
    
    # 1. 總結與大盤 (保持獨立，清楚)
    fields.append({"name": "🔮 市場情緒總結", "value": summary_text, "inline": False})
    fields.append({"name": "📊 美股大盤指數", "value": market_text if market_text else "無法讀取", "inline": False})

    # --- 排版優化：使用分類字串，而不是一堆 Grid ---
    
    # 輔助函式：產生單行格式
    def fmt_line(name, key):
        val = results.get(key)
        if not val: return f"> {name}: N/A"
        val_str, status = get_indicator_status(key, val)
        # 格式： > 🇺🇸 10年債: 4.20% (中性)
        return f"> {name}: **{val_str}** ({status})"

    # 分類 1: 🌊 流動性與風險 (總經)
    macro_str = ""
    macro_str += fmt_line("🇺🇸 10年債", "BOND_10Y") + "\n"
    macro_str += fmt_line("💵 美元 DXY", "DXY") + "\n"
    macro_str += fmt_line("🪙 比特幣", "BTC") + "\n"
    macro_str += fmt_line("⚖️ 風險胃口", "RISK_RATIO")
    fields.append({"name": "🌊 流動性與風險 (Macro)", "value": macro_str, "inline": False})

    # 分類 2: 🌡️ 技術與波動 (技術面)
    tech_str = ""
    tech_str += fmt_line("📈 大盤 RSI", "RSI") + "\n"
    tech_str += fmt_line("🌪️ VIX 波動", "VIX") + "\n"
    tech_str += fmt_line("😱 CNN 情緒", "CNN") + "\n"
    tech_str += fmt_line("📊 >200日線", "ABOVE_200_DAYS")
    fields.append({"name": "🌡️ 技術與波動 (Technical)", "value": tech_str, "inline": False})

    # 分類 3: 🐳 籌碼與情緒 (機構/散戶)
    fund_str = ""
    fund_str += fmt_line("🏦 機構持倉", "NAAIM") + "\n"
    fund_str += fmt_line("🦢 黑天鵝 SKEW", "SKEW") + "\n"
    fund_str += fmt_line("🐂 散戶 AAII", "AAII") + "\n"
    fund_str += fmt_line("⚖️ Put/Call", "PUT_CALL")
    fields.append({"name": "🐳 籌碼與情緒 (Smart Money)", "value": fund_str, "inline": False})

    data = {
        "embeds": [{
            "title": f"📅 每日財經情緒日報 ({today_date})", 
            "color": color,
            "fields": fields,
            "footer": {"text": "Github Actions Auto Bot (v2.7 Clean UI)"},
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
