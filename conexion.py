import mysql.connector
from mysql.connector import Error
import time

class DBConnection:
    def __init__(self):
        self.config = {
            'host': 'padrongral2023.mysql.database.azure.com',
            'user': 'adminpadrongral',
            'password': 'pericO2610',
            'database': 'padron_electoral',
            'ssl_disabled': False  # Azure requiere transporte seguro
        }
        self.max_reintentos = 3
        self.delay = 2  # segundos entre reintentos

    def conectar(self):
        intento = 0
        while intento < self.max_reintentos:
            try:
                conexion = mysql.connector.connect(**self.config)
                if conexion.is_connected():
                    print(f"✅ Conexión establecida en intento {intento + 1}")
                    return conexion
            except Error as e:
                print(f"⚠️ Error de conexión (intento {intento + 1}): {e}")
                intento += 1
                time.sleep(self.delay)
        raise Exception("❌ No se pudo conectar a la base de datos después de varios intentos.")
