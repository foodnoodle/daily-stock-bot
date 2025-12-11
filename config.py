# --- config.py ---
import data_fetchers as df # 匯入剛剛建立的 yfinance 抓取器
# 匯入現有的爬蟲模組
from aaii_index import fetch_aaii_bull_bear_diff
from fear_greed_index import fetch_fear_greed_meter
from naaim_index import fetch_naaim_exposure_index
from skew_index import fetch_skew_index
from above_200_days_average import fetch_above_200_days_average
from put_call_ratio import fetch_put_call_ratio

# 這裡控制你要跑哪些指標
INDICATORS = {
    # --- 1. 🌊 宏觀與資金 ---
    'BOND_10Y': {
        'name': '🇺🇸 10年債', 'category': 'macro', 'type': 'price', 'ticker': '^TNX',
        'thresholds': (3.5, 4.5), 'inverse': True, 'correction': 0.1
    },
    'DXY': {
        'name': '💵 美元 DXY', 'category': 'macro', 'type': 'price', 'ticker': 'DX-Y.NYB',
        'thresholds': (101, 105), 'inverse': True
    },
    'HYG': {
        'name': '💳 高收債 HYG', 'category': 'macro', 'type': 'trend', 'ticker': 'HYG',
        'thresholds': 'ma_trend'
    },
    'BTC': {
        'name': '🪙 比特幣', 'category': 'macro', 'type': 'custom', 'func': df.fetch_bitcoin_trend,
        'thresholds': (3.0, -3.0)
    },

    # --- 2. 🏗️ 結構與板塊 ---
    'IWM': {
        'name': '🏢 羅素2000', 'category': 'struct', 'type': 'trend', 'ticker': 'IWM',
        'thresholds': 'ma_trend'
    },
    'SOXX': {
        'name': '⚡ 半導體 SOXX', 'category': 'struct', 'type': 'trend', 'ticker': 'SOXX',
        'thresholds': 'ma_trend'
    },
    'RISK_RATIO': {
        'name': '⚖️ 風險胃口', 'category': 'struct', 'type': 'custom', 'func': df.fetch_risk_on_off_ratio,
        'thresholds': 'arrow_trend'
    },

    # --- 3. 🌡️ 技術與情緒 ---
    'RSI': {
        'name': '📈 大盤 RSI', 'category': 'tech', 'type': 'custom', 'func': df.fetch_rsi_index,
        'thresholds': (30, 70), 'inverse': True
    },
    'VIX': {
        'name': '🌪️ VIX 波動', 'category': 'tech', 'type': 'price', 'ticker': '^VIX',
        'thresholds': (30, 15), 'inverse': False
    },
    'CNN': {
        'name': '😱 CNN 情緒', 'category': 'tech', 'type': 'external', 'func': fetch_fear_greed_meter,
        'thresholds': (45, 55), 'inverse': True
    },
    'ABOVE_200_DAYS': {
        'name': '📊 >200日線', 'category': 'tech', 'type': 'external', 'func': fetch_above_200_days_average,
        'thresholds': (20, 80), 'inverse': True
    },

    # --- 4. 🐳 籌碼與內資 ---
    'NAAIM': {
        'name': '🏦 機構持倉', 'category': 'fund', 'type': 'external', 'func': fetch_naaim_exposure_index,
        'thresholds': (40, 90), 'inverse': True
    },
    'SKEW': {
        'name': '🦢 黑天鵝 SKEW', 'category': 'fund', 'type': 'external', 'func': fetch_skew_index,
        'thresholds': (120, 140), 'inverse': True
    },
    'AAII': {
        'name': '🐂 散戶 AAII', 'category': 'fund', 'type': 'external', 'func': fetch_aaii_bull_bear_diff,
        'thresholds': (-15, 15), 'inverse': True
    },
    'PUT_CALL': {
        'name': '⚖️ Put/Call', 'category': 'fund', 'type': 'external', 'func': fetch_put_call_ratio,
        'thresholds': (1.0, 0.8), 'inverse': False
    }
}
