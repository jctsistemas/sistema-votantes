from datetime import datetime
from pytz import timezone

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
                registrar_log(current_user.id, current_user.nombre_usuario, f"Actualizó visita para índice {indice}")
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
# Mapa de visitas
# ────────────────────────────────────────────────────────────────
@app.route('/mapa_visitas')
@login_required
def mapa_visitas():
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT indice, nombre, apellido, latitud, longitud, observacion, nivel
            FROM visitas
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
        """)
        puntos = cursor.fetchall()
    except Exception as e:
        flash(f"Error al cargar datos geográficos: {str(e)}")
        puntos = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return render_template('mapa_visitas.html', puntos=puntos)


# ────────────────────────────────────────────────────────────────
# Historial personal
# ────────────────────────────────────────────────────────────────
@app.route('/mi_historial')
@login_required
def mi_historial():
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT indice, nombre, apellido, observacion, nivel, fecha_visita, latitud, longitud
            FROM visitas
            WHERE usuario_id = %s
            ORDER BY fecha_visita DESC
        """, [current_user.id])
        visitas = cursor.fetchall()
    except Exception as e:
        flash(f"Error al cargar historial personal: {str(e)}")
        visitas = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return render_template('mi_historial.html', visitas=visitas, usuario=current_user)


# ────────────────────────────────────────────────────────────────
# Ejecución
# ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)