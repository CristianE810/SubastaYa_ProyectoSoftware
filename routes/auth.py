from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash
from models import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    Iniciar sesión
    ---
    tags:
      - Autenticación
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: comprador1@test.com
            password:
              type: string
              example: test1234
    responses:
      200:
        description: Login exitoso
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 2
            nombre:
              type: string
              example: Comprador Uno
            email:
              type: string
              example: comprador1@test.com
      400:
        description: Faltan email o password
        schema:
          type: object
          properties:
            error:
              type: string
              example: Se requieren email y password
      401:
        description: Email o contraseña incorrectos
        schema:
          type: object
          properties:
            error:
              type: string
              example: Email o contraseña incorrectos
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Falta el cuerpo JSON del pedido"}), 400

    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Se requieren email y password"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is None or not check_password_hash(usuario.password_hash, password):
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    session["usuario_id"] = usuario.id
    return jsonify({"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email})


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    """
    Cerrar sesión
    Elimina la cookie de sesión actual.
    ---
    tags:
      - Autenticación
    responses:
      200:
        description: Sesión cerrada
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: Sesión cerrada
    """
    session.pop("usuario_id", None)
    return jsonify({"mensaje": "Sesión cerrada"})


@auth_bp.route("/api/auth/me", methods=["GET"])
def me():
    """
    Usuario logueado actualmente
    Devuelve los datos del usuario de la sesión actual, o null si nadie inició sesión.
    ---
    tags:
      - Autenticación
    responses:
      200:
        description: Estado de la sesión
        schema:
          type: object
          properties:
            usuario:
              type: object
              properties:
                id:
                  type: integer
                  example: 2
                nombre:
                  type: string
                  example: Comprador Uno
                email:
                  type: string
                  example: comprador1@test.com
    """
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return jsonify({"usuario": None})

    usuario = Usuario.query.get(usuario_id)
    if usuario is None:
        session.pop("usuario_id", None)
        return jsonify({"usuario": None})

    return jsonify({"usuario": {"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email}})