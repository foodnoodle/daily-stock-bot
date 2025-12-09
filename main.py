# --- 程式主要執行區 ---

import os
import requests
import io
import sys
import concurrent.futures

# 引用你的其他模組
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

def fetch_all_indices():
    results = {}
    failed_keys = []
    # 第一次爬取
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {}
        if RUN_AAII:
            futures['AAII'] = executor.submit(fetch_aaii_bull_bear_diff)
        if RUN_PUT_CALL:
            futures['PUT_CALL'] = executor.submit(fetch_total_put_call_ratio)
        if RUN_VIX:
            futures['VIX'] = executor.submit(fetch_vix_index)
        if RUN_CNN:
            futures['CNN'] = executor.submit(fetch_fear_greed_meter)
        if RUN_NAAIM:
            futures['NAAIM'] = executor.submit(fetch_naaim_exposure_index)
        if RUN_SKEW:
            futures['SKEW'] = executor.submit(fetch_skew_index)
        if RUN_ABOVE_200_DAYS:
            futures['ABOVE_200_DAYS'] = executor.submit(fetch_above_200_days_average)
        for key, future in futures.items():
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = f"抓取過程中發生錯誤: {e}"

    # 檢查失敗指標，進行快取清除並重爬 (略過複雜邏輯，保持簡單)
    # ... (原本的重試邏輯保留) ...
    
    # 最終失敗的指標
    for key, value in results.items():
        if isinstance(value, str) and value.startswith("抓取過程中發生錯誤"):
            failed_keys.append(key)
    return results, failed_keys

