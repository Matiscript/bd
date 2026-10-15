# 🛠️ Digitalización y Modernización del Catálogo: Ferretería Puerta Carmona

Repositorio de ingeniería de software y gestión de datos desarrollado para la asignatura **Gestión de Sistemas de Información (GSI)** de la **Escuela Técnica Superior de Ingeniería Informática (Universidad de Sevilla)**.

El propósito de este proyecto es modernizar la infraestructura digital y el catálogo comercial de un negocio tradicional histórico (**Ferretería Puerta Carmona**, fundada en 1936), trasladando sus catálogos impresos a un sistema de gestión de contenidos (CMS) basado en **WordPress** y **WooCommerce** bajo el marco metodológico **Scrum**.

---

## 📌 Contexto y Objetivos del Proyecto

La ferretería disponía de su inventario comercial en múltiples catálogos distribuidos en documentos PDF no estructurados (diseñados para imprenta en cuadrículas de 3 columnas con precios sin IVA)[cite: 6]. 

Este repositorio documenta el flujo completo de ingeniería: **Extracción, Transformación, Carga (ETL), curación de activos multimedia y sincronización con el CMS** para dar cumplimiento a los requisitos modelados en la metodología REM / REMUS:
* **OBJ-01:** Digitalización integral del catálogo histórico para consulta de particulares y profesionales[cite: 7].
* **RI-01 (Ficha técnica de producto):** Almacenamiento normalizado de SKU, marca, taxonomía (categoría y subcategoría), precio con/sin IVA, imagen de alta resolución y disponibilidad.
* **RN-01 (Regla de negocio de precios):** Cálculo y desglose explícito del 21% de IVA aplicable sobre el precio mayorista/catálogo[cite: 6, 7].

---

## 🏗️ Pipeline de Ingeniería y Procesamiento de Datos (ETL)

El procesamiento del inventario desde los documentos originales hasta la base de datos se estructuró en cuatro etapas:
[4 PDFs Originales] (Droguería, Electricidad, Cerrajería, Ferretería General)
│
├──► 1. Ingesta y Normalización Semántica (Gemini Pro / Multimodal)
│       └── Generación de 'catalogo_maestro.csv' (310 productos, 9 columnas)
│
├──► 2. Pipeline Dual de Activos Gráficos (Imágenes)
│       ├── Ruta A: Extracción espacial del PDF (PyMuPDF / Pillow)
│       └── Ruta B: Web scraping comercial en alta definición (Serper Google Images API)
│
├──► 3. Validación y Curación Asistida (Human-in-the-Loop)
│       ├── Dashboard web interactivo: 'comparador_ab.html'
│       └── Ensamblaje automatizado: 'aplicar_decisiones.py'
│
└──► 4. Carga Masiva y Despliegue en WordPress (WooCommerce / phpMyAdmin)

### 1. Extracción y Normalización de Datos (`catalogo_maestro.csv`)
A partir de los 4 catálogos base (`drogueria.pdf`, `electricidad.pdf`, `cerrajeria.pdf` y `varios_general.pdf`), se extrajeron y normalizaron **310 productos únicos** clasificados en:
* **Droguería:** 99 referencias (`DROG-001` a `DROG-099`).
* **Electricidad:** 83 referencias (`ELEC-001` a `ELEC-083`).
* **Cerrajería:** 64 referencias (`CERR-001` a `CERR-064`).
* **Ferretería General:** 64 referencias (`VARI-001` a `VARI-064`).

Cada registro cuenta con:
* `SKU`: Código único identificador con prefijo departamental.
* `Nombre` y `Marca`: Detección de fabricante y limpieza de artefactos de maquetación ("Catálogo de", "Precios sin IVA").
* `Categoria` y `Subcategoria`: Taxonomía jerárquica coherente para filtros faceted en frontend[cite: 6, 7].
* `Precio_Sin_IVA` y `Precio_Con_IVA`: Cálculo de impuestos verificado mediante redondeo comercial estándar (`Decimal ROUND_HALF_UP`).
* `ID_Imagen`: Identificador posicional `{categoria}_p{pagina:02d}_{posicion:02d}.png`.
* `Descripcion_Visual`: Resumen semántico del artículo para trazabilidad física.

---

## 🖼️ Resolución del Problema de Activos Visuales (Imágenes)

Uno de los principales retos técnicos radicó en la gestión de imágenes:
1. **El orden interno del PDF no es secuencial:** Los archivos PDF almacenan las imágenes como objetos según su orden de inserción interna (`X17`, `X19`, etc.), no según la lectura humana, provocando desfases en las extracciones lineales básicas.
2. **Limitaciones de calidad:** Los recortes del PDF contaban con baja resolución para e-commerce (72 ppp) y algunos artículos con variantes (medidas de brochas, amperajes) compartían una única foto grupal.

### Solución Implementada: Pipeline Híbrido

* **Extracción Espacial Corregida (`extraer_fotos_perfectas.py`):**
  * Utiliza `PyMuPDF` (`fitz`) para calcular las cajas delimitadoras (*bounding boxes*) de cada objeto en la página.
  * Corrige los márgenes de cabecera (`y0 > 15`) para no ignorar la primera fila de productos.
  * Aplica un algoritmo de deduplicación de celdas por distancia euclídea para evitar saltos provocados por capas superpuestas.
  * Normaliza las fotos mediante `Pillow` sobre un lienzo blanco neutro de **$500 \times 500\text{ px}$** con máscara de nitidez (*UnsharpMask*).

* **Enriquecimiento Web Comercial (`descargar_imagenes_serper.py`):**
  * Script automatizado que utiliza la API de **Serper (Google Images)** para consultar fotografías oficiales de catálogo en alta definición.
  * Aplica gramática con exclusión de ruido (`-vector -dibujo -clipart -stock`) y fallback multinivel (imagen original $\rightarrow$ miniatura en caché de Google).

* **Herramienta de Decisión A/B (`comparador_ab.html` + `aplicar_decisiones.py`):**
  * Interfaz web interactiva *Human-in-the-Loop* que permite visualizar en paralelo la opción A (Web HD) frente a la opción B (Fiel del PDF original).
  * Exporta la selección en formato `JSON` y genera automáticamente la carpeta consolidada `imagenes_catalogo_final/`.

---

## 📁 Estructura del Repositorio

```text
├── catalogo_maestro.csv              # Dataset maestro consolidado (310 productos)
├── extraer_fotos_perfectas.py        # Extractor espacial de imágenes desde PDF con PyMuPDF
├── descargar_imagenes_serper.py      # Scraper/API para descarga de imágenes comerciales HD
├── generar_comparador.py             # Generador del panel interactivo HTML de comparación A/B
├── aplicar_decisiones.py             # Script de consolidación final según decisiones JSON
├── generar_visor.py                  # Visor de catálogo local con filtros y búsqueda dinámica
├── comparador_ab.html                # Panel web interactivo para validación de imágenes
├── verificador.html                  # Galería de inspección de estado del catálogo
└── README.md                         # Documentación técnica del proyecto
