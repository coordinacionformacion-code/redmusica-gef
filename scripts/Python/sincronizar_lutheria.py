"""
GEF Red Músicas de Medellín
Script: sincronizar_lutheria.py v5
Descripción: Sincroniza TODOS los registros del Sheets de Luthería
             con la BD Solicitudes Luthería en Notion via URL CSV pública.
             Una sola URL — lee todas las pestañas.
             Sin filtros — todos los registros son importados.
             El mes se asigna según la pestaña de origen.
Uso: python sincronizar_lutheria.py
"""

import requests
import csv
import io

# ── Configuración ──
NOTION_TOKEN    = "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"
ID_LUTHIERIA    = "32b41296407480d2a569e453ad92ca49"
ID_GESTIONES_BD = "32a41296407480d6b790cc693a7f57d9"
ID_ESCUELAS_BD  = "32a41296407480bda75a000b7617a3de"

# URL base del Sheets publicado — el GID identifica cada pestaña
SHEETS_BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTtxMIHX47El9s0k2FAZo9sfgydMylY7cuGEI6_Yvu4ZeRtY21ffkz-D9pIU9uirtda241SSbYhCHN5/pub"

# Pestañas — añadir GID de cada mes nuevo aquí
PESTANAS = {
    "Febrero": "210158856",
    "Marzo":   "1216569413",
    "Abril":   "1718498447",
    # Agregar nuevos meses aquí:
    # "Mayo": "GID_MAYO",
}

HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def extraer_bd(db_id):
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
    return resultados

def get_titulo(props, *campos):
    for campo in campos:
        items = props.get(campo, {}).get("title", [])
        if items:
            return items[0]["plain_text"].strip()
    return ""

def cargar_gestiones():
    registros = extraer_bd(ID_GESTIONES_BD)
    mapa = {}
    for r in registros:
        titulo = get_titulo(r["properties"], "Gestión", "Name", "Nombre")
        if titulo:
            mapa[titulo.strip()] = r["id"]
    print(f"  Gestiones cargadas: {list(mapa.keys())}")
    return mapa

def cargar_escuelas():
    registros = extraer_bd(ID_ESCUELAS_BD)
    mapa = {}
    for r in registros:
        titulo = get_titulo(r["properties"], "Nombre", "Name", "Escuela")
        if titulo:
            mapa[titulo.strip()] = r["id"]
    print(f"  Escuelas cargadas: {len(mapa)}")
    return mapa

def cargar_existentes():
    registros = extraer_bd(ID_LUTHIERIA)
    existentes = set()
    for r in registros:
        titulo = get_titulo(r["properties"], "Registro")
        if titulo:
            existentes.add(titulo)
    return existentes

def leer_csv(gid):
    url = f"{SHEETS_BASE_URL}?gid={gid}&single=true&output=csv"
    r = requests.get(url)
    r.encoding = "utf-8"
    reader = csv.DictReader(io.StringIO(r.text))
    return list(reader)

