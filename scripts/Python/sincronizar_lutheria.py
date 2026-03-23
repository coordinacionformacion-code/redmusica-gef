"""
GEF Red Músicas de Medellín
Script: sincronizar_lutheria.py
Descripción: Sincroniza las solicitudes de Luthería desde el Google Sheets
             del equipo de luthiers hacia la BD de Notion.
             Detecta duplicados automáticamente — seguro para ejecutar
             múltiples veces sin crear registros repetidos.
Ejecutar: Mensualmente cuando los luthiers actualicen su planilla
Uso: python sincronizar_lutheria.py
"""

import requests
import pandas as pd
import time

# ── Configuración ──
TOKEN          = "TU_TOKEN_DE_NOTION"
ID_SOLICITUDES = "TU_ID_BD_SOLICITUDES_LUTHERIA"
ID_LUTHIERS    = "TU_ID_BD_LUTHIERS"
ID_GESTIONES   = "TU_ID_BD_GESTIONES"
ID_ESCUELAS    = "TU_ID_BD_ESCUELAS"

# URL del CSV publicado desde Google Sheets
# (Archivo → Publicar en la web → hoja correspondiente → CSV)
CSV_URL = "TU_URL_CSV_SHEETS_LUTHERIA"

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
        print(f"  Error: {r.status_code} — {r.json().get('message','')}")
        return None
    return r.json()["id"]

def limpiar(val):
    if pd.isna(val): return ""
    return str(val).strip()

def obtener_mapa(db_id, campo_titulo="Nombre"):
    """Carga todos los registros de una BD y devuelve un dict {NOMBRE_UPPER: id}"""
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    resultados = []
    payload = {"page_size": 100}
    while True:
        r = requests.post(url, headers=HEADERS, json=payload)
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
    """Carga los títulos de solicitudes ya existentes para evitar duplicados."""
    url = f"https://api.notion.com/v1/databases/{ID_SOLICITUDES}/query"
    resultados = []
    payload = {"page_size": 100}
    while True:
        r = requests.post(url, headers=HEADERS, json=payload)
        data = r.json()
        resultados.extend(data.get("results", []))
        if data.get("has_more"):
            payload["start_cursor"] = data["next_cursor"]
        else:
            break
    existentes = set()
    for item in resultados:
        props = item["properties"]
        titulo = props.get("Registro", {}).get("title", [])
        if titulo:
            existentes.add(titulo[0]["plain_text"].strip())
    return existentes

# ── Main ──
if __name__ == "__main__":
    print("=" * 50)
    print("SINCRONIZACIÓN LUTHERÍA — Red Músicas de Medellín")
    print("=" * 50)

    print("\nLeyendo Sheets de Luthería...")
    df = pd.read_csv(CSV_URL)
    df = df.fillna("")
    df = df[df["LUTHIER"].str.strip() != ""]
    df = df[df["ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA"].str.strip() != ""]
    print(f"  Registros encontrados: {len(df)}")

    print("\nCargando mapas de Notion...")
    mapa_gestiones = obtener_mapa(ID_GESTIONES)
    mapa_escuelas  = obtener_mapa(ID_ESCUELAS)
    mapa_luthiers  = obtener_mapa(ID_LUTHIERS, campo_titulo="Nombre")
    existentes     = obtener_solicitudes_existentes()

    print(f"  Gestiones: {len(mapa_gestiones)}")
    print(f"  Escuelas:  {len(mapa_escuelas)}")
    print(f"  Luthiers:  {len(mapa_luthiers)}")
    print(f"  Solicitudes existentes: {len(existentes)}")

    print("\nSincronizando solicitudes...")
    creadas  = 0
    omitidas = 0

    for _, row in df.iterrows():
        semana    = limpiar(row.get("SEMANA", ""))
        gestion   = limpiar(row.get("GESTIÓN", ""))
        luthier   = limpiar(row.get("LUTHIER", ""))
        dia       = limpiar(row.get("DÍA", ""))
        jornada   = limpiar(row.get("JORNADA", ""))
        tipo_esc  = limpiar(row.get("TIPO DE ESCUELA O AGRUPACIÓN INTEGRADA", ""))
        escuela   = limpiar(row.get("ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA", ""))
        modalidad = limpiar(row.get("MODALIDAD", ""))
        realizada = row.get("REALIZADA", False)
        obs       = limpiar(row.get("OBSERVACIÓN", ""))

        # Título único para evitar duplicados
        titulo = f"{semana} — {luthier} — {escuela} — {dia} — {jornada} — {modalidad} — {obs}"

        if titulo in existentes:
            omitidas += 1
            continue

        props = {
            "Registro":  {"title": [{"text": {"content": titulo}}]},
            "Realizada": {"checkbox": bool(realizada) if realizada != "" else False},
        }

        if semana:   props["Semana"]    = {"select": {"name": semana}}
        if dia:      props["Día"]       = {"select": {"name": dia}}
        if jornada:  props["Jornada"]   = {"select": {"name": jornada}}
        if modalidad: props["Modalidad"] = {"select": {"name": modalidad}}
        if tipo_esc: props["Tipo de Escuela o Agrupación Integrada"] = {"select": {"name": tipo_esc}}
        if obs:      props["Observación"] = {"rich_text": [{"text": {"content": obs[:2000]}}]}

        # Relación Gestión
        gestion_key = gestion.upper()
        for key, gid in mapa_gestiones.items():
            if gestion_key in key or key in gestion_key:
                props["Gestión"] = {"relation": [{"id": gid}]}
                break

        # Relación Escuela
        escuela_key = escuela.upper()
        if escuela_key in mapa_escuelas:
            props["Escuela o Agrupación Integrada"] = {"relation": [{"id": mapa_escuelas[escuela_key]}]}

        # Relación Luthier
        luthier_key = luthier.upper()
        if luthier_key in mapa_luthiers:
            props["Luthier"] = {"relation": [{"id": mapa_luthiers[luthier_key]}]}

        page_id = crear_pagina(ID_SOLICITUDES, props)
        if page_id:
            existentes.add(titulo)
            creadas += 1
            print(f"  OK {titulo[:80]}")

        time.sleep(0.35)

    print("\n" + "=" * 50)
    print("SINCRONIZACIÓN COMPLETADA")
    print(f"  Solicitudes creadas:  {creadas}")
    print(f"  Omitidas (existían):  {omitidas}")
    print("=" * 50)
