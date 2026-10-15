import os
import io
import time
import requests
import pandas as pd
from PIL import Image

# ==========================================
# CONFIGURACIÓN
# ==========================================
SERPER_API_KEY = ""
ARCHIVO_CSV = "catalogo_maestro.csv"
CARPETA_SALIDA = "imagenes_productos2"
SERPER_ENDPOINT = "https://google.serper.dev/images"

HEADERS_DESCARGA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}

# ==========================================
# REGLAS DE GRAMÁTICA Y CONSTRUCCIÓN DE CONSULTA
# ==========================================
def construir_consulta_busqueda(fila):
    nombre = str(fila['Nombre']).strip()
    marca = str(fila['Marca']).strip()
    subcat = str(fila['Subcategoria']).strip()
    desc_visual = str(fila['Descripcion_Visual']).strip()

    partes = [nombre]

    # Añadir marca si no es genérica
    if marca.lower() not in ['genérica', 'generica', 'nan', '']:
        if marca.lower() not in nombre.lower():
            partes.append(marca)

    # Añadir contexto de ferretería y la descripción visual del PDF
    partes.append("ferreteria")
    if desc_visual and desc_visual.lower() not in ['nan', '']:
        # Tomar las primeras palabras de la descripción para orientar el tipo de objeto
        partes.append(desc_visual)

    # Exclusiones estrictas para evitar vectores y dibujos de stock
    consulta = " ".join(partes) + " -vector -dibujo -clipart -ilustracion -stock"
    return " ".join(consulta.split())
# ==========================================
# DESCARGA Y PROCESAMIENTO DE IMÁGENES
# ==========================================
def descargar_y_convertir_png(url_candidata, ruta_guardado):
    """Descarga la imagen web, verifica su validez y la guarda como PNG legítimo."""
    resp = requests.get(url_candidata, headers=HEADERS_DESCARGA, timeout=8)
    if resp.status_code == 200 and len(resp.content) > 1000:
        # Abrir imagen con Pillow para verificar que no esté dañada
        img = Image.open(io.BytesIO(resp.content))
        
        # Convertir a RGBA si tiene transparencia, o RGB estándar
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img_final = img.convert('RGBA')
        else:
            img_final = img.convert('RGB')
            
        img_final.save(ruta_guardado, format="PNG", optimize=True)
        return True
    return False

def procesar_descargas():
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    if not os.path.exists(ARCHIVO_CSV):
        print(f"[ERROR] No se encontró el archivo '{ARCHIVO_CSV}'.")
        return

    df = pd.read_csv(ARCHIVO_CSV)
    
    # Agrupar por ID_Imagen para evitar llamadas duplicadas a la API
    imagenes_unicas = df.drop_duplicates(subset=['ID_Imagen'])
    total_imagenes = len(imagenes_unicas)
    
    print(f"===========================================================")
    print(f"Catálogos cargados: Cerrajería, Droguería, Electricidad, Ferretería General")
    print(f"Productos en CSV: {len(df)} | Imágenes únicas a procesar: {total_imagenes}")
    print(f"Carpeta destino: ./{CARPETA_SALIDA}/")
    print(f"===========================================================\n")

    headers_api = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    descargadas = 0
    omitidas = 0
    errores = 0

    for idx, (_, fila) in enumerate(imagenes_unicas.iterrows(), start=1):
        nombre_archivo = fila['ID_Imagen']
        ruta_guardado = os.path.join(CARPETA_SALIDA, nombre_archivo)

        # 1. Saltarse las que ya estén en disco (permite pausar y reanudar sin coste)
        if os.path.exists(ruta_guardado):
            omitidas += 1
            continue

        query = construir_consulta_busqueda(fila)
        categoria_prod = fila['Categoria']
        sku_prod = fila['SKU']

        print(f"[{idx}/{total_imagenes}] ({categoria_prod} | {sku_prod}) Buscando: '{query}'")

        # 2. Consultar Serper (pedimos 3 alternativas por seguridad)
        payload = {
            "q": query,
            "gl": "es",
            "hl": "es",
            "num": 3
        }

        exito = False
        try:
            resp_api = requests.post(SERPER_ENDPOINT, headers=headers_api, json=payload, timeout=10)
            
            if resp_api.status_code == 200:
                data = resp_api.json()
                lista_imagenes = data.get("images", [])

                if not lista_imagenes:
                    print(f"  [!] Sin resultados en Serper.")
                    errores += 1
                    continue

                # 3. Intentar descargar cada una de las 3 opciones recibidas
                for item in lista_imagenes:
                    url_original = item.get("imageUrl")
                    url_miniatura = item.get("thumbnailUrl")

                    # Intento A: Imagen principal a tamaño completo
                    if url_original:
                        try:
                            if descargar_y_convertir_png(url_original, ruta_guardado):
                                exito = True
                                print(f"  -> OK (Alta resolución guardada)")
                                break
                        except Exception:
                            pass

                    # Intento B: Si la web de origen bloquea, recurrir a la miniatura de Google
                    if url_miniatura and not exito:
                        try:
                            if descargar_y_convertir_png(url_miniatura, ruta_guardado):
                                exito = True
                                print(f"  -> OK (Respaldo Google Thumbnail)")
                                break
                        except Exception:
                            pass

                if exito:
                    descargadas += 1
                else:
                    print(f"  [X] Falló la descarga de las 3 opciones disponibles.")
                    errores += 1

            elif resp_api.status_code == 403:
                print(f"[ERROR CRÍTICO] Clave de Serper inválida o créditos agotados.")
                break
            else:
                print(f"  [X] Error en API Serper: Código {resp_api.status_code}")
                errores += 1

        except Exception as e:
            print(f"  [X] Error de conexión: {e}")
            errores += 1

        # Pausa ligera para no sobrecargar conexiones
        time.sleep(0.12)

    print(f"\n===========================================================")
    print(f"RESUMEN FINAL DE DESCARGAS:")
    print(f" - Nuevas imágenes descargadas: {descargadas}")
    print(f" - Omitidas (ya existían en disco): {omitidas}")
    print(f" - Errores / Sin imagen: {errores}")
    print(f"===========================================================")

if __name__ == "__main__":
    if SERPER_API_KEY == "PEGA_AQUI_TU_API_KEY_DE_SERPER":
        print("[AVISO] Recuerda pegar tu API Key de Serper en la variable SERPER_API_KEY.")
    else:
        procesar_descargas()