import requests
import pandas as pd
import time

# ══════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════
TOKEN        = "TU_TOKEN_NOTION"
ID_GESTIONES = "TU_ID_BD_GESTIONES"
ID_ESCUELAS  = "TU_ID_BD_ESCUELAS"
ID_FORMADORES= "TU_ID_BD_FORMADORES"
ID_BITACORA  = "TU_ID_BD_BITACORA"
CSV_PATH     = "TU_RUTA_CSV_FORMADORES"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ══════════════════════════════════════════════
# FUNCIÓN AUXILIAR
# ══════════════════════════════════════════════
def crear_pagina(db_id, propiedades):
    url = "https://api.notion.com/v1/pages"
    body = {
        "parent": {"database_id": db_id},
        "properties": propiedades
    }
    r = requests.post(url, headers=HEADERS, json=body)
    if r.status_code != 200:
        print(f"  ⚠ Error: {r.status_code} — {r.json().get('message','')}")
        return None
    return r.json()["id"]

def limpiar_celular(valor):
    # Toma solo el primer número si hay varios separados por salto de línea
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().split("\n")[0].strip()
    # Elimina caracteres no numéricos excepto +
    resultado = ""
    for c in texto:
        if c.isdigit() or c == "+":
            resultado += c
    return resultado

# ══════════════════════════════════════════════
# BLOQUE 1 — Gestiones
# ══════════════════════════════════════════════
print("\n🎯 Cargando Gestiones...")
gestiones_lista = [
    "Iniciación", "Canto y Movimiento", "Neurodiversidad",
    "Cuerdas Frotadas y Pulsadas", "Bronces y Percusión",
    "Maderas", "Conjuntos Instrumentales", "POR DEFINIR"
]
mapa_gestiones = {}
for g in gestiones_lista:
    props = {"Nombre": {"title": [{"text": {"content": g}}]}}
    page_id = crear_pagina(ID_GESTIONES, props)
    if page_id:
        mapa_gestiones[g] = page_id
        print(f"  ✓ {g}")
    time.sleep(0.35)

# ══════════════════════════════════════════════
# BLOQUE 2 — Escuelas
# ══════════════════════════════════════════════
print("\n🏫 Cargando Escuelas y Agrupaciones...")
df = pd.read_csv(CSV_PATH)
escuelas_df = df.groupby("ESCUELA DE MÚSICA").agg({
    "ZONA": "first",
    "TIPOLOGÍA": "first",
    "DIRECTOR(A)": "first"
}).reset_index()

mapa_escuelas = {}
for _, row in escuelas_df.iterrows():
    nombre    = str(row["ESCUELA DE MÚSICA"]).strip()
    zona      = str(row["ZONA"]).strip() if pd.notna(row["ZONA"]) else ""
    tipologia = str(row["TIPOLOGÍA"]).strip() if pd.notna(row["TIPOLOGÍA"]) else ""
    director  = str(row["DIRECTOR(A)"]).strip() if pd.notna(row["DIRECTOR(A)"]) else ""

    props = {
        "Nombre": {"title": [{"text": {"content": nombre}}]},
    }
    if zona:
        props["Zona"] = {"select": {"name": zona}}
    if tipologia:
        props["Tipología"] = {"select": {"name": tipologia}}
    if director:
        props["Director(a)"] = {"rich_text": [{"text": {"content": director}}]}

    page_id = crear_pagina(ID_ESCUELAS, props)
    if page_id:
        mapa_escuelas[nombre] = page_id
        print(f"  ✓ {nombre}")
    time.sleep(0.35)

# ══════════════════════════════════════════════
# BLOQUE 3 — Artistas Formadores
# ══════════════════════════════════════════════
print("\n👤 Cargando Artistas Formadores...")

cols = ["FORMADOR(A)","ÁREA/SUBÁREA","CELULAR","CORREO","GESTIÓN","TIPO CONTRATO","NIVEL DE FORMACIÓN"]
formadores_df = df[cols].drop_duplicates(subset=["FORMADOR(A)"]).reset_index(drop=True)

relacion_escuelas = df.groupby("FORMADOR(A)")["ESCUELA DE MÚSICA"].apply(
    lambda x: list(x.unique())
).to_dict()

mapa_formadores = {}
import requests
import pandas as pd
import time

# ══════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════
TOKEN = "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"

ID_GESTIONES  = "32a41296407480d6b790cc693a7f57d9"
ID_ESCUELAS   = "32a4129640748079825cf524a9b87382"
ID_FORMADORES = "32a41296407480ee8e8bccf5de59dc11"
ID_BITACORA   = "32a4129640748095b87ff45d081bc4bc"

CSV_PATH = "formadores.csv"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ══════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════
def crear_pagina(db_id, propiedades):
    url = "https://api.notion.com/v1/pages"
    body = {"parent": {"database_id": db_id}, "properties": propiedades}
    r = requests.post(url, headers=HEADERS, json=body)
    if r.status_code != 200:
        print(f"  Error: {r.status_code} — {r.json().get('message','')}")
        return None
    return r.json()["id"]

