import requests
import pandas as pd
import io
import time
from urllib.parse import quote

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
TOKEN          = "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"
ID_SOLICITUDES = "32b41296407480d2a569e453ad92ca49"
ID_LUTHIERS    = "32b41296407480b3a3c4e06f8297106d"
ID_GESTIONES   = "32a41296407480d6b790cc693a7f57d9"
ID_ESCUELAS    = "32a4129640748079825cf524a9b87382"

SHEET_ID = "1rYu2N0WwN6j1cM_a9JGxVHsuhPZtsm_PxhI8ogsU9CA"

# ── Agrega el nombre de cada pestaña nueva al inicio del mes ───────────────────
PESTANAS = ["Febrero", "Marzo", "Abril"]
# ──────────────────────────────────────────────────────────────────────────────

HEADERS_NOTION = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def leer_pestana(nombre):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre)}"
    r = requests.get(url, timeout=15)
    if r.status_code != 200 or len(r.text.strip()) < 20:
        print(f"  ⚠ '{nombre}': no se pudo leer o está vacía")
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(r.text))
    df = df.fillna("")
    # Solo eliminar filas donde GESTIÓN, LUTHIER y ESCUELA están todos vacíos
    col_gestion = next((c for c in df.columns if "GESTIÓN" in c.upper() or "GESTION" in c.upper()), None)
    col_luthier = next((c for c in df.columns if "LUTHIER" in c.upper()), None)
    col_escuela = next((c for c in df.columns if "ESCUELA" in c.upper()), None)
    mask_vacias = pd.Series([True] * len(df))
    if col_gestion:
        mask_vacias = mask_vacias & (df[col_gestion].str.strip() == "")
    if col_luthier:
        mask_vacias = mask_vacias & (df[col_luthier].str.strip() == "")
    if col_escuela:
        mask_vacias = mask_vacias & (df[col_escuela].str.strip() == "")
    df = df[~mask_vacias]
    df["_pestana"] = nombre
    return df

def leer_sheet_completo():
    dfs = []
    for nombre in PESTANAS:
        df = leer_pestana(nombre)
        if not df.empty:
            dfs.append(df)
            print(f"  ✓ '{nombre}': {len(df)} registros")
        else:
            print(f"  - '{nombre}': sin registros válidos")
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def limpiar(val):
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()

def crear_pagina(db_id, props):
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS_NOTION,
        json={"parent": {"database_id": db_id}, "properties": props}
    )
    if r.status_code != 200:
        print(f"  ✗ Error Notion: {r.status_code} — {r.json().get('message','')}")
        return None
    return r.json()["id"]

def obtener_mapa(db_id, campo_titulo="Nombre"):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    resultados = []
    payload = {"page_size": 100}
    while True:
        r = requests.post(url, headers=HEADERS_NOTION, json=payload)
        data = r.json()
        resultados.extend(data.get("results", []))
        if data.get("has_more"):
            payload["start_cursor"] = data["next_cursor"]
        else:
            break
    mapa = {}
    for item in resultados:
        props = item["properties"]
        titulo = props.get(campo_titulo, {}).get("title", [])
        nombre = titulo[0]["plain_text"] if titulo else ""
        if nombre:
            mapa[nombre.strip().upper()] = item["id"]
    return mapa

def obtener_solicitudes_existentes():
    url = f"https://api.notion.com/v1/databases/{ID_SOLICITUDES}/query"
    resultados = []
    payload = {"page_size": 100}
    while True:
        r = requests.post(url, headers=HEADERS_NOTION, json=payload)
        data = r.json()
        resultados.extend(data.get("results", []))
        if data.get("has_more"):
            payload["start_cursor"] = data["next_cursor"]
        else:
            break
    existentes = set()
    for item in resultados:
        titulo = item["properties"].get("Registro", {}).get("title", [])
        if titulo:
            existentes.add(titulo[0]["plain_text"].strip())
    return existentes

print("=" * 55)
print("SINCRONIZACIÓN LUTHERÍA — SHEETS → NOTION")
print("=" * 55)

