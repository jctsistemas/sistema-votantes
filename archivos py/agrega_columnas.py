# agrega_columnas.py
import pandas as pd
import os
import shutil
from pathlib import Path

# ---------- CONFIGURACIÓN ----------
CARPETA   = r"D:\pj2\SistemaVotantes"          # tu ruta real
COLUMNAS  = ["CODIGO", "OBSERVACION", "FECHA VISITA", "USUARIO", "ENCARGADO"]
EXT       = (".xlsx", ".xlsm")
# -----------------------------------

def main():
    carpeta = Path(CARPETA)
    backup  = carpeta / "backup"
    backup.mkdir(exist_ok=True)

    archivos = [f for f in carpeta.iterdir() if f.suffix.lower() in EXT]
    if not archivos:
        print("No se encontraron archivos Excel en la carpeta.")
        return

    for archivo in archivos:
        # copia de seguridad
        shutil.copy(archivo, backup / archivo.name)

        # lee Excel
        df = pd.read_excel(archivo, sheet_name=0)

        # inserta columnas al inicio
        for col in reversed(COLUMNAS):
            df.insert(0, col, "")

        # guarda (sobrescribe original)
        df.to_excel(archivo, index=False, sheet_name="Hoja1")
        print(f"✓ Procesado: {archivo.name}")

    print(f"\n¡Listo! Se procesaron {len(archivos)} archivos.")
    print(f"Copias de seguridad en: {backup}")

if __name__ == "__main__":
    main()