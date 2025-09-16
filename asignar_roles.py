from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from conexion import DBConnection


app = Flask(__name__)
db = DBConnection()

@app.route('/asignar_roles', methods=['GET', 'POST'])
@login_required
def asignar_roles():
    if 'administrador' not in current_user.roles:
        flash("Acceso denegado")
        return redirect(url_for('dashboard'))

    try:
        conexion = db.conectar()
        cursor = conexion.cursor()

        # Procesar asignación de roles
        if request.method == 'POST':
            usuario_id = request.form['usuario_id']
            rol_ids = request.form.getlist('rol_id')

            for rol_id in rol_ids:
                cursor.execute("""
                    SELECT COUNT(*) FROM usuario_roles
                    WHERE usuario_id = %s AND rol_id = %s
                """, (usuario_id, rol_id))
                existe = cursor.fetchone()[0]

                if not existe:
                    cursor.execute("""
                        INSERT INTO usuario_roles (usuario_id, rol_id, asignado_en)
                        VALUES (%s, %s, NOW())
                    """, (usuario_id, rol_id))

            conexion.commit()
            flash("✅ Roles asignados correctamente.")

        # Cargar datos para renderizar el formulario
        cursor.execute("SELECT id, nombre_usuario FROM usuarios WHERE activo = TRUE")
        usuarios = cursor.fetchall()

        cursor.execute("SELECT id, nombre, descripcion FROM roles")
        roles = cursor.fetchall()

        cursor.execute("""
            SELECT ur.id, u.nombre_usuario, r.nombre, ur.asignado_en
            FROM usuario_roles ur
            JOIN usuarios u ON ur.usuario_id = u.id
            JOIN roles r ON ur.rol_id = r.id
            ORDER BY ur.asignado_en DESC
        """)
        asignaciones = cursor.fetchall()

        return render_template('asignar_roles.html', usuarios=usuarios, roles=roles, asignaciones=asignaciones)

    except Exception as e:
        flash(f"Error al cargar datos: {str(e)}")
        return render_template('asignar_roles.html', usuarios=[], roles=[], asignaciones=[])
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

@app.route('/eliminar_rol/<int:asignacion_id>', methods=['POST'])
@login_required
def eliminar_rol(asignacion_id):
    if 'administrador' not in current_user.roles:
        flash("Acceso denegado")
        return redirect(url_for('dashboard'))

    try:
        conexion = db.conectar()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM usuario_roles WHERE id = %s", [asignacion_id])
        conexion.commit()
        flash("Rol eliminado correctamente")
    except Exception as e:
        flash(f"Error al eliminar rol: {str(e)}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

    return redirect(url_for('asignar_roles'))
