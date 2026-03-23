// ══════════════════════════════════════════════
// GEF Red Músicas de Medellín
// Script: configurarPermisos.gs
// Descripción: Configura permisos por gestor en el Google Sheets SGR
//              Cada gestor solo puede editar su propia pestaña
//              El PANEL solo lo puede editar el coordinador
// Ejecutar: Solo una vez al inicio del sistema
// ══════════════════════════════════════════════

function configurarPermisos() {

  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // ── Configurar correos antes de ejecutar ──
  const coordinador = "coordinacionformacion@redmusicasmedellin.co";

  const gestores = [
    { hoja: "G. Iniciación",          correo: "juliocadavid.redmusica@gmail.com" },
    { hoja: "G. Canto y Movimiento",  correo: "claudiacano503@gmail.com" },
    { hoja: "G. Neurodiversidad",     correo: "valeramirez1219@gmail.com" },
    { hoja: "G. Cuerdas",             correo: "santiagoisazacello@gmail.com" },
    { hoja: "G. Bronces y Percusión", correo: "santigarcia.musica@gmail.com" },
    { hoja: "G. Vientos Maderas",     correo: "ehilinpena.redmusica@gmail.com" },
  ];

  // Compartir el archivo con cada gestor como Editor
  gestores.forEach(g => { ss.addEditor(g.correo); });

  // Proteger cada pestaña — solo coordinador + gestor dueño pueden editar
  gestores.forEach(g => {
    const hoja = ss.getSheetByName(g.hoja);
    if (!hoja) return;
    const proteccion = hoja.protect();
    proteccion.setDescription("Protegida — solo " + g.hoja);
    proteccion.addEditor(coordinador);
    proteccion.addEditor(g.correo);
    const editoresActuales = proteccion.getEditors();
    editoresActuales.forEach(editor => {
      const email = editor.getEmail();
      if (email !== coordinador && email !== g.correo) {
        proteccion.removeEditor(email);
      }
    });
  });

  // Proteger el PANEL — solo el coordinador
  const panel = ss.getSheetByName("PANEL");
  if (panel) {
    const protPanel = panel.protect();
    protPanel.setDescription("PANEL — solo el coordinador puede editar");
    protPanel.addEditor(coordinador);
    const editoresPanel = protPanel.getEditors();
    editoresPanel.forEach(editor => {
      const email = editor.getEmail();
      if (email !== coordinador) protPanel.removeEditor(email);
    });
  }

  Logger.log("✅ Permisos configurados correctamente.");
}
