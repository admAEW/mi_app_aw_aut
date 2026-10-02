from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Auto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    version = db.Column(db.String(50))
    anio = db.Column(db.Integer)
    km = db.Column(db.Integer)
    fecha_compra = db.Column(db.String(20))
    condicion_prendado = db.Column(db.String(20))  # "Prendado" o "No prendado"
    tipo_compra = db.Column(db.String(50))
    costo_compra = db.Column(db.Float)

    # Datos adicionales
    fecha_venta = db.Column(db.String(20))
    lugar_compra = db.Column(db.String(100))
    precio_compra = db.Column(db.Float)
    precio_venta = db.Column(db.Float)
    cliente_nombre = db.Column(db.String(100))
    cliente_telefono = db.Column(db.String(20))
    cliente_mail = db.Column(db.String(100))

    # Relación con Arreglo (con cascade)
    arreglos = db.relationship(
        'Arreglo',
        backref='auto',
        lazy=True,
        cascade="all, delete-orphan"
    )

class Arreglo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_auto = db.Column(db.Integer, db.ForeignKey('auto.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    costo = db.Column(db.Float)
    fecha_arreglo = db.Column(db.String(20))
    lugar_arreglo = db.Column(db.String(100))
