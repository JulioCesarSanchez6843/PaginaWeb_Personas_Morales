# app/routes.py
from flask import jsonify, request
from app import app
from app.db import get_connection
from datetime import datetime
from app import app

@app.route('/')
def home():
    return "API funcionando correctamente"

# ---------------------------
# Personas Morales
# ---------------------------

@app.route('/personas_morales', methods=['GET'])
def listar_personas_morales():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
        SELECT id_moral, razon_social, rfc, fecha_constitucion, domicilio_fiscal,
               telefono, email, estado, fecha_registro
        FROM personas_morales
        ORDER BY id_moral
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()

    return jsonify([
        {
            'id_moral': r[0],
            'razon_social': r[1],
            'rfc': r[2],
            'fecha_constitucion': r[3].isoformat() if r[3] else None,
            'domicilio_fiscal': r[4],
            'telefono': r[5],
            'email': r[6],
            'estado': r[7],
            'fecha_registro': r[8].isoformat() if r[8] else None
        } for r in rows
    ])

@app.route('/personas_morales/<int:id_moral>', methods=['GET'])
def obtener_persona_moral(id_moral):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id_moral, razon_social, rfc FROM personas_morales WHERE id_moral = :id", {'id': id_moral})
    r = cursor.fetchone()
    cursor.close(); conn.close()
    if not r: return jsonify({'error':'No encontrada'}), 404
    return jsonify({'id_moral':r[0],'razon_social':r[1],'rfc':r[2]})

@app.route('/personas_morales', methods=['POST'])
def crear_persona_moral():
    data = request.json or {}
    for f in ('razon_social','rfc'): 
        if f not in data: return jsonify({'error':f'Falta {f}'}),400

    # fechas opcionales
    def pdate(field):
        v = data.get(field)
        return datetime.fromisoformat(v) if v else None

    params = {
        'razon_social': data['razon_social'],
        'rfc': data['rfc'],
        'fecha_constitucion': pdate('fecha_constitucion'),
        'domicilio_fiscal': data.get('domicilio_fiscal'),
        'telefono': data.get('telefono'),
        'email': data.get('email'),
        'estado': data.get('estado','ACTIVO'),
        'fecha_registro': pdate('fecha_registro'),
    }

    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO personas_morales
            (razon_social, rfc, fecha_constitucion, domicilio_fiscal, telefono, email, estado, fecha_registro)
            VALUES (:razon_social, :rfc, :fecha_constitucion, :domicilio_fiscal, :telefono, :email, :estado, :fecha_registro)
        """, params)
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Creada'}),201

@app.route('/personas_morales/<int:id_moral>', methods=['PUT'])
def actualizar_persona_moral(id_moral):
    data = request.json or {}
    allowed = ['razon_social','rfc','fecha_constitucion','domicilio_fiscal','telefono','email','estado','fecha_registro']
    set_cl = []; params = {'id':id_moral}
    for f in allowed:
        if f in data:
            if 'fecha' in f and data[f]:
                set_cl.append(f"{f}=TO_DATE(:{f},'YYYY-MM-DD')")
            else:
                set_cl.append(f"{f} = :{f}")
            params[f] = data[f]
    if not set_cl: return jsonify({'error':'Nada que actualizar'}),400

    sql = f"UPDATE personas_morales SET {', '.join(set_cl)} WHERE id_moral = :id"
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        if cursor.rowcount==0: return jsonify({'error':'No encontrada'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Actualizada'})

@app.route('/personas_morales/<int:id_moral>', methods=['DELETE'])
def eliminar_persona_moral(id_moral):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM personas_morales WHERE id_moral = :id", {'id':id_moral})
        if cursor.rowcount==0: return jsonify({'error':'No encontrada'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Eliminada'})


# ---------------------------
# Representantes Legales
# ---------------------------

@app.route('/representantes_legales', methods=['GET'])
def listar_representantes_legales():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
      SELECT id_representante, id_moral, nombre, curp, rfc, telefono, email, fecha_nacimiento, apellido
      FROM representantes_legales ORDER BY id_representante
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify([
        {
          'id_representante':r[0],
          'id_moral':r[1],
          'nombre':r[2],
          'curp':r[3],
          'rfc':r[4],
          'telefono':r[5],
          'email':r[6],
          'fecha_nacimiento':r[7].isoformat() if r[7] else None,
          'apellido':r[8]
        } for r in rows
    ])

@app.route('/representantes_legales/<int:id_rep>', methods=['GET'])
def obtener_representante(id_rep):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
      SELECT id_representante, id_moral, nombre, curp, rfc, telefono, email, fecha_nacimiento, apellido
      FROM representantes_legales WHERE id_representante = :id
    """, {'id':id_rep})
    r = cursor.fetchone()
    cursor.close(); conn.close()
    if not r: return jsonify({'error':'No encontrado'}),404
    return jsonify({
      'id_representante':r[0],'id_moral':r[1],'nombre':r[2],
      'curp':r[3],'rfc':r[4],'telefono':r[5],'email':r[6],
      'fecha_nacimiento':r[7].isoformat() if r[7] else None,
      'apellido':r[8]
    })

