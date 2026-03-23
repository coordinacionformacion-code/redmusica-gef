"""
GEF Red Músicas de Medellín
Script: importar_sgr.py
Descripción: Importación inicial de Gestiones, Escuelas y Artistas Formadores
             desde un archivo CSV a las bases de datos de Notion.
Ejecutar: Solo una vez al inicio del sistema
Uso: python importar_sgr.py
"""

import requests
import pandas as pd
import time

# ── Configuración ──
TOKEN        = "TU_TOKEN_DE_NOTION"
ID_GESTIONES = "TU_ID_BD_GESTIONES"
ID_ESCUELAS  = "TU_ID_BD_ESCUELAS"
ID_FORMADORES= "TU_ID_BD_FORMADORES"
CSV_PATH     = "formadores.csv"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ── Funciones auxiliares ──
def crear_pagina(db_id, props):
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS,
        json={"parent": {"database_id": db_id}, "properties": props})
    if r.status_code != 200:
        print(f"  Error {r.status_code}: {r.json().get('message','')}")
        return None
    return r.json()["id"]

def limpiar(val):
    if pd.isna(val): return ""
    return str(val).strip()

def obtener_o_crear(db_id, nombre, campo_titulo="Nombre"):
    """Busca un registro por nombre o lo crea si no existe."""
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    r = requests.post(url, headers=HEADERS, json={"page_size": 100})
    for item in r.json().get("results", []):
        titulo = item["properties"].get(campo_titulo, {}).get("title", [])
        if titulo and titulo[0]["plain_text"].strip() == nombre.strip():
            return item["id"]
    # No existe — crear
    return crear_pagina(db_id, {campo_titulo: {"title": [{"text": {"content": nombre}}]}})

# ── Importar Gestiones ──
def importar_gestiones():
    gestiones = [
        "G. Iniciación", "G. Canto y Movimiento", "G. Neurodiversidad",
        "G. Cuerdas Frotadas y Pulsadas", "G. Bronces y Percusión",
        "G. Vientos Maderas", "Conjuntos Instrumentales", "POR DEFINIR"
    ]
    mapa = {}
    print("Importando Gestiones...")
    for g in gestiones:
        gid = obtener_o_crear(ID_GESTIONES, g)
        if gid:
            mapa[g.upper()] = gid
            print(f"  OK {g}")
        time.sleep(0.3)
    return mapa

# ── Importar Escuelas ──
def importar_escuelas(df):
    mapa = {}
    print("\nImportando Escuelas...")
    escuelas_unicas = df[["ESCUELA", "ZONA", "TIPOLOGÍA", "DIRECTOR"]].drop_duplicates(subset="ESCUELA")
    for _, row in escuelas_unicas.iterrows():
        nombre = limpiar(row["ESCUELA"])
        if not nombre: continue
        props = {
            "Nombre": {"title": [{"text": {"content": nombre}}]},
        }
        if limpiar(row.get("ZONA", "")):
            props["Zona"] = {"select": {"name": limpiar(row["ZONA"])}}
        if limpiar(row.get("TIPOLOGÍA", "")):
            props["Tipología"] = {"select": {"name": limpiar(row["TIPOLOGÍA"])}}
        if limpiar(row.get("DIRECTOR", "")):
            props["Director"] = {"rich_text": [{"text": {"content": limpiar(row["DIRECTOR"])}}]}

        eid = crear_pagina(ID_ESCUELAS, props)
        if eid:
            mapa[nombre.upper()] = eid
            print(f"  OK {nombre}")
        time.sleep(0.3)
    return mapa

# ── Importar Formadores ──
def importar_formadores(df, mapa_gestiones, mapa_escuelas):
    print("\nImportando Artistas Formadores...")
    creados = 0
    errores = 0

    formadores_unicos = df.drop_duplicates(subset="NOMBRE FORMADOR")

    for _, row in formadores_unicos.iterrows():
        nombre   = limpiar(row.get("NOMBRE FORMADOR", ""))
        gestion  = limpiar(row.get("GESTIÓN", ""))
        contrato = limpiar(row.get("TIPO CONTRATO", ""))
        nivel    = limpiar(row.get("NIVEL FORMACIÓN", ""))
        celular  = limpiar(row.get("CELULAR", ""))
        correo   = limpiar(row.get("CORREO", ""))

        if not nombre: continue

        props = {
            "Nombre": {"title": [{"text": {"content": nombre}}]},
            "Estado": {"select": {"name": "Activo"}},
        }
        if contrato:
            props["Tipo de contrato"] = {"select": {"name": contrato}}
        if nivel:
            props["Nivel de formación"] = {"select": {"name": nivel}}
        if celular:
            props["Celular"] = {"phone_number": celular}
        if correo:
            props["Email"] = {"email": correo}

        # Relación con Gestión
        gestion_key = gestion.upper()
        for key, gid in mapa_gestiones.items():
            if gestion_key in key or key in gestion_key:
                props["Gestión"] = {"relation": [{"id": gid}]}
                break

        # Relaciones con Escuelas (puede tener varias)
        escuelas_formador = df[df["NOMBRE FORMADOR"] == nombre]["ESCUELA"].dropna().unique()
        relaciones_esc = []
        for esc in escuelas_formador:
            esc_key = str(esc).strip().upper()
            if esc_key in mapa_escuelas:
                relaciones_esc.append({"id": mapa_escuelas[esc_key]})
        if relaciones_esc:
            props["Escuelas"] = {"relation": relaciones_esc}

        fid = crear_pagina(ID_FORMADORES, props)
        if fid:
            creados += 1
            print(f"  OK {nombre}")
        else:
            errores += 1
        time.sleep(0.35)

    return creados, errores

# ── Main ──
if __name__ == "__main__":
    print("=" * 50)
    print("IMPORTACIÓN SGR — Red Músicas de Medellín")
    print("=" * 50)

    df = pd.read_csv(CSV_PATH, encoding="utf-8")
    print(f"\nArchivo: {CSV_PATH} — {len(df)} filas")

    mapa_gestiones = importar_gestiones()
    mapa_escuelas  = importar_escuelas(df)
    creados, errores = importar_formadores(df, mapa_gestiones, mapa_escuelas)

    print("\n" + "=" * 50)
    print("IMPORTACIÓN COMPLETADA")
    print(f"  Gestiones importadas: {len(mapa_gestiones)}")
    print(f"  Escuelas importadas:  {len(mapa_escuelas)}")
    print(f"  Formadores creados:   {creados}")
    print(f"  Errores:              {errores}")
    print("=" * 50)
