from datetime import datetime
from typing import Any, Dict, List
import pandas as pd
import yfinance as yf
import requests
from flask import current_app

from app.ml.feature_engineering import create_features
from app.ml.model import load_or_train_model, predict_direction
from app.services.cache_service import cache_get_json, cache_set_json


# ============================================
# INDIAN STOCKS API CONFIGURATION
# ============================================

# Free Indian Stock Market API (No API key required)
INDIAN_STOCK_API = "https://military-jobye-haiqstudios-14f59639.koyeb.app"

# NIFTY 50 Stocks List (for quick access)
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "LT",
    "AXISBANK", "WIPRO", "ASIANPAINT", "HCLTECH", "MARUTI",
    "BAJFINANCE", "TITAN", "SUNPHARMA", "TECHM", "NESTLEIND",
    "POWERGRID", "ULTRACEMCO", "ADANIENT", "TATAMOTORS", "ONGC",
    "TATASTEEL", "JSWSTEEL", "NTPC", "INDUSINDBK", "M&M",
    "COALINDIA", "BAJAJFINSV", "HINDALCO", "DRREDDY", "GRASIM",
    "DIVISLAB", "BAJAJ-AUTO", "BRITANNIA", "HEROMOTOCO", "ADANIPORTS",
    "CIPLA", "UPL", "SBILIFE", "EICHERMOT", "BPCL",
    "TATACONSUM", "APOLLOHOSP", "SHREECEM", "HDFC", "NIFTY50", "SENSEX"
]

# Indian stock suffixes
INDIAN_SUFFIXES = ['.NS', '.BO', 'NIFTY', 'SENSEX', 'BANKNIFTY']


def is_indian_stock(symbol: str) -> bool:
    """Check if the symbol is an Indian stock"""
    symbol_upper = symbol.upper()
    return (symbol_upper in NIFTY_50_SYMBOLS or 
            any(suffix in symbol_upper for suffix in INDIAN_SUFFIXES))


