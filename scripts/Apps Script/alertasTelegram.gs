// ══════════════════════════════════════════════
// GEF Red Músicas de Medellín — Código.gs
// Versión completa — incluye todos los scripts
// ══════════════════════════════════════════════

// ── Configuración global ──
const TELEGRAM_TOKEN   = "TU_TOKEN_TELEGRAM";
const TELEGRAM_CHAT_ID = "TU_CHAT_ID_GRUPO";
const NOTION_TOKEN     = "TU_TOKEN_NOTION";
const ID_BITACORA   = "TU_ID_BD_BITACORA";
const ID_VISITAS    = "TU_ID_BD_VISITAS";
const ID_LUTHIERIA  = "TU_ID_BD_LUTHIERIA";
const ID_REUNIONES  = "TU_ID_BD_REUNIONES";
const ID_FORMADORES = "TU_ID_BD_FORMADORES";
const CALENDAR_ID   = "TU_ID_GOOGLE_CALENDAR";

const GESTIONES = [
  "G. Iniciación", "G. Canto y Movimiento", "G. Neurodiversidad",
  "G. Cuerdas", "G. Bronces y Percusión", "G. Vientos Maderas"
];

// ══════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════

function enviarTelegram(mensaje) {
  const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;
  UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: mensaje,
      parse_mode: "HTML"
    })
  });
  Utilities.sleep(600);
}

function consultarNotion(dbId, filtro) {
  const url = `https://api.notion.com/v1/databases/${dbId}/query`;
  const payload = filtro ? { filter: filtro } : {};
  const r = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      "Authorization": `Bearer ${NOTION_TOKEN}`,
      "Notion-Version": "2022-06-28"
    },
    payload: JSON.stringify(payload)
  });
  return JSON.parse(r.getContentText()).results || [];
}

function fmt(fecha) {
  return Utilities.formatDate(new Date(fecha), "America/Bogota", "dd/MM/yyyy");
}

function esHabil() {
  const dia = new Date().getDay();
  return dia >= 1 && dia <= 6; // Lunes a Sábado
}

// ══════════════════════════════════════════════
// ALERTAS TELEGRAM — 6 mensajes diarios
// ══════════════════════════════════════════════

function mensajeEncabezado() {
  const dias = ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"];
  const diaNom = dias[new Date().getDay()];
  const fecha = Utilities.formatDate(new Date(), "America/Bogota", "dd/MM/yyyy");
  return `🎵 <b>GEF — Red Músicas de Medellín</b>\n📅 ${diaNom}, ${fecha}\n\nAquí está tu resumen diario del sistema. Se enviarán 5 reportes a continuación.`;
}

function mensajeTareas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hoy = new Date(); hoy.setHours(0,0,0,0);
  const en3dias = new Date(hoy); en3dias.setDate(en3dias.getDate() + 3);
  let vencidas = [], proximas = [], enCurso = 0, pendientes = 0;

  GESTIONES.forEach(nombre => {
    const hoja = ss.getSheetByName(nombre);
    if (!hoja) return;
    const datos = hoja.getRange("A2:J51").getValues();
    datos.forEach(fila => {
      const tarea = fila[1], estado = fila[4], fechaLim = fila[6];
      if (!tarea || estado === "Listo") return;
      if (estado === "En curso") enCurso++;
      if (estado === "Pendiente") pendientes++;
      if (!fechaLim) return;
      const fecha = new Date(fechaLim); fecha.setHours(0,0,0,0);
      if (fecha < hoy) {
        vencidas.push({ gestion: nombre.replace("G. ",""), tarea, fecha: fmt(fecha) });
      } else if (fecha <= en3dias) {
        proximas.push({ gestion: nombre.replace("G. ",""), tarea, fecha: fmt(fecha) });
      }
    });
  });

  let msg = `📋 <b>TAREAS DEL EQUIPO</b>\nEn curso: ${enCurso}  ·  Pendientes: ${pendientes}\n\n`;
  if (vencidas.length > 0) {
    msg += `🔴 <b>Vencidas (${vencidas.length})</b>\n`;
    vencidas.forEach(t => { msg += `• ${t.gestion}: ${t.tarea} (${t.fecha})\n`; });
    msg += "\n";
  }
  if (proximas.length > 0) {
    msg += `🟡 <b>Vencen en 3 días (${proximas.length})</b>\n`;
    proximas.forEach(t => { msg += `• ${t.gestion}: ${t.tarea} → ${t.fecha}\n`; });
  }
  if (vencidas.length === 0 && proximas.length === 0) {
    msg += `✅ Sin tareas vencidas ni próximas a vencer.`;
  }
  return msg;
}

