from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_connection

actividades_economicas_view = Blueprint(
    'actividades_economicas_view',
    __name__,
    url_prefix='/vista/actividades_economicas'
)

MAX_LENGTH_NOMBRE = 150
MAX_LENGTH_DESCRIPCION = 500

# Página con opciones: consultar o crear
@actividades_economicas_view.route('/opciones', methods=['GET'])
def opciones():
    return render_template('actividades_economicas_opciones.html')

# Listar actividades económicas (endpoint: listado)
@actividades_economicas_view.route('/', methods=['GET'])
def listado():
    nombre = request.args.get('nombre', '').strip().upper()

    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT id_actividad, nombre, descripcion
        FROM actividades_economicas
        WHERE 1=1
    """
    params = {}

    if nombre:
        sql += " AND UPPER(nombre) LIKE :nombre"
        params['nombre'] = f"%{nombre}%"

    sql += " ORDER BY id_actividad"

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    actividades = [
        {'id_actividad': r[0], 'nombre': r[1], 'descripcion': r[2]}
        for r in rows
    ]

    return render_template(
        'actividades_economicas.html',
        actividades=actividades,
        filtro_nombre=nombre
    )

# Crear actividad económica (endpoint: nueva_actividad)
@actividades_economicas_view.route('/nueva', methods=['GET', 'POST'])
def nueva_actividad():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        # Validaciones de campos obligatorios y longitud
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('actividad_form.html', accion='Crear', actividad=request.form)
        if len(nombre) > MAX_LENGTH_NOMBRE:
            flash(f'El nombre no puede tener más de {MAX_LENGTH_NOMBRE} caracteres.', 'danger')
            return render_template('actividad_form.html', accion='Crear', actividad=request.form)

        if not descripcion:
            flash('La descripción es obligatoria.', 'danger')
            return render_template('actividad_form.html', accion='Crear', actividad=request.form)
        if len(descripcion) > MAX_LENGTH_DESCRIPCION:
            flash(f'La descripción no puede tener más de {MAX_LENGTH_DESCRIPCION} caracteres.', 'danger')
            return render_template('actividad_form.html', accion='Crear', actividad=request.form)

        conn = get_connection()
        cur = conn.cursor()

        # Validar nombre duplicado
        cur.execute("""
            SELECT COUNT(*) FROM actividades_economicas
            WHERE UPPER(nombre) = :nombre
        """, {'nombre': nombre.upper()})
        if cur.fetchone()[0] > 0:
            flash('Ya existe una actividad con ese nombre.', 'danger')
            cur.close()
            conn.close()
            return render_template('actividad_form.html', accion='Crear', actividad=request.form)

        try:
            cur.execute("""
                INSERT INTO actividades_economicas (nombre, descripcion)
                VALUES (:nombre, :descripcion)
            """, {'nombre': nombre, 'descripcion': descripcion})
            conn.commit()
            flash('Actividad creada correctamente.', 'success')
            return redirect(url_for('actividades_economicas_view.listado'))
        except Exception as e:
            conn.rollback()
            # Manejo específico de errores Oracle comunes
            error_str = str(e).upper()
            if "ORA-12899" in error_str:
                flash(f'Error: Alguno de los campos excede la longitud máxima permitida.', 'danger')
            elif "ORA-01400" in error_str:
                flash(f'Error: No se permiten campos vacíos.', 'danger')
            else:
                flash(f'Ocurrió un error inesperado al crear la actividad.', 'danger')
            return render_template('actividad_form.html', accion='Crear', actividad=request.form)
        finally:
            cur.close()
            conn.close()

    return render_template('actividad_form.html', accion='Crear', actividad={})

# Editar actividad (endpoint: editar_actividad)
@actividades_economicas_view.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_actividad(id):
    conn = get_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        # Validaciones
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('actividad_form.html', accion='Editar', actividad=request.form)
        if len(nombre) > MAX_LENGTH_NOMBRE:
            flash(f'El nombre no puede tener más de {MAX_LENGTH_NOMBRE} caracteres.', 'danger')
            return render_template('actividad_form.html', accion='Editar', actividad=request.form)

        if not descripcion:
            flash('La descripción es obligatoria.', 'danger')
            return render_template('actividad_form.html', accion='Editar', actividad=request.form)
        if len(descripcion) > MAX_LENGTH_DESCRIPCION:
            flash(f'La descripción no puede tener más de {MAX_LENGTH_DESCRIPCION} caracteres.', 'danger')
            return render_template('actividad_form.html', accion='Editar', actividad=request.form)

        # Validar nombre duplicado
        cur.execute("""
            SELECT COUNT(*) FROM actividades_economicas
            WHERE UPPER(nombre) = :nombre AND id_actividad != :id
        """, {'nombre': nombre.upper(), 'id': id})
        if cur.fetchone()[0] > 0:
            flash('Ya existe otra actividad con ese nombre.', 'danger')
            return render_template('actividad_form.html', accion='Editar', actividad=request.form)

        try:
            cur.execute("""
                UPDATE actividades_economicas
                SET nombre = :nombre, descripcion = :descripcion
                WHERE id_actividad = :id
            """, {'nombre': nombre, 'descripcion': descripcion, 'id': id})
            conn.commit()
            flash('Actividad actualizada correctamente.', 'success')
            return redirect(url_for('actividades_economicas_view.listado'))
        except Exception as e:
            conn.rollback()
            error_str = str(e).upper()
            if "ORA-12899" in error_str:
                flash(f'Error: Alguno de los campos excede la longitud máxima permitida.', 'danger')
            elif "ORA-01400" in error_str:
                flash(f'Error: No se permiten campos vacíos.', 'danger')
            else:
                flash(f'Ocurrió un error inesperado al editar la actividad.', 'danger')
            return render_template('actividad_form.html', accion='Editar', actividad=request.form)
        finally:
            cur.close()
            conn.close()

    # GET: obtener actividad para mostrar en formulario
    cur.execute("""
        SELECT nombre, descripcion
        FROM actividades_economicas
        WHERE id_actividad = :id
    """, {'id': id})
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        flash('Actividad no encontrada.', 'warning')
        return redirect(url_for('actividades_economicas_view.listado'))

    actividad = {'nombre': row[0], 'descripcion': row[1]}
    return render_template('actividad_form.html', accion='Editar', actividad=actividad)

# Eliminar actividad (endpoint: eliminar_actividad)
@actividades_economicas_view.route('/eliminar/<int:id>', methods=['GET'])
def eliminar_actividad(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM actividades_economicas
        WHERE id_actividad = :id
    """, {'id': id})
    conn.commit()
    cur.close()
    conn.close()
    flash('Actividad eliminada correctamente.', 'success')
    return redirect(url_for('actividades_economicas_view.listado'))