@app.route('/representantes_legales', methods=['POST'])
def crear_representante():
    data = request.json or {}
    for f in ('id_moral','nombre'):
        if f not in data: return jsonify({'error':f'Falta {f}'}),400

    # fecha opcional
    fn = data.get('fecha_nacimiento')
    if fn:
        try: data['fecha_nacimiento'] = datetime.fromisoformat(fn)
        except: return jsonify({'error':'Formato fecha inválido'}),400

    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
          INSERT INTO representantes_legales
            (id_moral,nombre,curp,rfc,telefono,email,fecha_nacimiento,apellido)
          VALUES
            (:id_moral,:nombre,:curp,:rfc,:telefono,:email,:fecha_nacimiento,:apellido)
        """, data)
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Creado'}),201

@app.route('/representantes_legales/<int:id_rep>', methods=['PUT'])
def actualizar_representante(id_rep):
    data = request.json or {}
    allowed = ['id_moral','nombre','curp','rfc','telefono','email','fecha_nacimiento','apellido']
    set_cl=[]; params={'id':id_rep}
    for f in allowed:
        if f in data:
            if f=='fecha_nacimiento' and data[f]:
                set_cl.append(f"{f}=TO_DATE(:{f},'YYYY-MM-DD')")
            else:
                set_cl.append(f"{f} = :{f}")
            params[f]=data[f]
    if not set_cl: return jsonify({'error':'Nada que actualizar'}),400

    sql = f"UPDATE representantes_legales SET {', '.join(set_cl)} WHERE id_representante = :id"
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        if cursor.rowcount==0: return jsonify({'error':'No encontrado'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Actualizado'})

@app.route('/representantes_legales/<int:id_rep>', methods=['DELETE'])
def eliminar_representante(id_rep):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM representantes_legales WHERE id_representante = :id", {'id':id_rep})
        if cursor.rowcount==0: return jsonify({'error':'No encontrado'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Eliminado'})


# ---------------------------
# Actividades Económicas
# ---------------------------

@app.route('/actividades_economicas', methods=['GET'])
def listar_actividades():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id_actividad, nombre, descripcion FROM actividades_economicas ORDER BY id_actividad")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify([
        {
            'id_actividad': r[0],
            'nombre': r[1],
            'descripcion': r[2]
        } for r in rows
    ])

@app.route('/actividades_economicas/<int:id_act>', methods=['GET'])
def obtener_actividad(id_act):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
        SELECT id_actividad, nombre, descripcion 
        FROM actividades_economicas 
        WHERE id_actividad = :id
    """, {'id': id_act})
    r = cursor.fetchone()
    cursor.close(); conn.close()
    if not r:
        return jsonify({'error': 'No encontrada'}), 404
    return jsonify({
        'id_actividad': r[0],
        'nombre': r[1],
        'descripcion': r[2]
    })

@app.route('/actividades_economicas', methods=['POST'])
def crear_actividad():
    data = request.json or {}
    if 'descripcion' not in data or 'nombre' not in data:
        return jsonify({'error': 'Faltan campos requeridos: nombre y/o descripcion'}), 400

    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO actividades_economicas(nombre, descripcion) 
            VALUES(:nombre, :descripcion)
        """, {
            'nombre': data['nombre'].strip(),
            'descripcion': data['descripcion'].strip()
        })
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message': 'Creada'}), 201

@app.route('/actividades_economicas/<int:id_act>', methods=['PUT'])
def actualizar_actividad(id_act):
    data = request.json or {}
    if 'descripcion' not in data and 'nombre' not in data:
        return jsonify({'error': 'Falta al menos un campo para actualizar (nombre o descripcion)'}), 400

    conn = get_connection(); cursor = conn.cursor()
    try:
        update_fields = []
        params = {'id': id_act}

        if 'nombre' in data:
            update_fields.append("nombre = :nombre")
            params['nombre'] = data['nombre'].strip()

        if 'descripcion' in data:
            update_fields.append("descripcion = :descripcion")
            params['descripcion'] = data['descripcion'].strip()

        if not update_fields:
            return jsonify({'error': 'Nada que actualizar'}), 400

        sql = f"""
            UPDATE actividades_economicas 
            SET {', '.join(update_fields)} 
            WHERE id_actividad = :id
        """
        cursor.execute(sql, params)

        if cursor.rowcount == 0:
            return jsonify({'error': 'No encontrada'}), 404
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message': 'Actualizada'})

@app.route('/actividades_economicas/<int:id_act>', methods=['DELETE'])
def eliminar_actividad(id_act):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM actividades_economicas WHERE id_actividad = :id", {'id': id_act})
        if cursor.rowcount == 0:
            return jsonify({'error': 'No encontrada'}), 404
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message': 'Eliminada'})


# ---------------------------
# Moral Actividades (relación)
# ---------------------------

@app.route('/moral_actividades', methods=['GET'])
def listar_moral_actividades():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id_moral, id_actividad FROM moral_actividades ORDER BY id_moral, id_actividad")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify([{'id_moral':r[0],'id_actividad':r[1]} for r in rows])

@app.route('/moral_actividades/<int:id_moral>/<int:id_act>', methods=['GET'])
def obtener_moral_actividad(id_moral, id_act):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
      SELECT id_moral, id_actividad
      FROM moral_actividades
      WHERE id_moral = :idm AND id_actividad = :ida
    """, {'idm':id_moral,'ida':id_act})
    r = cursor.fetchone()
    cursor.close(); conn.close()
    if not r: return jsonify({'error':'No encontrada'}),404
    return jsonify({'id_moral':r[0],'id_actividad':r[1]})

