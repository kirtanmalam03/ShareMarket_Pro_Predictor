from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
from app.extensions import socketio

# Initialize extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to access this page.'

# This is the missing user_loader - IMPORTANT!
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.get_by_id(int(user_id))

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Import models here to avoid circular imports
    from app.models.user import init_db
    
    # Initialize database
    init_db()
    
    # Register blueprints
    from app.routes.web import web_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    
    # Initialize SocketIO
    socketio.init_app(app, async_mode=app.config["SOCKETIO_ASYNC_MODE"], cors_allowed_origins="*")
    
    return app