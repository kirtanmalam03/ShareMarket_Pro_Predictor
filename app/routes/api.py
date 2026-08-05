from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required, current_user
from app.services.stock_service import get_historical_data, get_live_data, get_market_overview, get_prediction, search_indian_stocks, get_nifty50_stocks, is_indian_stock
from app.services.portfolio_service import PortfolioService

api_bp = Blueprint("api", __name__)

@api_bp.get("/live/<symbol>")
def live(symbol: str):
    try:
        return jsonify({"ok": True, "data": get_live_data(symbol)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.get("/historical/<symbol>")
def historical(symbol: str):
    period = request.args.get("period", "3mo")
    interval = request.args.get("interval", "1d")
    try:
        return jsonify({"ok": True, "data": get_historical_data(symbol, period, interval)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.get("/predict/<symbol>")
def predict(symbol: str):
    try:
        return jsonify({"ok": True, "data": get_prediction(symbol)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.get("/market/overview")
def market_overview():
    symbols = request.args.get("symbols")
    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else current_app.config["TOP_STOCKS"]
    try:
        return jsonify({"ok": True, "data": get_market_overview(symbol_list[:6])})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

# ============================================
# INDIAN STOCKS API ENDPOINTS (NEW)
# ============================================

@api_bp.get("/indian/search/<query>")
def search_indian(query: str):
    """Search for Indian stocks by symbol or name"""
    try:
        results = search_indian_stocks(query)
        return jsonify({"ok": True, "data": results})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.get("/indian/nifty50")
def get_nifty50():
    """Get all NIFTY 50 stocks"""
    try:
        stocks = get_nifty50_stocks()
        return jsonify({"ok": True, "data": stocks})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.get("/indian/check/<symbol>")
def check_indian(symbol: str):
    """Check if a symbol is an Indian stock"""
    try:
        is_indian = is_indian_stock(symbol)
        return jsonify({"ok": True, "data": {"symbol": symbol.upper(), "is_indian": is_indian}})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

# ============================================
# PORTFOLIO API ENDPOINTS
# ============================================

@api_bp.get("/portfolio")
@login_required
def get_portfolio():
    try:
        portfolio = PortfolioService.get_user_portfolio(current_user.id)
        return jsonify({"ok": True, "data": portfolio})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.post("/portfolio/add")
@login_required
def add_to_portfolio():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        shares = int(data.get('shares', 0))
        buy_price = float(data.get('buy_price', 0))
        notes = data.get('notes', '')
        
        if not symbol:
            return jsonify({"ok": False, "error": "Symbol required"}), 400
        
        result = PortfolioService.add_stock(current_user.id, symbol, shares, buy_price, notes)
        if result:
            return jsonify({"ok": True, "message": f"{symbol} added to portfolio"})
        else:
            return jsonify({"ok": False, "error": "Failed to add stock"}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.delete("/portfolio/remove/<symbol>")
@login_required
def remove_from_portfolio(symbol):
    try:
        result = PortfolioService.remove_stock(current_user.id, symbol.upper())
        if result:
            return jsonify({"ok": True, "message": f"{symbol} removed from portfolio"})
        else:
            return jsonify({"ok": False, "error": "Failed to remove stock"}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@api_bp.put("/portfolio/update/<symbol>")
@login_required
def update_portfolio_stock(symbol):
    try:
        data = request.get_json()
        shares = data.get('shares')
        buy_price = data.get('buy_price')
        notes = data.get('notes')
        
        result = PortfolioService.update_stock(current_user.id, symbol.upper(), shares, buy_price, notes)
        if result:
            return jsonify({"ok": True, "message": f"{symbol} updated"})
        else:
            return jsonify({"ok": False, "error": "Failed to update stock"}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400