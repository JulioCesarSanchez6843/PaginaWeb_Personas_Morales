from flask import Blueprint, request, jsonify, abort
from app.db import get_connection
from datetime import datetime

documentos_bp = Blueprint('documentos_bp', __name__, url_prefix='/documentos')

# GET all documentos
@documentos_bp.route('/', methods=['GET'])
def get_all_documentos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id_documento, id_moral, tipo_documento AS tipo, nombre_archivo, fecha_subida
        FROM documento_persona_moral
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            'id_documento': r[0],
            'id_moral': r[1],
            'tipo': r[2],
            'nombre_archivo': r[3],
            'fecha_subida': r[4].strftime('%Y-%m-%d') if r[4] else None
        })
    return jsonify(result)

# GET documento by id
@documentos_bp.route('/<int:id_documento>', methods=['GET'])
def get_documento(id_documento):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id_documento, id_moral, tipo_documento AS tipo, nombre_archivo, fecha_subida
        FROM documento_persona_moral
        WHERE id_documento = :id
    ''', [id_documento])
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        abort(404, description="Documento no encontrado")

    result = {
        'id_documento': row[0],
        'id_moral': row[1],
        'tipo': row[2],
        'nombre_archivo': row[3],
        'fecha_subida': row[4].strftime('%Y-%m-%d') if row[4] else None
    }
    return jsonify(result)

# POST crear documento
@documentos_bp.route('/', methods=['POST'])
def create_documento():
    data = request.get_json()

    required_fields = ['id_moral', 'tipo', 'nombre_archivo']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Falta el campo requerido: {field}")

    id_moral = data['id_moral']
    tipo = data['tipo']
    nombre_archivo = data['nombre_archivo']
    fecha_subida = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    # Validar que id_moral exista
    cursor.execute('SELECT id_moral FROM personas_morales WHERE id_moral = :id', [id_moral])
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        abort(400, description="id_moral no existe en personas_morales")

    try:
        cursor.execute("""
            INSERT INTO documento_persona_moral 
            (id_documento, id_moral, tipo_documento, nombre_archivo, fecha_subida)
            VALUES (documento_persona_moral_seq.NEXTVAL, :id_moral, :tipo_documento, :nombre_archivo, :fecha_subida)
        """, {
            'id_moral': id_moral,
            'tipo_documento': tipo,
            'nombre_archivo': nombre_archivo,
            'fecha_subida': fecha_subida
        })
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al crear documento: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Documento creado exitosamente"}), 201

# PUT actualizar documento
@documentos_bp.route('/<int:id_documento>', methods=['PUT'])
def update_documento(id_documento):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id_documento FROM documento_persona_moral WHERE id_documento = :id', [id_documento])
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        abort(404, description="Documento no encontrado")

    # Si se actualiza id_moral, validar que exista
    if 'id_moral' in data:
        cursor.execute('SELECT id_moral FROM personas_morales WHERE id_moral = :id', [data['id_moral']])
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            abort(400, description="id_moral no existe en personas_morales")

    fields = ['id_moral', 'tipo_documento', 'nombre_archivo', 'fecha_subida']
    updates = []
    params = {}
    for f in fields:
        if f in data:
            if f == 'fecha_subida':
                updates.append(f"{f} = TO_DATE(:{f}, 'YYYY-MM-DD')")
                params[f] = data[f]  # debe venir como string "YYYY-MM-DD"
            else:
                updates.append(f"{f} = :{f}")
                if f == 'tipo_documento':
                    params[f] = data.get('tipo')
                else:
                    params[f] = data[f]

    if not updates:
        cursor.close()
        conn.close()
        abort(400, description="No hay campos para actualizar")

    params['id'] = id_documento
    sql = f"UPDATE documento_persona_moral SET {', '.join(updates)} WHERE id_documento = :id"

    try:
        cursor.execute(sql, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al actualizar documento: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Documento actualizado exitosamente"})

# DELETE eliminar documento
@documentos_bp.route('/<int:id_documento>', methods=['DELETE'])
def delete_documento(id_documento):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id_documento FROM documento_persona_moral WHERE id_documento = :id', [id_documento])
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        abort(404, description="Documento no encontrado")

    try:
        cursor.execute('DELETE FROM documento_persona_moral WHERE id_documento = :id', [id_documento])
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(500, description=f"Error al eliminar documento: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Documento eliminado exitosamente"})
