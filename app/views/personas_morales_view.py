# app/views/personas_morales_view.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_connection
import cx_Oracle

personas_morales_view = Blueprint(
    'personas_morales_view',
    __name__,
    url_prefix='/vista/personas_morales'
)

# 🟢 Página intermedia con opciones: Consultar o Crear
@personas_morales_view.route('/opciones', methods=['GET'])
def opciones():
    return render_template('personas_morales_opciones.html')


# 1️⃣ Listar (y filtrar) personas morales
@personas_morales_view.route('/', methods=['GET'])
def listado():
    # Extraer filtros de la query string
    filtros = {
        'razon_social':       request.args.get('razon_social', '').strip(),
        'rfc':                request.args.get('rfc', '').strip(),
        'fecha_constitucion': request.args.get('fecha_constitucion', '').strip(),
        'domicilio_fiscal':   request.args.get('domicilio_fiscal', '').strip(),
        'telefono':           request.args.get('telefono', '').strip(),
        'email':              request.args.get('email', '').strip(),
        'estado':             request.args.get('estado', '').strip()
    }

    # Construir la consulta dinámica
    where_clauses = ["estado = 'ACTIVO'"]
    params = {}

    if filtros['razon_social']:
        where_clauses.append("UPPER(razon_social) LIKE :rs")
        params['rs'] = f"%{filtros['razon_social'].upper()}%"
    if filtros['rfc']:
        where_clauses.append("UPPER(rfc) LIKE :rfc")
        params['rfc'] = f"%{filtros['rfc'].upper()}%"
    if filtros['fecha_constitucion']:
        where_clauses.append("TO_CHAR(fecha_constitucion,'YYYY-MM-DD') = :fc")
        params['fc'] = filtros['fecha_constitucion']
    if filtros['domicilio_fiscal']:
        where_clauses.append("UPPER(domicilio_fiscal) LIKE :df")
        params['df'] = f"%{filtros['domicilio_fiscal'].upper()}%"
    if filtros['telefono']:
        where_clauses.append("telefono LIKE :tel")
        params['tel'] = f"%{filtros['telefono']}%"
    if filtros['email']:
        where_clauses.append("UPPER(email) LIKE :em")
        params['em'] = f"%{filtros['email'].upper()}%"
    if filtros['estado']:
        where_clauses.append("estado = :est")
        params['est'] = filtros['estado']

    sql = f"""
        SELECT id_moral,
               razon_social,
               rfc,
               TO_CHAR(fecha_constitucion,'YYYY-MM-DD'),
               domicilio_fiscal,
               telefono,
               email,
               estado
          FROM personas_morales
         WHERE {' AND '.join(where_clauses)}
      ORDER BY id_moral
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    personas = [
        {
          'id_moral': r[0],
          'razon_social': r[1],
          'rfc': r[2],
          'fecha_constitucion': r[3],
          'domicilio_fiscal': r[4],
          'telefono': r[5],
          'email': r[6],
          'estado': r[7]
        }
        for r in rows
    ]

    return render_template(
        'personas_morales.html',
        personas=personas,
        filtros=filtros
    )


# 🟠 Eliminar (baja lógica)
@personas_morales_view.route('/eliminar/<int:id>', methods=['GET'])
def eliminar_persona(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE personas_morales
           SET estado = 'INACTIVO'
         WHERE id_moral = :id
    """, {'id': id})
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('personas_morales_view.listado'))


