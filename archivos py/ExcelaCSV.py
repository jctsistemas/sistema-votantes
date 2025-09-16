import os
import pandas as pd

# Ruta de entrada y salida
carpeta_excel = "D:/pj2/SistemaVotantes/"
carpeta_csv = "D:/pj2/SistemaVotantes/csv_generados/"

# Crear carpeta de salida si no existe
os.makedirs(carpeta_csv, exist_ok=True)

# Recorrer todos los archivos Excel
for archivo in os.listdir(carpeta_excel):
    if archivo.endswith(".xlsx"):
        ruta_excel = os.path.join(carpeta_excel, archivo)
        nombre_base = os.path.splitext(archivo)[0]
        ruta_csv = os.path.join(carpeta_csv, f"{nombre_base}.csv")

        try:
            df = pd.read_excel(ruta_excel, engine="openpyxl")
            df.to_csv(ruta_csv, index=False, encoding="utf-8")
            print(f"✅ Convertido: {archivo} → {nombre_base}.csv")
        except Exception as e:
            print(f"❌ Error en {archivo}: {e}")
