from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studymate.db'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()  # only creates missing tables, existing data is untouched
        from app.db_upgrade import upgrade_chat_tables, upgrade_user_premium
        upgrade_chat_tables()
        upgrade_user_premium()

    return app