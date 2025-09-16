import pandas as pd
import mysql.connector
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# Inicializar ventana oculta
root = tk.Tk()
root.withdraw()

# Selección de archivo CSV
archivo_csv = filedialog.askopenfilename(
    title="Seleccioná el archivo CSV a importar",
    filetypes=[("Archivos CSV", "*.csv")]
)

if not archivo_csv:
    print("❌ No se seleccionó ningún archivo.")
    exit()

print(f"📥 Archivo seleccionado: {archivo_csv}")

# Conexión a Azure MySQL
conexion = mysql.connector.connect(
    host="padrongral2023.mysql.database.azure.com",
    user="adminpadrongral",
    password="pericO2610",
    database="padron_electoral"
)
cursor = conexion.cursor()

# Normalizar columnas
def normalizar_columnas(cols):
    return [str(col).strip().lower().replace("_", " ") for col in cols]

# Leer CSV
try:
    df = pd.read_csv(archivo_csv, encoding="utf-8", dtype=str, low_memory=False)
    df.columns = normalizar_columnas(df.columns)
    df = df.fillna("")  # Reemplaza NaN por vacío
except Exception as e:
    print(f"❌ Error al leer el archivo: {e}")
    exit()

if "indice" not in df.columns:
    print("❌ El archivo no contiene la columna 'indice'. No se puede continuar.")
    exit()

if df.empty:
    print("⚠️ El archivo está vacío. No hay registros para importar.")
    exit()

# Función segura para obtener valores
def obtener_valor(fila, campo, tipo="str"):
    valor = fila.get(campo, "")
    if pd.isna(valor) or valor.strip() == "":
        return "" if tipo == "str" else None
    if tipo == "int":
        return int(valor) if str(valor).isdigit() else None
    return valor

# Insertar registros con commit cada 100
registros_insertados = 0
errores = 0
bloque = 0

for i, fila in df.iterrows():
    try:
        cursor.execute("""
            INSERT INTO registros (
                indice, nombre, direccion, dni, departamento,
                observacion, usuario, encargado,
                actualizado_por, actualizado_en,
                codigo, subcircuit, mesa, orden, escuela, seccional, edad
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            obtener_valor(fila, "indice", "int"),
            obtener_valor(fila, "nombre"),
            obtener_valor(fila, "direccion"),
            obtener_valor(fila, "dni"),
            obtener_valor(fila, "departamen"),
            obtener_valor(fila, "observacion"),
            obtener_valor(fila, "usuario"),
            obtener_valor(fila, "encargado"),
            "migracion_csv_bloques",
            datetime.now(),
            obtener_valor(fila, "codigo"),
            obtener_valor(fila, "subcircuit"),
            obtener_valor(fila, "mesa"),
            obtener_valor(fila, "orden"),
            obtener_valor(fila, "escuela"),
            obtener_valor(fila, "seccional"),
            obtener_valor(fila, "edad", "int")
        ))
        registros_insertados += 1
    except Exception as e:
        errores += 1
        print(f"❌ Error en índice {fila.get('indice', 'N/A')} (fila {i}): {e}")

    # Commit cada 100 registros
    if registros_insertados % 100 == 0:
        bloque += 1
        conexion.commit()
        print(f"✅ Bloque {bloque} confirmado (total insertados: {registros_insertados})")

# Commit final
conexion.commit()
cursor.close()
conexion.close()

print(f"\n✅ Migración finalizada.")
print(f"📊 Registros insertados: {registros_insertados}")
print(f"⚠️ Registros con error: {errores}")
