import pandas as pd

def convertir_csv_a_sql(archivo_csv, archivo_sql="insertar_datos.sql"):
    df = pd.read_csv(archivo_csv)
    
    with open(archivo_sql, "w", encoding="utf-8") as f:
        f.write("USE `wordpress`;\n\n")
        
        for _, fila in df.iterrows():
            nombre = str(fila['Nombre']).replace("'", "''")
            subcat = str(fila['Subcategoria']).replace("'", "''")
            
            sql = (
                f"INSERT INTO `catalogo_productos` "
                f"(`sku`, `nombre`, `categoria`, `subcategoria`, `precio_sin_iva`, `tipo_iva`, `imagen_url`, `disponible`) "
                f"VALUES ('{fila['SKU']}', '{nombre}', '{fila['Categoria']}', '{subcat}', "
                f"{fila['Precio_Sin_IVA']}, 21.00, '{fila['Imagen']}', 1);\n"
            )
            f.write(sql)
            
    print(f"Archivo SQL '{archivo_sql}' listo para importar en phpMyAdmin.")

if __name__ == "__main__":
    convertir_csv_a_sql("catalogo_maestro.csv")