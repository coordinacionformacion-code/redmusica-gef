"""
GEF Red Músicas de Medellín
Script: sincronizar_lutheria.py v3
Descripción: Sincroniza TODOS los registros de cada pestaña mensual
             del Sheets de Luthería con la BD Solicitudes Luthería en Notion.
             Sin filtros — todos los registros son importados.
             Cada pestaña (Febrero, Marzo, Abril...) asigna el campo Mes
             automáticamente según el nombre de la pestaña.
Uso: python sincronizar_lutheria.py
"""

import requests
import gspread
from google.oauth2.service_account import Credentials

# ── Configuración ──
NOTION_TOKEN     = "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"
SHEETS_ID        = "1hl9O87x7UsSo--jHKINa5dLIadysVmDM87yelpHD6yM"
ID_LUTHIERIA     = "32b41296-4074-8082-bf2c-000b9379960e"
ID_GESTIONES_BD  = "32a41296-4074-80b7-9bd9-000b46cf4fd5"
ID_LUTHIERS_BD   = "32b41296-4074-8091-bf03-000b35146f15"
CREDENTIALS_FILE = "credentials.json"

MESES_VALIDOS = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ── Funciones Notion ──
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

def get_titulo(props, campo):
    items = props.get(campo, {}).get("title", [])
    return items[0]["plain_text"].strip() if items else ""

def cargar_gestiones():
    registros = extraer_bd(ID_GESTIONES_BD)
    mapa = {}
    for r in registros:
        for campo in ["Gestión", "Name", "Nombre"]:
            titulo = get_titulo(r["properties"], campo)
            if titulo:
                mapa[titulo.strip()] = r["id"]
                break
    print(f"  Gestiones cargadas: {list(mapa.keys())}")
    return mapa

def cargar_luthiers():
    registros = extraer_bd(ID_LUTHIERS_BD)
    mapa = {}
    for r in registros:
        for campo in ["Nombre", "Name", "Luthier", "Registro"]:
            titulo = get_titulo(r["properties"], campo)
            if titulo:
                mapa[titulo.upper().strip()] = r["id"]
                break
    print(f"  Luthiers cargados: {list(mapa.keys())}")
    return mapa

def cargar_registros_existentes():
    registros = extraer_bd(ID_LUTHIERIA)
    existentes = set()
    for r in registros:
        titulo = get_titulo(r["properties"], "Registro")
        if titulo:
            existentes.add(titulo)
    return existentes

def crear_registro_notion(fila, mes, num_fila, gestiones_map, luthiers_map):
    semana    = str(fila.get("SEMANA", "")).strip()
    gestion   = str(fila.get("GESTIÓN", "")).strip()
    luthier   = str(fila.get("LUTHIER", "")).strip().upper()
    dia       = str(fila.get("DÍA", "")).strip()
    jornada   = str(fila.get("JORNADA", "")).strip()
    tipo      = str(fila.get("TIPO DE ESCUELA O AGRUPACIÓN INTEGRADA", "")).strip()
    escuela   = str(fila.get("ESCUELA DE MÚSICA O AGRUPACIÓN INTEGRADA", "")).strip()
    modalidad = str(fila.get("MODALIDAD", "")).strip()
    obs       = str(fila.get("OBSERVACIÓN", "")).strip()
    realizada = str(fila.get("REALIZADA", "FALSE")).strip().upper() == "TRUE"

    # Construir título único — incluye número de fila para evitar duplicados en filas vacías
    partes_titulo = [mes, f"F{num_fila:03d}"]
    if semana: partes_titulo.append(semana)
    if gestion: partes_titulo.append(gestion)
    if dia: partes_titulo.append(dia)
    if jornada: partes_titulo.append(jornada)
    if escuela: partes_titulo.append(escuela)
    titulo = " — ".join(partes_titulo)

    props = {
        "Registro":    {"title": [{"text": {"content": titulo[:200]}}]},
        "Mes":         {"select": {"name": mes}},
        "Semana":      {"rich_text": [{"text": {"content": semana}}]},
        "Observación": {"rich_text": [{"text": {"content": obs[:2000]}}]},
        "Realizada":   {"checkbox": realizada},
    }

    # Día
    if dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]:
        props["Día"] = {"select": {"name": dia}}

    # Jornada
    if jornada in ["Mañana", "Tarde", "Noche"]:
        props["Jornada"] = {"select": {"name": jornada}}

    # Modalidad
    if modalidad in ["Presencial Escuela", "Presencial Equipamiento", "Taller"]:
        props["Modalidad"] = {"select": {"name": modalidad}}

    # Tipo de Escuela
    tipos_validos = ["Agrupación Integrada", "Sinfónica", "Enfoques Alternativos", "Cuerdas Frotadas", "Vientos y Percusión"]
    if tipo in tipos_validos:
        props["Tipo de Escuela o Agrupación Integrada"] = {"select": {"name": tipo}}

    # Relación Gestión
    if gestion and gestion in gestiones_map:
        props["Gestión"] = {"relation": [{"id": gestiones_map[gestion]}]}

    # Relación Luthier — exacta o parcial
    if luthier:
        if luthier in luthiers_map:
            props["Luthier"] = {"relation": [{"id": luthiers_map[luthier]}]}
        else:
            for key in luthiers_map:
                if luthier in key or key in luthier:
                    props["Luthier"] = {"relation": [{"id": luthiers_map[key]}]}
                    break

    return titulo, props

