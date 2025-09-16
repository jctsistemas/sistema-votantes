import mysql.connector
from werkzeug.security import generate_password_hash

# Nueva clave que querés asignar
nueva_clave = "admin123"
hash = generate_password_hash(nueva_clave)

# Conexión a Azure MySQL
conexion = mysql.connector.connect(
    host="padrongral2023.mysql.database.azure.com",
    user="adminpadrongral",
    password="pericO2610",
    database="padron_electoral"
)
cursor = conexion.cursor()


# Actualizar el hash en la base
cursor.execute("""
    UPDATE usuarios
    SET password_hash = %s
    WHERE nombre_usuario = 'admin'
""", [hash])

conexion.commit()
cursor.close()
conexion.close()
print("✅ Clave actualizada correctamente para el usuario 'admin'.")
