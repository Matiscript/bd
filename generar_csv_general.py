import pdfplumber
import re
import pandas as pd
import os

CATALOGOS = [
    {"archivo": "drogueria.pdf", "categoria": "Droguería", "prefijo": "DROG"},
    {"archivo": "electricidad.pdf", "categoria": "Electricidad", "prefijo": "ELEC"},
    {"archivo": "cerrajeria.pdf", "categoria": "Cerrajería", "prefijo": "CERR"},
    {"archivo": "varios_general.pdf", "categoria": "Ferretería General", "prefijo": "VARI"}
]

SUBCATEGORIAS_LISTA = [
    "QUIMICOS", "MASILLAS/SILICONAS", "PEGAMENTOS", "PINTURAS", 
    "LIMPIEZA", "HERRAMIENTAS", "CABLES", "ILUMINACION", "CANDADOS"
]

TEXTOS_A_IGNORAR = [
    "CATÁLOGO DE", "PRODUCTOS", "PRECIOS SIN IVA", "DROGUERIA", 
    "ELECTRICIDAD", "CERRAJERIA", "VARIOS", "FERRETERIA PUERTA CARMONA",
    "DESDE 1936", "90 AÑOS", "PRECIO SEGÚN", "TAMAÑO"
]

def es_texto_basura(texto):
    t = texto.strip().upper()
    if len(t) <= 1:
        return True
    for ign in TEXTOS_A_IGNORAR:
        if ign in t:
            return True
    return False

def procesar_catalogo():
    todos_los_productos = []
    regex_precio = re.compile(r'(\d+[.,]\d{2})\s*€')

    for cat in CATALOGOS:
        ruta = cat["archivo"] if os.path.exists(cat["archivo"]) else cat["archivo"] + ".pdf"
        if not os.path.exists(ruta):
            print(f"[AVISO] No existe '{ruta}'. Saltando...")
            continue

        print(f"-> Procesando con precisión: {ruta}...")
        nombre_base = os.path.splitext(os.path.basename(ruta))[0].lower()
        subcategoria_actual = cat["categoria"]
        contador_img = 1

        with pdfplumber.open(ruta) as pdf:
            # Empezamos en la página 2 (índice 1) saltando la portada
            for num_pag in range(1, len(pdf.pages)):
                pag = pdf.pages[num_pag]
                ancho = pag.width
                alto = pag.height

                # 1. Detectar si la página cambia de subcategoría
                texto_pag = pag.extract_text() or ""
                for sub in SUBCATEGORIAS_LISTA:
                    if sub in texto_pag.upper():
                        subcategoria_actual = sub.title()

                # 2. Dividir en las 3 columnas reales (omitiendo pie de página de IVA)
                ancho_col = ancho / 3.0
                margen_inf = alto - 55

                # Recoger productos de la página organizados por columna
                productos_pagina = [[], [], []]

                for col_idx in range(3):
                    x0 = col_idx * ancho_col
                    x1 = (col_idx + 1) * ancho_col
                    
                    recorte = pag.crop((x0, 20, x1, margen_inf))
                    palabras = recorte.extract_words()
                    if not palabras:
                        continue

                    # Agrupar palabras por líneas según coordenada 'top'
                    lineas_dict = {}
                    for p in palabras:
                        y_aprox = round(p['top'] / 4) * 4
                        lineas_dict.setdefault(y_aprox, []).append(p['text'])

                    lineas_ordenadas = [" ".join(lineas_dict[k]).strip() for k in sorted(lineas_dict.keys())]

                    buffer_nombre = []
                    top_y_producto = None

                    for linea in lineas_ordenadas:
                        if es_texto_basura(linea):
                            continue
                        if any(sub in linea.upper() for sub in SUBCATEGORIAS_LISTA):
                            continue

                        # Si la línea tiene precio: fin de la ficha de ese producto
                        match = regex_precio.search(linea)
                        if match:
                            precio_sin_iva = float(match.group(1).replace(',', '.'))
                            precio_con_iva = round(precio_sin_iva * 1.21, 2)

                            # Texto sobrante si el nombre estaba pegado al precio
                            resto = regex_precio.sub('', linea).strip()
                            if resto and not es_texto_basura(resto):
                                buffer_nombre.append(resto)

                            nombre_final = " ".join(buffer_nombre).strip()
                            if nombre_final:
                                productos_pagina[col_idx].append({
                                    "top_y": top_y_producto if top_y_producto else 0,
                                    "col": col_idx,
                                    "nombre": nombre_final.title(),
                                    "subcategoria": subcategoria_actual,
                                    "precio_sin_iva": precio_sin_iva,
                                    "precio_con_iva": precio_con_iva
                                })
                            buffer_nombre = []
                            top_y_producto = None
                        else:
                            if not top_y_producto:
                                top_y_producto = 1
                            buffer_nombre.append(linea)

                # 3. Ordenar los productos de la página en orden natural de lectura
                # (Fila por fila: de arriba hacia abajo y de izquierda a derecha)
                lista_plana = []
                for c in range(3):
                    for prod in productos_pagina[c]:
                        lista_plana.append(prod)

                # Ordenar por coordenada vertical aproximada y luego por columna
                lista_plana.sort(key=lambda p: (round(p['top_y'] / 150), p['col']))

                for prod in lista_plana:
                    sku = f"{cat['prefijo']}-{contador_img:03d}"
                    img = f"{nombre_base}_prod_{contador_img:03d}.png"

                    todos_los_productos.append({
                        "ID": len(todos_los_productos) + 1,
                        "SKU": sku,
                        "Nombre": prod["nombre"],
                        "Categoria": cat["categoria"],
                        "Subcategoria": prod["subcategoria"],
                        "Precio_Sin_IVA": prod["precio_sin_iva"],
                        "Tipo_IVA": 21.00,
                        "Precio_Con_IVA": prod["precio_con_iva"],
                        "Imagen": img,
                        "Disponible": 1
                    })
                    contador_img += 1

    df_final = pd.DataFrame(todos_los_productos)
    df_final.to_csv("catalogo_completo.csv", index=False, encoding="utf-8-sig")
    print(f"\n[CORREGIDO] {len(df_final)} productos extraídos limpiamente en 'catalogo_completo.csv'.")
    return df_final

if __name__ == "__main__":
    procesar_catalogo()