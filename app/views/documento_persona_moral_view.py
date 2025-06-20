from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from io import BytesIO
from datetime import datetime
from app.db import get_db

documentos_view = Blueprint(
    'documentos_view',
    __name__,
    url_prefix='/vista/documentos'
)

# 🔹 Vista intermedia con opciones
@documentos_view.route('/')
def opciones():
    return render_template('documentos_opciones.html')

# 🔸 Consultar documentos con filtros
@documentos_view.route('/consultar', methods=['GET'])
def listar_documentos():
    db = get_db()
    cursor = db.cursor()

    # Obtener parámetros de búsqueda
    nombre_moral = request.args.get('nombre_moral', '').strip()
    nombre_archivo = request.args.get('nombre_archivo', '').strip()
    tipo_documento = request.args.get('tipo_documento', '').strip()
    fecha_subida = request.args.get('fecha_subida', '').strip()

    # Consulta base con JOIN
    sql = """
        SELECT 
          d.ID_DOCUMENTO, 
          d.ID_MORAL, 
          p.RAZON_SOCIAL,
          d.NOMBRE_ARCHIVO, 
          d.TIPO_DOCUMENTO, 
          d.FECHA_SUBIDA
        FROM DOCUMENTO_PERSONA_MORAL d
        JOIN PERSONAS_MORALES p ON d.ID_MORAL = p.ID_MORAL
        WHERE 1=1
    """
    params = {}

    # Agregar filtros si existen
    if nombre_moral:
        sql += " AND LOWER(p.RAZON_SOCIAL) LIKE :nombre_moral"
        params['nombre_moral'] = f"%{nombre_moral.lower()}%"
    if nombre_archivo:
        sql += " AND LOWER(d.NOMBRE_ARCHIVO) LIKE :nombre_archivo"
        params['nombre_archivo'] = f"%{nombre_archivo.lower()}%"
    if tipo_documento:
        sql += " AND LOWER(d.TIPO_DOCUMENTO) LIKE :tipo_documento"
        params['tipo_documento'] = f"%{tipo_documento.lower()}%"
    if fecha_subida:
        sql += " AND TO_CHAR(d.FECHA_SUBIDA, 'YYYY-MM-DD') = :fecha_subida"
        params['fecha_subida'] = fecha_subida

    sql += " ORDER BY d.ID_DOCUMENTO"

    cursor.execute(sql, params)
    documentos = []
    for row in cursor.fetchall():
        documentos.append({
            'id_documento': row[0],
            'id_moral': row[1],
            'nombre_moral': row[2],
            'nombre_archivo': row[3],
            'tipo_documento': row[4],
            'fecha_subida': row[5]
        })

    cursor.close()

    filtros = {
        'nombre_moral': nombre_moral,
        'nombre_archivo': nombre_archivo,
        'tipo_documento': tipo_documento,
        'fecha_subida': fecha_subida
    }

    return render_template('documento_persona_moral.html', documentos=documentos, filtros=filtros)

# 🔸 Subir nuevo documento
@documentos_view.route('/crear', methods=['GET', 'POST'])
def nuevo_documento():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        id_moral = request.form.get('id_moral')
        archivo = request.files.get('archivo')
        tipo_documento = request.form.get('tipo_documento', '').strip()

        if not id_moral or not archivo:
            flash('Persona Moral y Archivo son obligatorios', 'warning')
            cursor.close()
            return redirect(url_for('documentos_view.nuevo_documento'))

        nombre_archivo = archivo.filename
        contenido = archivo.read()

        cursor.execute("""
            INSERT INTO DOCUMENTO_PERSONA_MORAL 
            (ID_DOCUMENTO, ID_MORAL, NOMBRE_ARCHIVO, TIPO_DOCUMENTO, CONTENIDO, FECHA_SUBIDA)
            VALUES (MORAL.ISEQ$$_72235.nextval, :id_moral, :nombre, :tipo, :contenido, SYSDATE)
        """, {
            'id_moral': id_moral,
            'nombre': nombre_archivo,
            'tipo': tipo_documento,
            'contenido': contenido
        })
        db.commit()
        cursor.close()

        flash('Documento subido correctamente', 'success')
        return redirect(url_for('documentos_view.listar_documentos'))

    cursor.execute("""
        SELECT ID_MORAL, RAZON_SOCIAL 
        FROM PERSONAS_MORALES 
        WHERE ESTADO = 'ACTIVO'
        ORDER BY RAZON_SOCIAL
    """)
    personas_morales = cursor.fetchall()
    cursor.close()

    return render_template('documento_form.html', documento=None, personas_morales=personas_morales)

# 🔸 Editar documento
@documentos_view.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_documento(id):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        id_moral = request.form.get('id_moral')
        tipo_documento = request.form.get('tipo_documento', '').strip()

        if not id_moral:
            flash('Persona Moral es obligatoria', 'warning')
            return redirect(url_for('documentos_view.editar_documento', id=id))

        cursor.execute("""
            UPDATE DOCUMENTO_PERSONA_MORAL
            SET ID_MORAL = :id_moral, TIPO_DOCUMENTO = :tipo
            WHERE ID_DOCUMENTO = :id
        """, {
            'id_moral': id_moral,
            'tipo': tipo_documento,
            'id': id
        })
        db.commit()
        cursor.close()

        flash('Documento actualizado correctamente', 'success')
        return redirect(url_for('documentos_view.listar_documentos'))

    cursor.execute("""
        SELECT ID_DOCUMENTO, ID_MORAL, NOMBRE_ARCHIVO, TIPO_DOCUMENTO, FECHA_SUBIDA 
        FROM DOCUMENTO_PERSONA_MORAL 
        WHERE ID_DOCUMENTO = :id
    """, {'id': id})
    row = cursor.fetchone()

    cursor.execute("""
        SELECT ID_MORAL, RAZON_SOCIAL 
        FROM PERSONAS_MORALES 
        WHERE ESTADO = 'ACTIVO'
        ORDER BY RAZON_SOCIAL
    """)
    personas_morales = cursor.fetchall()
    cursor.close()

    if not row:
        flash('Documento no encontrado', 'danger')
        return redirect(url_for('documentos_view.listar_documentos'))

    documento = {
        'id_documento': row[0],
        'id_moral': row[1],
        'nombre_archivo': row[2],
        'tipo_documento': row[3],
        'fecha_subida': row[4]
    }

    return render_template('documento_form.html', documento=documento, personas_morales=personas_morales)

# 🔸 Eliminar documento
@documentos_view.route('/eliminar/<int:id>')
def eliminar_documento(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM DOCUMENTO_PERSONA_MORAL WHERE ID_DOCUMENTO = :id", {'id': id})
    db.commit()
    cursor.close()
    flash('Documento eliminado', 'success')
    return redirect(url_for('documentos_view.listar_documentos'))

# 🔸 Descargar documento
@documentos_view.route('/descargar/<int:id>')
def descargar_documento(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT NOMBRE_ARCHIVO, CONTENIDO 
        FROM DOCUMENTO_PERSONA_MORAL 
        WHERE ID_DOCUMENTO = :id
    """, {'id': id})
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        flash('Documento no encontrado', 'danger')
        return redirect(url_for('documentos_view.listar_documentos'))

    nombre_archivo, contenido_lob = row

    contenido_bytes = contenido_lob.read()

    return send_file(BytesIO(contenido_bytes), download_name=nombre_archivo, as_attachment=True)