def get_indian_stock_data(symbol: str) -> Dict[str, Any]:
    """Fetch Indian stock data using free API"""
    try:
        # Try the free Indian stock API
        response = requests.get(f"{INDIAN_STOCK_API}/stock", 
                                params={"symbol": symbol, "res": "num"},
                                timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract price from response
            price = data.get('price', 0)
            if price == 0:
                # Try alternative field names
                price = data.get('currentPrice', data.get('lastPrice', 0))
            
            previous_close = data.get('previousClose', price)
            change = price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                "symbol": symbol.upper(),
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": data.get('volume', 0),
                "day_high": data.get('dayHigh', price),
                "day_low": data.get('dayLow', price),
                "previous_close": round(previous_close, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "is_indian": True,
                "currency": "INR"
            }
    except Exception as e:
        print(f"Indian API error for {symbol}: {e}")
    
    # Fallback to yfinance with .NS suffix
    try:
        yf_symbol = f"{symbol.upper()}.NS"
        ticker = yf.Ticker(yf_symbol)
        info = ticker.fast_info
        
        if info and hasattr(info, 'last_price') and info.last_price:
            current_price = float(info.last_price)
            previous_close = float(info.previous_close) if hasattr(info, 'previous_close') else current_price
            
            return {
                "symbol": symbol.upper(),
                "price": round(current_price, 2),
                "change": round(current_price - previous_close, 2),
                "change_percent": round(((current_price - previous_close) / previous_close * 100), 2),
                "volume": int(info.last_volume) if hasattr(info, 'last_volume') else 0,
                "day_high": round(float(info.day_high), 2) if hasattr(info, 'day_high') else current_price,
                "day_low": round(float(info.day_low), 2) if hasattr(info, 'day_low') else current_price,
                "previous_close": round(previous_close, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "is_indian": True,
                "currency": "INR"
            }
    except:
        pass
    
    return None


def search_indian_stocks(query: str) -> List[Dict[str, str]]:
    """Search for Indian stocks by symbol or name using free API"""
    results = []
    query_upper = query.upper()
    
    # Search in NIFTY 50 list first
    for symbol in NIFTY_50_SYMBOLS:
        if query_upper in symbol:
            results.append({
                "symbol": symbol,
                "name": get_stock_name(symbol),
                "type": "NIFTY 50",
                "suffix": ".NS",
                "currency": "INR"
            })
    
    # Try the API search endpoint
    try:
        response = requests.get(f"{INDIAN_STOCK_API}/search", 
                                params={"q": query},
                                timeout=10)
        if response.status_code == 200:
            api_results = response.json()
            if isinstance(api_results, list):
                for item in api_results[:10]:
                    result_symbol = item.get('symbol', '').upper()
                    if result_symbol and result_symbol not in [r['symbol'] for r in results]:
                        results.append({
                            "symbol": result_symbol,
                            "name": item.get('name', result_symbol),
                            "type": item.get('type', 'NSE'),
                            "suffix": ".NS",
                            "currency": "INR"
                        })
    except:
        pass
    
    return results[:20]  # Return top 20 results


def get_stock_name(symbol: str) -> str:
    """Get company name for Indian stock symbol"""
    names = {
        "RELIANCE": "Reliance Industries Ltd.",
        "TCS": "Tata Consultancy Services Ltd.",
        "HDFCBANK": "HDFC Bank Ltd.",
        "INFY": "Infosys Ltd.",
        "ICICIBANK": "ICICI Bank Ltd.",
        "HINDUNILVR": "Hindustan Unilever Ltd.",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel Ltd.",
        "KOTAKBANK": "Kotak Mahindra Bank Ltd.",
        "LT": "Larsen & Toubro Ltd.",
        "WIPRO": "Wipro Ltd.",
        "ASIANPAINT": "Asian Paints Ltd.",
        "HCLTECH": "HCL Technologies Ltd.",
        "MARUTI": "Maruti Suzuki India Ltd.",
        "BAJFINANCE": "Bajaj Finance Ltd.",
        "TITAN": "Titan Company Ltd.",
        "SUNPHARMA": "Sun Pharmaceutical Industries Ltd.",
        "TECHM": "Tech Mahindra Ltd.",
        "NESTLEIND": "Nestle India Ltd.",
        "POWERGRID": "Power Grid Corporation of India Ltd.",
        "ULTRACEMCO": "UltraTech Cement Ltd.",
        "ADANIENT": "Adani Enterprises Ltd.",
        "TATAMOTORS": "Tata Motors Ltd.",
        "ONGC": "Oil and Natural Gas Corporation Ltd.",
        "TATASTEEL": "Tata Steel Ltd.",
        "JSWSTEEL": "JSW Steel Ltd.",
        "NTPC": "NTPC Ltd.",
        "INDUSINDBK": "IndusInd Bank Ltd.",
        "M&M": "Mahindra & Mahindra Ltd.",
        "COALINDIA": "Coal India Ltd.",
        "BAJAJFINSV": "Bajaj Finserv Ltd.",
        "HINDALCO": "Hindalco Industries Ltd.",
        "DRREDDY": "Dr. Reddy's Laboratories Ltd.",
        "GRASIM": "Grasim Industries Ltd.",
        "NIFTY50": "NIFTY 50 Index",
        "SENSEX": "BSE SENSEX Index",
        "BANKNIFTY": "NIFTY Bank Index"
    }
    return names.get(symbol.upper(), symbol)


def get_nifty50_stocks() -> List[Dict[str, str]]:
    """Get all NIFTY 50 stocks with details"""
    stocks = []
    for symbol in NIFTY_50_SYMBOLS[:50]:  # First 50 are NIFTY 50
        stocks.append({
            "symbol": symbol,
            "name": get_stock_name(symbol),
            "type": "NIFTY 50",
            "suffix": ".NS",
            "currency": "INR"
        })
    return stocks


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(_normalize_symbol(symbol))


def get_live_data(symbol: str) -> Dict[str, Any]:
    """Get real-time live stock data (supports US & Indian stocks)"""
    symbol = _normalize_symbol(symbol)
    cache_key = f"live:{symbol}"
    
    # Try to get from cache first
    cached = cache_get_json(cache_key)
    if cached:
        return cached
    
    # Check if it's an Indian stock
    if is_indian_stock(symbol):
        indian_data = get_indian_stock_data(symbol)
        if indian_data:
            cache_set_json(cache_key, indian_data, current_app.config.get("CACHE_TTL_SECONDS", 30))
            return indian_data
    
    # Handle US stocks with yfinance
    try:
        ticker = _ticker(symbol)
        
        # Try fast_info first (faster)
        try:
            info = ticker.fast_info
            if info and hasattr(info, 'last_price') and info.last_price:
                current_price = float(info.last_price)
                previous_close = float(info.previous_close) if hasattr(info, 'previous_close') and info.previous_close else current_price
                volume = int(info.last_volume) if hasattr(info, 'last_volume') and info.last_volume else 0
                day_high = float(info.day_high) if hasattr(info, 'day_high') and info.day_high else current_price
                day_low = float(info.day_low) if hasattr(info, 'day_low') and info.day_low else current_price
            else:
                raise AttributeError("fast_info not available")
        except:
            # Fallback to info dictionary
            info = ticker.info
            current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            previous_close = info.get('regularMarketPreviousClose', info.get('previousClose', current_price))
            volume = info.get('regularMarketVolume', 0)
            day_high = info.get('regularMarketDayHigh', current_price)
            day_low = info.get('regularMarketDayLow', current_price)
        
        if current_price == 0:
            raise ValueError(f"No live data available for {symbol}")
        
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0.0
        
        data = {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(volume),
            "day_high": round(day_high, 2),
            "day_low": round(day_low, 2),
            "previous_close": round(previous_close, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "is_indian": False,
            "currency": "USD"
        }
        
        # Cache for 30 seconds
        cache_set_json(cache_key, data, current_app.config.get("CACHE_TTL_SECONDS", 30))
        return data
        
    except Exception as e:
        raise ValueError(f"Error fetching live data for {symbol}: {str(e)}")


def get_historical_data(symbol: str, period: str = "3mo", interval: str = "1d") -> Dict[str, Any]:
    """Get historical stock data for charts"""
    symbol = _normalize_symbol(symbol)
    cache_key = f"hist:{symbol}:{period}:{interval}"
    
    # Try cache first
    cached = cache_get_json(cache_key)
    if cached:
        return cached
    
    # For Indian stocks, use yfinance with .NS suffix
    yf_symbol = f"{symbol}.NS" if is_indian_stock(symbol) else symbol
    
    try:
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            raise ValueError(f"No historical data found for {symbol}")
        
        # Reset index to get dates as column
        df = df.reset_index()
        
        payload = {
            "symbol": symbol,
            "dates": [d.strftime("%Y-%m-%d") for d in df['Date']],
            "close": [round(float(v), 2) for v in df['Close'].tolist()],
            "open": [round(float(v), 2) for v in df['Open'].tolist()],
            "high": [round(float(v), 2) for v in df['High'].tolist()],
            "low": [round(float(v), 2) for v in df['Low'].tolist()],
            "volume": [int(v) for v in df['Volume'].fillna(0).tolist()]
        }
        
        # Cache for 1 hour (3600 seconds)
        cache_set_json(cache_key, payload, 3600)
        return payload
        
    except Exception as e:
        raise ValueError(f"Error fetching historical data for {symbol}: {str(e)}")


def get_prediction(symbol: str) -> Dict[str, Any]:
    """Get ML prediction for stock"""
    symbol = _normalize_symbol(symbol)
    cache_key = f"pred:{symbol}"
    
    # Try cache first (predictions cached for 30 minutes)
    cached = cache_get_json(cache_key)
    if cached:
        return cached
    
    # For Indian stocks, use yfinance with .NS suffix
    yf_symbol = f"{symbol}.NS" if is_indian_stock(symbol) else symbol
    
    try:
        # Fetch 2 years of data for training
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period="2y", interval="1d")
        
        if len(df) < 60:
            raise ValueError(f"Insufficient data for {symbol}. Need at least 60 days.")
        
        # Create features and train model
        features_df = create_features(df)
        model, model_acc = load_or_train_model(df, current_app.config["MODEL_PATH"])
        
        # Make prediction
        pred = predict_direction(model, features_df, model_acc)
        
        payload = {
            "symbol": symbol,
            "direction": pred.direction,
            "confidence": pred.confidence,
            "up_probability": pred.up_probability,
            "down_probability": pred.down_probability,
            "model_accuracy": pred.model_accuracy,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache for 30 minutes (1800 seconds)
        cache_set_json(cache_key, payload, 1800)
        return payload
        
    except Exception as e:
        raise ValueError(f"Error getting prediction for {symbol}: {str(e)}")


def get_market_overview(symbols: List[str]) -> Dict[str, Any]:
    """Get overview for multiple stocks"""
    stocks_data = []
    
    for symbol in symbols:
        try:
            data = get_live_data(symbol)
            stocks_data.append(data)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue
    
    if not stocks_data:
        raise ValueError("Failed to load any market data")
    
    return {"stocks": stocks_data, "count": len(stocks_data)}


def get_portfolio_performance(symbols: List[str]) -> Dict[str, Any]:
    """Get performance data for portfolio stocks"""
    portfolio_data = []
    total_value = 0
    total_change = 0
    
    for symbol in symbols:
        try:
            live = get_live_data(symbol)
            portfolio_data.append(live)
            total_value += live['price']
        except:
            continue
    
    return {
        "stocks": portfolio_data,
        "total_value": round(total_value, 2),
        "total_change": round(total_change, 2),
        "timestamp": datetime.utcnow().isoformat()
    }