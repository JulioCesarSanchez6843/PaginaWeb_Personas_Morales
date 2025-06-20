# app/views/representantes_legales_view.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_connection
from datetime import datetime

representantes_legales_view = Blueprint(
    'representantes_legales_view',
    __name__,
    url_prefix='/representantes_legales'
)

def cargar_personas_morales():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ID_MORAL, RAZON_SOCIAL
              FROM PERSONAS_MORALES
             WHERE ESTADO = 'ACTIVO'
          ORDER BY RAZON_SOCIAL
        """)
        personas = [{'id': r[0], 'razon_social': r[1]} for r in cur.fetchall()]
    except Exception:
        personas = []
    finally:
        cur.close()
        conn.close()
    return personas

def campos_unicos_representante(cur, curp, rfc, telefono, email, id_representante=None):
    errores = []
    excluye = ""
    params = {}

    if id_representante:
        excluye = " AND ID_REPRESENTANTE != :id"
        params['id'] = id_representante

    # CURP
    cur.execute(f"""
        SELECT COUNT(*) FROM REPRESENTANTES_LEGALES
         WHERE ESTADO = 'ACTIVO' AND CURP = :valor{excluye}
    """, {**params, 'valor': curp})
    if cur.fetchone()[0]:
        errores.append("CURP ya existe")

    # RFC
    cur.execute(f"""
        SELECT COUNT(*) FROM REPRESENTANTES_LEGALES
         WHERE ESTADO = 'ACTIVO' AND RFC = :valor{excluye}
    """, {**params, 'valor': rfc})
    if cur.fetchone()[0]:
        errores.append("RFC ya existe")

    # Teléfono
    if telefono:
        cur.execute(f"""
            SELECT COUNT(*) FROM REPRESENTANTES_LEGALES
             WHERE ESTADO = 'ACTIVO' AND TELEFONO = :valor{excluye}
        """, {**params, 'valor': telefono})
        if cur.fetchone()[0]:
            errores.append("Teléfono ya existe")

    # Email
    if email:
        cur.execute(f"""
            SELECT COUNT(*) FROM REPRESENTANTES_LEGALES
             WHERE ESTADO = 'ACTIVO' AND EMAIL = :valor{excluye}
        """, {**params, 'valor': email})
        if cur.fetchone()[0]:
            errores.append("Correo electrónico ya existe")

    return errores

@representantes_legales_view.route('/opciones')
def opciones():
    return render_template('representantes_legales_opciones.html')

@representantes_legales_view.route('', methods=['GET'])
def listar_representantes():
    # 1️⃣ Leer filtros de la querystring
    filtros = {
        'id_moral':         request.args.get('id_moral','').strip(),
        'nombre':           request.args.get('nombre','').strip(),
        'apellido_paterno': request.args.get('apellido_paterno','').strip(),
        'apellido_materno': request.args.get('apellido_materno','').strip(),
        'curp':             request.args.get('curp','').strip(),
        'rfc':              request.args.get('rfc','').strip(),
        'telefono':         request.args.get('telefono','').strip(),
        'email':            request.args.get('email','').strip(),
        'fecha_nacimiento': request.args.get('fecha_nacimiento','').strip(),
        'estado':           request.args.get('estado','').strip(),
    }

    # 2️⃣ Construir WHERE dinámico
    where = []
    params = {}

    if filtros['id_moral']:
        where.append("r.ID_MORAL = :id_moral")
        params['id_moral'] = int(filtros['id_moral'])

    if filtros['fecha_nacimiento']:
        where.append("TO_CHAR(r.FECHA_NACIMIENTO,'YYYY-MM-DD') = :fecha_nacimiento")
        params['fecha_nacimiento'] = filtros['fecha_nacimiento']

# Campos que usan LIKE (insensible a mayúsculas)
    for campo in ('nombre','apellido_paterno','apellido_materno','curp','rfc','telefono','email'):
        val = filtros[campo]
        if val:
            where.append(f"UPPER(r.{campo.upper()}) LIKE :{campo}")
            params[campo] = f"%{val.upper()}%"

# Campo estado con comparación exacta (si está filtro, si no, por defecto ACTIVO)
    if filtros['estado']:
        where.append("UPPER(r.ESTADO) = :estado")
        params['estado'] = filtros['estado'].upper()
    else:
        where.append("r.ESTADO = 'ACTIVO'")

    sql = f"""
        SELECT r.ID_REPRESENTANTE,
               r.ID_MORAL,
               pm.RAZON_SOCIAL,
               r.NOMBRE,
               r.APELLIDO_PATERNO,
               r.APELLIDO_MATERNO,
               r.CURP,
               r.RFC,
               r.TELEFONO,
               r.EMAIL,
               TO_CHAR(r.FECHA_NACIMIENTO,'YYYY-MM-DD'),
               r.ESTADO
          FROM REPRESENTANTES_LEGALES r
          JOIN PERSONAS_MORALES pm ON r.ID_MORAL = pm.ID_MORAL
         WHERE {' AND '.join(where)}
      ORDER BY r.ID_REPRESENTANTE
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    representantes = [{
        'id_representante': row[0],
        'id_moral':         row[1],
        'razon_social':     row[2],
        'nombre':           row[3],
        'apellido_paterno': row[4],
        'apellido_materno': row[5],
        'curp':             row[6],
        'rfc':              row[7],
        'telefono':         row[8],
        'email':            row[9],
        'fecha_nacimiento': row[10],
        'estado':           row[11],
    } for row in cur.fetchall()]
    cur.close()
    conn.close()

    # 👉 aquí le pasamos también la lista de personas morales para el filtro
    personas_morales = cargar_personas_morales()

    return render_template(
        'representantes_legales.html',
        representantes=representantes,
        filtros=filtros,
        personas_morales=personas_morales
    )

