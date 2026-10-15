import pandas as pd
import os

def markdown_a_csv_maestro(archivo_txt="tablas_markdown.txt", salida_csv="catalogo_maestro.csv"):
    if not os.path.exists(archivo_txt):
        print(f"[ERROR] No se encuentra el archivo '{archivo_txt}'.")
        return

    with open(archivo_txt, "r", encoding="utf-8") as f:
        lineas = [l.strip() for l in f.readlines() if l.strip()]

    cabeceras = None
    filas_datos = []

    for linea in lineas:
        # Solo procesar líneas que formen parte de tablas markdown
        if not linea.startswith('|'):
            continue

        # Dividir por tuberías '|' y limpiar espacios
        partes = [p.strip() for p in linea.split('|')]
        
        # Eliminar elementos vacíos en los extremos por los '|' de inicio y fin
        if partes and partes[0] == '':
            partes = partes[1:]
        if partes and partes[-1] == '':
            partes = partes[:-1]

        # Ignorar las líneas divisorias de formato (|:---|:---|)
        if any('---' in p for p in partes):
            continue

        # Detectar cabecera (la primera vez que aparece 'SKU')
        if any('SKU' in p.upper() for p in partes):
            if cabeceras is None:
                cabeceras = partes
            continue

        # Fila de producto
        if cabeceras:
            # Ajustar por si alguna fila tiene celdas de más o de menos
            if len(partes) < len(cabeceras):
                partes += [''] * (len(cabeceras) - len(partes))
            elif len(partes) > len(cabeceras):
                partes = partes[:len(cabeceras)]
            filas_datos.append(partes)

    df = pd.DataFrame(filas_datos, columns=cabeceras)
    
    # Guardar en CSV compatible con Excel, phpMyAdmin y WooCommerce
    df.to_csv(salida_csv, index=False, encoding="utf-8-sig")
    print(f"\n[ÉXITO] Se han consolidado {len(df)} productos en '{salida_csv}'.")

if __name__ == "__main__":
    markdown_a_csv_maestro()