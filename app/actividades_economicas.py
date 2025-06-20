from flask import Blueprint, request, jsonify, abort
from app.db import get_connection
from datetime import datetime

actividades_economicas_bp = Blueprint('actividades_economicas_bp', __name__, url_prefix='/actividades_economicas')

# GET all actividades_economicas, con filtro opcional por nombre o descripción
@actividades_economicas_bp.route('/', methods=['GET'])
def get_all():
    nombre_filtro = request.args.get('nombre', '').strip().lower()
    descripcion_filtro = request.args.get('descripcion', '').strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = {}

        if nombre_filtro:
            filtros.append("LOWER(nombre) LIKE :nombre")
            params['nombre'] = f"%{nombre_filtro}%"
        if descripcion_filtro:
            filtros.append("LOWER(descripcion) LIKE :descripcion")
            params['descripcion'] = f"%{descripcion_filtro}%"

        where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"""
            SELECT id_actividad, nombre, descripcion, fecha_registro
            FROM actividades_economicas
            {where_clause}
            ORDER BY id_actividad
        """, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    result = []
    for r in rows:
        result.append({
            'id_actividad': r[0],
            'nombre': r[1],
            'descripcion': r[2],
            'fecha_registro': r[3].strftime('%Y-%m-%d') if r[3] else None
        })
    return jsonify(result)

# GET una actividad por ID
@actividades_economicas_bp.route('/<int:id_actividad>', methods=['GET'])
def get_one(id_actividad):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id_actividad, nombre, descripcion, fecha_registro
            FROM actividades_economicas
            WHERE id_actividad = :id
        """, {'id': id_actividad})
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if row is None:
        abort(404, description="Actividad económica no encontrada")

    result = {
        'id_actividad': row[0],
        'nombre': row[1],
        'descripcion': row[2],
        'fecha_registro': row[3].strftime('%Y-%m-%d') if row[3] else None
    }
    return jsonify(result)

# POST crear nueva actividad
@actividades_economicas_bp.route('/', methods=['POST'])
def create():
    data = request.get_json()

    if 'nombre' not in data or not data['nombre'].strip():
        abort(400, description="Falta o es vacío el campo requerido: nombre")
    if 'descripcion' not in data or not data['descripcion'].strip():
        abort(400, description="Falta o es vacío el campo requerido: descripcion")

    nombre = data['nombre'].strip()
    descripcion = data['descripcion'].strip()
    fecha_registro = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO actividades_economicas 
            (id_actividad, nombre, descripcion, fecha_registro)
            VALUES (actividades_economicas_seq.NEXTVAL, :nombre, :descripcion, :fecha_registro)
        """, {
            'nombre': nombre,
            'descripcion': descripcion,
            'fecha_registro': fecha_registro
        })
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al crear actividad económica: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Actividad económica creada exitosamente"}), 201

# PUT actualizar actividad
@actividades_economicas_bp.route('/<int:id_actividad>', methods=['PUT'])
def update(id_actividad):
    data = request.get_json()

    if 'nombre' in data and not data['nombre'].strip():
        abort(400, description="El campo nombre no puede estar vacío")
    if 'descripcion' in data and not data['descripcion'].strip():
        abort(400, description="El campo descripcion no puede estar vacío")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT id_actividad FROM actividades_economicas WHERE id_actividad = :id', {'id': id_actividad})
        if cursor.fetchone() is None:
            abort(404, description="Actividad económica no encontrada")

        fields = ['nombre', 'descripcion', 'fecha_registro']
        updates = []
        params = {}

        for f in fields:
            if f in data:
                if f == 'fecha_registro':
                    updates.append(f"{f} = TO_DATE(:{f}, 'YYYY-MM-DD')")
                else:
                    updates.append(f"{f} = :{f}")
                params[f] = data[f].strip() if isinstance(data[f], str) else data[f]

        if not updates:
            abort(400, description="No hay campos para actualizar")

        params['id'] = id_actividad
        sql = f"UPDATE actividades_economicas SET {', '.join(updates)} WHERE id_actividad = :id"

        cursor.execute(sql, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al actualizar actividad económica: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Actividad económica actualizada exitosamente"})

# DELETE eliminar actividad
@actividades_economicas_bp.route('/<int:id_actividad>', methods=['DELETE'])
def delete(id_actividad):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT id_actividad FROM actividades_economicas WHERE id_actividad = :id', {'id': id_actividad})
        if cursor.fetchone() is None:
            abort(404, description="Actividad económica no encontrada")

        cursor.execute('DELETE FROM actividades_economicas WHERE id_actividad = :id', {'id': id_actividad})
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al eliminar actividad económica: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Actividad económica eliminada exitosamente"})
