import pandas as pd
import mysql.connector
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import time
import os

# Inicializar ventana oculta
root = tk.Tk()
root.withdraw()

# Selección múltiple de archivos CSV
archivos_csv = filedialog.askopenfilenames(
    title="Seleccioná uno o más archivos CSV para importar",
    filetypes=[("Archivos CSV", "*.csv")]
)

if not archivos_csv:
    print("❌ No se seleccionó ningún archivo.")
    exit()

# Conexión a Azure MySQL
conexion = mysql.connector.connect(
    host="padrongral2023.mysql.database.azure.com",
    user="adminpadrongral@padrongral2023",
    password="Perico2610",
    database="padron_electoral"
)
conexion.autocommit = False
cursor = conexion.cursor()

# Función segura para obtener valores
def obtener_valor(fila, campo, tipo="str"):
    valor = fila.get(campo, "")
    if pd.isna(valor) or valor.strip() == "":
        return "" if tipo == "str" else None
    if tipo == "int":
        return int(valor) if str(valor).isdigit() else None
    return valor

# Procesar cada archivo
for archivo_csv in archivos_csv:
    print(f"\n📥 Procesando archivo: {os.path.basename(archivo_csv)}")
    try:
        df = pd.read_csv(archivo_csv, encoding="utf-8", dtype=str, low_memory=False)
        df.columns = [str(col).strip().lower().replace("_", " ") for col in df.columns]
        df = df.fillna("")
    except Exception as e:
        print(f"❌ Error al leer el archivo {archivo_csv}: {e}")
        continue

    if "indice" not in df.columns or df.empty:
        print(f"⚠️ Archivo {archivo_csv} inválido o vacío. Se omite.")
        continue

    registros_insertados = 0
    errores = 0
    bloque = 0
    inicio_total = time.time()

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
                f"migracion_{os.path.basename(archivo_csv)}",
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
            if errores <= 10:
                print(f"❌ Error en índice {fila.get('indice', 'N/A')} (fila {i}): {e}")

        # Commit + pausa cada 200 registros
        if registros_insertados % 200 == 0:
            bloque += 1
            inicio_bloque = time.time()
            conexion.commit()
            duracion = round(time.time() - inicio_bloque, 2)

            # Pausa adaptativa
            if duracion < 1:
                pausa = 0.2
            elif duracion < 3:
                pausa = 0.5
            else:
                pausa = 1.0

            print(f"✅ Bloque {bloque} confirmado (insertados: {registros_insertados}) en {duracion} segundos. Pausa: {pausa}s")
            time.sleep(pausa)

    conexion.commit()
    duracion_total = round(time.time() - inicio_total, 2)
    print(f"✅ Archivo {os.path.basename(archivo_csv)} finalizado en {duracion_total} segundos.")
    print(f"📊 Registros insertados: {registros_insertados}")
    print(f"⚠️ Registros con error: {errores}")

# Cierre final
cursor.close()
conexion.close()
print("\n🏁 Todos los archivos procesados correctamente.")
