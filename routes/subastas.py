from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from database import db
from models import Subasta, Categoria, Usuario, AuditoriaLog
from utils import to_iso_utc, usuario_autenticado_id

subastas_bp = Blueprint("subastas", _name_)

@subastas_bp.route("/api/auctions", methods=["GET"])
def listar_subastas():
    """
    Listado de subastas
    Devuelve subastas con filtros opcionales, ordenamiento y paginación.
    ---
    tags:
      - Subastas
    parameters:
      - name: estado
        in: query
        type: string
        enum: [ACTIVA, PROGRAMADA, FINALIZADA]
        required: false
        description: "FINALIZADA incluye también DESIERTA y CANCELADA."
      - name: categoria_id
        in: query
        type: integer
        required: false
      - name: precio_min
        in: query
        type: number
        required: false
      - name: precio_max
        in: query
        type: number
        required: false
      - name: orden
        in: query
        type: string
        enum: [tiempo, puja]
        required: false
        description: "'tiempo' = menor tiempo restante primero. 'puja' = mayor puja primero."
      - name: pagina
        in: query
        type: integer
        default: 1
      - name: por_pagina
        in: query
        type: integer
        default: 8
    responses:
      200:
        description: Página de subastas que coinciden con los filtros
        schema:
          type: object
          properties:
            subastas:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  titulo:
                    type: string
                    example: Notebook Gamer
                  descripcion:
                    type: string
                    example: Notebook gamer usada, buen estado.
                  categoria:
                    type: string
                    example: Tecnología
                  url_imagen:
                    type: string
                    example: null
                  precio_base:
                    type: string
                    example: "30000.00"
                  incremento_minimo:
                    type: string
                    example: "5000.00"
                  fecha_inicio:
                    type: string
                    example: "2026-09-03T02:42:47Z"
                  fecha_fin:
                    type: string
                    example: "2026-09-03T04:07:47Z"
                  estado:
                    type: string
                    example: ACTIVA
                  puja_actual:
                    type: string
                    example: "75000.00"
                  cantidad_pujas:
                    type: integer
                    example: 5
            pagina:
              type: integer
              example: 1
            por_pagina:
              type: integer
              example: 8
            total:
              type: integer
              example: 12
            total_paginas:
              type: integer
              example: 2
    """
    query = Subasta.query

    estado_filtro = request.args.get("estado")
    if estado_filtro == "ACTIVA":
        query = query.filter(Subasta.estado == "ACTIVA")
    elif estado_filtro == "PROGRAMADA":
        query = query.filter(Subasta.estado == "PROGRAMADA")
    elif estado_filtro == "FINALIZADA":
        query = query.filter(Subasta.estado.in_(["FINALIZADA", "DESIERTA", "CANCELADA"]))

    categoria_id = request.args.get("categoria_id", type=int)
    if categoria_id is not None:
        query = query.filter(Subasta.categoria_id == categoria_id)

    precio_min = request.args.get("precio_min", type=float)
    if precio_min is not None:
        query = query.filter(Subasta.precio_base >= precio_min)

    precio_max = request.args.get("precio_max", type=float)
    if precio_max is not None:
        query = query.filter(Subasta.precio_base <= precio_max)

    subastas = query.all()

    filas = []
    for s in subastas:
        pujas_ordenadas = sorted(s.pujas, key=lambda p: p.monto, reverse=True)
        puja_mas_alta = pujas_ordenadas[0].monto if pujas_ordenadas else s.precio_base
        filas.append((s, puja_mas_alta))

    orden = request.args.get("orden")
    if orden == "tiempo":
        filas.sort(key=lambda fila: fila[0].fecha_fin)
    elif orden == "puja":
        filas.sort(key=lambda fila: fila[1], reverse=True)

    total = len(filas)

    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1

    por_pagina = request.args.get("por_pagina", 8, type=int)
    por_pagina = max(1, min(por_pagina, 50))

    import math
    total_paginas = max(1, math.ceil(total / por_pagina))
    inicio = (pagina - 1) * por_pagina
    filas_pagina = filas[inicio:inicio + por_pagina]

    subastas_json = [
        {
            "id": s.id,
            "titulo": s.titulo,
            "descripcion": s.descripcion,
            "categoria": s.categoria.nombre,
            "url_imagen": s.url_imagen,
            "precio_base": str(s.precio_base),
            "incremento_minimo": str(s.incremento_minimo),
            "fecha_inicio": to_iso_utc(s.fecha_inicio),
            "fecha_fin": to_iso_utc(s.fecha_fin),
            "estado": s.estado,
            "puja_actual": str(puja_mas_alta),
            "cantidad_pujas": len(s.pujas),
        }
        for s, puja_mas_alta in filas_pagina
    ]

    return jsonify({
        "subastas": subastas_json,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": total,
        "total_paginas": total_paginas,
    })


