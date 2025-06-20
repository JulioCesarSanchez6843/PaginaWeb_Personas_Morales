from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_connection

moral_actividades_view = Blueprint(
    'moral_actividades_view',
    __name__,
    url_prefix='/vista/moral_actividades'
)

# Página intermedia con opciones: Consultar o Crear
@moral_actividades_view.route('/opciones', methods=['GET'])
def opciones():
    return render_template('moral_actividades_opciones.html')


# Listar (y filtrar) asignaciones usando selects desplegables
@moral_actividades_view.route('/', methods=['GET'])
def listado():
    conn = get_connection()
    cur = conn.cursor()

    # Carga listas para los selects
    cur.execute("SELECT ID_MORAL, RAZON_SOCIAL FROM personas_morales ORDER BY RAZON_SOCIAL")
    personas_morales = cur.fetchall()
    cur.execute("SELECT ID_ACTIVIDAD, NOMBRE FROM actividades_economicas ORDER BY NOMBRE")
    actividades = cur.fetchall()

    # Lee filtros por ID desde el querystring
    filtro_moral     = request.args.get('id_moral', '').strip()
    filtro_actividad = request.args.get('id_actividad', '').strip()

    where_clauses = []
    params = {}

    if filtro_moral:
        where_clauses.append("ma.ID_MORAL = :id_moral")
        params['id_moral'] = filtro_moral
    if filtro_actividad:
        where_clauses.append("ma.ID_ACTIVIDAD = :id_actividad")
        params['id_actividad'] = filtro_actividad

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    sql = f"""
        SELECT
          ma.ID_MORAL,
          pm.RAZON_SOCIAL   AS NOMBRE_MORAL,
          ma.ID_ACTIVIDAD,
          ae.NOMBRE         AS NOMBRE_ACTIVIDAD,
          ae.DESCRIPCION    AS DESCRIPCION
        FROM moral_actividades ma
        JOIN personas_morales pm
          ON ma.ID_MORAL = pm.ID_MORAL
        JOIN actividades_economicas ae
          ON ma.ID_ACTIVIDAD = ae.ID_ACTIVIDAD
        {where_sql}
      ORDER BY pm.RAZON_SOCIAL, ae.NOMBRE
    """

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    asignaciones = [
        {
            'id_moral':         r[0],
            'nombre_moral':     r[1],
            'id_actividad':     r[2],
            'nombre_actividad': r[3],
            'descripcion':      r[4],
        }
        for r in rows
    ]

    return render_template(
        'moral_actividades.html',
        personas_morales=personas_morales,
        actividades=actividades,
        asignaciones=asignaciones,
        filtro_moral=filtro_moral,
        filtro_actividad=filtro_actividad
    )


# Eliminar asignación
@moral_actividades_view.route('/eliminar/<int:id_moral>/<int:id_actividad>', methods=['POST'])
def eliminar_asignacion(id_moral, id_actividad):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM moral_actividades
         WHERE ID_MORAL     = :id_moral
           AND ID_ACTIVIDAD = :id_actividad
    """, {'id_moral': id_moral, 'id_actividad': id_actividad})
    conn.commit()
    cur.close()
    conn.close()
    flash('Asignación eliminada correctamente.', 'success')
    return redirect(url_for('moral_actividades_view.listado'))


# Crear nueva asignación
@moral_actividades_view.route('/nuevo', methods=['GET', 'POST'])
def nueva_asignacion():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ID_MORAL, RAZON_SOCIAL FROM personas_morales ORDER BY RAZON_SOCIAL")
    personas_morales = cur.fetchall()
    cur.execute("SELECT ID_ACTIVIDAD, NOMBRE FROM actividades_economicas ORDER BY NOMBRE")
    actividades = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        id_moral     = request.form.get('id_moral', '').strip()
        id_actividad = request.form.get('id_actividad', '').strip()

        if not id_moral or not id_actividad:
            flash('Persona Moral y Actividad son obligatorios.', 'warning')
            return render_template(
                'moral_actividad_form.html',
                accion='Crear',
                personas_morales=personas_morales,
                actividades=actividades
            )

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM moral_actividades
             WHERE ID_MORAL = :id_moral
               AND ID_ACTIVIDAD = :id_actividad
        """, {'id_moral': id_moral, 'id_actividad': id_actividad})
        if cur.fetchone()[0] > 0:
            flash('Esta asignación ya existe.', 'danger')
            cur.close()
            conn.close()
            return render_template(
                'moral_actividad_form.html',
                accion='Crear',
                personas_morales=personas_morales,
                actividades=actividades
            )

        cur.execute("""
            INSERT INTO moral_actividades (ID_MORAL, ID_ACTIVIDAD)
            VALUES (:id_moral, :id_actividad)
        """, {'id_moral': id_moral, 'id_actividad': id_actividad})
        conn.commit()
        cur.close()
        conn.close()
        flash('Asignación creada correctamente.', 'success')
        return redirect(url_for('moral_actividades_view.listado'))

    return render_template(
        'moral_actividad_form.html',
        accion='Crear',
        personas_morales=personas_morales,
        actividades=actividades
    )


# Editar asignación (no implementado)
@moral_actividades_view.route('/editar/<int:id_moral>/<int:id_actividad>', methods=['GET', 'POST'])
def editar_asignacion(id_moral, id_actividad):
    if request.method == 'POST':
        flash('Funcionalidad de edición no implementada.', 'info')
        return redirect(url_for('moral_actividades_view.listado'))

    return render_template(
        'moral_actividad_form.html',
        accion='Editar',
        asignacion={'id_moral': id_moral, 'id_actividad': id_actividad}
    )