function mensajeVisitasAlerta() {
  const hoy = new Date(); hoy.setHours(0,0,0,0);
  const en7dias = new Date(hoy); en7dias.setDate(en7dias.getDate() + 7);
  const visitas = consultarNotion(ID_VISITAS, {
    property: "Estado", select: { equals: "Programada" }
  });
  const proximas = visitas.filter(v => {
    const fecha = v.properties["Fecha y hora"]?.date?.start;
    if (!fecha) return false;
    const f = new Date(fecha); f.setHours(0,0,0,0);
    return f >= hoy && f <= en7dias;
  });

  let msg = `🗓️ <b>VISITAS PRÓXIMAS (7 días)</b>\n`;
  if (proximas.length === 0) {
    msg += `✅ Sin visitas programadas para los próximos 7 días.`;
  } else {
    msg += `${proximas.length} visita(s) programada(s)\n\n`;
    proximas.forEach(v => {
      const props = v.properties;
      const nombre = props["Nombre"]?.title?.[0]?.plain_text || "Sin nombre";
      const fecha  = props["Fecha y hora"]?.date?.start || "";
      msg += `• <b>${nombre}</b>\n  📅 ${fecha ? fmt(fecha) : "Sin fecha"}\n`;
    });
  }
  return msg;
}

function mensajeLutheria() {
  const luthieria = consultarNotion(ID_LUTHIERIA, {
    property: "Realizada", checkbox: { equals: false }
  });

  let msg = `🎻 <b>LUTHERÍA PENDIENTE</b>\n`;
  if (luthieria.length === 0) {
    msg += `✅ Todas las solicitudes de Luthería están completadas.`;
  } else {
    msg += `${luthieria.length} solicitud(es) sin realizar\n\n`;
    const agrup = {};
    luthieria.forEach(l => {
      const semana = l.properties["Semana"]?.select?.name || "Sin semana";
      const registro = l.properties["Registro"]?.title?.[0]?.plain_text || "—";
      const partes = registro.split(" — ");
      if (!agrup[semana]) agrup[semana] = [];
      agrup[semana].push(`${partes[0] || registro} (${partes[1] || ""})`);
    });
    Object.entries(agrup).slice(0, 5).forEach(([semana, items]) => {
      msg += `<b>Semana ${semana}:</b>\n`;
      items.slice(0, 4).forEach(i => { msg += `• ${i}\n`; });
      if (items.length > 4) msg += `  ...y ${items.length - 4} más\n`;
    });
  }
  return msg;
}

function mensajeBitacora() {
  const escalados = consultarNotion(ID_BITACORA, {
    and: [
      { property: "Requiere Coordinador", checkbox: { equals: true } },
      { property: "Estado", select: { does_not_equal: "Cerrado" } }
    ]
  });
  const riesgos = consultarNotion(ID_BITACORA, {
    and: [
      { property: "Tipo de registro", select: { equals: "Riesgo" } },
      { property: "Estado", select: { does_not_equal: "Cerrado" } }
    ]
  });
  const formRiesgo = consultarNotion(ID_FORMADORES, {
    property: "Situaci\u00f3n de riesgo",
    checkbox: { equals: true }
  });

  let msg = `🚨 <b>BITÁCORA — ATENCIÓN REQUERIDA</b>\n`;
  if (escalados.length === 0 && riesgos.length === 0 && formRiesgo.length === 0) {
    msg += `✅ Sin casos escalados ni riesgos activos.`;
    return msg;
  }
  if (escalados.length > 0) {
    msg += `\n🔴 <b>Casos escalados (${escalados.length})</b>\n`;
    escalados.forEach(e => {
      const props = e.properties;
      const titulo = props["Título"]?.title?.[0]?.plain_text || "Sin título";
      const tipo   = props["Tipo de registro"]?.select?.name || "—";
      const prior  = props["Prioridad"]?.select?.name || "—";
      const gestor = props["Registrado por"]?.select?.name || "—";
      msg += `• [${tipo}] <b>${titulo}</b>\n  ${prior} · ${gestor}\n`;
    });
  }
  if (riesgos.length > 0) {
    msg += `\n⚠️ <b>Riesgos activos (${riesgos.length})</b>\n`;
    riesgos.forEach(r => {
      const titulo = r.properties["Título"]?.title?.[0]?.plain_text || "Sin título";
      const prior  = r.properties["Prioridad"]?.select?.name || "—";
      const gestor = r.properties["Registrado por"]?.select?.name || "—";
      msg += `• <b>${titulo}</b> · ${prior} · ${gestor}\n`;
    });
  }
  if (formRiesgo.length > 0) {
    msg += `\n🟠 <b>Formadores en riesgo (${formRiesgo.length})</b>\n`;
    formRiesgo.slice(0, 5).forEach(f => {
      const nombre = f.properties["Nombre"]?.title?.[0]?.plain_text || "—";
      msg += `• ${nombre}\n`;
    });
    if (formRiesgo.length > 5) msg += `  ...y ${formRiesgo.length - 5} más\n`;
  }
  return msg;
}

