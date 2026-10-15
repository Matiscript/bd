import fitz  # PyMuPDF
import os

def extraer_imagenes_pdf(ruta_pdf, carpeta_salida="imagenes_productos"):
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)
        
    doc = fitz.open(ruta_pdf)
    nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0].lower()
    contador = 1
    
    print(f"Procesando imágenes de: {ruta_pdf}")
    
    # Se omiten la portada (página 0) y elementos decorativos
    for num_pagina in range(1, len(doc)):
        pagina = doc[num_pagina]
        lista_imagenes = pagina.get_images(full=True)
        
        for img_info in lista_imagenes:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            imagen_bytes = base_image["image"]
            extension = base_image["ext"]
            ancho = base_image["width"]
            alto = base_image["height"]
            
            # Filtro: descartar iconos diminutos o banners de cabecera/pie
            if ancho > 100 and alto > 100 and not (ancho > 1000 and alto < 200):
                nombre_archivo = f"{nombre_base}_prod_{contador:03d}.{extension}"
                ruta_guardado = os.path.join(carpeta_salida, nombre_archivo)
                
                with open(ruta_guardado, "wb") as f:
                    f.write(imagen_bytes)
                    
                contador += 1

    print(f"-> Extraídas {contador - 1} imágenes en '{carpeta_salida}'.")

if __name__ == "__main__":
    # Podéis pasarle los 7 PDFs en un bucle
    archivos = ["drogueria.pdf","electricidad.pdf","cerrajeria.pdf","varios_general"]
    for pdf in archivos:
        if os.path.exists(pdf):
            extraer_imagenes_pdf(pdf)