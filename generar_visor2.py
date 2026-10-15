import pandas as pd
import os
import json

ARCHIVO_CSV = "catalogo_maestro.csv"

# Detectar automáticamente qué carpeta de imágenes existe
CARPETAS_POSIBLES = ["imagenes_productos2"]
CARPETA_IMG = next((c for c in CARPETAS_POSIBLES if os.path.exists(c)), "imagenes_productos")

def generar_verificador():
    if not os.path.exists(ARCHIVO_CSV):
        print(f"[ERROR] No se encuentra '{ARCHIVO_CSV}'.")
        return

    df = pd.read_csv(ARCHIVO_CSV)
    total_prods = len(df)
    
    # Comprobar existencia real de cada imagen en disco
    df['Existe'] = df['ID_Imagen'].apply(lambda img: os.path.exists(os.path.join(CARPETA_IMG, str(img))))
    total_existentes = df['Existe'].sum()
    total_faltantes = total_prods - total_existentes

    categorias = sorted(df['Categoria'].dropna().unique().tolist())

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validador de Catálogo - Ferretería Puerta Carmona</title>
    <style>
        :root {{
            --bg: #f8fafc;
            --surface: #ffffff;
            --border: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --brand: #2563eb;
            --brand-light: #eff6ff;
            --success: #16a34a;
            --danger: #dc2626;
            --danger-bg: #fef2f2;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            padding: 24px;
        }}
        .header {{
            max-width: 1400px;
            margin: 0 auto 24px;
            background: var(--surface);
            padding: 20px 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .header h1 {{ font-size: 1.5rem; margin-bottom: 8px; color: #1e293b; }}
        .stats {{
            display: flex;
            gap: 16px;
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 16px;
        }}
        .stats span b {{ color: var(--text-main); }}
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            justify-content: space-between;
        }}
        .search-box {{
            flex: 1;
            min-width: 280px;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            outline: none;
        }}
        .search-box:focus {{ border-color: var(--brand); }}
        .filters {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .filter-btn {{
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 0.85rem;
            cursor: pointer;
            font-weight: 500;
            color: var(--text-muted);
            transition: all 0.15s;
        }}
        .filter-btn.active {{
            background: var(--brand);
            color: #ffffff;
            border-color: var(--brand);
        }}
        .grid {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 16px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .card.missing-img {{ border-color: #fca5a5; background: #fffaf0; }}
        .img-wrapper {{
            width: 100%;
            height: 180px;
            background: #ffffff;
            border-radius: 6px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #f1f5f9;
            overflow: hidden;
        }}
        .img-wrapper img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .badge-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .sku {{ font-family: monospace; font-weight: 700; font-size: 0.8rem; color: #475569; }}
        .cat-tag {{
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            background: var(--brand-light);
            color: var(--brand);
            font-weight: 600;
        }}
        .title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 4px;
            line-height: 1.3;
        }}
        .brand {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}
        .pdf-desc {{
            font-size: 0.75rem;
            color: #334155;
            background: #f1f5f9;
            padding: 6px 10px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 3px solid var(--brand);
            line-height: 1.25;
        }}
        .price-bar {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            padding-top: 8px;
            border-top: 1px solid var(--border);
        }}
        .price-sin {{ font-size: 0.8rem; color: var(--text-muted); }}
        .price-con {{ font-size: 1.1rem; font-weight: 700; color: #047857; }}
        .img-file {{
            font-size: 0.7rem;
            font-family: monospace;
            color: var(--text-muted);
            text-align: right;
            margin-top: 6px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Validador Visual del Catálogo Maestro</h1>
        <div class="stats">
            <span>Productos: <b>{total_prods}</b></span>
            <span>Carpeta: <code>./{CARPETA_IMG}/</code></span>
            <span>En disco: <b style="color: var(--success);">{total_existentes}</b></span>
            <span>Faltantes: <b style="color: var(--danger);">{total_faltantes}</b></span>
        </div>
        <div class="controls">
            <input type="text" id="buscador" class="search-box" placeholder="Buscar por nombre, SKU, marca o archivo...">
            <div class="filters">
                <button class="filter-btn active" onclick="filtrar('todas')">Todas ({total_prods})</button>
    """

    for cat in categorias:
        count_cat = (df['Categoria'] == cat).sum()
        html_content += f'<button class="filter-btn" onclick="filtrar(\'{cat}\')">{cat} ({count_cat})</button>\n'

    html_content += """
            </div>
        </div>
    </div>

    <div class="grid" id="grid">
    """

    for _, row in df.iterrows():
        sku = str(row['SKU'])
        nombre = str(row['Nombre'])
        marca = str(row['Marca'])
        cat = str(row['Categoria'])
        subcat = str(row['Subcategoria'])
        p_sin = f"{float(row['Precio_Sin_IVA']):.2f}"
        p_con = f"{float(row['Precio_Con_IVA']):.2f}"
        id_img = str(row['ID_Imagen'])
        desc_visual = str(row['Descripcion_Visual']) if pd.notna(row['Descripcion_Visual']) else "Sin descripción en catálogo"
        existe = row['Existe']

        ruta_relativa = f"{CARPETA_IMG}/{id_img}".replace("\\", "/")
        card_class = "card" if existe else "card missing-img"

        html_content += f"""
        <div class="{card_class}" data-cat="{cat}" data-search="{sku.lower()} {nombre.lower()} {marca.lower()} {id_img.lower()}">
            <div class="badge-bar">
                <span class="sku">{sku}</span>
                <span class="cat-tag">{subcat}</span>
            </div>
            <div class="img-wrapper">
                <img src="{ruta_relativa}" alt="{nombre}" onerror="this.onerror=null; this.src='https://placehold.co/300x200?text=Falta+Imagen';">
            </div>
            <div class="title">{nombre}</div>
            <div class="brand">Marca: <b>{marca}</b></div>
            <div class="pdf-desc" title="Lo que indica el catálogo en papel">
                <b>En el PDF:</b> {desc_visual}
            </div>
            <div class="price-bar">
                <span class="price-sin">{p_sin} € s/IVA</span>
                <span class="price-con">{p_con} €</span>
            </div>
            <div class="img-file">{id_img}</div>
        </div>
        """

    html_content += """
    </div>

    <script>
        let categoriaActiva = 'todas';
        const buscador = document.getElementById('buscador');
        const cards = document.querySelectorAll('.card');

        function actualizarVista() {
            const query = buscador.value.trim().toLowerCase();

            cards.forEach(card => {
                const matchCat = (categoriaActiva === 'todas') || (card.getAttribute('data-cat') === categoriaActiva);
                const matchQuery = query === '' || card.getAttribute('data-search').includes(query);

                if (matchCat && matchQuery) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function filtrar(categoria) {
            categoriaActiva = categoria;
            document.querySelectorAll('.filter-btn').forEach(btn => {
                if (btn.innerText.startsWith(categoria) || (categoria === 'todas' && btn.innerText.startsWith('Todas'))) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            actualizarVista();
        }

        buscador.addEventListener('input', actualizarVista);
    </script>
</body>
</html>
    """

    salida_html = "verificador.html"
    with open(salida_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n[ÉXITO] Visor generado en '{salida_html}' leyendo desde './{CARPETA_IMG}/'.")
    print(f"-> Abre 'verificador.html' en tu navegador para revisar.")

if __name__ == "__main__":
    generar_verificador()