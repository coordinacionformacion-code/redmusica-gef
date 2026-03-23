# 🎵 Sistema Operativo GEF — Red Músicas de Medellín

Sistema de gestión del Equipo de Formación de la Red Músicas de Medellín, construido sobre Google Workspace, Notion y herramientas gratuitas.

---

## 📋 ¿Qué es el sistema GEF?

El **Sistema Operativo GEF** centraliza la gestión del equipo de formación en una plataforma híbrida que integra:

- **Google Sheets** — gestión de tareas del equipo estratégico
- **Notion** — CRM de Artistas Formadores, bitácora, visitas, reuniones y Luthería
- **Google Calendar** — calendario compartido del equipo
- **Telegram** — alertas automáticas diarias
- **Netlify** — dashboard web en tiempo real

---

## 🗂️ Estructura del repositorio

```
redmusica-gef/
├── README.md                    # Este archivo
├── scripts/
│   ├── Apps Script/
│   │   ├── construirSGR.gs      # Crea la estructura del Google Sheets
│   │   ├── configurarPermisos.gs # Configura permisos por gestor
│   │   ├── alertasTelegram.gs   # Alertas automáticas a Telegram
│   │   └── sincronizarVisitas.gs # Sincroniza visitas con Google Calendar
│   └── Python/
│       ├── importar_sgr.py      # Importación inicial de formadores a Notion
│       ├── sincronizar_lutheria.py # Sincroniza Luthería desde Sheets a Notion
│       └── exportar_notion.py   # Exporta datos de Notion a CSV para el dashboard
├── dashboard/
│   └── index.html               # Dashboard web publicado en Netlify
└── docs/
    └── Guia_Sistema_GEF.pdf     # Guía del sistema para el equipo de gestión
```

---

## 🚀 Scripts Python

### Requisitos

```bash
pip install requests pandas
```

### 1. `importar_sgr.py`
Importación inicial de Artistas Formadores, Escuelas y Gestiones desde un CSV a Notion.

```bash
python importar_sgr.py
```

**Configura antes de ejecutar:**
- `TOKEN` — token de la integración de Notion
- `ID_GESTIONES`, `ID_ESCUELAS`, `ID_FORMADORES`, `ID_BITACORA` — IDs de las BDs en Notion
- `CSV_PATH` — ruta al archivo CSV con los formadores

### 2. `sincronizar_lutheria.py`
Sincroniza las solicitudes de Luthería desde el Google Sheets del equipo de luthiers hacia Notion. Detecta duplicados automáticamente.

```bash
python sincronizar_lutheria.py
```

**Ejecutar:** mensualmente cuando los luthiers actualicen su planilla.

### 3. `exportar_notion.py`
Extrae datos de todas las BDs de Notion y los exporta como archivos CSV en la carpeta `SGR_PowerBI/`. Estos CSVs alimentan el dashboard web.

```bash
python exportar_notion.py
```

**Archivos generados:**
- `SGR_PowerBI/formadores_crm.csv`
- `SGR_PowerBI/bitacora.csv`
- `SGR_PowerBI/visitas.csv`
- `SGR_PowerBI/luthieria.csv`
- `SGR_PowerBI/reuniones.csv`

---

## ⚙️ Scripts Google Apps Script

Se ejecutan desde **Extensiones → Apps Script** dentro del archivo Google Sheets `SGR — Seguimiento de Tareas`.

| Script | Función | Cuándo ejecutar |
|--------|---------|-----------------|
| `construirSGR.gs` | Crea las 6 pestañas de gestión + PANEL | Solo una vez al inicio |
| `configurarPermisos.gs` | Asigna permisos por gestor | Solo una vez al inicio |
| `alertasTelegram.gs` | Envía resumen diario a Telegram | Automático 8am (trigger) |
| `sincronizarVisitas.gs` | Sincroniza visitas de Notion a Google Calendar | Automático 11pm (trigger) |

---

## 🌐 Dashboard web

El dashboard está publicado en:

**[https://redmusicasgef.netlify.app/](https://redmusicasgef.netlify.app/)**

Para actualizar los datos:
1. Ejecuta `exportar_notion.py` — genera los CSVs actualizados
2. Sube la carpeta `dashboard/` junto con `SGR_PowerBI/` a Netlify

---

## 🔑 Variables de configuración

Todos los scripts usan estas variables que debes configurar con tus propios valores:

| Variable | Descripción |
|----------|-------------|
| `TOKEN` | Token de integración de Notion (`secret_...`) |
| `TELEGRAM_TOKEN` | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | ID del grupo de Telegram |
| `CALENDAR_ID` | ID del Google Calendar del equipo |
| `ID_*` | IDs de las bases de datos en Notion |

> ⚠️ **Importante:** No subas tokens ni credenciales reales al repositorio. Los valores en los scripts son de referencia — reemplázalos con los tuyos antes de ejecutar.

---

## 📱 Bases de datos en Notion

| BD | Contenido | Registros iniciales |
|----|-----------|---------------------|
| 🎯 Gestiones | 8 gestiones del equipo | 8 |
| 🏫 Escuelas y Agrupaciones | Escuelas y agrupaciones integradas | 40 |
| 👤 Artistas Formadores | Perfil completo de cada formador | 124 |
| 📋 Bitácora | Permisos, casos y situaciones de riesgo | Crece con el tiempo |
| 🗓️ Visitas a Procesos | Cronograma de visitas del equipo | Crece con el tiempo |
| 🔧 Solicitudes de Luthería | Intervenciones del equipo de luthiers | Sincronizado desde Sheets |
| 📅 Reuniones | Registro de reuniones con enlace al acta | Crece con el tiempo |

---

## 👥 Equipo

**Coordinador de Formación:** coordinacionformacion@redmusicasmedellin.co

**Gestiones:**
- G. Iniciación — Julio Cadavid
- G. Canto y Movimiento — Claudia Cano
- G. Neurodiversidad — Valentina Ramírez
- G. Cuerdas Frotadas y Pulsadas — Santiago Isaza
- G. Bronces y Percusión — Santiago García
- G. Vientos Maderas — Ehilin Peña

---

## 📄 Licencia

Proyecto interno — Red Músicas de Medellín 2026.
