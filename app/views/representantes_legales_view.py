from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_connection
import cx_Oracle
from datetime import datetime

representantes_legales_view = Blueprint(
    'representantes_legales_view',
    __name__,
    url_prefix='/vista/representantes_legales'
)

@representantes_legales_view.route('/opciones', methods=['GET'])
def opciones():
    return render_template('representantes_legales_opciones.html')


@representantes_legales_view.route('/nuevo', methods=['GET', 'POST'])
def nuevo_representante():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id_moral, razon_social FROM personas_morales WHERE estado='ACTIVO'")
    personas_morales = [{'id': row[0], 'razon_social': row[1]} for row in cur.fetchall()]

    if request.method == 'POST':
        data = request.form
        id_moral = data.get('id_moral', '').strip()
        nombre = data.get('nombre', '').strip()
        apellido_paterno = data.get('apellido_paterno', '').strip()
        apellido_materno = data.get('apellido_materno', '').strip()
        curp = data.get('curp', '').strip().upper()
        rfc = data.get('rfc', '').strip().upper()
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()
        fecha_nacimiento = data.get('fecha_nacimiento', '').strip()

        errores = []

        campos_obligatorios = {
            'Persona Moral': id_moral,
            'Nombre': nombre,
            'Apellido Paterno': apellido_paterno,
            'Apellido Materno': apellido_materno,
            'CURP': curp,
            'RFC': rfc,
            'Teléfono': telefono,
            'Email': email,
            'Fecha de Nacimiento': fecha_nacimiento
        }

        for campo, valor in campos_obligatorios.items():
            if not valor:
                errores.append(f'El campo {campo} es obligatorio.')

        if fecha_nacimiento:
            try:
                datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
            except ValueError:
                errores.append('La Fecha de Nacimiento debe tener formato YYYY-MM-DD.')

        if errores:
            for e in errores:
                flash(e, 'danger')
            cur.close()
            conn.close()
            return render_template('representante_form.html', representante=data, personas_morales=personas_morales)

        # Validaciones únicas
        campos_unicos = [
            ('CURP', 'curp', curp.upper()),
            ('RFC', 'rfc', rfc.upper()),
            ('Teléfono', 'telefono', telefono),
            ('Email', 'LOWER(email)', email.lower())
        ]
        for nombre_campo, campo_sql, valor in campos_unicos:
            cur.execute(f"SELECT COUNT(*) FROM representantes_legales WHERE {campo_sql} = :valor AND estado='ACTIVO'", {'valor': valor})
            if cur.fetchone()[0] > 0:
                flash(f'El {nombre_campo} "{valor}" ya existe.', 'danger')
                cur.close()
                conn.close()
                return render_template('representante_form.html', representante=data, personas_morales=personas_morales)

        try:
            cur.execute("""
                INSERT INTO representantes_legales (
                    id_moral, nombre, apellido_paterno, apellido_materno,
                    curp, rfc, telefono, email, fecha_nacimiento, estado
                ) VALUES (
                    :id_moral, :nombre, :ap_paterno, :ap_materno,
                    :curp, :rfc, :telefono, :email,
                    TO_DATE(:fecha_nacimiento,'YYYY-MM-DD'), 'ACTIVO'
                )
            """, {
                'id_moral': id_moral,
                'nombre': nombre,
                'ap_paterno': apellido_paterno,
                'ap_materno': apellido_materno,
                'curp': curp,
                'rfc': rfc,
                'telefono': telefono,
                'email': email,
                'fecha_nacimiento': fecha_nacimiento
            })
            conn.commit()
            flash('Representante legal creado correctamente.', 'success')
            return redirect(url_for('representantes_legales_view.listar_representantes'))
        except cx_Oracle.IntegrityError as e:
            error_obj, = e.args
            flash(f'Error de integridad: {error_obj.message}', 'danger')
            conn.rollback()
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    return render_template('representante_form.html', representante={}, personas_morales=personas_morales)