def sincronizar_pestaña(hoja, mes, gestiones_map, luthiers_map, existentes):
    # Leer TODOS los valores incluyendo filas vacías
    todos_los_valores = hoja.get_all_values()
    if not todos_los_valores:
        return 0, 0

    encabezados = todos_los_valores[0]
    creados = 0
    omitidos = 0

    for idx, fila_raw in enumerate(todos_los_valores[1:], start=2):
        # Mapear fila a diccionario usando encabezados
        fila = {}
        for i, col in enumerate(encabezados):
            fila[col.strip()] = fila_raw[i] if i < len(fila_raw) else ""

        titulo, props = crear_registro_notion(fila, mes, idx, gestiones_map, luthiers_map)

        # Evitar duplicados
        if titulo in existentes:
            omitidos += 1
            continue

        payload = {
            "parent": {"database_id": ID_LUTHIERIA},
            "properties": props
        }
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS_NOTION,
            json=payload
        )
        if r.status_code == 200:
            existentes.add(titulo)
            creados += 1
        else:
            print(f"    ⚠️  Error fila {idx}: {r.status_code} — {r.text[:100]}")

    return creados, omitidos

# ── Main ──
if __name__ == "__main__":
    print("=" * 55)
    print("SINCRONIZACIÓN LUTHERÍA — Red Músicas de Medellín")
    print("Modo: TODOS los registros sin filtros")
    print("=" * 55)

    print("\nConectando con Google Sheets...")
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEETS_ID)

    print("Cargando datos de Notion...")
    gestiones_map = cargar_gestiones()
    luthiers_map  = cargar_luthiers()
    existentes    = cargar_registros_existentes()
    print(f"  Registros existentes en Notion: {len(existentes)}")

    print("\nSincronizando pestañas...")
    total_creados  = 0
    total_omitidos = 0

    for hoja in spreadsheet.worksheets():
        nombre = hoja.title.strip()
        mes = None
        for m in MESES_VALIDOS:
            if nombre.lower() == m.lower():
                mes = m
                break

        if not mes:
            print(f"  Pestaña '{nombre}' — omitida (no es mes válido)")
            continue

        print(f"\n  📅 Procesando: {nombre} → Mes = {mes}")
        creados, omitidos = sincronizar_pestaña(
            hoja, mes, gestiones_map, luthiers_map, existentes
        )
        print(f"     ✅ Creados: {creados} | Duplicados omitidos: {omitidos}")
        total_creados  += creados
        total_omitidos += omitidos

    print("\n" + "=" * 55)
    print(f"SINCRONIZACIÓN COMPLETADA")
    print(f"  Total creados:   {total_creados}")
    print(f"  Total omitidos:  {total_omitidos}")
    print("=" * 55)
