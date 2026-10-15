import fitz  # PyMuPDF
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import math

ARCHIVO_CSV = "catalogo_maestro.csv"
CARPETA_SALIDA = "imagenes_productos"

MAPA_PDFS = {
    "drogueria": ["drogueria.pdf", "DROGUERIA_20260212_201920_0000.pdf", "DROGUERIA.pdf"],
    "electricidad": ["electricidad.pdf", "ELECTRICIDAD.pdf"],
    "cerrajeria": ["cerrajeria.pdf", "CERRAJERIA.pdf"],
    "varios_general": ["varios_general.pdf", "VARIOS_GENERAL.pdf", "varios.pdf"]
}

def encontrar_archivo_pdf(prefijo):
    for p in MAPA_PDFS.get(prefijo, [f"{prefijo}.pdf"]):
        if os.path.exists(p):
            return p
    return None

def mejorar_imagen(image_bytes, tamano_final=(500, 500)):
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    lienzo = Image.new("RGB", tamano_final, (255, 255, 255))
    ancho_orig, alto_orig = img.size
    ratio = min((tamano_final[0] - 40) / ancho_orig, (tamano_final[1] - 40) / alto_orig)
    nuevo_ancho = max(1, int(ancho_orig * ratio))
    nuevo_alto = max(1, int(alto_orig * ratio))
    
    img_redim = img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
    offset_x = (tamano_final[0] - nuevo_ancho) // 2
    offset_y = (tamano_final[1] - nuevo_alto) // 2
    
    mascara = img_redim.split()[3] if len(img_redim.split()) == 4 else None
    lienzo.paste(img_redim.convert("RGB"), (offset_x, offset_y), mask=mascara)
    
    lienzo = lienzo.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
    return ImageEnhance.Contrast(lienzo).enhance(1.08)

def deduplicar_celdas(lista_imagenes):
    """Evita que dos capas de imagen en el mismo producto desplacen la numeración."""
    unicas = []
    for im in lista_imagenes:
        duplicada = False
        for existente in unicas:
            distancia = math.hypot(im['center_x'] - existente['center_x'], im['center_y'] - existente['center_y'])
            if distancia < 45:  # Están en la misma celda del producto
                duplicada = True
                break
        if not duplicada:
            unicas.append(im)
    return unicas

def procesar_extraccion_visual():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    df = pd.read_csv(ARCHIVO_CSV)
    prefijos_unicos = df['ID_Imagen'].apply(lambda x: x.split('_p')[0]).unique()

    total_extraidas = 0

    for prefijo in prefijos_unicos:
        ruta_pdf = encontrar_archivo_pdf(prefijo)
        if not ruta_pdf:
            print(f"[AVISO] No se encontró el PDF para '{prefijo}'.")
            continue

        print(f"\nProcesando PDF: {ruta_pdf} ({prefijo})")
        doc = fitz.open(ruta_pdf)

        df_cat = df[df['ID_Imagen'].str.startswith(f"{prefijo}_p")]
        paginas_en_csv = df_cat['ID_Imagen'].apply(lambda x: int(x.split('_p')[1].split('_')[0])).unique()

        for num_pag_humana in sorted(paginas_en_csv):
            idx_pagina_fitz = int(num_pag_humana) - 1
            if idx_pagina_fitz >= len(doc):
                continue

            pagina = doc[idx_pagina_fitz]
            alto_pag = pagina.rect.height

            imagenes_brutas = []
            for img_info in pagina.get_images(full=True):
                xref = img_info[0]
                for r in pagina.get_image_rects(xref):
                    # Filtro corregido: r.y0 > 15 capta la primera fila de todas las páginas
                    # r.width < 300 descarta el banner ancho de cabecera de la página 2
                    if 35 < r.width < 300 and 35 < r.height < 350 and r.y0 > 15 and r.y1 < (alto_pag - 35):
                        imagenes_brutas.append({
                            'xref': xref,
                            'center_x': (r.x0 + r.x1) / 2,
                            'center_y': (r.y0 + r.y1) / 2
                        })

            # 1. Eliminar capas duplicadas en la misma celda
            imagenes_limpias = deduplicar_celdas(imagenes_brutas)

            # 2. Ordenar de arriba a abajo (filas) y de izquierda a derecha (columnas)
            imagenes_limpias.sort(key=lambda im: (round(im['center_y'] / 130), im['center_x']))

            # 3. Guardar con el ID exacto
            esperadas_csv = df_cat[df_cat['ID_Imagen'].str.startswith(f"{prefijo}_p{int(num_pag_humana):02d}_")]['ID_Imagen'].nunique()
            print(f"  -> Pág {int(num_pag_humana):02d}: CSV espera {esperadas_csv:2d} | Extraídas: {len(imagenes_limpias):2d}")

            for pos_idx, im_data in enumerate(imagenes_limpias, start=1):
                nombre_archivo = f"{prefijo}_p{int(num_pag_humana):02d}_{pos_idx:02d}.png"
                ruta_salida = os.path.join(CARPETA_SALIDA, nombre_archivo)

                try:
                    img_base = doc.extract_image(im_data['xref'])
                    img_procesada = mejorar_imagen(img_base["image"])
                    img_procesada.save(ruta_salida, "PNG", quality=95)
                    total_extraidas += 1
                except Exception as e:
                    print(f"     Error en {nombre_archivo}: {e}")

    print(f"\n[ÉXITO] {total_extraidas} imágenes extraídas y alineadas en '{CARPETA_SALIDA}'.")

if __name__ == "__main__":
    procesar_extraccion_visual()