function mensajeReuniones() {
  const hoy = new Date(); hoy.setHours(0,0,0,0);
  const en7dias = new Date(hoy); en7dias.setDate(en7dias.getDate() + 7);
  const reuniones = consultarNotion(ID_REUNIONES, {
    property: "Estado", select: { equals: "Programada" }
  });
  const proximas = reuniones.filter(r => {
    const fecha = r.properties["Fecha"]?.date?.start;
    if (!fecha) return false;
    const f = new Date(fecha); f.setHours(0,0,0,0);
    return f >= hoy && f <= en7dias;
  });
  const conCompromisos = consultarNotion(ID_REUNIONES, {
    and: [
      { property: "Estado", select: { equals: "Realizada" } },
      { property: "Compromisos pendientes", number: { greater_than: 0 } }
    ]
  });

  let msg = `📝 <b>REUNIONES</b>\n`;
  if (proximas.length > 0) {
    msg += `\n📅 <b>Próximas (7 días)</b>\n`;
    proximas.forEach(r => {
      const props = r.properties;
      const nombre = props["Nombre"]?.title?.[0]?.plain_text || "Sin nombre";
      const fecha  = props["Fecha"]?.date?.start || "";
      const tipo   = props["Tipo"]?.select?.name || "—";
      msg += `• <b>${nombre}</b>\n  ${tipo} · ${fecha ? fmt(fecha) : "Sin fecha"}\n`;
    });
  } else {
    msg += `\n📅 Sin reuniones en los próximos 7 días.\n`;
  }
  if (conCompromisos.length > 0) {
    const total = conCompromisos.reduce((s,r) =>
      s + (parseInt(r.properties["Compromisos pendientes"]?.number || 0)), 0);
    msg += `\n⏳ <b>Compromisos pendientes (${total})</b>\n`;
    conCompromisos.slice(0, 3).forEach(r => {
      const nombre = r.properties["Nombre"]?.title?.[0]?.plain_text || "—";
      const comp   = r.properties["Compromisos pendientes"]?.number || 0;
      msg += `• ${nombre}: ${comp} compromiso(s)\n`;
    });
  } else {
    msg += `\n✅ Sin compromisos pendientes de reuniones anteriores.`;
  }
  return msg;
}

function enviarAlertas() {
  if (!esHabil()) return;
  try { enviarTelegram(mensajeEncabezado()); }    catch(e) { Logger.log("Error encabezado: " + e); }
  try { enviarTelegram(mensajeTareas()); }        catch(e) { Logger.log("Error tareas: " + e); }
  try { enviarTelegram(mensajeVisitasAlerta()); } catch(e) { Logger.log("Error visitas: " + e); }
  try { enviarTelegram(mensajeLutheria()); }      catch(e) { Logger.log("Error luthería: " + e); }
  try { enviarTelegram(mensajeBitacora()); }      catch(e) { Logger.log("Error bitácora: " + e); }
  try { enviarTelegram(mensajeReuniones()); }     catch(e) { Logger.log("Error reuniones: " + e); }
}

// ══════════════════════════════════════════════
// SINCRONIZACIÓN VISITAS → GOOGLE CALENDAR
// ══════════════════════════════════════════════

function sincronizarVisitas() {
  const visitas = consultarNotion(ID_VISITAS, {
    property: "Estado", select: { equals: "Programada" }
  });

  const calendar = CalendarApp.getCalendarById(CALENDAR_ID);
  const ahora = new Date();
  const en90dias = new Date(); en90dias.setDate(en90dias.getDate() + 90);
  const existentes = calendar.getEvents(ahora, en90dias).map(e => e.getTitle());

  let creados = 0, omitidos = 0;

  visitas.forEach(v => {
    const props = v.properties;
    const titulo   = props["Nombre"]?.title?.[0]?.plain_text || "Visita sin título";
    const fecha    = props["Fecha y hora"]?.date?.start;
    const objetivo = props["Objetivo"]?.rich_text?.[0]?.plain_text || "";
    if (!fecha) { omitidos++; return; }
    if (existentes.includes(titulo)) { omitidos++; return; }
    const fechaEvento = new Date(fecha + (fecha.includes('T') ? '' : 'T09:00:00'));
    const fechaFin = new Date(fechaEvento);
    fechaFin.setHours(fechaFin.getHours() + 2);
    calendar.createEvent(titulo, fechaEvento, fechaFin, {
      description: `Objetivo: ${objetivo}\nRegistrado en: GEF — Notion`
    });
    creados++;
  });

  Logger.log(`✅ Sincronización completada. Creados: ${creados}. Omitidos: ${omitidos}`);
}

// ══════════════════════════════════════════════
// CONFIGURACIÓN DE TRIGGERS
// ══════════════════════════════════════════════

function configurarTriggerAlertas() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "enviarAlertas") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("enviarAlertas")
    .timeBased().everyDays(1).atHour(8).create();
  Logger.log("✅ Trigger de alertas configurado — lunes a sábado a las 8am.");
}

function configurarTriggerVisitas() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "sincronizarVisitas") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("sincronizarVisitas")
    .timeBased().everyDays(1).atHour(23).create();
  Logger.log("✅ Trigger de visitas configurado — diario a las 11pm.");
}

function configurarTodosTriggers() {
  configurarTriggerAlertas();
  configurarTriggerVisitas();
  Logger.log("✅ Todos los triggers configurados correctamente.");
}
