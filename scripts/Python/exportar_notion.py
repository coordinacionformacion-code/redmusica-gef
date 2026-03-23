"""
GEF Red Músicas de Medellín
Script: exportar_notion.py v2
Descripción: Extrae datos de todas las bases de datos de Notion,
             exporta CSVs y los sube automáticamente a GitHub.
             Netlify detecta el cambio y republica el dashboard solo.
Ejecutar: Cada vez que quieras actualizar el dashboard
Uso: python exportar_notion.py
"""

import requests
import pandas as pd
import os
import subprocess
import shutil
from datetime import datetime

# ── Configuración Notion ──
TOKEN         = "TU_TOKEN_NOTION"
ID_FORMADORES = "TU_ID_BD_FORMADORES"
ID_DIRECTORES = "TU_ID_BD_DIRECTORES"
ID_BITACORA   = "TU_ID_BD_BITACORA"
ID_VISITAS    = "TU_ID_BD_VISITAS"
ID_LUTHIERIA  = "TU_ID_BD_LUTHIERIA"
ID_REUNIONES  = "TU_ID_BD_REUNIONES"

# ── Configuración GitHub ──
GITHUB_TOKEN  = "TU_TOKEN_GITHUB"
GITHUB_USER   = "TU_USUARIO_GITHUB"
GITHUB_REPO   = "redmusica-gef"
REPO_LOCAL    = r"C:\Users\Paulo\Documents\redmusica-gef"

HEADERS_NOTION = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

CARPETA_CSV = "SGR_PowerBI"

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

def get_prop(props, nombre, tipo):
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
    if tipo == "phone":
        return prop.get("phone_number", "") or ""
    if tipo == "email":
        return prop.get("email", "") or ""
    return ""

# ── Función GitHub push ──
def subir_a_github(carpeta_csv, repo_local):
    print("\nSubiendo archivos a GitHub...")

    dest = os.path.join(repo_local, "SGR_PowerBI")
    os.makedirs(dest, exist_ok=True)

    # Copiar CSVs al repositorio local
    for archivo in os.listdir(carpeta_csv):
        if archivo.endswith(".csv"):
            shutil.copy2(
                os.path.join(carpeta_csv, archivo),
                os.path.join(dest, archivo)
            )
            print(f"  Copiado: {archivo}")

    # Copiar index.html si existe en Downloads
    index_src = r"C:\Users\Paulo\Downloads\index.html"
    if os.path.exists(index_src):
        shutil.copy2(index_src, os.path.join(repo_local, "dashboard", "index.html"))
        print("  Copiado: index.html")

    # Configurar remote con token
    remote_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"

    def git(cmd, cwd=repo_local):
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, shell=True
        )
        if result.returncode != 0 and result.stderr:
            print(f"  Git: {result.stderr.strip()}")
        return result

    # Configurar remote con token
    git(f'git remote set-url origin {remote_url}')

    # Pull para sincronizar antes de push
    git("git pull origin main --rebase")

    # Stage, commit y push
    git("git add SGR_PowerBI/ dashboard/")
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    git(f'git commit -m "Actualización automática dashboard — {fecha}"')
    result = git("git push origin main")

    if result.returncode == 0:
        print("  ✅ Archivos subidos a GitHub correctamente")
        print("  🌐 Netlify republicará el dashboard en ~1 minuto")
        print(f"  → https://redmusicasgef.netlify.app/")
    else:
        print("  ⚠️  Error al subir a GitHub:")
        print(f"     {result.stderr}")

# ── Main ──
if __name__ == "__main__":
    os.makedirs(CARPETA_CSV, exist_ok=True)

    print("=" * 50)
    print("EXPORTACIÓN NOTION → CSV")
    print("Red Músicas de Medellín — Sistema GEF")
    print("=" * 50)

    # Formadores
    print("\nExtrayendo Formadores...")
    filas = []
    for r in extraer_bd(ID_FORMADORES):
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
    df_formadores.to_csv(f"{CARPETA_CSV}/formadores_crm.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_formadores)} formadores exportados")

    # Directores
    print("Extrayendo Directores...")
    filas = []
    for r in extraer_bd(ID_DIRECTORES):
        p = r["properties"]
        filas.append({
            "Nombre":              get_prop(p, "Nombre", "title"),
            "Estado":              get_prop(p, "Estado", "select"),
            "Tipo de contrato":    get_prop(p, "Tipo de contrato", "select"),
            "Nivel de formacion":  get_prop(p, "Nivel de formación", "select"),
            "Tipologia":           get_prop(p, "Tipología", "select"),
            "Situacion de riesgo": get_prop(p, "Situación de riesgo", "checkbox"),
            "Celular":             get_prop(p, "Celular", "phone"),
            "Email":               get_prop(p, "Email", "email"),
            "Escuelas":            get_prop(p, "Escuelas o agrupaciones integradas", "relation"),
            "Gestion":             get_prop(p, "Gestión", "relation"),
        })
    df_directores = pd.DataFrame(filas)
    df_directores.to_csv(f"{CARPETA_CSV}/directores.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_directores)} directores exportados")

    # Bitácora
    print("Extrayendo Bitácora...")
    filas = []
    for r in extraer_bd(ID_BITACORA):
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
    df_bitacora.to_csv(f"{CARPETA_CSV}/bitacora.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_bitacora)} registros exportados")

    # Visitas
    print("Extrayendo Visitas...")
    filas = []
    for r in extraer_bd(ID_VISITAS):
        p = r["properties"]
        filas.append({
            "Nombre":  get_prop(p, "Nombre", "title"),
            "Estado":  get_prop(p, "Estado", "select"),
            "Fecha":   get_prop(p, "Fecha y hora", "date"),
            "Gestor":  get_prop(p, "Gestor", "relation"),
            "Escuela": get_prop(p, "Escuela", "relation"),
        })
    df_visitas = pd.DataFrame(filas)
    df_visitas.to_csv(f"{CARPETA_CSV}/visitas.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_visitas)} visitas exportadas")

    # Luthería
    print("Extrayendo Luthería...")
    filas = []
    for r in extraer_bd(ID_LUTHIERIA):
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
    df_luthieria.to_csv(f"{CARPETA_CSV}/luthieria.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_luthieria)} solicitudes exportadas")

    # Reuniones
    print("Extrayendo Reuniones...")
    filas = []
    for r in extraer_bd(ID_REUNIONES):
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
    df_reuniones.to_csv(f"{CARPETA_CSV}/reuniones.csv", index=False, encoding="utf-8-sig")
    print(f"  {len(df_reuniones)} reuniones exportadas")

    print("\n" + "=" * 50)
    print("EXPORTACIÓN COMPLETADA")
    print(f"  - formadores_crm.csv  ({len(df_formadores)} registros)")
    print(f"  - directores.csv      ({len(df_directores)} registros)")
    print(f"  - bitacora.csv        ({len(df_bitacora)} registros)")
    print(f"  - visitas.csv         ({len(df_visitas)} registros)")
    print(f"  - luthieria.csv       ({len(df_luthieria)} registros)")
    print(f"  - reuniones.csv       ({len(df_reuniones)} registros)")
    print("=" * 50)

    # Subir a GitHub → Netlify republica automáticamente
    subir_a_github(CARPETA_CSV, REPO_LOCAL)