# — El resto de rutas (/nuevo, /editar, /eliminar) quedan exactamente igual —
#   No las repito para no alargar esta respuesta.


# — El resto de rutas (/nuevo, /editar, /eliminar) **quedan exactamente igual**.
#   No las repito para no alargar, pero sigue tal cual las tenías.

@representantes_legales_view.route('/nuevo', methods=['GET', 'POST'])
def nuevo_representante():
    personas_morales = cargar_personas_morales()
    if request.method == 'POST':
        data = request.form.to_dict()
        errores = []

        for campo in ['id_moral', 'nombre', 'curp', 'rfc', 'telefono', 'email']:
            if not data.get(campo) or not data[campo].strip():
                errores.append(f'El campo {campo.upper()} es obligatorio')

        fecha_nac = None
        if data.get('fecha_nacimiento'):
            try:
                fecha_nac = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d')
            except ValueError:
                errores.append('Fecha de nacimiento inválida')

        if errores:
            for msg in errores:
                flash(msg, 'warning')
            return render_template('representante_form.html',
                                   personas_morales=personas_morales,
                                   representante=data)

        conn = get_connection()
        cur = conn.cursor()
        errores_unicidad = campos_unicos_representante(
            cur, data['curp'], data['rfc'], data['telefono'], data['email'])
        if errores_unicidad:
            for msg in errores_unicidad:
                flash(msg, 'warning')
            cur.close()
            conn.close()
            return render_template('representante_form.html',
                                   personas_morales=personas_morales,
                                   representante=data)

        cur.execute("""
            INSERT INTO REPRESENTANTES_LEGALES
              (ID_REPRESENTANTE, ID_MORAL, NOMBRE, APELLIDO_PATERNO, APELLIDO_MATERNO,
               CURP, RFC, TELEFONO, EMAIL, FECHA_NACIMIENTO, ESTADO)
            VALUES
              (MORAL.ISEQ$$_72227.NEXTVAL, :idm, :nom, :apep, :apem,
               :curp, :rfc, :tel, :email, :fn, 'ACTIVO')
        """, {
            'idm': data['id_moral'],
            'nom': data['nombre'].strip(),
            'apep': data.get('apellido_paterno', '').strip(),
            'apem': data.get('apellido_materno', '').strip(),
            'curp': data['curp'].strip(),
            'rfc': data['rfc'].strip(),
            'tel': data['telefono'].strip(),
            'email': data['email'].strip(),
            'fn': fecha_nac
        })
        conn.commit()
        cur.close()
        conn.close()
        flash('Representante creado correctamente.', 'success')
        return redirect(url_for('representantes_legales_view.listar_representantes'))

    return render_template(
        'representante_form.html',
        personas_morales=personas_morales,
        representante=None
    )

