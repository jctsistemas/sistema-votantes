import mysql.connector
from datetime import datetime

# Conexión a Azure MySQL
conexion = mysql.connector.connect(
    host="padrongral2023.mysql.database.azure.com",
    user="adminpadrongral",
    password="pericO2610",
    database="padron_electoral"
)
cursor = conexion.cursor()


# Mapeo de asignaciones: usuario → rol
asignaciones = {
    "admin": "administrador",
    "editor": "operador",
    "cargador": "consulta"
}

for usuario_nombre, rol_nombre in asignaciones.items():
    # Obtener ID del usuario
    cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = %s", [usuario_nombre])
    usuario = cursor.fetchone()
    if not usuario:
        print(f"❌ Usuario '{usuario_nombre}' no encontrado.")
        continue
    usuario_id = usuario[0]

    # Obtener ID del rol
    cursor.execute("SELECT id FROM roles WHERE nombre = %s", [rol_nombre])
    rol = cursor.fetchone()
    if not rol:
        print(f"❌ Rol '{rol_nombre}' no encontrado.")
        continue
    rol_id = rol[0]

    # Verificar si ya existe la asignación
    cursor.execute("""
        SELECT COUNT(*) FROM usuario_roles
        WHERE usuario_id = %s AND rol_id = %s
    """, (usuario_id, rol_id))
    existe = cursor.fetchone()[0]

    if existe:
        print(f"⚠️ El usuario '{usuario_nombre}' ya tiene el rol '{rol_nombre}'.")
    else:
        cursor.execute("""
            INSERT INTO usuario_roles (usuario_id, rol_id, asignado_en)
            VALUES (%s, %s, NOW())
        """, (usuario_id, rol_id))
        print(f"✅ Asignado: {usuario_nombre} → {rol_nombre}")

conexion.commit()
cursor.close()
conexion.close()
print("🎯 Asignaciones completadas.")
