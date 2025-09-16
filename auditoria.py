from conexion import DBConnection
from flask import request
import datetime

db = DBConnection()

def registrar_log(usuario_id, usuario_nombre, accion):
    """
    Registra una acción en la tabla logs_errores.
    """
    ip = request.remote_addr or "IP desconocida"
    try:
        conexion = db.conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO logs_errores (usuario_id, usuario, accion, ip, fecha)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario_id, usuario_nombre, accion, ip, datetime.datetime.now()))
        conexion.commit()
    except Exception as e:
        print(f"Error al registrar log: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

def obtener_logs(filtro_usuario=None, limite=100):
    """
    Devuelve los últimos logs, opcionalmente filtrados por usuario.
    """
    try:
        conexion = db.conectar()
        cursor = conexion.cursor(dictionary=True)

        if filtro_usuario:
            cursor.execute("""
                SELECT usuario, accion, fecha, ip
                FROM logs_errores
                WHERE usuario_id = %s
                ORDER BY fecha DESC
                LIMIT %s
            """, (filtro_usuario, limite))
        else:
            cursor.execute("""
                SELECT usuario, accion, fecha, ip
                FROM logs_errores
                ORDER BY fecha DESC
                LIMIT %s
            """, (limite,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener logs: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()
