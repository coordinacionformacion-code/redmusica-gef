// ══════════════════════════════════════════════
// GEF Red Músicas de Medellín
// Script: sincronizarVisitas.gs
// Descripción: Sincroniza las visitas programadas en Notion
//              con el Google Calendar del equipo GEF
// Trigger: Diario a las 11pm (configurado con configurarTriggerVisitas)
// ══════════════════════════════════════════════

// ── Configuración ──
const CALENDAR_ID_VISITAS = "TU_ID_DE_GOOGLE_CALENDAR";
const NOTION_TOKEN_VIS    = "TU_TOKEN_DE_NOTION";
const ID_VISITAS          = "TU_ID_BD_VISITAS";

// ── Sincronizar visitas Notion → Google Calendar ──
function sincronizarVisitas() {
  const url = `https://api.notion.com/v1/databases/${ID_VISITAS}/query`;
  const payload = {
    filter: {
      property: "Estado",
      select: { equals: "Programada" }
    }
  };

  const response = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      "Authorization": `Bearer ${NOTION_TOKEN_VIS}`,
      "Notion-Version": "2022-06-28"
    },
    payload: JSON.stringify(payload)
  });

  const data = JSON.parse(response.getContentText());
  const visitas = data.results || [];
  const calendar = CalendarApp.getCalendarById(CALENDAR_ID_VISITAS);

  const ahora = new Date();
  const en90dias = new Date();
  en90dias.setDate(en90dias.getDate() + 90);
  const eventosExistentes = calendar.getEvents(ahora, en90dias).map(e => e.getTitle());

  let creados  = 0;
  let omitidos = 0;

  visitas.forEach(v => {
    const props = v.properties;
    const titulo   = props["Nombre"]?.title?.[0]?.plain_text || "Visita sin título";
    const fecha    = props["Fecha y hora"]?.date?.start;
    const objetivo = props["Objetivo"]?.rich_text?.[0]?.plain_text || "";

    if (!fecha) { omitidos++; return; }
    if (eventosExistentes.includes(titulo)) { omitidos++; return; }

    const fechaEvento = new Date(fecha + (fecha.includes('T') ? '' : 'T09:00:00'));
    const fechaFin    = new Date(fechaEvento);
    fechaFin.setHours(fechaFin.getHours() + 2);

    calendar.createEvent(titulo, fechaEvento, fechaFin, {
      description: `Objetivo: ${objetivo}\nRegistrado en: GEF — Notion`
    });
    creados++;
  });

  Logger.log(`✅ Sincronización completada. Creados: ${creados}. Omitidos: ${omitidos}`);
}

// ── Configurar trigger diario a las 11pm ──
function configurarTriggerVisitas() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "sincronizarVisitas") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("sincronizarVisitas")
    .timeBased()
    .everyDays(1)
    .atHour(23)
    .create();
  Logger.log("✅ Trigger de visitas configurado — se ejecutará diariamente a las 11pm.");
}
