from flask import Flask, render_template
from flask_migrate import Migrate
from flasgger import Swagger
from database import db
from routes.categorias import categorias_bp
from routes.subastas import subastas_bp
from routes.wallet import wallet_bp
from routes.bids import bids_bp
from routes.users import users_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///subastaya.db"
app.config["SECRET_KEY"] = "clave-secreta-para-el-tp-subastaya"

db.init_app(app)
migrate = Migrate(app, db)
swagger = Swagger(app)

from models import Categoria, Usuario, Billetera, Subasta, Puja, TransaccionLedger, AuditoriaLog

app.register_blueprint(categorias_bp)
app.register_blueprint(subastas_bp)
app.register_blueprint(wallet_bp)
app.register_blueprint(bids_bp)
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)

@app.route("/")
def home():
    return render_template("catalogo.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/publicar")
def publicar_page():
    return render_template("publicar.html")

@app.route("/subastas/<int:auction_id>")
def subasta_page(auction_id):
    return render_template("subasta.html")

@app.route("/billetera")
def billetera_page():
    return render_template("billetera.html")

@app.route("/actividades")
def actividades_page():
    return render_template("actividades.html")

if __name__ == "__main__":
    app.run(debug=True, threaded=True)