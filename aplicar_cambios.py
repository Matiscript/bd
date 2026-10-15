import json
import os
import shutil

ARCHIVO_JSON = "decisiones_imagenes.json"
CARPETA_WEB = "imagenes_productos2"
CARPETA_PDF = "imagenes_productos"
CARPETA_FINAL = "imagenes_catalogo_final"

def construir_carpeta_definitiva():
    if not os.path.exists(ARCHIVO_JSON):
        print(f"[ERROR] No se encontró '{ARCHIVO_JSON}'. Descárgalo primero desde comparador_ab.html.")
        return

    os.makedirs(CARPETA_FINAL, exist_ok=True)

    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        decisiones = json.load(f)

    copiadas_web = 0
    copiadas_pdf = 0
    no_encontradas = 0

    for id_img, eleccion in decisiones.items():
        ruta_web = os.path.join(CARPETA_WEB, id_img)
        ruta_pdf = os.path.join(CARPETA_PDF, id_img)
        ruta_destino = os.path.join(CARPETA_FINAL, id_img)

        if eleccion == "web" and os.path.exists(ruta_web):
            shutil.copy2(ruta_web, ruta_destino)
            copiadas_web += 1
        elif eleccion == "pdf" and os.path.exists(ruta_pdf):
            shutil.copy2(ruta_pdf, ruta_destino)
            copiadas_pdf += 1
        # Respaldo cruzado si la elegida no existe en disco
        elif os.path.exists(ruta_web):
            shutil.copy2(ruta_web, ruta_destino)
            copiadas_web += 1
        elif os.path.exists(ruta_pdf):
            shutil.copy2(ruta_pdf, ruta_destino)
            copiadas_pdf += 1
        else:
            no_encontradas += 1
            print(f"  [!] Falta archivo en ambas carpetas: {id_img}")

    print("\n=============================================")
    print("CARPETA DEFINITIVA GENERADA CON ÉXITO")
    print(f" - Carpeta: ./{CARPETA_FINAL}/")
    print(f" - Desde Web (Alta Res): {copiadas_web}")
    print(f" - Desde PDF (Fieles):   {copiadas_pdf}")
    print(f" - Faltantes totales:    {no_encontradas}")
    print("=============================================")

if __name__ == "__main__":
    construir_carpeta_definitiva()