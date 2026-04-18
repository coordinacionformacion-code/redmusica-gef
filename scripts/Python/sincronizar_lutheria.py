import requests
import pandas as pd
import time
from urllib.parse import quote
 
# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
TOKEN              = "TU_TOKEN_NOTION"
ID_SOLICITUDES     = "TU_ID_BD_SOLICITUDES_LUTHERIA"
ID_LUTHIERS        = "TU_ID_BD_LUTHIERS"
ID_GESTIONES       = "TU_ID_BD_GESTIONES"
ID_ESCUELAS        = "TU_ID_BD_ESCUELAS"
 
SHEET_ID           = "1rYu2N0WwN6j1cM_a9JGxVHsuhPZtsm_PxhI8ogsU9CA"
GOOGLE_API_KEY     = "TU_API_KEY_GOOGLE"   # Ver instrucciones al final del script
# ──────────────────────────────────────────────────────────────────────────────
 
HEADERS_NOTION = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
 
# ─── LEER TODAS LAS PESTAÑAS DEL SHEET ───────────────────────────────────────
 
def get_nombres_pestanas():
    """Obtiene la lista de todas las pestañas del Sheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}?key={GOOGLE_API_KEY}&fields=sheets.properties"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Error al leer el Sheet: {r.status_code} — {r.text}")
        return []
    data = r.json()
    return [s["properties"]["title"] for s in data.get("sheets", [])]
 
def leer_pestana(nombre):
    """Lee los datos de una pestaña y los devuelve como DataFrame."""
    rango = f"{quote(nombre)}!A:J"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rango}?key={GOOGLE_API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"  Error leyendo '{nombre}': {r.status_code}")
        return pd.DataFrame()
    values = r.json().get("values", [])
    if not values or len(values) < 2:
        print(f"  '{nombre}': sin datos")
        return pd.DataFrame()
    headers = values[0]
    filas = []
    for row in values[1:]:
        while len(row) < len(headers):
            row.append("")
        filas.append(row[:len(headers)])
    df = pd.DataFrame(filas, columns=headers)
    df["_pestana"] = nombre  # para trazabilidad
    return df
 
def leer_sheet_completo():
    """Concatena los datos de todas las pestañas."""
    pestanas = get_nombres_pestanas()
    print(f"Pestañas encontradas: {pestanas}")
    dfs = []
    for nombre in pestanas:
        df = leer_pestana(nombre)
        if not df.empty:
            dfs.append(df)
            print(f"  ✓ '{nombre}': {len(df)} filas")
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)
 
# ─── HELPERS NOTION ───────────────────────────────────────────────────────────
 
def crear_pagina(db_id, props):
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS_NOTION,
        json={"parent": {"database_id": db_id}, "properties": props}
    )
    if r.status_code != 200:
        print(f"  Error Notion: {r.status_code} — {r.json().get('message','')}")
        return None
    return r.json()["id"]
 
def limpiar(val):
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()
 
def obtener_mapa(db_id, campo_titulo="Nombre"):
    """Descarga todos los registros de una BD Notion y devuelve {NOMBRE_UPPER: id}."""
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
    """Devuelve el set de títulos 'Registro' ya creados en Solicitudes Luthería."""
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
 
# ─── SINCRONIZACIÓN PRINCIPAL ─────────────────────────────────────────────────
 
print("=" * 55)
print("SINCRONIZACIÓN LUTHERÍA — SHEETS → NOTION")
print("=" * 55)
 
print("\nLeyendo Sheet completo (todas las pestañas)...")
df = leer_sheet_completo()
 
if df.empty:
    print("No se encontraron datos. Verifica el SHEET_ID y GOOGLE_API_KEY.")
    exit()
 
# Filtrar filas vacías
df = df.fillna("")
df = df[df.get("LUTHIER", pd.Series(dtype=str)).str.strip() != ""]
df = df[df.get("ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA", pd.Series(dtype=str)).str.strip() != ""]
print(f"\nRegistros válidos a procesar: {len(df)}")
 
print("\nCargando datos de Notion...")
mapa_gestiones = obtener_mapa(ID_GESTIONES)
mapa_escuelas  = obtener_mapa(ID_ESCUELAS)
mapa_luthiers  = obtener_mapa(ID_LUTHIERS)
existentes     = obtener_solicitudes_existentes()
 
print(f"  Gestiones en Notion:   {len(mapa_gestiones)}")
print(f"  Escuelas en Notion:    {len(mapa_escuelas)}")
print(f"  Luthiers en Notion:    {len(mapa_luthiers)}")
print(f"  Solicitudes existentes: {len(existentes)}")
 
print("\nSincronizando...")
creadas  = 0
omitidas = 0
errores  = 0
 
for _, row in df.iterrows():
    semana   = limpiar(row.get("SEMANA", ""))
    gestion  = limpiar(row.get("GESTIÓN", ""))
    luthier  = limpiar(row.get("LUTHIER", ""))
    dia      = limpiar(row.get("DÍA", ""))
    jornada  = limpiar(row.get("JORNADA", ""))
    tipo_esc = limpiar(row.get("TIPO DE ESCUELA O AGRUPACIÓN INTEGRADA", ""))
    escuela  = limpiar(row.get("ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA", ""))
    modalidad = limpiar(row.get("MODALIDAD", ""))
    obs      = limpiar(row.get("OBSERVACIÓN", ""))
    pestana  = limpiar(row.get("_pestana", ""))
 
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
 
    # Semana ahora es TEXTO LIBRE — acepta cualquier rango de días
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
 
    # Relaciones por coincidencia parcial
    gestion_key = gestion.upper()
    for key, gid in mapa_gestiones.items():
        if gestion_key in key or key in gestion_key:
            props["Gestión"] = {"relation": [{"id": gid}]}
            break
 
    escuela_key = escuela.upper()
    if escuela_key in mapa_escuelas:
        props["Escuela o Agrupación Integrada"] = {"relation": [{"id": mapa_escuelas[escuela_key]}]}
 
    luthier_key = luthier.upper()
    if luthier_key in mapa_luthiers:
        props["Luthier"] = {"relation": [{"id": mapa_luthiers[luthier_key]}]}
 
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
print(f"  Solicitudes creadas:  {creadas}")
print(f"  Omitidas (ya existen): {omitidas}")
print(f"  Errores:              {errores}")
print("=" * 55)
