# app/personas_morales.py
from flask import Blueprint, request, jsonify, abort
from app.db import get_connection
from datetime import datetime

personas_morales_bp = Blueprint('personas_morales_bp', __name__, url_prefix='/personas_morales')

# GET all personas_morales
@personas_morales_bp.route('/', methods=['GET'])
def get_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id_moral, razon_social, rfc, fecha_constitucion, domicilio_fiscal, telefono, email, estado, fecha_registro FROM personas_morales')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            'id_moral': r[0],
            'razon_social': r[1],
            'rfc': r[2],
            'fecha_constitucion': r[3].strftime('%Y-%m-%d') if r[3] else None,
            'domicilio_fiscal': r[4],
            'telefono': r[5],
            'email': r[6],
            'estado': r[7],
            'fecha_registro': r[8].strftime('%Y-%m-%d') if r[8] else None
        })
    return jsonify(result)

# GET one persona_moral by id
@personas_morales_bp.route('/<int:id_moral>', methods=['GET'])
def get_one(id_moral):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id_moral, razon_social, rfc, fecha_constitucion, domicilio_fiscal, telefono, email, estado, fecha_registro FROM personas_morales WHERE id_moral = :id', [id_moral])
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        abort(404, description="Persona moral no encontrada")

    result = {
        'id_moral': row[0],
        'razon_social': row[1],
        'rfc': row[2],
        'fecha_constitucion': row[3].strftime('%Y-%m-%d') if row[3] else None,
        'domicilio_fiscal': row[4],
        'telefono': row[5],
        'email': row[6],
        'estado': row[7],
        'fecha_registro': row[8].strftime('%Y-%m-%d') if row[8] else None
    }
    return jsonify(result)

# POST crear nueva persona_moral
@personas_morales_bp.route('/', methods=['POST'])
def create():
    data = request.get_json()

    required_fields = ['razon_social', 'rfc']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Falta el campo requerido: {field}")

    razon_social = data.get('razon_social')
    rfc = data.get('rfc')
    fecha_constitucion = data.get('fecha_constitucion')  # espera 'YYYY-MM-DD' o None
    domicilio_fiscal = data.get('domicilio_fiscal')
    telefono = data.get('telefono')
    email = data.get('email')
    estado = data.get('estado')
    fecha_registro = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO personas_morales 
            (id_moral, razon_social, rfc, fecha_constitucion, domicilio_fiscal, telefono, email, estado, fecha_registro)
            VALUES (personas_morales_seq.NEXTVAL, :razon_social, :rfc, TO_DATE(:fecha_constitucion, 'YYYY-MM-DD'), :domicilio_fiscal, :telefono, :email, :estado, :fecha_registro)
        """, {
            'razon_social': razon_social,
            'rfc': rfc,
            'fecha_constitucion': fecha_constitucion,
            'domicilio_fiscal': domicilio_fiscal,
            'telefono': telefono,
            'email': email,
            'estado': estado,
            'fecha_registro': fecha_registro
        })
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        abort(500, description=f"Error al crear persona moral: {str(e)}")

    cursor.close()
    conn.close()
    return jsonify({"message": "Persona moral creada exitosamente"}), 201

# PUT actualizar persona_moral
@personas_morales_bp.route('/<int:id_moral>', methods=['PUT'])
def update(id_moral):
    data = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si existe
    cursor.execute('SELECT id_moral FROM personas_morales WHERE id_moral = :id', [id_moral])
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        abort(404, description="Persona moral no encontrada")

    # Construir update dinámico solo con campos que vengan en el JSON
    fields = ['razon_social', 'rfc', 'fecha_constitucion', 'domicilio_fiscal', 'telefono', 'email', 'estado', 'fecha_registro']
    updates = []
    params = {}
    for f in fields:
        if f in data:
            if f == 'fecha_constitucion' or f == 'fecha_registro':
                updates.append(f"{f} = TO_DATE(:{f}, 'YYYY-MM-DD')")
            else:
                updates.append(f"{f} = :{f}")
            params[f] = data[f]

    if not updates:
        cursor.close()
        conn.close()
        abort(400, description="No hay campos para actualizar")

    params['id'] = id_moral
    sql = f"UPDATE personas_morales SET {', '.join(updates)} WHERE id_moral = :id"

    try:
        cursor.execute(sql, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        abort(500, description=f"Error al actualizar persona moral: {str(e)}")

    cursor.close()
    conn.close()
    return jsonify({"message": "Persona moral actualizada exitosamente"})

# DELETE eliminar persona_moral
@personas_morales_bp.route('/<int:id_moral>', methods=['DELETE'])
def delete(id_moral):
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si existe
    cursor.execute('SELECT id_moral FROM personas_morales WHERE id_moral = :id', [id_moral])
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        abort(404, description="Persona moral no encontrada")

    try:
        cursor.execute('DELETE FROM personas_morales WHERE id_moral = :id', [id_moral])
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        abort(500, description=f"Error al eliminar persona moral: {str(e)}")

    cursor.close()
    conn.close()
    return jsonify({"message": "Persona moral eliminada exitosamente"})
