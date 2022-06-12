import os
from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

io = SocketIO()
db = SQLAlchemy()
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '87adt976tcnm9wa67tmgc9d67a768cd87dcam5'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1977Clauwind_@localhost:5432/postgres'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    io.init_app(app)
    db.init_app(app)

    from .views import views
    from .auth  import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import association_table, Usr, Project, Ticket
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'      #where should flask redirect us if the user is not logged
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Usr.query.get(int(id))

    return app