from flask import Flask
from flask_migrate import Migrate
from database import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///subastaya.db"

db.init_app(app)
migrate = Migrate(app, db)

from models import Categoria, Usuario, Billetera, Subasta, Puja, TransaccionLedger, AuditoriaLog

@app.route("/")
def home():
    return "SubastaYa está funcionando 🎉"

if __name__ == "__main__":
    app.run(debug=True)