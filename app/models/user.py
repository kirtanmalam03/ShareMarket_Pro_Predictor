import sqlite3
from flask_login import UserMixin
import os

# Don't import bcrypt at top level - will be passed
DB_PATH = 'instance/stock_predictor.db'

def get_db():
    """Get database connection"""
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create portfolio table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            shares INTEGER DEFAULT 0,
            buy_price REAL DEFAULT 0,
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, symbol)
        )
    ''')
    
    conn.commit()
    conn.close()

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    @staticmethod
    def create(username, email, password):
        """Create a new user"""
        from app import bcrypt  # Import here to avoid circular import
        
        conn = get_db()
        cursor = conn.cursor()
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(row['id'], row['username'], row['email'], row['password_hash'])
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(row['id'], row['username'], row['email'], row['password_hash'])
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(row['id'], row['username'], row['email'], row['password_hash'])
        return None
    
    def check_password(self, password):
        """Check password"""
        from app import bcrypt  # Import here to avoid circular import
        return bcrypt.check_password_hash(self.password_hash, password)