from flask import Flask, render_template, request, redirect, url_for
from models import db, Auto, Arreglo

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///autos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    autos = Auto.query.all()
    return render_template('index.html', autos=autos)

@app.route('/agregar', methods=['POST'])
def agregar_auto():
    nuevo_auto = Auto(
        marca=request.form['marca'],
        modelo=request.form['modelo'],
        version=request.form['version'],
        anio=request.form['anio'],
        km=request.form['km'],
        fecha_compra=request.form['fecha_compra'],
        lugar_compra=request.form['lugar_compra'],
        tipo_compra=request.form['tipo_compra'],
        costo_compra=request.form['costo_compra']
    )
    db.session.add(nuevo_auto)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>')
def eliminar_auto(id):
    auto = Auto.query.get_or_404(id)
    db.session.delete(auto)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_auto(id):
    auto = Auto.query.get_or_404(id)
    if request.method == 'POST':
        auto.marca = request.form['marca']
        auto.modelo = request.form['modelo']
        auto.version = request.form['version']
        auto.anio = request.form['anio']
        auto.km = request.form['km']
        auto.fecha_compra = request.form['fecha_compra']
        auto.condicion_prendado = request.form['condicion_prendado']
        auto.tipo_compra = request.form['tipo_compra']
        auto.costo_compra = request.form['costo_compra']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('editar.html', auto=auto)

@app.route('/eliminar_arreglo/<int:id>')
def eliminar_arreglo(id):
    arreglo = Arreglo.query.get_or_404(id)
    auto_id = arreglo.id_auto
    db.session.delete(arreglo)
    db.session.commit()
    return redirect(url_for('arreglos_auto', id=auto_id))

@app.route('/editar_arreglo/<int:id>', methods=['GET', 'POST'])
def editar_arreglo(id):
    arreglo = Arreglo.query.get_or_404(id)
    if request.method == 'POST':
        arreglo.descripcion = request.form['descripcion']
        arreglo.fecha_arreglo = request.form['fecha_arreglo']
        arreglo.costo = request.form['costo']
        arreglo.lugar_arreglo = request.form['lugar_arreglo']
        db.session.commit()
        return redirect(url_for('arreglos_auto', id=arreglo.id_auto))
    return render_template('editar_arreglo.html', arreglo=arreglo)

@app.route('/informacion/<int:id>')
def informacion_auto(id):
    auto = Auto.query.get_or_404(id)
    # Usamos id_auto porque así está definido en el modelo
    arreglos = Arreglo.query.filter_by(id_auto=id).all()
    return render_template('informacion.html', auto=auto, arreglos=arreglos)

@app.route('/arreglos/<int:id>')
def arreglos_auto(id):
    auto = Auto.query.get_or_404(id)
    arreglos = Arreglo.query.filter_by(id_auto=id).all()
    return render_template('arreglos.html', auto=auto, arreglos=arreglos)
@app.route('/agregar_arreglo/<int:id>', methods=['POST'])
def agregar_arreglo(id):
    auto = Auto.query.get_or_404(id)
    nuevo_arreglo = Arreglo(
        descripcion=request.form['descripcion'],
        fecha_arreglo=request.form['fecha_arreglo'],
        costo=request.form['costo'],
        lugar_arreglo=request.form['lugar_arreglo'],
        id_auto=auto.id   # importante: usar id_auto porque así está en tu modelo
    )
    db.session.add(nuevo_arreglo)
    db.session.commit()
    return redirect(url_for('arreglos_auto', id=auto.id))


if __name__ == '__main__':
    app.run(debug=True)
