import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator

FEATURE_COLUMNS = [
    "sma_5",
    "sma_10", 
    "sma_20",
    "sma_50",
    "ema_12",
    "ema_26",
    "rsi",
    "macd",
    "macd_signal",
    "bb_high",
    "bb_low",
    "atr",
    "obv",
    "volume_ratio",
    "returns_1d",
    "log_returns_1d",
    "rolling_volatility_20",
    "price_position_20",
]

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create technical features for ML model"""
    data = df.copy()
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]
    
    # Moving averages
    data["sma_5"] = SMAIndicator(close, window=5).sma_indicator()
    data["sma_10"] = SMAIndicator(close, window=10).sma_indicator()
    data["sma_20"] = SMAIndicator(close, window=20).sma_indicator()
    data["sma_50"] = SMAIndicator(close, window=50).sma_indicator()
    data["ema_12"] = EMAIndicator(close, window=12).ema_indicator()
    data["ema_26"] = EMAIndicator(close, window=26).ema_indicator()
    
    # RSI
    data["rsi"] = RSIIndicator(close, window=14).rsi()
    
    # MACD
    macd = MACD(close)
    data["macd"] = macd.macd()
    data["macd_signal"] = macd.macd_signal()
    
    # Bollinger Bands
    bb = BollingerBands(close, window=20, window_dev=2)
    data["bb_high"] = bb.bollinger_hband()
    data["bb_low"] = bb.bollinger_lband()
    
    # ATR
    data["atr"] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    
    # OBV
    data["obv"] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
    
    # Volume ratio
    data["volume_ratio"] = volume / volume.rolling(20).mean()
    
    # Returns
    data["returns_1d"] = close.pct_change()
    data["log_returns_1d"] = np.log(close / close.shift(1))
    
    # Volatility
    data["rolling_volatility_20"] = data["returns_1d"].rolling(20).std()
    
    # Price position
    min_20 = close.rolling(20).min()
    max_20 = close.rolling(20).max()
    data["price_position_20"] = (close - min_20) / (max_20 - min_20 + 1e-9)
    
    # Target variable
    data["target"] = (close.shift(-1) > close).astype(int)
    
    # Drop NaN values
    data = data.dropna()
    
    return data