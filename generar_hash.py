import mysql.connector
from werkzeug.security import generate_password_hash

# Conexión a Azure MySQL
conexion = mysql.connector.connect(
    host="padrongral2023.mysql.database.azure.com",
    user="adminpadrongral",
    password="pericO2610",
    database="padron_electoral"
)
cursor = conexion.cursor()


# Usuarios a insertar
usuarios = [
    ("admin", "Administrador General", "admin@sistema.com", "admin123"),
    ("editor", "Editor de Datos", "editor@sistema.com", "editor123"),
    ("cargador", "Cargador Provincial", "cargador@sistema.com", "cargador123")
]

# Inserción con hash
for nombre_usuario, nombre_completo, email, clave in usuarios:
    hash = generate_password_hash(clave)
    cursor.execute("""
        INSERT INTO usuarios (nombre_usuario, nombre_completo, email, activo, password_hash)
        VALUES (%s, %s, %s, TRUE, %s)
    """, (nombre_usuario, nombre_completo, email, hash))

conexion.commit()
cursor.close()
conexion.close()
print("✅ Usuarios insertados correctamente en padron_electoral.")
