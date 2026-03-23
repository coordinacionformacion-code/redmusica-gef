// ══════════════════════════════════════════════
// GEF Red Músicas de Medellín
// Script: alertasTelegram.gs
// Descripción: Envía alertas automáticas al grupo de Telegram del equipo
//              - Tareas vencidas y próximas a vencer (desde Sheets)
//              - Casos escalados al coordinador (desde Notion)
//              - Resumen diario del estado del equipo
// Trigger: Diario a las 8:00am (configurado con configurarTriggerAlertas)
// ══════════════════════════════════════════════

// ── Configuración ──
const TELEGRAM_TOKEN   = "TU_TOKEN_DE_TELEGRAM";
const TELEGRAM_CHAT_ID = "TU_CHAT_ID_DEL_GRUPO";
const NOTION_TOKEN     = "TU_TOKEN_DE_NOTION";
const ID_BITACORA      = "TU_ID_BD_BITACORA";

const GESTIONES = [
  "G. Iniciación",
  "G. Canto y Movimiento",
  "G. Neurodiversidad",
  "G. Cuerdas",
  "G. Bronces y Percusión",
  "G. Vientos Maderas"
];

// ── Enviar mensaje a Telegram ──
function enviarTelegram(mensaje) {
  const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;
  const payload = {
    chat_id: TELEGRAM_CHAT_ID,
    text: mensaje,
    parse_mode: "HTML"
  };
  UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  });
}

// ── Alerta 1: Tareas vencidas y próximas en Sheets ──
function alertasTareasSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const en2dias = new Date(hoy);
  en2dias.setDate(en2dias.getDate() + 2);

  let vencidas = [];
  let proximas = [];

  GESTIONES.forEach(nombre => {
    const hoja = ss.getSheetByName(nombre);
    if (!hoja) return;
    const datos = hoja.getRange("A2:J51").getValues();
    datos.forEach(fila => {
      const tarea   = fila[1];
      const estado  = fila[4];
      const fechaLim = fila[6];
      if (!tarea || estado === "Listo" || !fechaLim) return;
      const fecha = new Date(fechaLim);
      fecha.setHours(0, 0, 0, 0);
      if (fecha < hoy) {
        vencidas.push({ gestion: nombre, tarea, fecha: Utilities.formatDate(fecha, "America/Bogota", "dd/MM/yyyy") });
      } else if (fecha <= en2dias) {
        proximas.push({ gestion: nombre, tarea, fecha: Utilities.formatDate(fecha, "America/Bogota", "dd/MM/yyyy") });
      }
    });
  });

  return { vencidas, proximas };
}

// ── Alerta 2: Casos escalados en Notion ──
function alertasNotion() {
  const url = `https://api.notion.com/v1/databases/${ID_BITACORA}/query`;
  const payload = {
    filter: {
      and: [
        { property: "Requiere Coordinador", checkbox: { equals: true } },
        { property: "Estado", select: { does_not_equal: "Cerrado" } }
      ]
    }
  };
  const response = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      "Authorization": `Bearer ${NOTION_TOKEN}`,
      "Notion-Version": "2022-06-28"
    },
    payload: JSON.stringify(payload)
  });
  const data = JSON.parse(response.getContentText());
  return (data.results || []).map(r => {
    const props = r.properties;
    return {
      titulo: props["Título"]?.title?.[0]?.plain_text || "Sin título",
      tipo:   props["Tipo de registro"]?.select?.name || "—",
      prior:  props["Prioridad"]?.select?.name || "—",
      gestor: props["Registrado por"]?.select?.name || "—",
    };
  });
}

// ── Resumen diario desde PANEL ──
function resumenDiario() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const panel = ss.getSheetByName("PANEL");
  if (!panel) return [];
  const datos = panel.getRange("A2:G7").getValues();
  return datos.filter(f => f[0]).map(f => ({
    gestion: f[0], total: f[1], pend: f[2], curso: f[3], vencidas: f[6]
  }));
}

// ── Función principal ──
function enviarAlertas() {
  const fecha = Utilities.formatDate(new Date(), "America/Bogota", "dd/MM/yyyy");
  let mensajes = [];

  const { vencidas, proximas } = alertasTareasSheets();

  if (vencidas.length > 0) {
    let msg = `🔴 <b>TAREAS VENCIDAS — ${fecha}</b>\n\n`;
    vencidas.forEach(t => { msg += `• <b>${t.gestion}</b>\n  ${t.tarea} (${t.fecha})\n`; });
    mensajes.push(msg);
  }

  if (proximas.length > 0) {
    let msg = `🟡 <b>TAREAS PRÓXIMAS A VENCER — ${fecha}</b>\n\n`;
    proximas.forEach(t => { msg += `• <b>${t.gestion}</b>\n  ${t.tarea} → vence ${t.fecha}\n`; });
    mensajes.push(msg);
  }

  const escalados = alertasNotion();
  if (escalados.length > 0) {
    let msg = `🚨 <b>CASOS ESCALADOS AL COORDINADOR — ${fecha}</b>\n\n`;
    escalados.forEach(e => { msg += `• [${e.tipo}] <b>${e.titulo}</b>\n  Prioridad: ${e.prior} · Gestor: ${e.gestor}\n`; });
    mensajes.push(msg);
  }

  const resumen = resumenDiario();
  if (resumen.length > 0) {
    let msg = `📊 <b>RESUMEN DIARIO GEF — ${fecha}</b>\n\n`;
    resumen.forEach(r => {
      const alerta = r.vencidas > 0 ? ` ⚠️ ${r.vencidas} vencida(s)` : "";
      msg += `• <b>${r.gestion}</b>: ${r.total} tareas · ${r.pend} pend · ${r.curso} en curso${alerta}\n`;
    });
    mensajes.push(msg);
  }

  if (mensajes.length === 0) {
    mensajes.push(`✅ <b>GEF Red Músicas — ${fecha}</b>\n\nTodo en orden. Sin alertas activas.`);
  }

  mensajes.forEach(m => {
    enviarTelegram(m);
    Utilities.sleep(500);
  });
}

// ── Configurar trigger diario a las 8am ──
function configurarTriggerAlertas() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "enviarAlertas") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("enviarAlertas")
    .timeBased()
    .everyDays(1)
    .atHour(8)
    .create();
  Logger.log("✅ Trigger de alertas configurado — se ejecutará diariamente a las 8am.");
}