def limpiar_celular(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().split("\n")[0].strip()
    return "".join(c for c in texto if c.isdigit() or c == "+")

def limpiar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()

# ══════════════════════════════════════════════
# BLOQUE 1 — Gestiones
# ══════════════════════════════════════════════
print("\n🎯 Cargando Gestiones...")
gestiones_lista = [
    "Iniciación", "Canto y Movimiento", "Neurodiversidad",
    "Cuerdas Frotadas y Pulsadas", "Bronces y Percusión",
    "Maderas", "Conjuntos Instrumentales", "POR DEFINIR"
]
mapa_gestiones = {}
for g in gestiones_lista:
    props = {"Nombre": {"title": [{"text": {"content": g}}]}}
    page_id = crear_pagina(ID_GESTIONES, props)
    if page_id:
        mapa_gestiones[g] = page_id
        print(f"  ✓ {g}")
    time.sleep(0.35)

# ══════════════════════════════════════════════
# BLOQUE 2 — Escuelas
# ══════════════════════════════════════════════
print("\n🏫 Cargando Escuelas y Agrupaciones...")
df = pd.read_csv(CSV_PATH)

escuelas_df = df.groupby("ESCUELA DE MÚSICA").agg({
    "ZONA": "first",
    "TIPOLOGÍA": "first",
    "DIRECTOR(A)": "first"
}).reset_index()

mapa_escuelas = {}
for _, row in escuelas_df.iterrows():
    nombre    = limpiar_texto(row["ESCUELA DE MÚSICA"])
    zona      = limpiar_texto(row["ZONA"])
    tipologia = limpiar_texto(row["TIPOLOGÍA"])
    director  = limpiar_texto(row["DIRECTOR(A)"])

    props = {"Nombre": {"title": [{"text": {"content": nombre}}]}}
    if zona:
        props["Zona"] = {"select": {"name": zona}}
    if tipologia:
        props["Tipología"] = {"select": {"name": tipologia}}
    if director:
        props["Director"] = {"rich_text": [{"text": {"content": director}}]}

    page_id = crear_pagina(ID_ESCUELAS, props)
    if page_id:
        mapa_escuelas[nombre] = page_id
        print(f"  ✓ {nombre}")
    time.sleep(0.35)

# ══════════════════════════════════════════════
# BLOQUE 3 — Artistas Formadores
# ══════════════════════════════════════════════
print("\n👤 Cargando Artistas Formadores...")

cols = ["FORMADOR(A)","ÁREA/SUBÁREA","CELULAR","CORREO","GESTIÓN","TIPO CONTRATO","NIVEL DE FORMACIÓN"]
formadores_df = df[cols].drop_duplicates(subset=["FORMADOR(A)"]).reset_index(drop=True)

# Elimina filas con nombre vacío o nan
formadores_df = formadores_df[formadores_df["FORMADOR(A)"].notna()]
formadores_df = formadores_df[formadores_df["FORMADOR(A)"].str.strip() != ""]
formadores_df = formadores_df[formadores_df["FORMADOR(A)"].str.strip().str.lower() != "nan"]

# Relación formador -> escuelas
relacion_escuelas = df.groupby("FORMADOR(A)")["ESCUELA DE MÚSICA"].apply(
    lambda x: list(x.unique())
).to_dict()

mapa_formadores = {}
vistos = set()  # para evitar duplicados

for _, row in formadores_df.iterrows():
    nombre = limpiar_texto(row["FORMADOR(A)"])

    # Evita duplicados
    if nombre in vistos:
        print(f"  → Duplicado omitido: {nombre}")
        continue
    vistos.add(nombre)

    area     = limpiar_texto(row["ÁREA/SUBÁREA"])
    celular  = limpiar_celular(row["CELULAR"])
    correo   = limpiar_texto(row["CORREO"])
    gestion  = limpiar_texto(row["GESTIÓN"])
    contrato = limpiar_texto(row["TIPO CONTRATO"])
    nivel    = limpiar_texto(row["NIVEL DE FORMACIÓN"])

    props = {"Nombre": {"title": [{"text": {"content": nombre}}]}}

    if area:
        props["Área"] = {"select": {"name": area}}
    if celular:
        props["Celular"] = {"phone_number": celular}
    if correo:
        props["Email"] = {"email": correo}
    if contrato:
        props["Tipo de contrato"] = {"select": {"name": contrato}}
    if nivel:
        props["Nivel de formación"] = {"select": {"name": nivel}}
    if gestion and gestion in mapa_gestiones:
        props["Gestión"] = {"relation": [{"id": mapa_gestiones[gestion]}]}

    # Relación con Escuelas
    escuelas_del_formador = relacion_escuelas.get(nombre, [])
    ids_escuelas = [{"id": mapa_escuelas[e]} for e in escuelas_del_formador if e in mapa_escuelas]
    if ids_escuelas:
        props["Escuelas"] = {"relation": ids_escuelas}

    props["Estado"] = {"select": {"name": "Activo"}}

    page_id = crear_pagina(ID_FORMADORES, props)
    if page_id:
        mapa_formadores[nombre] = page_id
        print(f"  ✓ {nombre}")
    time.sleep(0.35)

# ══════════════════════════════════════════════
# RESUMEN
# ══════════════════════════════════════════════
print("\n" + "="*50)
print("IMPORTACION COMPLETADA")
print(f"  Gestiones cargadas:  {len(mapa_gestiones)}")
print(f"  Escuelas cargadas:   {len(mapa_escuelas)}")
print(f"  Formadores cargados: {len(mapa_formadores)}")
print("="*50)