@app.route('/moral_actividades', methods=['POST'])
def crear_moral_actividad():
    data = request.json or {}
    for f in ('id_moral','id_actividad'):
        if f not in data: return jsonify({'error':f'Falta {f}'}),400

    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
          INSERT INTO moral_actividades(id_moral,id_actividad)
          VALUES(:id_moral,:id_actividad)
        """, data)
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Creada'}),201

@app.route('/moral_actividades/<int:id_moral>/<int:id_act>', methods=['DELETE'])
def eliminar_moral_actividad(id_moral, id_act):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
          DELETE FROM moral_actividades
          WHERE id_moral = :idm AND id_actividad = :ida
        """, {'idm':id_moral,'ida':id_act})
        if cursor.rowcount==0: return jsonify({'error':'No encontrada'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Eliminada'})


# ---------------------------
# Documento Persona Moral
# ---------------------------

@app.route('/documento_persona_moral', methods=['GET'])
def listar_documentos():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
      SELECT id_documento, id_moral, nombre_archivo, tipo_documento, fecha_subida
      FROM documento_persona_moral
      ORDER BY id_documento
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify([
        {
          'id_documento':r[0],
          'id_moral':r[1],
          'nombre_archivo':r[2],
          'tipo_documento':r[3],
          'fecha_subida':r[4].isoformat() if r[4] else None
        } for r in rows
    ])

@app.route('/documento_persona_moral/<int:id_doc>', methods=['GET'])
def obtener_documento(id_doc):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
      SELECT id_documento, id_moral, nombre_archivo, tipo_documento, fecha_subida
      FROM documento_persona_moral
      WHERE id_documento = :id
    """, {'id':id_doc})
    r = cursor.fetchone()
    cursor.close(); conn.close()
    if not r: return jsonify({'error':'No encontrado'}),404
    return jsonify({
      'id_documento':r[0],'id_moral':r[1],
      'nombre_archivo':r[2],'tipo_documento':r[3],
      'fecha_subida':r[4].isoformat() if r[4] else None
    })

@app.route('/documento_persona_moral', methods=['POST'])
def crear_documento():
    data = request.json or {}
    for f in ('id_moral','nombre_archivo'):
        if f not in data: return jsonify({'error':f'Falta {f}'}),400

    # fecha subida opcional
    fs = data.get('fecha_subida')
    if fs:
        try: data['fecha_subida'] = datetime.fromisoformat(fs)
        except: return jsonify({'error':'Formato fecha inválido'}),400

    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
          INSERT INTO documento_persona_moral
            (id_moral,nombre_archivo,tipo_documento,contenido,fecha_subida)
          VALUES
            (:id_moral,:nombre_archivo,:tipo_documento,EMPTY_BLOB(),:fecha_subida)
        """, data)
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Creado'}),201

@app.route('/documento_persona_moral/<int:id_doc>', methods=['PUT'])
def actualizar_documento(id_doc):
    data = request.json or {}
    campos = ['id_moral','nombre_archivo','tipo_documento','fecha_subida']
    set_cl=[]; params={'id':id_doc}
    for f in campos:
        if f in data:
            if f=='fecha_subida' and data[f]:
                set_cl.append(f"{f}=TO_DATE(:{f},'YYYY-MM-DD')")
            else:
                set_cl.append(f"{f} = :{f}")
            params[f]= data[f]
    if not set_cl: return jsonify({'error':'Nada que actualizar'}),400

    sql = f"UPDATE documento_persona_moral SET {', '.join(set_cl)} WHERE id_documento = :id"
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        if cursor.rowcount==0: return jsonify({'error':'No encontrado'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Actualizado'})

@app.route('/documento_persona_moral/<int:id_doc>', methods=['DELETE'])
def eliminar_documento(id_doc):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM documento_persona_moral WHERE id_documento = :id", {'id':id_doc})
        if cursor.rowcount==0: return jsonify({'error':'No encontrado'}),404
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error':str(e)}),500
    finally:
        cursor.close(); conn.close()
    return jsonify({'message':'Eliminado'})
