def to_iso_utc(fecha):
    if fecha is None:
        return None
    return fecha.isoformat() + "Z"


from flask import session


def usuario_autenticado_id():
    return session.get("usuario_id")