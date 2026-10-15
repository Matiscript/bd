import pandas as pd
import os
import json

ARCHIVO_CSV = "catalogo_maestro.csv"
CARPETA_WEB = "imagenes_productos2"  # Carpeta con las fotos descargadas de Serper/Web
CARPETA_PDF = "imagenes_productos"   # Carpeta con las fotos extraídas del PDF

def crear_comparador_html():
    if not os.path.exists(ARCHIVO_CSV):
        print(f"[ERROR] No se encuentra '{ARCHIVO_CSV}'.")
        return

    df = pd.read_csv(ARCHIVO_CSV)
    # Filtramos por imagen única (280 imágenes) para no elegir 4 veces la misma foto en variantes
    df_unicas = df.drop_duplicates(subset=['ID_Imagen']).copy()
    categorias = sorted(df_unicas['Categoria'].dropna().unique().tolist())

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Comparador A/B de Imágenes - Catálogo GSI</title>
    <style>
        :root {{
            --bg: #f1f5f9;
            --card: #ffffff;
            --primary: #2563eb;
            --pdf-color: #d97706;
            --border: #cbd5e1;
            --text: #0f172a;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); padding-bottom: 90px; }}
        .topbar {{
            position: sticky; top: 0; z-index: 100; background: #1e293b; color: white;
            padding: 16px 24px; display: flex; flex-wrap: wrap; justify-content: space-between;
            align-items: center; gap: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        .topbar h1 {{ font-size: 1.2rem; }}
        .controls {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
        .btn-filter {{
            background: #334155; color: #e2e8f0; border: none; padding: 7px 12px;
            border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500;
        }}
        .btn-filter.active {{ background: var(--primary); color: white; }}
        .btn-save {{
            background: #16a34a; color: white; border: none; padding: 10px 18px;
            border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 0.9rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        .btn-save:hover {{ background: #15803d; }}
        .search {{ padding: 8px 12px; border-radius: 6px; border: none; min-width: 220px; }}
        .grid {{
            max-width: 1440px; margin: 24px auto; padding: 0 16px;
            display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 18px;
        }}
        .card {{
            background: var(--card); border-radius: 10px; border: 1px solid var(--border);
            padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .card-header {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.8rem; color: #64748b; }}
        .sku {{ font-family: monospace; font-weight: bold; color: #334155; }}
        .title {{ font-size: 1rem; font-weight: 700; margin-bottom: 4px; color: #1e293b; }}
        .desc {{
            font-size: 0.78rem; background: #f8fafc; padding: 6px 10px;
            border-left: 3px solid var(--primary); margin-bottom: 12px; color: #475569;
        }}
        .ab-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .option {{
            border: 3px solid #e2e8f0; border-radius: 8px; padding: 8px;
            text-align: center; cursor: pointer; transition: all 0.15s; position: relative;
            background: #fff;
        }}
        .option:hover {{ border-color: #94a3b8; }}
        .option.selected-web {{ border-color: var(--primary); background: #eff6ff; }}
        .option.selected-pdf {{ border-color: var(--pdf-color); background: #fffbeb; }}
        .option img {{ width: 100%; height: 150px; object-fit: contain; display: block; margin-bottom: 6px; background: white; border-radius: 4px; }}
        .opt-label {{ font-size: 0.8rem; font-weight: 700; display: block; padding: 4px; border-radius: 4px; }}
        .selected-web .opt-label {{ background: var(--primary); color: white; }}
        .selected-pdf .opt-label {{ background: var(--pdf-color); color: white; }}
        .img-id {{ font-family: monospace; font-size: 0.7rem; color: #94a3b8; margin-top: 8px; text-align: right; }}
    </style>
</head>
<body>

<div class="topbar">
    <div>
        <h1>Comparador A/B ({len(df_unicas)} imágenes únicas)</h1>
        <small id="counter">Haz clic en la foto que prefieras para cada producto</small>
    </div>
    <div class="controls">
        <input type="text" id="search" class="search" placeholder="Buscar producto o SKU...">
        <button class="btn-filter active" onclick="filtrar('todas', this)">Todas</button>
    """

    for cat in categorias:
        html += f'<button class="btn-filter" onclick="filtrar(\'{cat}\', this)">{cat}</button>\n'

    html += """
        <button class="btn-save" onclick="exportarDecisiones()">💾 Guardar y Descargar Selección (JSON)</button>
    </div>
</div>

<div class="grid" id="grid">
    """

    decisiones_iniciales = {}

    for _, row in df_unicas.iterrows():
        id_img = str(row['ID_Imagen'])
        sku = str(row['SKU'])
        nombre = str(row['Nombre'])
        cat = str(row['Categoria'])
        subcat = str(row['Subcategoria'])
        desc = str(row['Descripcion_Visual'])

        ruta_web = f"{CARPETA_WEB}/{id_img}".replace("\\", "/")
        ruta_pdf = f"{CARPETA_PDF}/{id_img}".replace("\\", "/")

        existe_web = os.path.exists(os.path.join(CARPETA_WEB, id_img)) and os.path.getsize(os.path.join(CARPETA_WEB, id_img)) > 1000
        existe_pdf = os.path.exists(os.path.join(CARPETA_PDF, id_img))

        # Si existe la de la web, por defecto marcamos 'web', si no, 'pdf'
        eleccion_defecto = "web" if existe_web else "pdf"
        decisiones_iniciales[id_img] = eleccion_defecto

        clase_web = "option selected-web" if eleccion_defecto == "web" else "option"
        clase_pdf = "option selected-pdf" if eleccion_defecto == "pdf" else "option"

        html += f"""
        <div class="card" data-cat="{cat}" data-search="{sku.lower()} {nombre.lower()} {id_img.lower()}">
            <div class="card-header">
                <span class="sku">{sku}</span>
                <span>{cat} &gt; {subcat}</span>
            </div>
            <div class="title">{nombre}</div>
            <div class="desc"><b>PDF describe:</b> {desc}</div>
            <div class="ab-container">
                <div class="{clase_web}" id="web-{id_img}" onclick="seleccionar('{id_img}', 'web')">
                    <img src="{ruta_web}" onerror="this.src='https://placehold.co/200x150?text=No+Web'">
                    <span class="opt-label">A: Web (Alta Res)</span>
                </div>
                <div class="{clase_pdf}" id="pdf-{id_img}" onclick="seleccionar('{id_img}', 'pdf')">
                    <img src="{ruta_pdf}" onerror="this.src='https://placehold.co/200x150?text=No+PDF'">
                    <span class="opt-label">B: PDF (Original)</span>
                </div>
            </div>
            <div class="img-id">{id_img}</div>
        </div>
        """

    html += f"""
</div>

<script>
    const decisiones = {json.dumps(decisiones_iniciales)};
    let catActual = 'todas';

    function actualizarContador() {{
        const totalWeb = Object.values(decisiones).filter(v => v === 'web').length;
        const totalPdf = Object.values(decisiones).filter(v => v === 'pdf').length;
        document.getElementById('counter').innerText = `Seleccionadas -> Web: ${{totalWeb}} | PDF: ${{totalPdf}}`;
    }}

    function seleccionar(idImg, origen) {{
        decisiones[idImg] = origen;
        const elWeb = document.getElementById('web-' + idImg);
        const elPdf = document.getElementById('pdf-' + idImg);

        if (origen === 'web') {{
            elWeb.className = 'option selected-web';
            elPdf.className = 'option';
        }} else {{
            elWeb.className = 'option';
            elPdf.className = 'option selected-pdf';
        }}
        actualizarContador();
    }}

    function filtrar(cat, btn) {{
        catActual = cat;
        document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        aplicarFiltros();
    }}

    function aplicarFiltros() {{
        const q = document.getElementById('search').value.toLowerCase();
        document.querySelectorAll('.card').forEach(card => {{
            const matchCat = (catActual === 'todas') || (card.getAttribute('data-cat') === catActual);
            const matchQ = q === '' || card.getAttribute('data-search').includes(q);
            card.style.display = (matchCat && matchQ) ? 'block' : 'none';
        }});
    }}

    document.getElementById('search').addEventListener('input', aplicarFiltros);

    function exportarDecisiones() {{
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(decisiones, null, 2));
        const a = document.createElement('a');
        a.setAttribute("href", dataStr);
        a.setAttribute("download", "decisiones_imagenes.json");
        document.body.appendChild(a);
        a.click();
        a.remove();
    }}

    actualizarContador();
</script>
</body>
</html>
    """

    with open("comparador_ab.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("[ÉXITO] Abre 'comparador_ab.html' en tu navegador.")

if __name__ == "__main__":
    crear_comparador_html()