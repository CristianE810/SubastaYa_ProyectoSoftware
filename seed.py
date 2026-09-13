from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app import app
from database import db
from models import Categoria, Usuario, Billetera, Subasta, Puja, TransaccionLedger

with app.app_context():
    ahora = datetime.now(timezone.utc)

    
    tecnologia = Categoria(nombre="Tecnología")
    coleccionables = Categoria(nombre="Coleccionables")
    indumentaria = Categoria(nombre="Indumentaria")
    vehiculos = Categoria(nombre="Vehículos")
    db.session.add_all([tecnologia, coleccionables, indumentaria, vehiculos])

    
    vendedor = Usuario(email="vendedor@test.com", nombre="Vendedor Demo", password_hash="temporal")
    comprador1 = Usuario(email="comprador1@test.com", nombre="Comprador Uno", password_hash="temporal")
    comprador2 = Usuario(email="comprador2@test.com", nombre="Comprador Dos", password_hash="temporal")
    sinfondos = Usuario(email="sinfondos@test.com", nombre="Sin Fondos", password_hash="temporal")
    db.session.add_all([vendedor, comprador1, comprador2, sinfondos])

    db.session.flush()

    
    billetera_vendedor = Billetera(usuario_id=vendedor.id, saldo_total=Decimal("0"), saldo_retenido=Decimal("0"), saldo_disponible=Decimal("0"))
    billetera_c1 = Billetera(usuario_id=comprador1.id, saldo_total=Decimal("150000"), saldo_retenido=Decimal("45000"), saldo_disponible=Decimal("105000"))
    billetera_c2 = Billetera(usuario_id=comprador2.id, saldo_total=Decimal("200000"), saldo_retenido=Decimal("0"), saldo_disponible=Decimal("200000"))
    billetera_sf = Billetera(usuario_id=sinfondos.id, saldo_total=Decimal("500"), saldo_retenido=Decimal("0"), saldo_disponible=Decimal("500"))
    db.session.add_all([billetera_vendedor, billetera_c1, billetera_c2, billetera_sf])

    db.session.flush()

    
    subasta_activa = Subasta(
        vendedor_id=vendedor.id, categoria_id=tecnologia.id,
        titulo="Notebook Gamer", descripcion="Notebook gamer usada, buen estado.",
        precio_base=Decimal("30000"), incremento_minimo=Decimal("5000"),
        fecha_inicio=ahora - timedelta(hours=1), fecha_fin=ahora + timedelta(minutes=25),
        estado="ACTIVA",
    )
    subasta_critica = Subasta(
        vendedor_id=vendedor.id, categoria_id=coleccionables.id,
        titulo="Reloj de colección", descripcion="Reloj antiguo en caja original.",
        precio_base=Decimal("10000"), incremento_minimo=Decimal("1000"),
        fecha_inicio=ahora - timedelta(minutes=10), fecha_fin=ahora + timedelta(seconds=90),
        estado="ACTIVA",
    )
    subasta_proxima = Subasta(
        vendedor_id=vendedor.id, categoria_id=indumentaria.id,
        titulo="Campera de cuero", descripcion="Campera de cuero talle M, sin uso.",
        precio_base=Decimal("5000"), incremento_minimo=Decimal("500"),
        fecha_inicio=ahora + timedelta(hours=24), fecha_fin=ahora + timedelta(hours=48),
        estado="PROGRAMADA",
    )
    subasta_vencida_ganador = Subasta(
        vendedor_id=vendedor.id, categoria_id=vehiculos.id,
        titulo="Auto a escala 1:18", descripcion="Modelo a escala de colección.",
        precio_base=Decimal("20000"), incremento_minimo=Decimal("2000"),
        fecha_inicio=ahora - timedelta(days=3), fecha_fin=ahora - timedelta(days=1),
        estado="ACTIVA",
    )
    subasta_vencida_desierta = Subasta(
        vendedor_id=vendedor.id, categoria_id=tecnologia.id,
        titulo="Teclado mecánico", descripcion="Teclado mecánico sin uso, en caja.",
        precio_base=Decimal("8000"), incremento_minimo=Decimal("1000"),
        fecha_inicio=ahora - timedelta(days=3), fecha_fin=ahora - timedelta(days=1),
        estado="ACTIVA",
    )
    db.session.add_all([subasta_activa, subasta_critica, subasta_proxima, subasta_vencida_ganador, subasta_vencida_desierta])

    db.session.flush()

   
    db.session.add_all([
        Puja(subasta_id=subasta_activa.id, comprador_id=comprador2.id, monto=Decimal("40000"), fecha_puja=ahora - timedelta(minutes=40)),
        Puja(subasta_id=subasta_activa.id, comprador_id=comprador1.id, monto=Decimal("45000"), fecha_puja=ahora - timedelta(minutes=20)),
        Puja(subasta_id=subasta_vencida_ganador.id, comprador_id=comprador2.id, monto=Decimal("22000"), fecha_puja=ahora - timedelta(days=2)),
    ])

   
    db.session.add_all([
        TransaccionLedger(billetera_id=billetera_c1.id, tipo="DEPOSITO", monto=Decimal("150000")),
        TransaccionLedger(billetera_id=billetera_c2.id, tipo="DEPOSITO", monto=Decimal("200000")),
        TransaccionLedger(billetera_id=billetera_sf.id, tipo="DEPOSITO", monto=Decimal("500")),
        TransaccionLedger(billetera_id=billetera_c1.id, tipo="RETENCION", monto=Decimal("45000"), subasta_id=subasta_activa.id),
    ])

    db.session.commit()

    print(f"Categorías: {Categoria.query.count()}")
    print(f"Usuarios: {Usuario.query.count()}")
    print(f"Billeteras: {Billetera.query.count()}")
    print(f"Subastas: {Subasta.query.count()}")
    print(f"Pujas: {Puja.query.count()}")
    print(f"Movimientos en el ledger: {TransaccionLedger.query.count()}")