def crear_props(fila, mes, num_fila, gestiones_map, escuelas_map):
    semana    = str(fila.get("SEMANA", "")).strip()
    gestion   = str(fila.get("GESTIÓN", "")).strip()
    luthier   = str(fila.get("LUTHIER", "")).strip()
    dia       = str(fila.get("DÍA", "")).strip()
    jornada   = str(fila.get("JORNADA", "")).strip()
    tipo      = str(fila.get("TIPO DE ESCUELA O AGRUPACIÓN INTEGRADA", "")).strip()
    escuela   = str(fila.get("ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA", "")).strip()
    modalidad = str(fila.get("MODALIDAD", "")).strip()
    obs       = str(fila.get("OBSERVACIÓN", "")).strip()
    realizada = str(fila.get("REALIZADA", "FALSE")).strip().upper() == "TRUE"

    # Título único con número de fila
    partes = [mes, f"F{num_fila:03d}"]
    if semana:  partes.append(semana)
    if gestion: partes.append(gestion)
    if luthier: partes.append(luthier)
    if dia:     partes.append(dia)
    if escuela: partes.append(escuela)
    titulo = " — ".join(partes)

    props = {
        "Registro":    {"title": [{"text": {"content": titulo[:200]}}]},
        "Mes":         {"select": {"name": mes}},
        "Semana":      {"rich_text": [{"text": {"content": semana}}]},
        "Observación": {"rich_text": [{"text": {"content": obs[:2000]}}]},
        "Realizada":   {"checkbox": realizada},
    }

    if dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]:
        props["Día"] = {"select": {"name": dia}}
    if jornada in ["Mañana", "Tarde", "Noche"]:
        props["Jornada"] = {"select": {"name": jornada}}
    if modalidad in ["Presencial Escuela", "Presencial Equipamiento", "Taller"]:
        props["Modalidad"] = {"select": {"name": modalidad}}
    tipos_validos = ["Agrupación Integrada", "Sinfónica", "Enfoques Alternativos",
                     "Cuerdas Frotadas", "Vientos y Percusión"]
    if tipo in tipos_validos:
        props["Tipo de Escuela o Agrupación Integrada"] = {"select": {"name": tipo}}
    if gestion and gestion in gestiones_map:
        props["Gestión"] = {"relation": [{"id": gestiones_map[gestion]}]}

    # Relación Escuela de Música o Agrupación Integrada
    if escuela and escuela in escuelas_map:
        props["Escuela de Música o Agrupación Integrada"] = {"relation": [{"id": escuelas_map[escuela]}]}
    elif escuela:
        # Buscar coincidencia parcial
        for key in escuelas_map:
            if escuela.lower() in key.lower() or key.lower() in escuela.lower():
                props["Escuela de Música o Agrupación Integrada"] = {"relation": [{"id": escuelas_map[key]}]}
                break

    return titulo, props

def sincronizar_mes(mes, gid, gestiones_map, escuelas_map, existentes):
    print(f"\n  📅 Procesando: {mes}")
    filas = leer_csv(gid)
    creados = 0
    omitidos = 0

    for idx, fila in enumerate(filas, start=2):
        titulo, props = crear_props(fila, mes, idx, gestiones_map, escuelas_map)
        if titulo in existentes:
            omitidos += 1
            continue
        payload = {
            "parent": {"database_id": ID_LUTHIERIA},
            "properties": props
        }
        r = requests.post("https://api.notion.com/v1/pages",
                          headers=HEADERS_NOTION, json=payload)
        if r.status_code == 200:
            existentes.add(titulo)
            creados += 1
        else:
            print(f"    ⚠️  Error fila {idx}: {r.status_code} — {r.text[:100]}")

    print(f"     ✅ Creados: {creados} | Duplicados omitidos: {omitidos}")
    return creados, omitidos

if __name__ == "__main__":
    print("=" * 55)
    print("SINCRONIZACIÓN LUTHERÍA — Red Músicas de Medellín")
    print("Modo: TODOS los registros sin filtros")
    print("=" * 55)

    print("\nCargando datos de Notion...")
    gestiones_map = cargar_gestiones()
    escuelas_map  = cargar_escuelas()
    existentes    = cargar_existentes()
    print(f"  Registros existentes en Notion: {len(existentes)}")

    total_creados = 0
    total_omitidos = 0

    for mes, gid in PESTANAS.items():
        if gid == "PENDIENTE":
            print(f"\n  ⚠️  {mes} — GID pendiente de configurar, omitida")
            continue
        c, o = sincronizar_mes(mes, gid, gestiones_map, escuelas_map, existentes)
        total_creados  += c
        total_omitidos += o

    print("\n" + "=" * 55)
    print(f"SINCRONIZACIÓN COMPLETADA")
    print(f"  Total creados:   {total_creados}")
    print(f"  Total omitidos:  {total_omitidos}")
    print("=" * 55)
