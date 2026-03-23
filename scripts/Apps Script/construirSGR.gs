// ══════════════════════════════════════════════
// GEF Red Músicas de Medellín
// Script: construirSGR.gs
// Descripción: Crea la estructura completa del Google Sheets SGR
//              6 pestañas de gestión + pestaña PANEL del coordinador
// Ejecutar: Solo una vez al inicio del sistema
// ══════════════════════════════════════════════

function construirSGR() {

  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const gestiones = [
    { nombre: "G. Iniciación",          color: "#0d7f3f" },
    { nombre: "G. Canto y Movimiento",  color: "#e65100" },
    { nombre: "G. Neurodiversidad",     color: "#6a1b9a" },
    { nombre: "G. Cuerdas",             color: "#1565c0" },
    { nombre: "G. Bronces y Percusión", color: "#b71c1c" },
    { nombre: "G. Vientos Maderas",     color: "#004d40" },
  ];

  const columnas = [
    "ID", "Nombre de la tarea", "Categoría", "Prioridad",
    "Estado", "Fecha de creación", "Fecha límite",
    "Articulación", "Notas", "Creado por"
  ];

  const categorias   = ["Planeación","Seguimiento","Reporte","Visita","Formación","Comunicación","Administrativo"];
  const prioridades  = ["Alta","Media","Baja"];
  const estados      = ["Pendiente","En curso","Listo","Bloqueado"];
  const articulacion = ["Ninguna","G. Iniciación","G. Canto y Movimiento",
                        "G. Neurodiversidad","G. Cuerdas",
                        "G. Bronces y Percusión","G. Vientos Maderas"];
  const creadoPor    = ["Eq. Estratégico","Gestor"];

  const hojasActuales = ss.getSheets();
  hojasActuales.forEach((h, i) => { if (i > 0) ss.deleteSheet(h); });

  gestiones.forEach((g, idx) => {
    let hoja = (idx === 0) ? ss.getSheets()[0] : ss.insertSheet();
    hoja.setName(g.nombre);
    hoja.setTabColor(g.color);
    hoja.setFrozenRows(1);

    const encabezado = hoja.getRange(1, 1, 1, columnas.length);
    encabezado.setValues([columnas]);
    encabezado.setBackground("#1e3a5f");
    encabezado.setFontColor("#ffffff");
    encabezado.setFontWeight("bold");

    hoja.setColumnWidth(1, 50);
    hoja.setColumnWidth(2, 250);
    hoja.setColumnWidth(3, 120);
    hoja.setColumnWidth(4, 90);
    hoja.setColumnWidth(5, 100);
    hoja.setColumnWidth(6, 120);
    hoja.setColumnWidth(7, 120);
    hoja.setColumnWidth(8, 180);
    hoja.setColumnWidth(9, 220);
    hoja.setColumnWidth(10, 140);

    crearLista(hoja, 2, 3, 50, categorias);
    crearLista(hoja, 2, 4, 50, prioridades);
    crearLista(hoja, 2, 5, 50, estados);
    crearLista(hoja, 2, 8, 50, articulacion);
    crearLista(hoja, 2, 10, 50, creadoPor);

    // Formato condicional fechas
    const rangoFechas = hoja.getRange("F2:G51");
    rangoFechas.setNumberFormat("dd/mm/yyyy");
    const reglaFecha = SpreadsheetApp.newDataValidation()
      .requireDate()
      .setAllowInvalid(false)
      .setHelpText("Selecciona una fecha del calendario")
      .build();
    rangoFechas.setDataValidation(reglaFecha);

    // Formato condicional por estado
    const rangoEstado = hoja.getRange("E2:E51");
    const reglas = [];
    reglas.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("Listo").setBackground("#e6f4ea").setFontColor("#137333")
      .setRanges([rangoEstado]).build());
    reglas.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("En curso").setBackground("#fef7e0").setFontColor("#b06000")
      .setRanges([rangoEstado]).build());
    reglas.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("Pendiente").setBackground("#fce8e6").setFontColor("#c5221f")
      .setRanges([rangoEstado]).build());
    reglas.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("Bloqueado").setBackground("#f1f3f4").setFontColor("#5f6368")
      .setRanges([rangoEstado]).build());
    hoja.setConditionalFormatRules(reglas);

    // Separador historial
    const separador = hoja.getRange(52, 1, 1, columnas.length);
    separador.merge();
    separador.setValue("── HISTORIAL ──");
    separador.setBackground("#e8eaed");
    separador.setFontColor("#5f6368");
    separador.setFontWeight("bold");
    separador.setHorizontalAlignment("center");
    const proteccion = separador.protect();
    proteccion.setDescription("Separador de historial — no borrar");
    proteccion.setWarningOnly(true);
  });

  // PANEL del coordinador
  const panel = ss.insertSheet();
  panel.setName("PANEL");
  panel.setTabColor("#1a73e8");
  panel.setFrozenRows(1);

  const colsPanel = ["Gestión","Total tareas","Pendientes","En curso","Listas","Bloqueadas","Vencidas"];
  const encPanel = panel.getRange(1, 1, 1, colsPanel.length);
  encPanel.setValues([colsPanel]);
  encPanel.setBackground("#1e3a5f");
  encPanel.setFontColor("#ffffff");
  encPanel.setFontWeight("bold");

  panel.setColumnWidth(1, 200);
  [2,3,4,5,6,7].forEach(c => panel.setColumnWidth(c, 100));

  gestiones.forEach((g, i) => {
    const fila = i + 2;
    const nombre = g.nombre;
    panel.getRange(fila, 1).setValue(nombre);
    panel.getRange(fila, 2).setFormula(`=COUNTA('${nombre}'!B2:B51)`);
    panel.getRange(fila, 3).setFormula(`=COUNTIF('${nombre}'!E2:E51,"Pendiente")`);
    panel.getRange(fila, 4).setFormula(`=COUNTIF('${nombre}'!E2:E51,"En curso")`);
    panel.getRange(fila, 5).setFormula(`=COUNTIF('${nombre}'!E2:E51,"Listo")`);
    panel.getRange(fila, 6).setFormula(`=COUNTIF('${nombre}'!E2:E51,"Bloqueado")`);
    panel.getRange(fila, 7).setFormula(
      `=COUNTIFS('${nombre}'!G2:G51,"<"&TODAY(),'${nombre}'!E2:E51,"<>Listo")`
    );
  });

  const reglaVencidas = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(0)
    .setBackground("#fce8e6").setFontColor("#c5221f")
    .setRanges([panel.getRange("G2:G7")]).build();
  panel.setConditionalFormatRules([reglaVencidas]);

  Logger.log("✅ Sistema SGR construido correctamente.");
}

function crearLista(hoja, fila, col, cant, opciones) {
  const rango = hoja.getRange(fila, col, cant, 1);
  const regla = SpreadsheetApp.newDataValidation()
    .requireValueInList(opciones, true)
    .setAllowInvalid(false)
    .build();
  rango.setDataValidation(regla);
}
