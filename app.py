from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS autos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, marca TEXT, modelo TEXT, version TEXT, anio INTEGER, precio REAL,
        combustible TEXT, kms INTEGER, color TEXT, descripcion TEXT, puertas TEXT, transmision TEXT, motor TEXT, traccion TEXT, slug TEXT, concesionario TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS parametros (
        clave TEXT PRIMARY KEY, etiqueta TEXT, valor REAL, categoria TEXT)""")
    cur.execute("SELECT COUNT(*) FROM parametros")
    if cur.fetchone()[0]==0:
        defaults=[('nacion_fija','Nación Fija',65,'TNA'),('nacion_uva','Nación UVA',8,'TNA'),('provincia_fija','Provincia Fija',70,'TNA'),('provincia_uva','Provincia UVA',9,'TNA'),('iva_intereses','IVA sobre intereses',21,'Impuestos')]
        cur.executemany("INSERT OR IGNORE INTO parametros (clave, etiqueta, valor, categoria) VALUES (?,?,?,?)", defaults)
    cur.execute("""CREATE TABLE IF NOT EXISTS debitos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, convenio TEXT, id_deuda TEXT, moneda TEXT, fecha_venc1 TEXT, importe_venc1 REAL, mensaje TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS clientes_debitos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, identificador TEXT, nombre TEXT NOT NULL, dni_cuit TEXT, convenio TEXT, id_deuda TEXT, moneda TEXT DEFAULT '0',
        cbu TEXT, alias_cbu TEXT, banco_cuenta TEXT, tipo_cuenta TEXT, telefono TEXT, email TEXT, importe_base REAL, fecha_venc TEXT,
        estado TEXT DEFAULT 'ACTIVO', mensaje TEXT, canal_venta TEXT, condicion TEXT, observaciones TEXT,
        auto_marca TEXT, auto_anio TEXT, auto_dominio TEXT, cantidad_cuotas INTEGER, resultado_debito TEXT, motivo_rechazo TEXT,
        tarjeta_numero TEXT, tarjeta_tipo TEXT, tarjeta_banco TEXT, tarjeta_titular TEXT, empresa TEXT DEFAULT 'autos', fecha_alta TEXT DEFAULT CURRENT_TIMESTAMP)""")
    for col in ["canal_venta TEXT","condicion TEXT","observaciones TEXT","fecha_venc TEXT","mensaje TEXT","estado TEXT DEFAULT 'ACTIVO'","cbu TEXT","alias_cbu TEXT","banco_cuenta TEXT","tipo_cuenta TEXT","auto_marca TEXT","auto_anio TEXT","auto_dominio TEXT","cantidad_cuotas INTEGER","resultado_debito TEXT","motivo_rechazo TEXT","tarjeta_numero TEXT","tarjeta_tipo TEXT","tarjeta_banco TEXT","tarjeta_titular TEXT","empresa TEXT DEFAULT 'autos'"]:
        try: cur.execute(f"ALTER TABLE clientes_debitos ADD COLUMN {col}")
        except: pass
    cur.execute("""CREATE TABLE IF NOT EXISTS cuotas_seguimiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_debito_id INTEGER NOT NULL, numero_cuota INTEGER NOT NULL,
        fecha_vencimiento TEXT, importe REAL, estado TEXT DEFAULT 'Pendiente', fecha_cobro TEXT, motivo_rechazo TEXT, observaciones TEXT,
        FOREIGN KEY (cliente_debito_id) REFERENCES clientes_debitos(id) ON DELETE CASCADE)""")
    conn.commit(); conn.close()

def init_db_clientes(): init_db()
init_db(); init_db_clientes()

def cuota_francesa(monto, tna_anual, n_cuotas):
    if tna_anual==0: return monto/n_cuotas
    i=(tna_anual/100)/12; return monto*i/(1-(1+i)**-n_cuotas)
def primera_cuota_con_iva(monto, tna_anual, n_cuotas, iva_pct):
    i=(tna_anual/100)/12; cuota_pura=cuota_francesa(monto,tna_anual,n_cuotas); interes=monto*i; return cuota_pura+interes*(iva_pct/100)

# Acceso y prestamos opcionales - si fallan no rompemos la app
try:
    from acceso import registrar as registrar_acceso
    registrar_acceso(app, get_db)
except Exception as e:
    print(f"[INFO] acceso no cargado: {e}")
try:
    from prestamos import registrar as registrar_prestamos
    registrar_prestamos(app, get_db)
except Exception as e:
    print(f"[INFO] prestamos no cargado: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/panel/autos')
def panel_autos():
    try:
        return render_template('panel_autos.html')
    except Exception as e:
        return f"<h3>Panel Autos - Falta panel_autos.html en templates/</h3><p>{e}</p><p><a href='/'>Volver</a></p>", 500

@app.route('/panel/hogar')
def panel_hogar():
    try:
        return render_template('panel_hogar.html')
    except:
        return "<h3>AW Hogar - Próximamente</h3><p>En construcción</p><p><a href='/'>Volver al inicio</a></p>"

@app.route('/autos')
def autos():
    init_db(); conn=get_db(); cur=conn.cursor()
    try: cur.execute("SELECT * FROM autos"); lista=cur.fetchall()
    except: lista=[]
    conn.close(); return render_template('autos.html', autos=lista)

@app.route('/nuevo_auto', methods=['GET','POST'])
def nuevo_auto():
    if request.method=='POST':
        conn=get_db(); cur=conn.cursor()
        cur.execute("INSERT INTO autos (marca, modelo, anio) VALUES (?,?,?)",(request.form['marca'],request.form['modelo'],request.form['anio']))
        conn.commit(); conn.close(); flash("Auto agregado correctamente"); return redirect('/autos')
    return render_template('nuevo_auto.html')

@app.route('/insertar_auto', methods=['POST'])
def insertar_auto():
    conn=get_db()
    conn.execute("INSERT INTO autos (marca, modelo, version, anio, precio, combustible, kms, color, descripcion, puertas, transmision, motor, traccion, slug, concesionario) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    (request.form['marca'],request.form['modelo'],request.form['version'],request.form['anio'],request.form['precio'],request.form['combustible'],request.form['kms'],request.form['color'],request.form['descripcion'],request.form['puertas'],request.form['transmision'],request.form['motor'],request.form['traccion'],request.form['slug'],request.form['concesionario']))
    conn.commit(); conn.close(); flash("Auto agregado"); return redirect('/autos')

@app.route('/borrar/<int:id>')
def borrar(id):
    conn=get_db(); cur=conn.cursor(); cur.execute("DELETE FROM autos WHERE id=?",(id,)); conn.commit(); conn.close(); flash("Auto borrado"); return redirect('/autos')

@app.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn=get_db(); cur=conn.cursor()
    if request.method=='POST':
        cur.execute("UPDATE autos SET marca=?, modelo=?, version=?, anio=?, precio=?, combustible=?, kms=?, color=?, descripcion=?, puertas=?, transmision=?, motor=?, traccion=?, slug=?, concesionario=? WHERE id=?",
        (request.form['marca'],request.form['modelo'],request.form['version'],request.form['anio'],request.form['precio'],request.form['combustible'],request.form['kms'],request.form['color'],request.form['descripcion'],request.form['puertas'],request.form['transmision'],request.form['motor'],request.form['traccion'],request.form['slug'],request.form['concesionario'],id))
        conn.commit(); conn.close(); flash("Auto actualizado"); return redirect('/autos')
    cur.execute("SELECT * FROM autos WHERE id=?",(id,)); auto=cur.fetchone(); conn.close(); return render_template('editar_auto.html', auto=auto)

@app.route('/parametros')
def parametros():
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT clave, etiqueta, valor, categoria FROM parametros ORDER BY categoria, etiqueta"); filas=cur.fetchall(); conn.close()
    agrupados={}
    for clave, etiqueta, valor, categoria in filas: agrupados.setdefault(categoria, []).append({'clave':clave,'etiqueta':etiqueta,'valor':valor})
    return render_template('parametros.html', agrupados=agrupados, auto_id=request.args.get('volver'))

@app.route('/guardar_parametros', methods=['POST'])
def guardar_parametros():
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT clave FROM parametros"); claves=[f[0] for f in cur.fetchall()]
    for clave in claves:
        if clave in request.form: cur.execute("UPDATE parametros SET valor=? WHERE clave=?",(float(request.form[clave]),clave))
    conn.commit(); conn.close(); flash("Parámetros actualizados")
    volver_id=request.form.get('volver_id')
    if volver_id: return redirect(url_for('calcular_auto', id=volver_id))
    return redirect(url_for('parametros'))

def sugerir_gastos_por_precio(precio):
    try: p=float(precio or 0)
    except: p=0
    if p < 15000000: return 600000
    if p < 20000000: return 850000
    if p < 30000000: return 1200000
    return 1600000

@app.route("/calcular_auto/<int:id>")
def calcular_auto(id):
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM autos WHERE id=?",(id,)); auto=cur.fetchone()
    cur.execute("SELECT clave, valor FROM parametros"); tasas={k:v for k,v in cur.fetchall()}; conn.close()
    if auto is None: flash("El auto con ese ID no existe"); return redirect(url_for('autos'))
    precio=auto[5] or 0; iva_pct=tasas.get('iva_intereses',21)
    # Anticipo y gastos pueden venir por query string para recalculo server-side, pero el JS hace todo dinámico
    try: anticipo=float(request.args.get('anticipo') or 0)
    except: anticipo=0
    try: gastos_param=request.args.get('gastos')
    except: gastos_param=None
    if gastos_param is not None:
        try: gastos_sugerido=float(gastos_param)
        except: gastos_sugerido=sugerir_gastos_por_precio(precio)
    else:
        gastos_sugerido=sugerir_gastos_por_precio(precio)
    financiar = precio + gastos_sugerido - anticipo
    if financiar < 0: financiar = 0
    plazos_nacion_fija=[12,24,36,48,60,72]; plazos_nacion_uva=[12,24,36,48,60]; plazos_provincia_fija=[12,24,36,48,60,72]; plazos_provincia_uva=[12,18,24,36,48]
    base_monto = financiar if financiar>0 else precio  # si no hay anticipo/gastos, usa precio para primera carga
    cuotas={'nacion_fija':[(n, round(primera_cuota_con_iva(base_monto, tasas['nacion_fija'], n, iva_pct),2)) for n in plazos_nacion_fija],'nacion_uva':[(n, round(primera_cuota_con_iva(base_monto, tasas['nacion_uva'], n, iva_pct),2)) for n in plazos_nacion_uva],'provincia_fija':[(n, round(cuota_francesa(base_monto, tasas['provincia_fija'], n),2)) for n in plazos_provincia_fija],'provincia_uva':[(n, round(cuota_francesa(base_monto, tasas['provincia_uva'], n),2)) for n in plazos_provincia_uva],}
    return render_template("calcular_auto.html", auto=auto, tasas=tasas, cuotas=cuotas, anticipo=anticipo, gastos_sugerido=gastos_sugerido)

@app.route('/debitos')
def debitos():
    init_db_clientes(); conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT * FROM clientes_debitos ORDER BY id DESC"); rows=cur.fetchall(); lista=[dict(r) for r in rows]
    cuotas_map={}
    for cliente in lista:
        cur.execute("SELECT * FROM cuotas_seguimiento WHERE cliente_debito_id=? ORDER BY numero_cuota ASC",(cliente['id'],))
        cuotas_map[cliente['id']]=[dict(r) for r in cur.fetchall()]
    try: cur.execute("SELECT COUNT(*) FROM debitos"); count_viejo=cur.fetchone()[0]
    except: count_viejo=0
    conn.close(); return render_template('debitos.html', debitos=lista, cuotas_map=cuotas_map, count_viejo=count_viejo)

@app.route('/nuevo_cliente_debito', methods=['GET','POST'])
def nuevo_cliente_debito():
    init_db_clientes()
    if request.method=='POST':
        conn=get_db(); cur=conn.cursor()
        cur.execute("INSERT INTO clientes_debitos (identificador, nombre, dni_cuit, convenio, id_deuda, moneda, fecha_venc, importe_base, mensaje, telefono, email, canal_venta, condicion, estado, observaciones, auto_marca, auto_anio, auto_dominio, cantidad_cuotas, resultado_debito, motivo_rechazo, cbu, banco_cuenta, tipo_cuenta, alias_cbu, tarjeta_numero, tarjeta_tipo, tarjeta_banco, tarjeta_titular, empresa) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (request.form.get('identificador'),request.form.get('nombre'),request.form.get('dni_cuit'),request.form.get('convenio'),request.form.get('id_deuda'),request.form.get('moneda','0'),request.form.get('fecha_venc'),float(request.form.get('importe_base') or 0) if request.form.get('importe_base') else None,request.form.get('mensaje'),request.form.get('telefono'),request.form.get('email'),request.form.get('canal_venta'),request.form.get('condicion'),request.form.get('estado','ACTIVO'),request.form.get('observaciones'),request.form.get('auto_marca'),request.form.get('auto_anio'),request.form.get('auto_dominio'),int(request.form.get('cantidad_cuotas') or 0) if request.form.get('cantidad_cuotas') else None,request.form.get('resultado_debito'),request.form.get('motivo_rechazo'),request.form.get('cbu'),request.form.get('banco_cuenta'),request.form.get('tipo_cuenta'),request.form.get('alias_cbu'),request.form.get('tarjeta_numero'),request.form.get('tarjeta_tipo'),request.form.get('tarjeta_banco'),request.form.get('tarjeta_titular'),request.form.get('empresa','autos')))
        cliente_id = cur.lastrowid
        try: cantidad = int(request.form.get('cantidad_cuotas') or 0)
        except: cantidad = 0
        fecha_venc_str = request.form.get('fecha_venc')
        importe_base = float(request.form.get('importe_base') or 0) if request.form.get('importe_base') else 0
        if cantidad>0:
            from datetime import datetime; import calendar
            try: base_fecha = datetime.strptime(fecha_venc_str, "%Y-%m-%d") if fecha_venc_str else datetime.now()
            except: base_fecha = datetime.now()
            for i in range(1, cantidad+1):
                mes = base_fecha.month -1 + i -1
                year = base_fecha.year + mes // 12
                month = mes % 12 + 1
                day = min(base_fecha.day, calendar.monthrange(year, month)[1])
                fecha_cuota = datetime(year, month, day).strftime("%Y-%m-%d")
                cur.execute("INSERT INTO cuotas_seguimiento (cliente_debito_id, numero_cuota, fecha_vencimiento, importe, estado) VALUES (?,?,?,?,?)",(cliente_id, i, fecha_cuota, importe_base, 'Pendiente'))
            conn.commit()
        flash(f"Débito cargado")
        conn.commit(); conn.close()
        return redirect(url_for('debitos'))
    return render_template('nuevo_cliente_debito.html')

@app.route('/editar_cliente_debito/<int:id>', methods=['GET','POST'])
def editar_cliente_debito(id):
    init_db_clientes(); conn=get_db(); cur=conn.cursor()
    if request.method=='POST':
        cur.execute("UPDATE clientes_debitos SET identificador=?, nombre=?, dni_cuit=?, convenio=?, id_deuda=?, moneda=?, fecha_venc=?, importe_base=?, mensaje=?, telefono=?, email=?, canal_venta=?, condicion=?, estado=?, observaciones=?, auto_marca=?, auto_anio=?, auto_dominio=?, cantidad_cuotas=?, resultado_debito=?, motivo_rechazo=?, cbu=?, banco_cuenta=?, tipo_cuenta=?, alias_cbu=?, tarjeta_numero=?, tarjeta_tipo=?, tarjeta_banco=?, tarjeta_titular=?, empresa=? WHERE id=?",
        (request.form.get('identificador'),request.form.get('nombre'),request.form.get('dni_cuit'),request.form.get('convenio'),request.form.get('id_deuda'),request.form.get('moneda'),request.form.get('fecha_venc'),float(request.form.get('importe_base') or 0) if request.form.get('importe_base') else None,request.form.get('mensaje'),request.form.get('telefono'),request.form.get('email'),request.form.get('canal_venta'),request.form.get('condicion'),request.form.get('estado'),request.form.get('observaciones'),request.form.get('auto_marca'),request.form.get('auto_anio'),request.form.get('auto_dominio'),int(request.form.get('cantidad_cuotas') or 0) if request.form.get('cantidad_cuotas') else None,request.form.get('resultado_debito'),request.form.get('motivo_rechazo'),request.form.get('cbu'),request.form.get('banco_cuenta'),request.form.get('tipo_cuenta'),request.form.get('alias_cbu'),request.form.get('tarjeta_numero'),request.form.get('tarjeta_tipo'),request.form.get('tarjeta_banco'),request.form.get('tarjeta_titular'),request.form.get('empresa','autos'),id))
        conn.commit(); conn.close(); flash("Débito actualizado"); return redirect(url_for('debitos'))
    cur.execute("SELECT * FROM clientes_debitos WHERE id=?",(id,)); cliente=cur.fetchone(); conn.close()
    if not cliente: flash("No encontrado"); return redirect(url_for('debitos'))
    return render_template('editar_cliente_debito.html', c=cliente)

@app.route('/borrar_cliente_debito/<int:id>')
def borrar_cliente_debito(id):
    conn=get_db(); cur=conn.cursor(); cur.execute("DELETE FROM clientes_debitos WHERE id=?",(id,)); conn.commit(); conn.close(); flash("Débito borrado"); return redirect(url_for('debitos'))

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    try:
        import pandas as pd
        file=request.files['file']
        if file and file.filename.endswith('.xlsx'):
            df=pd.read_excel(file); df=df.fillna(""); df.columns=df.columns.str.lower()
            conn=get_db(); cursor=conn.cursor(); ids_excel=df['id'].tolist()
            for _, row in df.iterrows():
                cursor.execute("INSERT OR REPLACE INTO autos (id, marca, modelo, version, anio, precio, combustible, kms, color, descripcion, puertas, transmision, motor, traccion, slug, concesionario) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(row.values))
            cursor.execute(f"DELETE FROM autos WHERE id NOT IN ({','.join(['?']*len(ids_excel))})", ids_excel)
            conn.commit(); conn.close(); flash("Base actualizada según Excel")
    except Exception as e:
        flash(f"Error Excel: {e}")
    return redirect(url_for('autos'))

@app.route('/debitos/<int:cliente_id>/cuotas')
def ver_cuotas(cliente_id):
    init_db(); conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT * FROM clientes_debitos WHERE id=?",(cliente_id,)); cliente=cur.fetchone()
    if not cliente: flash("Cliente no encontrado"); return redirect(url_for('debitos'))
    cliente=dict(cliente)
    cur.execute("SELECT * FROM cuotas_seguimiento WHERE cliente_debito_id=? ORDER BY numero_cuota ASC",(cliente_id,)); cuotas=[dict(r) for r in cur.fetchall()]
    conn.close(); return render_template('cuotas.html', cliente=cliente, cuotas=cuotas)

@app.route('/debitos/<int:cliente_id>/generar_cuotas')
def generar_cuotas(cliente_id):
    init_db(); conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT * FROM clientes_debitos WHERE id=?",(cliente_id,)); row=cur.fetchone()
    if not row: flash("Cliente no encontrado"); return redirect(url_for('debitos'))
    cliente=dict(row); cantidad=cliente.get('cantidad_cuotas') or 0
    if cantidad<=0: flash("Primero cargá cantidad de cuotas"); return redirect(url_for('ver_cuotas', cliente_id=cliente_id))
    cur.execute("SELECT COUNT(*) FROM cuotas_seguimiento WHERE cliente_debito_id=?",(cliente_id,))
    if cur.fetchone()[0]>0: flash("Ya existen cuotas generadas"); return redirect(url_for('ver_cuotas', cliente_id=cliente_id))
    from datetime import datetime; import calendar
    try: base_fecha=datetime.strptime(cliente['fecha_venc'], "%Y-%m-%d") if cliente['fecha_venc'] else datetime.now()
    except: base_fecha=datetime.now()
    importe=cliente['importe_base'] or 0
    for i in range(1, cantidad+1):
        mes=base_fecha.month-1+i-1; year=base_fecha.year+mes//12; month=mes%12+1; day=min(base_fecha.day, calendar.monthrange(year, month)[1])
        fecha_cuota=datetime(year, month, day).strftime("%Y-%m-%d")
        cur.execute("INSERT INTO cuotas_seguimiento (cliente_debito_id, numero_cuota, fecha_vencimiento, importe, estado) VALUES (?,?,?,?,?)",(cliente_id, i, fecha_cuota, importe, 'Pendiente'))
    conn.commit(); conn.close(); flash(f"Se generaron {cantidad} cuotas"); return redirect(url_for('ver_cuotas', cliente_id=cliente_id))

@app.route('/debitos/<int:cliente_id>/nueva_cuota', methods=['POST'])
def nueva_cuota(cliente_id):
    init_db(); conn=get_db(); cur=conn.cursor()
    num=int(request.form.get('numero_cuota') or 0)
    cur.execute("SELECT id FROM cuotas_seguimiento WHERE cliente_debito_id=? AND numero_cuota=?",(cliente_id, num))
    existente=cur.fetchone()
    if existente:
        cur.execute("UPDATE cuotas_seguimiento SET fecha_vencimiento=?, importe=?, estado=?, fecha_cobro=?, motivo_rechazo=?, observaciones=? WHERE id=?",
        (request.form.get('fecha_vencimiento'),float(request.form.get('importe') or 0) if request.form.get('importe') else None,request.form.get('estado') or 'Pendiente',request.form.get('fecha_cobro') or None,request.form.get('motivo_rechazo') or None,request.form.get('observaciones') or None,dict(existente)['id']))
        flash(f"Cuota #{num} actualizada")
    else:
        cur.execute("INSERT INTO cuotas_seguimiento (cliente_debito_id, numero_cuota, fecha_vencimiento, importe, estado, fecha_cobro, motivo_rechazo, observaciones) VALUES (?,?,?,?,?,?,?,?)",
        (cliente_id,num,request.form.get('fecha_vencimiento'),float(request.form.get('importe') or 0) if request.form.get('importe') else None,request.form.get('estado') or 'Pendiente',request.form.get('fecha_cobro') or None,request.form.get('motivo_rechazo') or None,request.form.get('observaciones') or None))
        flash("Cuota agregada")
    conn.commit(); conn.close(); return redirect(url_for('ver_cuotas', cliente_id=cliente_id))

@app.route('/cuotas/<int:cuota_id>/actualizar', methods=['POST'])
def actualizar_cuota(cuota_id):
    init_db(); conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT cliente_debito_id FROM cuotas_seguimiento WHERE id=?",(cuota_id,)); r=cur.fetchone()
    if not r: return redirect(url_for('debitos'))
    cliente_id=dict(r)['cliente_debito_id']
    cur.execute("UPDATE cuotas_seguimiento SET numero_cuota=?, fecha_vencimiento=?, importe=?, estado=?, fecha_cobro=?, motivo_rechazo=?, observaciones=? WHERE id=?",
    (int(request.form.get('numero_cuota') or 0),request.form.get('fecha_vencimiento'),float(request.form.get('importe') or 0) if request.form.get('importe') else None,request.form.get('estado'),request.form.get('fecha_cobro') or None,request.form.get('motivo_rechazo') or None,request.form.get('observaciones') or None,cuota_id))
    conn.commit(); conn.close(); flash("Cuota actualizada"); return redirect(url_for('ver_cuotas', cliente_id=cliente_id))

@app.route('/cuotas/<int:cuota_id>/borrar')
def borrar_cuota(cuota_id):
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT cliente_debito_id FROM cuotas_seguimiento WHERE id=?",(cuota_id,)); r=cur.fetchone()
    cliente_id=dict(r)['cliente_debito_id'] if r else None
    cur.execute("DELETE FROM cuotas_seguimiento WHERE id=?",(cuota_id,)); conn.commit(); conn.close(); flash("Cuota borrada")
    if cliente_id: return redirect(url_for('ver_cuotas', cliente_id=cliente_id))
    return redirect(url_for('debitos'))

@app.route('/cuotas/<int:cuota_id>/cambiar_estado/<string:nuevo_estado>')
def cambiar_estado_cuota(cuota_id, nuevo_estado):
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT cliente_debito_id FROM cuotas_seguimiento WHERE id=?",(cuota_id,)); r=cur.fetchone()
    cliente_id=dict(r)['cliente_debito_id'] if r else None
    from datetime import datetime; fecha_cobro=datetime.now().strftime("%Y-%m-%d") if nuevo_estado in ['Cobrada','Cobrado'] else None
    cur.execute("UPDATE cuotas_seguimiento SET estado=?, fecha_cobro=? WHERE id=?",(nuevo_estado, fecha_cobro, cuota_id))
    conn.commit(); conn.close()
    if cliente_id: return redirect(url_for('ver_cuotas', cliente_id=cliente_id))
    return redirect(url_for('debitos'))

if __name__=='__main__':
    port=int(os.environ.get('PORT',5000)); app.run(host='0.0.0.0', port=port, debug=False)
