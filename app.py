import zipfile
from io import BytesIO

from datetime import datetime
from pytz import timezone
import os
from werkzeug.utils import secure_filename

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user, UserMixin
)
from werkzeug.security import check_password_hash

from conexion import DBConnection
from auditoria import registrar_log

# ────────────────────────────────────────────────────────────────
# Configuración de la aplicación
# ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "clave_segura"

login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = DBConnection()

# ── Carpeta para guardar fotos ───────────────────────────────────
RUTA_FOTOS = os.path.join('static', 'fotos')
os.makedirs(RUTA_FOTOS, exist_ok=True)

# ────────────────────────────────────────────────────────────────
# Modelo de usuario
# ────────────────────────────────────────────────────────────────
class Usuario(UserMixin):
    def __init__(self, id, nombre_usuario, nombre_completo, email, activo):
        self.id = id
        self.nombre_usuario = nombre_usuario
        self.nombre_completo = nombre_completo
        self.email = email
        self.activo = activo
        self.roles = []

# ────────────────────────────────────────────────────────────────
# Cargador de usuario
# ────────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    try:
        conexion = db.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id, nombre_usuario, nombre_completo, email, activo "
            "FROM usuarios WHERE id = %s",
            [user_id]
        )
        data = cursor.fetchone()
        if data:
            usuario = Usuario(*data)
            usuario.roles = obtener_roles(usuario.id)
            return usuario
    except Exception as e:
        print(f"Error al cargar usuario: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()
    return None

# ────────────────────────────────────────────────────────────────
# Funciones auxiliares
# ────────────────────────────────────────────────────────────────
def obtener_roles(usuario_id):
    try:
        conexion = db.conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT r.nombre
            FROM roles r
            JOIN usuario_roles ur ON ur.rol_id = r.id
            WHERE ur.usuario_id = %s
        """, [usuario_id])
        return [r[0] for r in cursor.fetchall()]
    except Exception as e:
        print(f"Error al obtener roles: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

def obtener_contadores(usuario_id):
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) AS total_hoy
            FROM visitas
            WHERE usuario_id = %s AND DATE(fecha_visita) = CURDATE()
        """, [usuario_id])
        total_hoy = cursor.fetchone()['total_hoy']

        cursor.execute("""
            SELECT COUNT(*) AS total_general
            FROM visitas
            WHERE usuario_id = %s
        """, [usuario_id])
        total_general = cursor.fetchone()['total_general']

        return total_hoy, total_general

    except Exception as e:
        print(f"Error al obtener contadores: {e}")
        return 0, 0
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

def guardar_fotos_en_bd(indice, files):
    conexion = db.conectar()
    cursor = conexion.cursor()
    try:
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                nombre_unico = f"{indice}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                ruta_completa = os.path.join(RUTA_FOTOS, nombre_unico)
                file.save(ruta_completa)

                cursor.execute("""
                    INSERT INTO fotos_visita (indice, archivo, fecha_subida)
                    VALUES (%s, %s, %s)
                """, (indice, ruta_completa, datetime.now()))
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        flash(f"Error al guardar fotos: {str(e)}")
    finally:
        if conexion.is_connected():
            conexion.close()

def obtener_fotos_por_indice_lista(indices):
    conexion = db.conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        if not indices:
            return {}
        format_strings = ','.join(['%s'] * len(indices))
        cursor.execute(f"""
            SELECT indice, archivo
            FROM fotos_visita
            WHERE indice IN ({format_strings})
        """, indices)
        fotos = cursor.fetchall()
        resultado = {}
        for f in fotos:
            resultado.setdefault(f['indice'], []).append(f)
        return resultado
    except Exception as e:
        print(f"Error al obtener fotos por índices: {e}")
        return {}
    finally:
        if conexion.is_connected():
            conexion.close()

