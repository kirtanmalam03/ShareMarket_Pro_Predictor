import sqlite3
from app.models.user import get_db

class Portfolio:
    @staticmethod
    def add_stock(user_id, symbol, shares=0, buy_price=0, notes=""):
        """Add stock to user's portfolio"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO portfolio (user_id, symbol, shares, buy_price, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, symbol) DO UPDATE SET
                    shares = excluded.shares,
                    buy_price = excluded.buy_price,
                    notes = excluded.notes
            ''', (user_id, symbol.upper(), shares, buy_price, notes))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding stock: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def remove_stock(user_id, symbol):
        """Remove stock from portfolio"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM portfolio WHERE user_id = ? AND symbol = ?', (user_id, symbol.upper()))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_user_portfolio(user_id):
        """Get all stocks in user's portfolio"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM portfolio WHERE user_id = ? ORDER BY added_at DESC', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def update_stock(user_id, symbol, shares=None, buy_price=None, notes=None):
        """Update stock details"""
        conn = get_db()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if shares is not None:
            updates.append("shares = ?")
            params.append(shares)
        if buy_price is not None:
            updates.append("buy_price = ?")
            params.append(buy_price)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        
        if updates:
            params.extend([user_id, symbol.upper()])
            query = f'UPDATE portfolio SET {", ".join(updates)} WHERE user_id = ? AND symbol = ?'
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return True