import mysql.connector
import bcrypt

# Configuración de conexión a Azure MySQL
conexion = mysql.connector.connect(
    host="padrongral2023.mysql.database.azure.com",
    user="adminpadrongral@padrongral2023",
    password="pericO2610",  # reemplazá por tu contraseña real
    database="padron_electoral"
)
cursor = conexion.cursor()

# Datos del nuevo usuario
nombre_usuario = "julio"
nombre_completo = "Julio Córdoba"
email = "julio@example.com"
clave = "claveSegura123"

# Generar hash seguro con bcrypt
hash = bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt())

# Insertar usuario en la tabla
try:
    cursor.execute("""
        INSERT INTO usuarios (nombre_usuario, nombre_completo, email, password_hash)
        VALUES (%s, %s, %s, %s)
    """, (nombre_usuario, nombre_completo, email, hash.decode("utf-8")))
    conexion.commit()
    print("✅ Usuario registrado correctamente.")
except Exception as e:
    print(f"❌ Error al registrar usuario: {e}")

cursor.close()
conexion.close()
