from flask import Blueprint, jsonify
from models import Categoria

categorias_bp = Blueprint("categorias", __name__)

@categorias_bp.route("/api/categories", methods=["GET"])
def listar_categorias():
    """
    Listado de categorías
    Devuelve todas las categorías disponibles para clasificar subastas.
    ---
    tags:
      - Categorías
  responses:
    200:
      description: Lista de categorías
      schema:
        type: array
        items:
          type: object
          properties:
            id:
              type: integer
              example: 1
            nombre:
              type: string
              example: Tecnología
            url_icono:
              type: string
        example: null
    """
    categorias = Categoria.query.all()
    resultado = [
        {"id": c.id, "nombre": c.nombre, "url_icono": c.url_icono}
        for c in categorias
    ]
    return jsonify(resultado)