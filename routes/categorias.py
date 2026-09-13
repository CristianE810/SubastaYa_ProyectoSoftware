from flask import Blueprint, jsonify
from models import Categoria

categorias_bp = Blueprint("categorias", __name__)

@categorias_bp.route("/api/categories", methods=["GET"])
def listar_categorias():
    categorias = Categoria.query.all()
    resultado = [
        {"id": c.id, "nombre": c.nombre, "url_icono": c.url_icono}
        for c in categorias
    ]
    return jsonify(resultado)