@representantes_legales_view.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_representante(id):
    conn = get_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        data = request.form
        id_moral = data.get('id_moral', '').strip()
        nombre = data.get('nombre', '').strip()
        apellido_paterno = data.get('apellido_paterno', '').strip()
        apellido_materno = data.get('apellido_materno', '').strip()
        curp = data.get('curp', '').strip().upper()
        rfc = data.get('rfc', '').strip().upper()
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()
        fecha_nacimiento = data.get('fecha_nacimiento', '').strip()
        estado = data.get('estado', '').strip().upper()

        errores = []

        for campo, valor in {
            'Persona Moral': id_moral,
            'Nombre': nombre,
            'Apellido Paterno': apellido_paterno,
            'Apellido Materno': apellido_materno,
            'CURP': curp,
            'RFC': rfc,
            'Teléfono': telefono,
            'Email': email,
            'Fecha de Nacimiento': fecha_nacimiento,
            'Estado': estado
        }.items():
            if not valor:
                errores.append(f'El campo {campo} es obligatorio.')

        if fecha_nacimiento:
            try:
                datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
            except ValueError:
                errores.append('La Fecha de Nacimiento debe tener formato YYYY-MM-DD.')

        if errores:
            for e in errores:
                flash(e, 'danger')
            # Recargar personas morales para el select en el formulario
            cur.execute("SELECT id_moral, razon_social FROM personas_morales WHERE estado='ACTIVO'")
            personas_morales = [{'id': r[0], 'razon_social': r[1]} for r in cur.fetchall()]
            cur.close()
            conn.close()
            return render_template('representante_form.html', representante=data, personas_morales=personas_morales, accion='Editar')

        # Validar que CURP, RFC, teléfono y email sean únicos (excluyendo al actual)
        campos_unicos = [
            ('CURP', 'curp', curp.upper()),
            ('RFC', 'rfc', rfc.upper()),
            ('Teléfono', 'telefono', telefono),
            ('Email', 'LOWER(email)', email.lower())
        ]
        for nombre_campo, campo_sql, valor in campos_unicos:
            cur.execute(f"""
                SELECT COUNT(*) FROM representantes_legales 
                WHERE {campo_sql} = :valor AND estado='ACTIVO' AND id_representante != :id
            """, {'valor': valor, 'id': id})
            if cur.fetchone()[0] > 0:
                flash(f'El {nombre_campo} "{valor}" ya existe en otro registro activo.', 'danger')
                # Recargar personas morales para el select en el formulario
                cur.execute("SELECT id_moral, razon_social FROM personas_morales WHERE estado='ACTIVO'")
                personas_morales = [{'id': r[0], 'razon_social': r[1]} for r in cur.fetchall()]
                cur.close()
                conn.close()
                return render_template('representante_form.html', representante=data, personas_morales=personas_morales, accion='Editar')

        try:
            cur.execute("""
                UPDATE representantes_legales
                SET id_moral = :id_moral,
                    nombre = :nombre,
                    apellido_paterno = :ap_paterno,
                    apellido_materno = :ap_materno,
                    curp = :curp,
                    rfc = :rfc,
                    telefono = :telefono,
                    email = :email,
                    fecha_nacimiento = TO_DATE(:fecha_nacimiento,'YYYY-MM-DD'),
                    estado = :estado
                WHERE id_representante = :id
            """, {
                'id_moral': id_moral,
                'nombre': nombre,
                'ap_paterno': apellido_paterno,
                'ap_materno': apellido_materno,
                'curp': curp,
                'rfc': rfc,
                'telefono': telefono,
                'email': email,
                'fecha_nacimiento': fecha_nacimiento,
                'estado': estado,
                'id': id
            })
            conn.commit()
            flash('Representante legal actualizado correctamente.', 'success')
            return redirect(url_for('representantes_legales_view.listar_representantes'))
        except Exception as e:
            flash(f'Error al actualizar: {e}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    # GET: cargar datos existentes
    cur.execute("""
        SELECT id_moral, nombre, apellido_paterno, apellido_materno,
               curp, rfc, telefono, email,
               TO_CHAR(fecha_nacimiento,'YYYY-MM-DD'), estado
        FROM representantes_legales
        WHERE id_representante = :id
    """, {'id': id})
    row = cur.fetchone()

    if not row:
        flash('Representante legal no encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('representantes_legales_view.listar_representantes'))

    representante = dict(zip(
        ['id_moral', 'nombre', 'apellido_paterno', 'apellido_materno', 'curp', 'rfc',
         'telefono', 'email', 'fecha_nacimiento', 'estado'], row
    ))

    cur.execute("SELECT id_moral, razon_social FROM personas_morales WHERE estado='ACTIVO'")
    personas_morales = [{'id': r[0], 'razon_social': r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('representante_form.html', representante=representante, personas_morales=personas_morales, accion='Editar')

@representantes_legales_view.route('/listar', methods=['GET'])
def listar_representantes():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Obtener todos los filtros desde el formulario GET
    filtros = {
        'id_moral': request.args.get('id_moral', '').strip(),
        'nombre': request.args.get('nombre', '').strip(),
        'apellido_paterno': request.args.get('apellido_paterno', '').strip(),
        'apellido_materno': request.args.get('apellido_materno', '').strip(),
        'curp': request.args.get('curp', '').strip(),
        'rfc': request.args.get('rfc', '').strip(),
        'telefono': request.args.get('telefono', '').strip(),
        'email': request.args.get('email', '').strip(),
        'fecha_nacimiento': request.args.get('fecha_nacimiento', '').strip(),
        'estado': request.args.get('estado', '').strip()
    }

    # 2. Construir consulta dinámica con filtros
    query = """
        SELECT r.id_representante, pm.razon_social, r.nombre, r.apellido_paterno, r.apellido_materno,
               r.curp, r.rfc, r.telefono, r.email,
               TO_CHAR(r.fecha_nacimiento,'YYYY-MM-DD'), r.estado
        FROM representantes_legales r
        JOIN personas_morales pm ON r.id_moral = pm.id_moral
        WHERE 1 = 1
    """
    params = {}

    if filtros['id_moral']:
        query += " AND r.id_moral = :id_moral"
        params['id_moral'] = filtros['id_moral']
    if filtros['nombre']:
        query += " AND LOWER(r.nombre) LIKE :nombre"
        params['nombre'] = f"%{filtros['nombre'].lower()}%"
    if filtros['apellido_paterno']:
        query += " AND LOWER(r.apellido_paterno) LIKE :apellido_paterno"
        params['apellido_paterno'] = f"%{filtros['apellido_paterno'].lower()}%"
    if filtros['apellido_materno']:
        query += " AND LOWER(r.apellido_materno) LIKE :apellido_materno"
        params['apellido_materno'] = f"%{filtros['apellido_materno'].lower()}%"
    if filtros['curp']:
        query += " AND LOWER(r.curp) LIKE :curp"
        params['curp'] = f"%{filtros['curp'].lower()}%"
    if filtros['rfc']:
        query += " AND LOWER(r.rfc) LIKE :rfc"
        params['rfc'] = f"%{filtros['rfc'].lower()}%"
    if filtros['telefono']:
        query += " AND r.telefono LIKE :telefono"
        params['telefono'] = f"%{filtros['telefono']}%"
    if filtros['email']:
        query += " AND LOWER(r.email) LIKE :email"
        params['email'] = f"%{filtros['email'].lower()}%"
    if filtros['fecha_nacimiento']:
        query += " AND TO_CHAR(r.fecha_nacimiento, 'YYYY-MM-DD') = :fecha_nacimiento"
        params['fecha_nacimiento'] = filtros['fecha_nacimiento']
    if filtros['estado']:
        query += " AND r.estado = :estado"
        params['estado'] = filtros['estado']

    query += " ORDER BY r.id_representante DESC"

    # 3. Ejecutar y construir resultados
    cur.execute(query, params)
    representantes = []
    for row in cur.fetchall():
        representantes.append({
            'id_representante': row[0],
            'razon_social': row[1],
            'nombre': row[2],
            'apellido_paterno': row[3],
            'apellido_materno': row[4],
            'curp': row[5],
            'rfc': row[6],
            'telefono': row[7],
            'email': row[8],
            'fecha_nacimiento': row[9],
            'estado': row[10]
        })

    # 4. Obtener lista de personas morales para el filtro
    cur.execute("SELECT id_moral, razon_social FROM personas_morales WHERE estado='ACTIVO'")
    personas_morales = [{'id': r[0], 'razon_social': r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('representantes_legales.html',
                           representantes=representantes,
                           filtros=filtros,
                           personas_morales=personas_morales)


# app/views/representantes_legales_view.py

@representantes_legales_view.route('/eliminar/<int:id>', methods=['GET'])
def eliminar_representante(id):
    conn = get_connection()
    cur = conn.cursor()

    # Obtener los campos clave y estado actual del representante a modificar
    cur.execute("""
        SELECT curp, rfc, telefono, email, estado
        FROM representantes_legales
        WHERE id_representante = :id
    """, {'id': id})
    row = cur.fetchone()

    if not row:
        flash("Representante no encontrado", "danger")
        cur.close()
        conn.close()
        return redirect(url_for('representantes_legales_view.listar_representantes'))

    curp, rfc, telefono, email, estado_actual = row
    nuevo_estado = 'INACTIVO' if estado_actual == 'ACTIVO' else 'ACTIVO'

    # Validar solo si se intenta reactivar
    if nuevo_estado == 'ACTIVO':
        # Validar que ninguno de esos campos esté en uso por otro representante activo diferente
        cur.execute("""
            SELECT id_representante, nombre, apellido_paterno, apellido_materno, curp, rfc, telefono, email
            FROM representantes_legales
            WHERE estado = 'ACTIVO'
              AND id_representante != :id
              AND (
                  curp = :curp OR
                  rfc = :rfc OR
                  telefono = :telefono OR
                  LOWER(email) = LOWER(:email)
              )
        """, {
            'id': id,
            'curp': curp,
            'rfc': rfc,
            'telefono': telefono,
            'email': email
        })
        conflicto = cur.fetchone()

        if conflicto:
            nombre_conflicto = f"{conflicto[1]} {conflicto[2]} {conflicto[3]}"
            campos_conflicto = []
            if conflicto[4].upper() == curp.upper():
                campos_conflicto.append("CURP")
            if conflicto[5].upper() == rfc.upper():
                campos_conflicto.append("RFC")
            if conflicto[6] == telefono:
                campos_conflicto.append("Teléfono")
            if conflicto[7].lower() == email.lower():
                campos_conflicto.append("Email")

            campos_str = ", ".join(campos_conflicto)
            flash(f"No se puede reactivar este representante porque los siguientes campos ya están en uso por {nombre_conflicto}: {campos_str}. Desactívalo primero.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for('representantes_legales_view.listar_representantes'))

    # Si no hay conflictos, proceder a cambiar el estado
    try:
        cur.execute("""
            UPDATE representantes_legales
            SET estado = :estado
            WHERE id_representante = :id
        """, {'estado': nuevo_estado, 'id': id})
        conn.commit()
        flash(f"Estado actualizado a {nuevo_estado}.", "success")
    except Exception as e:
        flash(f"Error al actualizar estado: {e}", "danger")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('representantes_legales_view.listar_representantes'))
