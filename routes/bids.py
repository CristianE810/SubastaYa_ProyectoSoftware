import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from decimal import Decimal, InvalidOperation
from database import db
from models import Subasta, Usuario, Puja, Billetera, TransaccionLedger, AuditoriaLog
from utils import to_iso_utc, usuario_autenticado_id

bids_bp = Blueprint("bids", _name_)

@bids_bp.route("/api/auctions/<int:auction_id>/bids", methods=["GET"])
def listar_pujas(auction_id):
    """
    Historial de ofertas de una subasta
    Devuelve todas las pujas de una subasta, de la más reciente a la más vieja.
    El postor aparece anonimizado, salvo que sea el usuario logueado (aparece como "Vos").
    ---
    tags:
      - Pujas
    parameters:
      - name: auction_id
        in: path
        type: integer
        required: true
        example: 1
    responses:
      200:
        description: Lista de ofertas
        schema:
          type: array
          items:
            type: object
            properties:
              monto:
                type: string
                example: "75000.00"
              fecha_puja:
                type: string
                example: "2026-09-04T17:21:59Z"
              postor:
                type: string
                example: "Postor #3"
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

    usuario_actual = usuario_autenticado_id()

    pujas_ordenadas = sorted(subasta.pujas, key=lambda p: p.fecha_puja, reverse=True)
    resultado = [
        {
            "monto": str(p.monto),
            "fecha_puja": to_iso_utc(p.fecha_puja),
            "postor": "Vos" if p.comprador_id == usuario_actual else f"Postor #{p.comprador_id}",
        }
        for p in pujas_ordenadas
    ]
    return jsonify(resultado)


@bids_bp.route("/api/auctions/<int:auction_id>/bids", methods=["POST"])
def crear_puja(auction_id):
    """
    Ofertar en una subasta
    Requiere sesión iniciada; el comprador se toma de la sesión, no del cuerpo del pedido.
    Un vendedor no puede pujar en su propia subasta.
    Aplica escrow (congela saldo), optimistic locking y la regla anti-sniping (extensión de 2 min si quedan 60s o menos).
    ---
    tags:
      - Pujas
    parameters:
      - name: auction_id
        in: path
        type: integer
        required: true
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - monto
          properties:
            monto:
              type: number
              example: 55000
    responses:
      201:
        description: Puja aceptada
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 8
            subasta_id:
              type: integer
              example: 6
            comprador_id:
              type: integer
              example: 2
            monto:
              type: string
              example: "55000"
            estado:
              type: string
              example: Liderando
            subasta_extendida:
              type: boolean
              example: false
            fecha_fin_subasta:
              type: string
              example: "2026-09-10T00:00:00Z"
      400:
        description: "Pedido inválido: subasta no activa, ya cerrada, monto insuficiente o no numérico"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "El monto debe ser al menos 65000.00"
      401:
        description: No hay sesión iniciada
        schema:
          type: object
          properties:
            error:
              type: string
              example: Necesitás iniciar sesión para pujar
      403:
        description: El comprador es el vendedor de esta misma subasta
        schema:
          type: object
          properties:
            error:
              type: string
              example: No podés pujar en tu propia subasta
      404:
        description: Subasta, comprador o billetera no encontrados
        schema:
          type: object
          properties:
            error:
              type: string
              example: Subasta no encontrada
      409:
        description: "Conflicto de concurrencia (optimistic locking): otra puja se procesó primero"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "La subasta cambió mientras se procesaba tu puja, reintentá"
      422:
        description: Saldo disponible insuficiente
        schema:
          type: object
          properties:
            error:
              type: string
              example: Saldo disponible insuficiente
    """
    comprador_id = usuario_autenticado_id()
    if comprador_id is None:
        return jsonify({"error": "Necesitás iniciar sesión para pujar"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Falta el cuerpo JSON del pedido"}), 400

    monto_raw = data.get("monto")
    if monto_raw is None:
        return jsonify({"error": "Se requiere monto"}), 400

    subasta = Subasta.query.get(auction_id)
    if subasta is None:
        return jsonify({"error": "Subasta no encontrada"}), 404

    if subasta.vendedor_id == comprador_id:
        return jsonify({"error": "No podés pujar en tu propia subasta"}), 403

    comprador = Usuario.query.get(comprador_id)
    if comprador is None:
        return jsonify({"error": "Comprador no encontrado"}), 404

    if subasta.estado != "ACTIVA":
        return jsonify({"error": "La subasta no está activa"}), 400

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    if subasta.fecha_fin <= ahora:
        return jsonify({"error": "La subasta ya cerró"}), 400

    try:
        monto = Decimal(str(monto_raw))
    except InvalidOperation:
        return jsonify({"error": "El monto no es un número válido"}), 400

    pujas_ordenadas = sorted(subasta.pujas, key=lambda p: p.monto, reverse=True)
    puja_anterior = pujas_ordenadas[0] if pujas_ordenadas else None

    if puja_anterior is not None:
        minimo_valido = puja_anterior.monto + subasta.incremento_minimo
    else:
        minimo_valido = subasta.precio_base

    if monto < minimo_valido:
        return jsonify({"error": f"El monto debe ser al menos {minimo_valido}"}), 400

    billetera_comprador = Billetera.query.filter_by(usuario_id=comprador.id).first()
    if billetera_comprador is None:
        return jsonify({"error": "El comprador no tiene billetera"}), 404

    if billetera_comprador.saldo_disponible < monto:
        db.session.add(AuditoriaLog(
            entidad="SUBASTA",
            entidad_id=subasta.id,
            accion="PUJA_RECHAZADA_SALDO_INSUFICIENTE",
            usuario_id=comprador.id,
            detalle_json=json.dumps({
                "monto_intentado": str(monto),
                "saldo_disponible": str(billetera_comprador.saldo_disponible),
            }),
        ))
        db.session.commit()
        return jsonify({"error": "Saldo disponible insuficiente"}), 422

    version_leida = subasta.version
    filas_afectadas = db.session.query(Subasta).filter(
        Subasta.id == subasta.id,
        Subasta.version == version_leida,
    ).update({Subasta.version: Subasta.version + 1})

    if filas_afectadas == 0:
        db.session.rollback()
        db.session.add(AuditoriaLog(
            entidad="SUBASTA",
            entidad_id=subasta.id,
            accion="PUJA_RECHAZADA_CONCURRENCIA",
            usuario_id=comprador.id,
            detalle_json=json.dumps({"monto_intentado": str(monto)}),
        ))
        db.session.commit()
        return jsonify({"error": "La subasta cambió mientras se procesaba tu puja, reintentá"}), 409

    tiempo_restante = subasta.fecha_fin - ahora
    extendida = tiempo_restante <= timedelta(seconds=60)
    if extendida:
        fecha_fin_anterior = subasta.fecha_fin
        subasta.fecha_fin = subasta.fecha_fin + timedelta(minutes=2)
        db.session.add(AuditoriaLog(
            entidad="SUBASTA",
            entidad_id=subasta.id,
            accion="EXTENSION_ANTISNIPING",
            usuario_id=comprador.id,
            detalle_json=json.dumps({
                "fecha_fin_anterior": to_iso_utc(fecha_fin_anterior),
                "fecha_fin_nueva": to_iso_utc(subasta.fecha_fin),
            }),
        ))

    if puja_anterior is not None:
        billetera_anterior = Billetera.query.filter_by(usuario_id=puja_anterior.comprador_id).first()
        billetera_anterior.saldo_retenido -= puja_anterior.monto
        billetera_anterior.saldo_disponible += puja_anterior.monto
        db.session.add(TransaccionLedger(
            billetera_id=billetera_anterior.id, tipo="LIBERACION",
            monto=puja_anterior.monto, subasta_id=subasta.id,
        ))

    billetera_comprador.saldo_disponible -= monto
    billetera_comprador.saldo_retenido += monto
    db.session.add(TransaccionLedger(
        billetera_id=billetera_comprador.id, tipo="RETENCION",
        monto=monto, subasta_id=subasta.id,
    ))

    nueva_puja = Puja(subasta_id=subasta.id, comprador_id=comprador.id, monto=monto)
    db.session.add(nueva_puja)

    db.session.commit()

    return jsonify({
        "id": nueva_puja.id,
        "subasta_id": subasta.id,
        "comprador_id": comprador.id,
        "monto": str(monto),
        "estado": "Liderando",
        "subasta_extendida": extendida,
        "fecha_fin_subasta": to_iso_utc(subasta.fecha_fin),
    }), 201