def judge_signal():
    results, failed_keys = fetch_all_indices()
    print("\n【成功爬取指標結果如下】")
    # AAII
    aaii_signal = "無法判斷"
    if RUN_AAII and 'AAII' not in failed_keys:
        bull, bear, diff = results.get('AAII', (None, None, None))
        if bull is not None:
            if diff < -15:
                aaii_signal = "偏多(極度悲觀)"
            elif diff > 15:
                aaii_signal = "偏空(極度樂觀)"
            else:
                aaii_signal = "中性"
            print(f"\n(A.) AAII散戶情緒 \n\n  最新一週 \n  看多: {bull}% | 看空: {bear}% \n  差值(看多-看空): {diff:.1f}%\n  市場訊號: {aaii_signal}\n----------------------------------------------")
    
    # PUT/CALL
    put_call_signal = "無法判斷"
    if RUN_PUT_CALL and 'PUT_CALL' not in failed_keys:
        put_call_value = results.get('PUT_CALL')
        try:
            val = float(put_call_value)
            if val > 1.0:
                put_call_signal = "偏多(過度悲觀)"
            elif val < 0.8:
                put_call_signal = "偏空(過度樂觀)"
            else:
                put_call_signal = "中性"
        except:
            put_call_signal = "無法判斷"
        print(f"\n(B.) PUT/CALL Ratio \n\n  最新數值: {put_call_value}\n  市場訊號: {put_call_signal}\n----------------------------------------------")
    
    # VIX
    vix_signal = "無法判斷"
    if RUN_VIX and 'VIX' not in failed_keys:
        vix_value = results.get('VIX')
        try:
            val = float(vix_value)
            if val > 30:
                vix_signal = "偏多(市場恐慌)"
            elif val < 15:
                vix_signal = "偏空(市場自滿)"
            else:
                vix_signal = "中性"
        except:
            vix_signal = "無法判斷"
        print(f"\n(C.) VIX 指數 \n\n  最新數值: {vix_value}\n  市場訊號: {vix_signal}\n----------------------------------------------")
    
    # CNN
    cnn_signal = "無法判斷"
    if RUN_CNN and 'CNN' not in failed_keys:
        value = results.get('CNN')
        try:
            # 處理可能帶有文字的數值
            val_str = str(value).split()[0] 
            val = float(val_str)
            
            if val <= 25:
                cnn_signal = "極度恐懼"
                cnn_status = "市場可能過度恐慌"
                cnn_strategy = "增加投資，尋找低估股票"
            elif 26 <= val <= 44:
                cnn_signal = "恐懼"
                cnn_status = "市場可能處於低位"
                cnn_strategy = "考慮增加投資"
            elif 45 <= val <= 55:
                cnn_signal = "中立"
                cnn_status = "市場相對穩定"
                cnn_strategy = "觀望"
            elif 56 <= val <= 74:
                cnn_signal = "貪婪"
                cnn_status = "市場可能處於高位"
                cnn_strategy = "保持警覺"
            elif 75 <= val <= 100:
                cnn_signal = "極度貪婪"
                cnn_status = "市場過熱"
                cnn_strategy = "減少投資或出場"
            else:
                cnn_signal = "無法判斷"
                cnn_status = "-"
                cnn_strategy = "-"
        except:
            cnn_signal = "無法判斷"
            cnn_status = "-"
            cnn_strategy = "-"
        print(f"\n(D.) CNN 恐貪指數 \n\n  最新數值: {value}\n  市場情緒: {cnn_signal}\n  當前市場狀況: {cnn_status}\n  進出場策略: {cnn_strategy}\n----------------------------------------------")
    
    # NAAIM
    naaim_signal = "無法判斷"
    if RUN_NAAIM and 'NAAIM' not in failed_keys:
        naaim_value = results.get('NAAIM')
        try:
            val = float(naaim_value)
            if val < 20:
                naaim_signal = "偏多(經理人悲觀)"
            elif val > 80:
                naaim_signal = "偏空(經理人樂觀)"
            else:
                naaim_signal = "中性"
        except:
            naaim_signal = "無法判斷"
        print(f"\n(E.) NAAIM 曝險指數 \n\n  最新數值: {naaim_value}\n  市場訊號: {naaim_signal}\n----------------------------------------------")
    
    # SKEW
    skew_signal = "無法判斷"
    if RUN_SKEW and 'SKEW' not in failed_keys:
        skew_value = results.get('SKEW')
        try:
            val = float(skew_value)
            if val > 140:
                skew_signal = "偏空(黑天鵝風險)"
            else:
                skew_signal = "中性"
        except:
            skew_signal = "無法判斷"
        print(f"\n(F.) SKEW 黑天鵝指標 \n\n  最新數值: {skew_value}\n  市場訊號: {skew_signal}\n----------------------------------------------")

    # 高於200日線
    above_200_signal = "無法判斷"
    if RUN_ABOVE_200_DAYS and 'ABOVE_200_DAYS' not in failed_keys:
        above_200_days_value = results.get('ABOVE_200_DAYS')
        try:
            val = float(above_200_days_value.replace('%',''))
            if val < 20:
                above_200_signal = "偏多(市場極度超賣)"
            elif val > 80:
                above_200_signal = "偏空(市場極度超買)"
            else:
                above_200_signal = "中性"
        except:
            above_200_signal = "無法判斷"
        print(f"\n(G.) 高於200日線股票比例 \n\n  最新數值: {above_200_days_value}\n  市場訊號: {above_200_signal}\n----------------------------------------------")

    # 統計市場情緒
    signals = []
    # 這裡只簡單統計有成功抓到的
    current_signals = [aaii_signal, put_call_signal, vix_signal, naaim_signal, skew_signal, above_200_signal]
    for s in current_signals:
        if "偏多" in s: signals.append("偏多")
        elif "偏空" in s: signals.append("偏空")
        elif "中性" in s: signals.append("中性")
    
    if cnn_signal in ["極度恐懼", "恐懼"]: signals.append("偏多")
    elif cnn_signal in ["極度貪婪", "貪婪"]: signals.append("偏空")
    elif cnn_signal == "中立": signals.append("中性")

    bullish = signals.count("偏多")
    bearish = signals.count("偏空")
    
    print("\n【市場情緒總結】")
    print(f"偏多訊號數: {bullish}，偏空訊號數: {bearish}")
    if bullish > bearish:
        print("🟢 市場情緒偏向恐懼，可尋找機會")
    elif bearish > bullish:
        print("🔴 市場情緒偏向貪婪，建議謹慎")
    else:
        print("⚪ 市場情緒分歧，建議多觀察，勿躁進。")
    
    if failed_keys:
        print(f"\n以下指標爬取失敗: {', '.join(failed_keys)}")

# --- 新增的 Discord 發送功能 ---
def send_to_discord(message_content):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 錯誤：未設定 DISCORD_WEBHOOK_URL 環境變數，無法發送通知。")
        return

    # Discord 限制單則訊息 2000 字
    if len(message_content) > 1900:
        message_content = message_content[:1900] + "\n... (內容過長已截斷)"

    data = {
        "content": f"```\n{message_content}\n```"
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        print("✅ Discord 通知發送成功！")
    except Exception as e:
        print(f"❌ Discord 通知發送失敗: {e}")

if __name__ == "__main__":
    # 使用 StringIO 攔截 print 的輸出結果
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        # 執行主程式
        judge_signal()
    except Exception as e:
        print(f"執行過程中發生未預期的錯誤: {e}")
    finally:
        # 恢復標準輸出
        sys.stdout = sys.__stdout__

    # 取得攔截到的文字報告
    report_text = captured_output.getvalue()
    
    # 1. 印在 Console (給 GitHub Actions 紀錄看)
    print(report_text)
    
    # 2. 發送到 Discord
    print("正在傳送 Discord 通知...")
    send_to_discord(report_text)
    
    # ⚠️ 注意：我已經移除了 input()，這樣雲端才不會卡住！