@subastas_bp.route("/api/auctions/<int:auction_id>", methods=["GET"])
def obtener_subasta(auction_id):
    """
    Detalle de una subasta
    Devuelve toda la información de una subasta puntual, incluida la puja más alta.
    ---
    tags:
      - Subastas
    parameters:
      - name: auction_id
        in: path
        type: integer
        required: true
        example: 1
    responses:
      200:
        description: Detalle de la subasta
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            titulo:
              type: string
              example: Notebook Gamer
            descripcion:
              type: string
              example: Notebook gamer usada, buen estado.
            categoria:
              type: string
              example: Tecnología
            vendedor:
              type: string
              example: Vendedor Demo
            vendedor_id:
              type: integer
              example: 1
            precio_base:
              type: string
              example: "30000.00"
            incremento_minimo:
              type: string
              example: "5000.00"
            fecha_inicio:
              type: string
              example: "2026-09-03T02:42:47Z"
            fecha_fin:
              type: string
              example: "2026-09-03T04:07:47Z"
            estado:
              type: string
              example: ACTIVA
            puja_actual:
              type: string
              example: "75000.00"
            cantidad_pujas:
              type: integer
              example: 5
      404:
        description: No existe una subasta con ese id
        schema:
          type: object
          properties:
            error:
              type: string
              example: Subasta no encontrada
    """
    subasta = Subasta.query.get(auction_id)
    if subasta is None:
        return jsonify({"error": "Subasta no encontrada"}), 404

    pujas_ordenadas = sorted(subasta.pujas, key=lambda p: p.monto, reverse=True)
    puja_mas_alta = pujas_ordenadas[0].monto if pujas_ordenadas else subasta.precio_base

    resultado = {
        "id": subasta.id,
        "titulo": subasta.titulo,
        "descripcion": subasta.descripcion,
        "categoria": subasta.categoria.nombre,
        "vendedor": subasta.vendedor.nombre,
        "vendedor_id": subasta.vendedor_id,
        "precio_base": str(subasta.precio_base),
        "incremento_minimo": str(subasta.incremento_minimo),
        "fecha_inicio": to_iso_utc(subasta.fecha_inicio),
        "fecha_fin": to_iso_utc(subasta.fecha_fin),
        "estado": subasta.estado,
        "puja_actual": str(puja_mas_alta),
        "cantidad_pujas": len(subasta.pujas),
    }
    return jsonify(resultado)


