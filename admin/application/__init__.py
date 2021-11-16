# application/__init__.py
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

login_manager = LoginManager()
bootstrap = Bootstrap()
UPLOAD_FOLDER = 'application/static/images'


def create_app():
    app = Flask(__name__, static_folder='static')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['WTF_CSRF_ENABLED'] = False
    app.config.update(
    TESTING=True,
    SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
    )
    login_manager.init_app(app)
    login_manager.login_message = "You must be login to access this page."
    login_manager.login_view = "frontend.login"

    bootstrap.init_app(app)

    with app.app_context():
        from .frontend import frontend_blueprint
        app.register_blueprint(frontend_blueprint)

        return app