@representantes_legales_view.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_representante(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID_REPRESENTANTE, ID_MORAL, NOMBRE,
               APELLIDO_PATERNO, APELLIDO_MATERNO,
               CURP, RFC, TELEFONO, EMAIL,
               TO_CHAR(FECHA_NACIMIENTO,'YYYY-MM-DD')
          FROM REPRESENTANTES_LEGALES
         WHERE ID_REPRESENTANTE = :id AND ESTADO = 'ACTIVO'
    """, {'id': id})
    row = cur.fetchone()
    if not row:
        flash('Representante no encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('representantes_legales_view.listar_representantes'))

    representante = dict(zip([
        'id_representante','id_moral','nombre','apellido_paterno',
        'apellido_materno','curp','rfc','telefono','email',
        'fecha_nacimiento'
    ], row))
    cur.close()
    conn.close()

    personas_morales = cargar_personas_morales()

    if request.method == 'POST':
        data = request.form.to_dict()
        errores = []

        for campo in ['id_moral', 'nombre', 'curp', 'rfc', 'telefono', 'email']:
            if not data.get(campo) or not data[campo].strip():
                errores.append(f'El campo {campo.upper()} es obligatorio')

        fecha_nac = None
        if data.get('fecha_nacimiento'):
            try:
                fecha_nac = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d')
            except ValueError:
                errores.append('Fecha de nacimiento inválida')

        if errores:
            for msg in errores:
                flash(msg, 'warning')
            data['id_representante'] = id
            return render_template('representante_form.html',
                                   personas_morales=personas_morales,
                                   representante=data)

        conn2 = get_connection()
        cur2 = conn2.cursor()
        errores_unicidad = campos_unicos_representante(
            cur2, data['curp'], data['rfc'], data['telefono'], data['email'], id)
        if errores_unicidad:
            for msg in errores_unicidad:
                flash(msg, 'warning')
            cur2.close()
            conn2.close()
            data['id_representante'] = id
            return render_template('representante_form.html',
                                   personas_morales=personas_morales,
                                   representante=data)

        cur2.execute("""
            UPDATE REPRESENTANTES_LEGALES
               SET ID_MORAL          = :idm,
                   NOMBRE            = :nom,
                   APELLIDO_PATERNO  = :apep,
                   APELLIDO_MATERNO  = :apem,
                   CURP              = :curp,
                   RFC               = :rfc,
                   TELEFONO          = :tel,
                   EMAIL             = :email,
                   FECHA_NACIMIENTO  = :fn
             WHERE ID_REPRESENTANTE = :id
        """, {
            'idm': data['id_moral'],
            'nom': data['nombre'].strip(),
            'apep': data.get('apellido_paterno', '').strip(),
            'apem': data.get('apellido_materno', '').strip(),
            'curp': data['curp'].strip(),
            'rfc': data['rfc'].strip(),
            'tel': data['telefono'].strip(),
            'email': data['email'].strip(),
            'fn': fecha_nac,
            'id': id
        })
        conn2.commit()
        cur2.close()
        conn2.close()
        flash('Representante actualizado correctamente.', 'success')
        return redirect(url_for('representantes_legales_view.listar_representantes'))

    return render_template('representante_form.html',
                           personas_morales=personas_morales,
                           representante=representante)

@representantes_legales_view.route('/eliminar/<int:id>')
def eliminar_representante(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE REPRESENTANTES_LEGALES
           SET ESTADO = 'INACTIVO'
         WHERE ID_REPRESENTANTE = :id
    """, {'id': id})
    conn.commit()
    cur.close()
    conn.close()
    flash('Representante marcado como inactivo.', 'success')
    return redirect(url_for('representantes_legales_view.listar_representantes'))