# ────────────────────────────────────────────────────────────────
# Rutas de autenticación
# ────────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_input = request.form['usuario']
        clave_input = request.form['clave']
        try:
            conexion = db.conectar()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT id, nombre_usuario, nombre_completo, email, activo, password_hash
                FROM usuarios
                WHERE nombre_usuario = %s OR email = %s
            """, (usuario_input, usuario_input))
            data = cursor.fetchone()
            if data:
                id_, nombre_usuario, nombre_completo, email, activo, password_hash = data
                if activo and check_password_hash(password_hash, clave_input):
                    usuario = Usuario(id_, nombre_usuario, nombre_completo, email, activo)
                    usuario.roles = obtener_roles(id_)
                    login_user(usuario)
                    registrar_log(id_, nombre_usuario, "Inicio de sesión exitoso")
                    return redirect(url_for('panel'))
            flash('Credenciales inválidas o usuario inactivo')
        except Exception as e:
            flash(f"Error de conexión: {str(e)}")
        finally:
            if 'conexion' in locals() and conexion.is_connected():
                conexion.close()
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    registrar_log(current_user.id, current_user.nombre_usuario, "Cierre de sesión")
    logout_user()
    session.clear()
    return redirect(url_for('login'))

# ────────────────────────────────────────────────────────────────
# Rutas principales
# ────────────────────────────────────────────────────────────────
@app.route('/panel')
@login_required
def panel():
    return render_template('panel.html', usuario=current_user)

# ────────────────────────────────────────────────────────────────
# Registro de visitas
# ────────────────────────────────────────────────────────────────
@app.route('/registro_visita', methods=['GET', 'POST'])
@login_required
def registro_visita():
    persona = None
    modo = "buscar"
    mensaje_estado = None
    total_hoy, total_general = obtener_contadores(current_user.id)

    if request.method == 'POST':
        indice = request.form['indice']
        observacion = request.form.get('observacion', '').strip()
        nivel = request.form.get('nivel')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')

        try:
            conexion = db.conectar()
            cursor = conexion.cursor(dictionary=True)

            if not observacion and not nivel:
                cursor.execute("SELECT * FROM visitas WHERE indice = %s", [indice])
                persona = cursor.fetchone()

                if persona:
                    persona["indice"] = indice
                    modo = "editar"
                    mensaje_estado = "Datos listos para completar"
                    if persona["fecha_visita"]:
                        flash("ℹ️ Este índice ya fue visitado el " + str(persona["fecha_visita"]))
                else:
                    cursor.execute("SELECT nombre FROM registros WHERE indice = %s", [indice])
                    datos = cursor.fetchone()
                    if datos:
                        nombre_completo = datos['nombre']
                        if ',' in nombre_completo:
                            apellido = nombre_completo.split(',')[0].strip()
                            nombre = nombre_completo.split(',')[1].strip()
                        else:
                            nombre = nombre_completo
                            apellido = ''
                        persona = {
                            "indice": indice,
                            "nombre": nombre,
                            "apellido": apellido,
                            "observacion": "",
                            "nivel": None
                        }
                        modo = "editar"
                        mensaje_estado = "Datos listos para completar"
                    else:
                        flash("⚠️ No se encontró el índice en registros")
                        modo = "buscar"

            elif observacion and nivel:
                if observacion == "":
                    flash("⚠️ La observación no puede estar vacía.")
                    return redirect(url_for('registro_visita'))

                cursor.execute("SELECT nombre FROM registros WHERE indice = %s", [indice])
                datos = cursor.fetchone()
                if not datos:
                    flash("⚠️ El índice no existe en registros.")
                    return redirect(url_for('registro_visita'))

                nombre_completo = datos['nombre']
                if ',' in nombre_completo:
                    apellido_real = nombre_completo.split(',')[0].strip()
                    nombre_real = nombre_completo.split(',')[1].strip()
                else:
                    nombre_real = nombre_completo.strip()
                    apellido_real = ''

                cursor.execute("SELECT nombre, apellido FROM visitas WHERE indice = %s", [indice])
                visita = cursor.fetchone()

                if visita:
                    if visita['nombre'].strip() != nombre_real or visita['apellido'].strip() != apellido_real:
                        flash("❌ El nombre y apellido no coinciden con el índice. Reingresá el número correctamente.")
                        return redirect(url_for('registro_visita'))
                else:
                    cursor.execute("""
                        INSERT INTO visitas (indice, nombre, apellido)
                        VALUES (%s, %s, %s)
                    """, (indice, nombre_real, apellido_real))

                argentina = timezone('America/Argentina/Cordoba')
                fecha_local = datetime.now(argentina).strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute("""
                    UPDATE visitas
                    SET observacion = %s,
                        nivel = %s,
                        fecha_visita = %s,
                        usuario_id = %s,
                        latitud = %s,
                        longitud = %s
                    WHERE indice = %s
                """, (observacion, nivel, fecha_local, current_user.id, latitud, longitud, indice))
                conexion.commit()

                # ✅ Guardar fotos en tabla dedicada
                fotos = request.files.getlist('fotos')
                guardar_fotos_en_bd(indice, fotos)

                total_hoy, total_general = obtener_contadores(current_user.id)
                flash(f"✅ Datos actualizados correctamente. Hoy llevás {total_hoy} visitas.")
                return redirect(url_for('registro_visita'))

        except Exception as e:
            flash(f"Error: {str(e)}")
        finally:
            if 'conexion' in locals() and conexion.is_connected():
                conexion.close()

    return render_template('registro_visita.html',
                           persona=persona,
                           modo=modo,
                           mensaje_estado=mensaje_estado,
                           contador_hoy=total_hoy,
                           contador_total=total_general)

# ────────────────────────────────────────────────────────────────
# Historial por índice
# ────────────────────────────────────────────────────────────────
@app.route('/historial/<int:indice>')
@login_required
def historial(indice):
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM visitas WHERE indice = %s", [indice])
        visita = cursor.fetchone()

        cursor.execute("SELECT id, archivo FROM fotos_visita WHERE indice = %s ORDER BY fecha_subida", [indice])
        fotos = cursor.fetchall()

    except Exception as e:
        flash(f"Error al cargar historial: {str(e)}")
        visita = None
        fotos = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return render_template('historial.html', visita=visita, fotos=fotos, indice=indice)

# ────────────────────────────────────────────────────────────────
# Agregar más fotos
# ────────────────────────────────────────────────────────────────
@app.route('/agregar_fotos/<int:indice>', methods=['POST'])
@login_required
def agregar_fotos(indice):
    try:
        fotos = request.files.getlist('fotos_nuevas')
        guardar_fotos_en_bd(indice, fotos)
        registrar_log(current_user.id, current_user.nombre_usuario, f"Agregó {len(fotos)} fotos al índice {indice}")
        flash("✅ Fotos agregadas correctamente.")
    except Exception as e:
        flash(f"Error al agregar fotos: {str(e)}")
    return redirect(url_for('historial', indice=indice))

# ────────────────────────────────────────────────────────────────
# Eliminar foto
# ────────────────────────────────────────────────────────────────
@app.route('/eliminar_foto/<int:foto_id>', methods=['POST'])
@login_required
def eliminar_foto(foto_id):
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT archivo, indice FROM fotos_visita WHERE id = %s", [foto_id])
        foto = cursor.fetchone()

        if not foto:
            flash("❌ Foto no encontrada.")
            return redirect(request.referrer or url_for('panel'))

        ruta_archivo = foto['archivo']
        indice = foto['indice']

        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)

        cursor.execute("DELETE FROM fotos_visita WHERE id = %s", [foto_id])
        conexion.commit()

        registrar_log(current_user.id, current_user.nombre_usuario, f"Eliminó foto ID {foto_id} de índice {indice}")
        flash("✅ Foto eliminada correctamente.")

    except Exception as e:
        flash(f"Error al eliminar foto: {str(e)}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return redirect(request.referrer or url_for('panel'))

# ────────────────────────────────────────────────────────────────
# Mi historial con fotos
# ────────────────────────────────────────────────────────────────
@app.route('/mi_historial')
@login_required
def mi_historial():
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT indice, nombre, apellido, observacion, nivel, fecha_visita
            FROM visitas
            WHERE usuario_id = %s
            ORDER BY fecha_visita DESC
        """, [current_user.id])
        visitas = cursor.fetchall()

        indices = [v['indice'] for v in visitas]
        fotos_por_visita = obtener_fotos_por_indice_lista(indices)

    except Exception as e:
        flash(f"Error al cargar historial: {str(e)}")
        visitas = []
        fotos_por_visita = {}
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return render_template('mi_historial.html', visitas=visitas, fotos_por_visita=fotos_por_visita, usuario=current_user)