print(f"\nLeyendo pestañas: {PESTANAS}")
df = leer_sheet_completo()

if df.empty:
    print("\nNo se encontraron datos.")
    exit()

print(f"\nTotal registros a procesar: {len(df)}")

print("\nCargando datos de Notion...")
mapa_gestiones = obtener_mapa(ID_GESTIONES)
mapa_escuelas  = obtener_mapa(ID_ESCUELAS)
mapa_luthiers  = obtener_mapa(ID_LUTHIERS)
existentes     = obtener_solicitudes_existentes()

print(f"  Gestiones:              {len(mapa_gestiones)}")
print(f"  Escuelas:               {len(mapa_escuelas)}")
print(f"  Luthiers:               {len(mapa_luthiers)}")
print(f"  Solicitudes existentes: {len(existentes)}")

print("\nSincronizando...")
creadas  = 0
omitidas = 0
errores  = 0

for _, row in df.iterrows():
    semana    = limpiar(row.get("SEMANA", ""))
    gestion   = limpiar(row.get("GESTIÓN", ""))
    luthier   = limpiar(row.get("LUTHIER", ""))
    dia       = limpiar(row.get("DÍA", ""))
    jornada   = limpiar(row.get("JORNADA", ""))
    tipo_esc  = limpiar(row.get("TIPO DE ESCUELA O AGRUPACIÓN INTEGRADA", ""))
    escuela   = limpiar(row.get("ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA", ""))
    modalidad = limpiar(row.get("MODALIDAD", ""))
    obs       = limpiar(row.get("OBSERVACIÓN", ""))
    pestana   = limpiar(row.get("_pestana", ""))

    realizada_raw = row.get("REALIZADA", "")
    if isinstance(realizada_raw, bool):
        realizada = realizada_raw
    else:
        realizada = str(realizada_raw).strip().upper() in ("TRUE", "VERDADERO", "1", "SI", "SÍ")

    titulo = f"{pestana} | {semana} — {luthier} — {escuela} — {dia} {jornada}"

    if titulo in existentes:
        omitidas += 1
        continue

    props = {
        "Registro": {"title": [{"text": {"content": titulo[:2000]}}]},
        "Realizada": {"checkbox": realizada},
    }

    if pestana:
        props["Mes"] = {"select": {"name": pestana}}
    if semana:
        props["Semana"] = {"rich_text": [{"text": {"content": semana}}]}
    if dia:
        props["Día"] = {"select": {"name": dia}}
    if jornada:
        props["Jornada"] = {"select": {"name": jornada}}
    if modalidad:
        props["Modalidad"] = {"select": {"name": modalidad}}
    if tipo_esc:
        props["Tipo de Escuela o Agrupación Integrada"] = {"select": {"name": tipo_esc}}
    if obs:
        props["Observación"] = {"rich_text": [{"text": {"content": obs[:2000]}}]}

    gestion_key = gestion.upper()
    for key, gid in mapa_gestiones.items():
        if gestion_key in key or key in gestion_key:
            props["Gestión"] = {"relation": [{"id": gid}]}
            break

    if escuela.upper() in mapa_escuelas:
        props["Escuela o Agrupación Integrada"] = {"relation": [{"id": mapa_escuelas[escuela.upper()]}]}

    if luthier.upper() in mapa_luthiers:
        props["Luthier"] = {"relation": [{"id": mapa_luthiers[luthier.upper()]}]}

    page_id = crear_pagina(ID_SOLICITUDES, props)
    if page_id:
        existentes.add(titulo)
        creadas += 1
        print(f"  ✓ {titulo}")
    else:
        errores += 1

    time.sleep(0.35)

print("\n" + "=" * 55)
print("SINCRONIZACIÓN COMPLETADA")
print(f"  Solicitudes creadas:   {creadas}")
print(f"  Omitidas (ya existen): {omitidas}")
print(f"  Errores:               {errores}")
print("=" * 55)

# ─── CADA MES NUEVO ───────────────────────────────────────────────────────────
#  PESTANAS = ["Febrero", "Marzo", "Abril", "Mayo"]
# ─────────────────────────────────────────────────────────────────────────────
