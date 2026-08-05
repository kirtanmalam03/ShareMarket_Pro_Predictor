from app.models.portfolio import Portfolio
from app.services.stock_service import get_live_data

class PortfolioService:
    @staticmethod
    def add_stock(user_id, symbol, shares=0, buy_price=0, notes=""):
        """Add stock to portfolio"""
        return Portfolio.add_stock(user_id, symbol, shares, buy_price, notes)
    
    @staticmethod
    def remove_stock(user_id, symbol):
        """Remove stock from portfolio"""
        return Portfolio.remove_stock(user_id, symbol)
    
    @staticmethod
    def get_user_portfolio(user_id):
        """Get portfolio with current prices"""
        stocks = Portfolio.get_user_portfolio(user_id)
        
        # Add current market data
        for stock in stocks:
            try:
                live_data = get_live_data(stock['symbol'])
                stock['current_price'] = live_data['price']
                stock['change_percent'] = live_data['change_percent']
                stock['current_value'] = stock['current_price'] * stock['shares'] if stock['shares'] else 0
                stock['profit_loss'] = stock['current_value'] - (stock['buy_price'] * stock['shares']) if stock['buy_price'] else 0
                stock['profit_loss_percent'] = ((stock['current_price'] - stock['buy_price']) / stock['buy_price'] * 100) if stock['buy_price'] else 0
            except:
                stock['current_price'] = 0
                stock['change_percent'] = 0
                stock['current_value'] = 0
                stock['profit_loss'] = 0
                stock['profit_loss_percent'] = 0
        
        return stocks
    
    @staticmethod
    def update_stock(user_id, symbol, shares=None, buy_price=None, notes=None):
        """Update stock details"""
        return Portfolio.update_stock(user_id, symbol, shares, buy_price, notes)