from flask import Blueprint, request, jsonify, abort
from app.db import get_connection
from datetime import datetime

representantes_bp = Blueprint('representantes_bp', __name__, url_prefix='/representantes_legales')

# GET all
@representantes_bp.route('/', methods=['GET'])
def get_all_representantes():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id_representante, id_moral, nombre, apellido_paterno, apellido_materno, curp, rfc, telefono, email, fecha_nacimiento, estado
            FROM representantes_legales
            WHERE estado = 'ACTIVO'
        ''')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    result = []
    for r in rows:
        result.append({
            'id_representante': r[0],
            'id_moral': r[1],
            'nombre': r[2],
            'apellido_paterno': r[3],
            'apellido_materno': r[4],
            'curp': r[5],
            'rfc': r[6],
            'telefono': r[7],
            'email': r[8],
            'fecha_nacimiento': r[9].strftime('%Y-%m-%d') if r[9] else None,
            'estado': r[10]
        })
    return jsonify(result)

# GET by ID
@representantes_bp.route('/<int:id>', methods=['GET'])
def get_representante(id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id_representante, id_moral, nombre, apellido_paterno, apellido_materno, curp, rfc, telefono, email, fecha_nacimiento, estado
            FROM representantes_legales WHERE id_representante = :id
        ''', {'id': id})
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not row:
        abort(404, description="Representante legal no encontrado")

    return jsonify({
        'id_representante': row[0],
        'id_moral': row[1],
        'nombre': row[2],
        'apellido_paterno': row[3],
        'apellido_materno': row[4],
        'curp': row[5],
        'rfc': row[6],
        'telefono': row[7],
        'email': row[8],
        'fecha_nacimiento': row[9].strftime('%Y-%m-%d') if row[9] else None,
        'estado': row[10]
    })

# POST crear nuevo
@representantes_bp.route('/', methods=['POST'])
def create_representante():
    data = request.get_json()

    required_fields = ['id_moral', 'nombre', 'apellido_paterno', 'apellido_materno', 'curp', 'rfc']
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            abort(400, description=f"Falta o está vacío el campo requerido: {field}")

    fecha_nac = data.get('fecha_nacimiento')
    if fecha_nac is not None and not isinstance(fecha_nac, str):
        abort(400, description="fecha_nacimiento debe ser una cadena en formato YYYY-MM-DD")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO representantes_legales 
            (id_representante, id_moral, nombre, apellido_paterno, apellido_materno, curp, rfc, telefono, email, fecha_nacimiento, estado)
            VALUES (representantes_legales_seq.NEXTVAL, :id_moral, :nombre, :apellido_paterno, :apellido_materno, :curp, :rfc, :telefono, :email, 
            CASE WHEN :fecha_nacimiento IS NULL THEN NULL ELSE TO_DATE(:fecha_nacimiento, 'YYYY-MM-DD') END, 'ACTIVO')
        """, {
            'id_moral': data['id_moral'],
            'nombre': data['nombre'].strip(),
            'apellido_paterno': data['apellido_paterno'].strip(),
            'apellido_materno': data['apellido_materno'].strip(),
            'curp': data['curp'].strip(),
            'rfc': data['rfc'].strip(),
            'telefono': data.get('telefono'),
            'email': data.get('email'),
            'fecha_nacimiento': fecha_nac
        })
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al crear representante legal: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({'message': 'Representante legal creado exitosamente'}), 201

# PUT actualizar
@representantes_bp.route('/<int:id>', methods=['PUT'])
def update_representante(id):
    data = request.get_json()

    str_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'curp', 'rfc', 'telefono', 'email', 'estado']
    for f in str_fields:
        if f in data and isinstance(data[f], str) and not data[f].strip():
            abort(400, description=f"El campo {f} no puede estar vacío")

    if 'fecha_nacimiento' in data and data['fecha_nacimiento'] is not None and not isinstance(data['fecha_nacimiento'], str):
        abort(400, description="fecha_nacimiento debe ser una cadena en formato YYYY-MM-DD")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM representantes_legales WHERE id_representante = :id", {'id': id})
        if not cursor.fetchone():
            abort(404, description="Representante legal no encontrado")

        fields = ['id_moral', 'nombre', 'apellido_paterno', 'apellido_materno', 'curp', 'rfc', 'telefono', 'email', 'fecha_nacimiento', 'estado']
        updates = []
        params = {}

        for field in fields:
            if field in data:
                if field == 'fecha_nacimiento':
                    updates.append(f"{field} = CASE WHEN :{field} IS NULL THEN NULL ELSE TO_DATE(:{field}, 'YYYY-MM-DD') END")
                else:
                    updates.append(f"{field} = :{field}")
                params[field] = data[field].strip() if isinstance(data[field], str) else data[field]

        if not updates:
            abort(400, description="No hay campos para actualizar")

        params['id'] = id
        sql = f"UPDATE representantes_legales SET {', '.join(updates)} WHERE id_representante = :id"

        cursor.execute(sql, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al actualizar: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({'message': 'Representante legal actualizado exitosamente'})

# DELETE eliminar (borrado físico)
@representantes_bp.route('/<int:id>', methods=['DELETE'])
def delete_representante(id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM representantes_legales WHERE id_representante = :id", {'id': id})
        if not cursor.fetchone():
            abort(404, description="Representante legal no encontrado")

        cursor.execute("DELETE FROM representantes_legales WHERE id_representante = :id", {'id': id})
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al eliminar: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({'message': 'Representante legal eliminado exitosamente'})
