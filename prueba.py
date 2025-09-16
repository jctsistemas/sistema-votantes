from db import DBConnection

db = DBConnection()
conexion = db.conectar()
print("✅ Conexión exitosa.")
conexion.close()
