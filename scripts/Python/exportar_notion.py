"""
GEF Red Músicas de Medellín
Script: exportar_notion.py
Descripción: Extrae datos de todas las bases de datos de Notion
             y los exporta como archivos CSV en la carpeta SGR_PowerBI/.
             Estos CSVs alimentan el dashboard web publicado en Netlify.
Ejecutar: Cada vez que quieras actualizar el dashboard con datos frescos
Uso: python exportar_notion.py
"""

import requests
import pandas as pd
import os

# ── Configuración ──
TOKEN         = "TU_TOKEN_DE_NOTION"
ID_FORMADORES = "TU_ID_BD_FORMADORES"
ID_BITACORA   = "TU_ID_BD_BITACORA"
ID_VISITAS    = "TU_ID_BD_VISITAS"
ID_LUTHIERIA  = "TU_ID_BD_SOLICITUDES_LUTHERIA"
ID_REUNIONES  = "TU_ID_BD_REUNIONES"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

CARPETA = "SGR_PowerBI"

# ── Funciones auxiliares ──
def extraer_bd(db_id):
    """Extrae todos los registros de una base de datos con paginación."""
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
    return resultados

def get_prop(props, nombre, tipo):
    """Extrae el valor de una propiedad de Notion según su tipo."""
    prop = props.get(nombre, {})
    if not prop: return ""
    if tipo == "title":
        items = prop.get("title", [])
        return items[0]["plain_text"] if items else ""
    if tipo == "select":
        sel = prop.get("select")
        return sel["name"] if sel else ""
    if tipo == "checkbox":
        return prop.get("checkbox", False)
    if tipo == "date":
        date = prop.get("date")
        return date["start"] if date else ""
    if tipo == "relation":
        return len(prop.get("relation", []))
    if tipo == "number":
        return prop.get("number", 0) or 0
    if tipo == "url":
        return prop.get("url", "") or ""
    if tipo == "phone":
        return prop.get("phone_number", "") or ""
    if tipo == "email":
        return prop.get("email", "") or ""
    return ""

# ── Extracción por BD ──
if __name__ == "__main__":
    os.makedirs(CARPETA, exist_ok=True)

    print("=" * 50)
    print("EXPORTACIÓN NOTION → CSV")
    print("Red Músicas de Medellín — Sistema GEF")
    print("=" * 50)

    # Formadores
    print("\nExtrayendo Formadores...")
    formadores = extraer_bd(ID_FORMADORES)
    filas = []
    for r in formadores:
        p = r["properties"]
        filas.append({
            "Nombre":              get_prop(p, "Nombre", "title"),
            "Estado":              get_prop(p, "Estado", "select"),
            "Area":                get_prop(p, "Área", "select"),
            "Tipo de contrato":    get_prop(p, "Tipo de contrato", "select"),
            "Nivel de formacion":  get_prop(p, "Nivel de formación", "select"),
            "Situacion de riesgo": get_prop(p, "Situación de riesgo", "checkbox"),
            "Celular":             get_prop(p, "Celular", "phone"),
            "Email":               get_prop(p, "Email", "email"),
        })
    df_formadores = pd.DataFrame(filas)
    df_formadores.to_csv(f"{CARPETA}/formadores_crm.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_formadores)} formadores exportados")

    # Bitácora
    print("Extrayendo Bitácora...")
    registros = extraer_bd(ID_BITACORA)
    filas = []
    for r in registros:
        p = r["properties"]
        filas.append({
            "Titulo":               get_prop(p, "Título", "title"),
            "Tipo de registro":     get_prop(p, "Tipo de registro", "select"),
            "Estado":               get_prop(p, "Estado", "select"),
            "Prioridad":            get_prop(p, "Prioridad", "select"),
            "Fecha":                get_prop(p, "Fecha", "date"),
            "Registrado por":       get_prop(p, "Registrado por", "select"),
            "Requiere Coordinador": get_prop(p, "Requiere Coordinador", "checkbox"),
        })
    df_bitacora = pd.DataFrame(filas)
    if not df_bitacora.empty:
        df_bitacora["Fecha"] = pd.to_datetime(df_bitacora["Fecha"], errors="coerce")
        df_bitacora["Mes"] = df_bitacora["Fecha"].dt.strftime("%Y-%m")
    df_bitacora.to_csv(f"{CARPETA}/bitacora.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_bitacora)} registros exportados")

    # Visitas
    print("Extrayendo Visitas...")
    visitas = extraer_bd(ID_VISITAS)
    filas = []
    for r in visitas:
        p = r["properties"]
        filas.append({
            "Nombre":  get_prop(p, "Nombre", "title"),
            "Estado":  get_prop(p, "Estado", "select"),
            "Fecha":   get_prop(p, "Fecha y hora", "date"),
            "Gestor":  get_prop(p, "Gestor", "relation"),
            "Escuela": get_prop(p, "Escuela", "relation"),
        })
    df_visitas = pd.DataFrame(filas)
    df_visitas.to_csv(f"{CARPETA}/visitas.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_visitas)} visitas exportadas")

    # Luthería
    print("Extrayendo Luthería...")
    luthieria = extraer_bd(ID_LUTHIERIA)
    filas = []
    for r in luthieria:
        p = r["properties"]
        filas.append({
            "Registro":  get_prop(p, "Registro", "title"),
            "Semana":    get_prop(p, "Semana", "select"),
            "Gestión":   get_prop(p, "Gestión", "relation"),
            "Realizada": get_prop(p, "Realizada", "checkbox"),
            "Modalidad": get_prop(p, "Modalidad", "select"),
            "Jornada":   get_prop(p, "Jornada", "select"),
        })
    df_luthieria = pd.DataFrame(filas)
    df_luthieria.to_csv(f"{CARPETA}/luthieria.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_luthieria)} solicitudes exportadas")

    # Reuniones
    print("Extrayendo Reuniones...")
    reuniones = extraer_bd(ID_REUNIONES)
    filas = []
    for r in reuniones:
        p = r["properties"]
        filas.append({
            "Nombre":                 get_prop(p, "Nombre", "title"),
            "Tipo":                   get_prop(p, "Tipo", "select"),
            "Fecha":                  get_prop(p, "Fecha", "date"),
            "Estado":                 get_prop(p, "Estado", "select"),
            "Modalidad":              get_prop(p, "Modalidad", "select"),
            "Compromisos pendientes": get_prop(p, "Compromisos pendientes", "number"),
            "Requiere Coordinador":   get_prop(p, "Requiere Coordinador", "checkbox"),
        })
    df_reuniones = pd.DataFrame(filas)
    df_reuniones.to_csv(f"{CARPETA}/reuniones.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_reuniones)} reuniones exportadas")

    print("\n" + "=" * 50)
    print("EXPORTACIÓN COMPLETADA")
    print(f"  Archivos en: {CARPETA}/")
    print(f"    - formadores_crm.csv  ({len(df_formadores)} registros)")
    print(f"    - bitacora.csv        ({len(df_bitacora)} registros)")
    print(f"    - visitas.csv         ({len(df_visitas)} registros)")
    print(f"    - luthieria.csv       ({len(df_luthieria)} registros)")
    print(f"    - reuniones.csv       ({len(df_reuniones)} registros)")
    print("=" * 50)
    print("\nPróximo paso: sube la carpeta SGR_PowerBI/ junto con index.html a Netlify")
