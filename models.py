from database import db
from datetime import datetime, timezone

class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    url_icono = db.Column(db.String(255))


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Billetera(db.Model):
    __tablename__ = "billeteras"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    saldo_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    saldo_retenido = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    saldo_disponible = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=1)

    usuario = db.relationship("Usuario", backref=db.backref("billetera", uselist=False))


class Subasta(db.Model):
    __tablename__ = "subastas"

    id = db.Column(db.Integer, primary_key=True)
    vendedor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    url_imagen = db.Column(db.String(255))
    precio_base = db.Column(db.Numeric(12, 2), nullable=False)
    incremento_minimo = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="PROGRAMADA")
    version = db.Column(db.Integer, nullable=False, default=1)

    vendedor = db.relationship("Usuario", backref="subastas_publicadas")
    categoria = db.relationship("Categoria", backref="subastas")


class Puja(db.Model):
    __tablename__ = "pujas"

    id = db.Column(db.Integer, primary_key=True)
    subasta_id = db.Column(db.Integer, db.ForeignKey("subastas.id"), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_puja = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subasta = db.relationship("Subasta", backref="pujas")
    comprador = db.relationship("Usuario", backref="pujas_realizadas")


class TransaccionLedger(db.Model):
    __tablename__ = "transacciones_ledger"

    id = db.Column(db.Integer, primary_key=True)
    billetera_id = db.Column(db.Integer, db.ForeignKey("billeteras.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    subasta_id = db.Column(db.Integer, db.ForeignKey("subastas.id"), nullable=True)

    billetera = db.relationship("Billetera", backref="movimientos")
    subasta = db.relationship("Subasta", backref="movimientos_ledger")


class AuditoriaLog(db.Model):
    __tablename__ = "auditoria_logs"

    id = db.Column(db.Integer, primary_key=True)
    entidad = db.Column(db.String(50), nullable=False)
    entidad_id = db.Column(db.Integer, nullable=False)
    accion = db.Column(db.String(50), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    detalle_json = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    usuario = db.relationship("Usuario", backref="acciones_auditadas")


   