# 2️⃣ Crear persona moral
@personas_morales_view.route('/nuevo', methods=['GET', 'POST'])
def nueva_persona():
    if request.method == 'POST':
        data = request.form
        razon_social = data.get('razon_social', '').strip()
        rfc_nuevo     = data.get('rfc', '').strip().upper()
        domicilio     = data.get('domicilio_fiscal', '').strip()
        telefono      = data.get('telefono', '').strip()
        email         = data.get('email', '').strip()
        fc            = data.get('fecha_constitucion', '').strip()

        # Validación de campos obligatorios
        if not razon_social or not rfc_nuevo:
            flash('Razón Social y RFC son obligatorios.', 'danger')
            return render_template('persona_form.html', accion='Crear', persona=data)

        conn = get_connection()
        cur = conn.cursor()

        # Validar unicidad RFC, teléfono y email
        cur.execute("""
            SELECT COUNT(*) FROM personas_morales 
             WHERE UPPER(rfc) = :rfc AND estado='ACTIVO'
        """, {'rfc': rfc_nuevo})
        if cur.fetchone()[0] > 0:
            flash(f'El RFC "{rfc_nuevo}" ya existe.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Crear', persona=data)

        cur.execute("""
            SELECT COUNT(*) FROM personas_morales 
             WHERE telefono = :tel AND estado='ACTIVO'
        """, {'tel': telefono})
        if telefono and cur.fetchone()[0] > 0:
            flash(f'El teléfono "{telefono}" ya existe.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Crear', persona=data)

        cur.execute("""
            SELECT COUNT(*) FROM personas_morales 
             WHERE LOWER(email) = :em AND estado='ACTIVO'
        """, {'em': email.lower()})
        if email and cur.fetchone()[0] > 0:
            flash(f'El email "{email}" ya existe.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Crear', persona=data)

        try:
            cur.execute("""
                INSERT INTO personas_morales
                  (razon_social, rfc, fecha_constitucion, domicilio_fiscal,
                   telefono, email, estado, fecha_registro)
                VALUES
                  (:rs, :rfc, TO_DATE(:fc,'YYYY-MM-DD'),
                   :df, :tel, :em, 'ACTIVO', SYSDATE)
            """, {
                'rs': razon_social,
                'rfc': rfc_nuevo,
                'fc': fc or None,
                'df': domicilio or None,
                'tel': telefono or None,
                'em': email or None
            })
            conn.commit()
            flash('Persona moral creada correctamente.', 'success')
            return redirect(url_for('personas_morales_view.listado'))
        except cx_Oracle.IntegrityError as e:
            flash(f'Error inesperado: {e}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    return render_template('persona_form.html', accion='Crear', persona={})


# 3️⃣ Editar persona moral existente
@personas_morales_view.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_persona(id):
    conn = get_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        data = request.form
        razon_social = data.get('razon_social', '').strip()
        rfc_editado  = data.get('rfc', '').strip().upper()
        domicilio    = data.get('domicilio_fiscal', '').strip()
        telefono     = data.get('telefono', '').strip()
        email        = data.get('email', '').strip()
        fc           = data.get('fecha_constitucion', '').strip()

        # Validación de campos obligatorios
        if not razon_social or not rfc_editado:
            flash('Razón Social y RFC son obligatorios.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Editar', persona=data)

        # Validar unicidad con exclusión del propio registro
        cur.execute("""
            SELECT COUNT(*) FROM personas_morales
             WHERE UPPER(rfc)=:rfc AND id_moral!=:id AND estado='ACTIVO'
        """, {'rfc': rfc_editado, 'id': id})
        if cur.fetchone()[0] > 0:
            flash(f'El RFC "{rfc_editado}" ya existe en otro registro.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Editar', persona=data)

        cur.execute("""
            SELECT COUNT(*) FROM personas_morales
             WHERE telefono=:tel AND id_moral!=:id AND estado='ACTIVO'
        """, {'tel': telefono, 'id': id})
        if telefono and cur.fetchone()[0] > 0:
            flash(f'El teléfono "{telefono}" ya existe en otro registro.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Editar', persona=data)

        cur.execute("""
            SELECT COUNT(*) FROM personas_morales
             WHERE LOWER(email)=:em AND id_moral!=:id AND estado='ACTIVO'
        """, {'em': email.lower(), 'id': id})
        if email and cur.fetchone()[0] > 0:
            flash(f'El email "{email}" ya existe en otro registro.', 'danger')
            cur.close(); conn.close()
            return render_template('persona_form.html', accion='Editar', persona=data)

        try:
            cur.execute("""
                UPDATE personas_morales
                   SET razon_social    = :rs,
                       rfc             = :rfc,
                       fecha_constitucion = TO_DATE(:fc,'YYYY-MM-DD'),
                       domicilio_fiscal   = :df,
                       telefono           = :tel,
                       email              = :em
                 WHERE id_moral = :id
            """, {
                'rs': razon_social,
                'rfc': rfc_editado,
                'fc': fc or None,
                'df': domicilio or None,
                'tel': telefono or None,
                'em': email or None,
                'id': id
            })
            conn.commit()
            flash('Persona moral actualizada correctamente.', 'success')
            return redirect(url_for('personas_morales_view.listado'))
        except cx_Oracle.IntegrityError as e:
            flash(f'Error inesperado: {e}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    # GET: cargar datos existentes
    cur.execute("""
        SELECT razon_social, rfc,
               TO_CHAR(fecha_constitucion,'YYYY-MM-DD'),
               domicilio_fiscal, telefono, email
          FROM personas_morales
         WHERE id_moral = :id
    """, {'id': id})
    row = cur.fetchone()
    cur.close()
    conn.close()

    persona = {
        'razon_social':       row[0],
        'rfc':                row[1],
        'fecha_constitucion': row[2],
        'domicilio_fiscal':   row[3],
        'telefono':           row[4],
        'email':              row[5]
    }

    return render_template(
        'persona_form.html',
        accion='Editar',
        persona=persona
    )
