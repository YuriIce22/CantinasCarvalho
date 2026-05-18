import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from cantinas_carvalho.models import Usuario, db

app = Flask(__name__)

# ======================
# CONFIGS
# ======================
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret")

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:admin@localhost:5432/cantinas_carvalho'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# EMAIL
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = "pmariaisabel229@gmail.com"
app.config['MAIL_PASSWORD'] = "ychnuibgjzpbutep"
app.config['MAIL_DEFAULT_SENDER'] = 'pmariaisabel229@gmail.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_TIMEOUT'] = 10

# ======================
# EXTENÇÕES
# ======================
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
mail = Mail(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

from cantinas_carvalho import routes