# ────────────────────────────────────────────────────────────────
# Admin - Ver todas las fotos
# ────────────────────────────────────────────────────────────────
@app.route('/admin/fotos')
@login_required
def admin_fotos():
    if 'admin' not in current_user.roles:
        flash("❌ No tenés permisos para acceder a esta sección.")
        return redirect(url_for('panel'))

    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT fv.id, fv.indice, fv.archivo, fv.fecha_subida,
                   v.nombre, v.apellido, u.nombre_usuario
            FROM fotos_visita fv
            JOIN visitas v ON fv.indice = v.indice
            JOIN usuarios u ON v.usuario_id = u.id
            ORDER BY fv.fecha_subida DESC
        """)
        fotos = cursor.fetchall()
    except Exception as e:
        flash(f"Error al cargar fotos: {str(e)}")
        fotos = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return render_template('admin_fotos.html', fotos=fotos)

# ────────────────────────────────────────────────────────────────
# Ejecución
# ────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────
# Descargar fotos como ZIP
# ────────────────────────────────────────────────────────────────
@app.route('/descargar_fotos/<int:indice>')
@login_required
def descargar_fotos(indice):
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT archivo FROM fotos_visita WHERE indice = %s", [indice])
        fotos = cursor.fetchall()

        if not fotos:
            flash("❌ No hay fotos para descargar.")
            return redirect(url_for('mi_historial'))

        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for foto in fotos:
                archivo = foto['archivo']
                if os.path.exists(archivo):
                    zf.write(archivo, os.path.basename(archivo))

        memory_file.seek(0)
        registrar_log(current_user.id, current_user.nombre_usuario, f"Descargó ZIP de fotos del índice {indice}")
        return send_file(memory_file, as_attachment=True, download_name=f"fotos_indice_{indice}.zip", mimetype='application/zip')

    except Exception as e:
        flash(f"Error al generar ZIP: {str(e)}")
        return redirect(url_for('mi_historial'))
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

if __name__ == '__main__':
    app.run(debug=True)