@subastas_bp.route("/api/auctions", methods=["POST"])
def crear_subasta():
    """
    Publicar una subasta nueva
    Requiere sesión iniciada. El vendedor se toma de la sesión, no del cuerpo del pedido.
    ---
    tags:
      - Subastas
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - categoria_id
            - titulo
            - descripcion
            - precio_base
            - incremento_minimo
            - fecha_inicio
            - fecha_fin
          properties:
            categoria_id:
              type: integer
              example: 1
            titulo:
              type: string
              example: Bicicleta de montaña
            descripcion:
              type: string
              example: Rodado 29, poco uso.
            url_imagen:
              type: string
              example: null
            precio_base:
              type: number
              example: 50000
            incremento_minimo:
              type: number
              example: 5000
            fecha_inicio:
              type: string
              example: "2026-09-20T00:00:00Z"
            fecha_fin:
              type: string
              example: "2026-09-27T00:00:00Z"
    responses:
      201:
        description: Subasta creada
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 12
            titulo:
              type: string
              example: Bicicleta de montaña
            estado:
              type: string
              example: PROGRAMADA
      400:
        description: Datos faltantes o inválidos
        schema:
          type: object
          properties:
            error:
              type: string
              example: "fecha_fin debe ser posterior a fecha_inicio"
      401:
        description: No hay sesión iniciada
        schema:
          type: object
          properties:
            error:
              type: string
              example: Necesitás iniciar sesión para publicar una subasta
      404:
        description: Categoría no encontrada
        schema:
          type: object
          properties:
            error:
              type: string
              example: Categoría no encontrada
    """
    vendedor_id = usuario_autenticado_id()
    if vendedor_id is None:
        return jsonify({"error": "Necesitás iniciar sesión para publicar una subasta"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Falta el cuerpo JSON del pedido"}), 400

    campos_requeridos = ["categoria_id", "titulo", "descripcion",
                          "precio_base", "incremento_minimo", "fecha_inicio", "fecha_fin"]
    faltantes = [c for c in campos_requeridos if data.get(c) is None]
    if faltantes:
        return jsonify({"error": f"Faltan campos: {', '.join(faltantes)}"}), 400

    vendedor = Usuario.query.get(vendedor_id)
    if vendedor is None:
        return jsonify({"error": "Vendedor no encontrado"}), 404

    categoria = Categoria.query.get(data["categoria_id"])
    if categoria is None:
        return jsonify({"error": "Categoría no encontrada"}), 404

    try:
        precio_base = Decimal(str(data["precio_base"]))
        incremento_minimo = Decimal(str(data["incremento_minimo"]))
    except InvalidOperation:
        return jsonify({"error": "precio_base e incremento_minimo deben ser números válidos"}), 400

    if precio_base <= 0 or incremento_minimo <= 0:
        return jsonify({"error": "precio_base e incremento_minimo deben ser positivos"}), 400

    try:
        fecha_inicio = datetime.fromisoformat(data["fecha_inicio"])
        fecha_fin = datetime.fromisoformat(data["fecha_fin"])
    except ValueError:
        return jsonify({"error": "fecha_inicio y fecha_fin deben tener formato ISO 8601"}), 400

    if fecha_inicio.tzinfo is None:
        fecha_inicio = fecha_inicio.replace(tzinfo=timezone.utc)
    if fecha_fin.tzinfo is None:
        fecha_fin = fecha_fin.replace(tzinfo=timezone.utc)

    if fecha_fin <= fecha_inicio:
        return jsonify({"error": "fecha_fin debe ser posterior a fecha_inicio"}), 400

    ahora = datetime.now(timezone.utc)
    estado_inicial = "ACTIVA" if fecha_inicio <= ahora else "PROGRAMADA"

    nueva_subasta = Subasta(
        vendedor_id=vendedor.id,
        categoria_id=categoria.id,
        titulo=data["titulo"],
        descripcion=data["descripcion"],
        url_imagen=data.get("url_imagen"),
        precio_base=precio_base,
        incremento_minimo=incremento_minimo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=estado_inicial,
    )
    db.session.add(nueva_subasta)
    db.session.commit()

    return jsonify({
        "id": nueva_subasta.id,
        "titulo": nueva_subasta.titulo,
        "estado": nueva_subasta.estado,
    }), 201


@subastas_bp.route("/api/auctions/<int:auction_id>", methods=["DELETE"])
def cancelar_subasta(auction_id):
    """
    tags:
      - Subastas
    parameters:
      - name: auction_id
        in: path
        type: integer
        required: true
        example: 12
    responses:
      200:
        description: Subasta cancelada
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 12
            estado:
              type: string
              example: CANCELADA
      400:
        description: La subasta ya tiene ofertas, o ya está en un estado final
        schema:
          type: object
          properties:
            error:
              type: string
              example: No podés cancelar una subasta que ya tiene ofertas
      401:
        description: No hay sesión iniciada
        schema:
          type: object
          properties:
            error:
              type: string
              example: Necesitás iniciar sesión
      403:
        description: La subasta no te pertenece
        schema:
          type: object
          properties:
            error:
              type: string
              example: No podés cancelar una subasta que no publicaste vos
      404:
        description: No existe una subasta con ese id
        schema:
          type: object
          properties:
            error:
              type: string
              example: Subasta no encontrada
    """
    usuario_id = usuario_autenticado_id()
    if usuario_id is None:
        return jsonify({"error": "Necesitás iniciar sesión"}), 401

    subasta = Subasta.query.get(auction_id)
    if subasta is None:
        return jsonify({"error": "Subasta no encontrada"}), 404

    if subasta.vendedor_id != usuario_id:
        return jsonify({"error": "No podés cancelar una subasta que no publicaste vos"}), 403

    if subasta.estado not in ("PROGRAMADA", "ACTIVA"):
        return jsonify({"error": "Esta subasta ya está en un estado final, no se puede cancelar"}), 400

    if len(subasta.pujas) > 0:
        return jsonify({"error": "No podés cancelar una subasta que ya tiene ofertas"}), 400

    subasta.estado = "CANCELADA"
    db.session.add(AuditoriaLog(
        entidad="SUBASTA",
        entidad_id=subasta.id,
        accion="SUBASTA_CANCELADA",
        usuario_id=usuario_id,
        detalle_json=None,
    ))
    db.session.commit()

    return jsonify({"id": subasta.id, "estado": subasta.estado}), 200