"""
Generador de PDF para Orden de Transporte - Formato ADK S.R.L.
Toda la configuración visual se edita en: utils/orden_template_config.json
"""
import datetime
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ─── carga de configuración ───────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).parent / "orden_template_config.json"


def _load_config() -> Dict[str, Any]:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ─── helpers de dibujo ────────────────────────────────────────────────────────

def _color(rgb: list):
    return colors.Color(rgb[0], rgb[1], rgb[2])


def _rect(c: canvas.Canvas, x, y, w, h,
          fill_color=None, line_width=0.5, stroke_color=colors.black):
    """Dibuja un rectángulo. Coordenadas en mm desde el borde inferior."""
    c.saveState()
    c.setLineWidth(line_width)
    c.setStrokeColor(stroke_color)
    if fill_color:
        c.setFillColor(fill_color)
        c.rect(x * mm, y * mm, w * mm, h * mm, fill=1, stroke=1)
    else:
        c.rect(x * mm, y * mm, w * mm, h * mm, fill=0, stroke=1)
    c.restoreState()


def _text(c: canvas.Canvas, x, y, text: str,
          font="Helvetica", size=8, align="left", color=colors.black):
    """Escribe texto. Coordenadas en mm."""
    if not text:
        return
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(color)
    px, py = x * mm, y * mm
    if align == "center":
        c.drawCentredString(px, py, text)
    elif align == "right":
        c.drawRightString(px, py, text)
    else:
        c.drawString(px, py, text)
    c.restoreState()


def _label_value(c: canvas.Canvas, x, y, label: str, value: str,
                 label_size=7, value_size=8.5):
    """Escribe una etiqueta seguida de su valor en negrita."""
    c.setFont("Helvetica", label_size)
    lw = c.stringWidth(label, "Helvetica", label_size) / mm
    _text(c, x, y, label, "Helvetica", label_size)
    _text(c, x + lw + 1, y, value, "Helvetica-Bold", value_size)


def _fmt_currency(value) -> str:
    """Formatea en pesos argentinos: $ 20.000,00"""
    if value is None:
        return ""
    try:
        val = float(value)
    except (TypeError, ValueError):
        return ""
    formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {formatted}"


# ─── generador principal ───────────────────────────────────────────────────────

def generar_pdf_orden_transporte(
    orden: Dict[str, Any],
    cliente: Dict[str, Any],
) -> bytes:
    """
    Genera el PDF leyendo el diseño desde orden_template_config.json.
    Para cambiar textos, colores o medidas → editá ese archivo JSON.
    """
    cfg = _load_config()

    # ── atajos a las secciones del config ──────────────────────────────────────
    emp     = cfg["empresa"]
    doc     = cfg["documento"]
    sec     = cfg["secciones"]
    col_d   = cfg["columna_derecha"]
    pie     = cfg["pie_pagina"]
    clr     = cfg["colores"]
    dim     = cfg["dimensiones"]
    tab     = cfg["tabla_financiera"]
    enc     = cfg["encabezado_columnas"]
    pie_col = cfg["pie_columnas"]
    fnt     = cfg["fuentes"]

    GRAY = _color(clr["barra_seccion"])

    # ── constantes de layout (mm desde borde inferior) ─────────────────────────
    LM  = dim["margen_izquierdo"]
    CW  = dim["ancho_contenido"]
    RM  = LM + CW

    H_H = dim["altura_encabezado"]
    H_Y = 297 - 10 - H_H           # top = 287 mm desde abajo

    ROW_DH = dim["alto_fila_datos"]
    DR_H   = ROW_DH * 3
    DR_Y   = H_Y - DR_H

    DL_H = dim["alto_barra_seccion"]
    DL_Y = DR_Y - DL_H

    DC_H = dim["alto_descripcion"]
    DC_Y = DL_Y - DC_H

    HL_H = dim["alto_barra_seccion"]
    HL_Y = DC_Y - HL_H

    ROW_H  = dim["alto_fila_financiera"]
    N_ROWS = dim["filas_valores_enviados"] + 1   # +1 por la cabecera
    FR_H   = ROW_H * N_ROWS
    FR_Y   = HL_Y - FR_H

    FT_H = dim["alto_pie"]
    FT_Y = FR_Y - FT_H

    FECHA_W = dim["ancho_caja_fecha"]
    DATA_W  = CW - FECHA_W
    FECHA_X = RM - FECHA_W

    FIN_LEFT_W  = CW * tab["porcentaje_tabla_izquierda"]
    FIN_RIGHT_W = CW - FIN_LEFT_W

    C0_W = tab["ancho_col_valores_enviados"]
    C1_W = tab["ancho_col_banco"]
    C2_W = tab["ancho_col_numero"]
    C3_W = FIN_LEFT_W - C0_W - C1_W - C2_W

    LOGO_W  = CW * enc["porcentaje_logo"]
    TITLE_W = CW * enc["porcentaje_titulo"]
    INFO_W  = CW - LOGO_W - TITLE_W

    F1_W = CW * pie_col["porcentaje_izquierda"]
    F2_W = CW * pie_col["porcentaje_centro"]
    F3_W = CW * pie_col["porcentaje_derecha"]

    RX   = LM + FIN_LEFT_W
    RL_W = FIN_RIGHT_W * tab["porcentaje_label_derecha"]
    RV_W = FIN_RIGHT_W - RL_W

    fin_top = FR_Y + FR_H

    # ── canvas ────────────────────────────────────────────────────────────────
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # ═══════════════════════════════════════════════════════════════════════════
    # 1 · ENCABEZADO
    # ═══════════════════════════════════════════════════════════════════════════
    _rect(c, LM,                    H_Y, LOGO_W,  H_H, line_width=0.8)
    _rect(c, LM + LOGO_W,           H_Y, TITLE_W, H_H, line_width=0.8)
    _rect(c, LM + LOGO_W + TITLE_W, H_Y, INFO_W,  H_H, line_width=0.8)

    # Celda logo
    _text(c, LM + 2, H_Y + 15, emp["nombre"], "Helvetica-Bold", 17)
    c.saveState()
    c.setLineWidth(1.2)
    for ly in [H_Y + 20, H_Y + 17, H_Y + 14]:
        c.line((LM + 14) * mm, ly * mm, (LM + LOGO_W - 3) * mm, ly * mm)
    c.restoreState()
    _text(c, LM + 2, H_Y + 3, emp["subtitulo"], "Helvetica", 6.5)

    # Celda título
    cx = LM + LOGO_W + TITLE_W / 2
    _text(c, cx, H_Y + 15, doc["titulo"], "Helvetica-Bold", fnt["titulo_size"],   "center")
    _text(c, cx, H_Y + 8,  doc["codigo"], "Helvetica",      fnt["subtitulo_size"], "center")

    # Celda info (derecha)
    ix = LM + LOGO_W + TITLE_W + 2
    _text(c, ix, H_Y + 18, doc["revision"],       "Helvetica", fnt["info_encabezado_size"])
    _text(c, ix, H_Y + 12, doc["fecha_vigencia"], "Helvetica", fnt["info_encabezado_size"])
    _text(c, ix, H_Y + 6,  doc["hoja"],           "Helvetica", fnt["info_encabezado_size"])

    # ═══════════════════════════════════════════════════════════════════════════
    # 2 · DATOS DEL DESTINATARIO
    # ═══════════════════════════════════════════════════════════════════════════
    _rect(c, LM, DL_Y, CW, DL_H, fill_color=GRAY)
    _text(c, LM + 2, DL_Y + 1.8, sec["datos_destinatario"],
          "Helvetica-Bold", fnt["label_size"] + 1)

    # Caja "Fecha de envío" (abarca las 3 filas de datos)
    _rect(c, FECHA_X, DR_Y, FECHA_W, DR_H, line_width=0.8)
    _text(c, FECHA_X + FECHA_W / 2, DR_Y + DR_H - 6,  "Fecha",     "Helvetica", fnt["label_size"], "center")
    _text(c, FECHA_X + FECHA_W / 2, DR_Y + DR_H - 11, "de envío:", "Helvetica", fnt["label_size"], "center")

    # Sub-cajas día / mes / año
    fecha_envio = orden.get("fecha_envio")
    if isinstance(fecha_envio, str):
        try:
            fecha_envio = datetime.date.fromisoformat(fecha_envio)
        except (ValueError, TypeError):
            fecha_envio = None

    day_s  = str(fecha_envio.day).zfill(2)   if fecha_envio else ""
    mon_s  = str(fecha_envio.month).zfill(2) if fecha_envio else ""
    year_s = str(fecha_envio.year)            if fecha_envio else ""

    DB_W = 8; DB_H = 10; DB_Y = DR_Y + 4; GAP = 1.5
    YR_W = FECHA_W - 4 - 2 * (DB_W + GAP)
    dx = FECHA_X + 2
    mx = dx + DB_W + GAP
    yx = mx + DB_W + GAP

    _rect(c, dx, DB_Y, DB_W, DB_H)
    _rect(c, mx, DB_Y, DB_W, DB_H)
    _rect(c, yx, DB_Y, YR_W, DB_H)
    _text(c, dx + DB_W / 2, DB_Y + 2.5, day_s,  "Helvetica-Bold", 10, "center")
    _text(c, mx + DB_W / 2, DB_Y + 2.5, mon_s,  "Helvetica-Bold", 10, "center")
    _text(c, yx + YR_W / 2, DB_Y + 2.5, year_s, "Helvetica-Bold", 10, "center")

    # Fila 1: Señor/es (70%) + Ciudad (30%)
    R1_Y  = H_Y - ROW_DH
    SEN_W = DATA_W * 0.70
    CIU_W = DATA_W - SEN_W
    _rect(c, LM,         R1_Y, SEN_W, ROW_DH)
    _rect(c, LM + SEN_W, R1_Y, CIU_W, ROW_DH)

    name       = cliente.get("name", "")
    cuit       = cliente.get("cuit", "")
    city       = cliente.get("ciudad", "")
    label_name = f"{name} (CUIT: {cuit})" if cuit else name
    _label_value(c, LM + 2,          R1_Y + 4.5, "Señor/es:", label_name,    fnt["label_size"], fnt["valor_size"])
    _label_value(c, LM + SEN_W + 2,  R1_Y + 4.5, "Ciudad:",   city.upper(),  fnt["label_size"], fnt["valor_size"])

    # Fila 2: Domicilio
    R2_Y = R1_Y - ROW_DH
    _rect(c, LM, R2_Y, DATA_W, ROW_DH)
    _label_value(c, LM + 2, R2_Y + 4.5, "Domicilio:", cliente.get("domicilio", ""),
                 fnt["label_size"], fnt["valor_size"])

    # Fila 3: Teléfono (50%) + Provincia (50%)
    R3_Y  = R2_Y - ROW_DH
    TEL_W = DATA_W * 0.50
    PRO_W = DATA_W - TEL_W
    _rect(c, LM,         R3_Y, TEL_W, ROW_DH)
    _rect(c, LM + TEL_W, R3_Y, PRO_W, ROW_DH)
    _label_value(c, LM + 2,          R3_Y + 4.5, "Telefono:", cliente.get("telefono", ""),            fnt["label_size"], fnt["valor_size"])
    _label_value(c, LM + TEL_W + 2,  R3_Y + 4.5, "Provincia:", cliente.get("provincia", "").upper(), fnt["label_size"], fnt["valor_size"])

    # ═══════════════════════════════════════════════════════════════════════════
    # 3 · DESCRIPCIÓN DE LA ORDEN
    # ═══════════════════════════════════════════════════════════════════════════
    _rect(c, LM, HL_Y, CW, HL_H, fill_color=GRAY)
    _text(c, LM + 2, HL_Y + 1.8, sec["descripcion_orden"],
          "Helvetica-Bold", fnt["label_size"] + 1)

    _rect(c, LM, DC_Y, CW, DC_H)

    desc     = orden.get("descripcion", "")
    contacto = orden.get("contacto", "") or ""
    movil    = orden.get("movil", "") or ""

    _text(c, LM + 3, DC_Y + DC_H - 9,  desc,            "Helvetica-Bold", fnt["descripcion_size"])
    _text(c, LM + 3, DC_Y + DC_H - 22, "Contacto:",     "Helvetica",      fnt["label_size"] + 1)
    if contacto:
        _text(c, LM + 3, DC_Y + DC_H - 30, contacto.upper(), "Helvetica-Bold", fnt["descripcion_size"])
    _text(c, LM + 3, DC_Y + DC_H - 42, "MOVIL:",        "Helvetica",      fnt["label_size"] + 1)
    if movil:
        _text(c, LM + 3, DC_Y + DC_H - 50, movil,       "Helvetica-Bold", fnt["descripcion_size"])

    # ═══════════════════════════════════════════════════════════════════════════
    # 4 · SECCIÓN FINANCIERA
    # ═══════════════════════════════════════════════════════════════════════════

    # Cabecera de tabla
    HR_Y = fin_top - ROW_H
    _rect(c, LM,                       HR_Y, C0_W, ROW_H)
    _rect(c, LM + C0_W,                HR_Y, C1_W, ROW_H)
    _rect(c, LM + C0_W + C1_W,         HR_Y, C2_W, ROW_H)
    _rect(c, LM + C0_W + C1_W + C2_W,  HR_Y, C3_W, ROW_H)
    _text(c, LM + 1.5,                           HR_Y + 2.5, sec["valores_enviados"], "Helvetica", 6.5)
    _text(c, LM + C0_W + C1_W / 2,              HR_Y + 2.5, sec["banco"],   "Helvetica", fnt["label_size"], "center")
    _text(c, LM + C0_W + C1_W + C2_W / 2,       HR_Y + 2.5, sec["numero"],  "Helvetica", fnt["label_size"], "center")
    _text(c, LM + C0_W + C1_W + C2_W + C3_W/2,  HR_Y + 2.5, sec["importe"], "Helvetica", fnt["label_size"], "center")

    # Filas de datos
    n_data_rows = dim["filas_valores_enviados"]
    valores = orden.get("valores_enviados") or []
    for i in range(n_data_rows):
        ry = HR_Y - (i + 1) * ROW_H
        _rect(c, LM,                       ry, C0_W, ROW_H)
        _rect(c, LM + C0_W,                ry, C1_W, ROW_H)
        _rect(c, LM + C0_W + C1_W,         ry, C2_W, ROW_H)
        _rect(c, LM + C0_W + C1_W + C2_W,  ry, C3_W, ROW_H)
        if i < len(valores):
            v = valores[i]
            if isinstance(v, dict):
                _text(c, LM + C0_W + C1_W / 2,              ry + 2.5, v.get("banco",  ""), "Helvetica", fnt["label_size"], "center")
                _text(c, LM + C0_W + C1_W + C2_W / 2,       ry + 2.5, v.get("numero", ""), "Helvetica", fnt["label_size"], "center")
                if v.get("importe"):
                    _text(c, LM + C0_W + C1_W + C2_W + C3_W / 2, ry + 2.5,
                          _fmt_currency(v["importe"]), "Helvetica", fnt["label_size"], "center")

    # Columna derecha
    right_rows = [
        (col_d["fila_1_label"], _fmt_currency(orden.get("valor_declarado")),   True),
        (col_d["fila_2_label"], _fmt_currency(orden.get("efectivo_enviado")),  True),
        (col_d["fila_3_label"], "",                                             False),
        (col_d["fila_4_label"], (orden.get("flete_a_cargo_de") or "").upper(), True),
        (col_d["fila_5_label"], (orden.get("transporte") or "").upper(),        True),
    ]

    for i, (label, value, bold) in enumerate(right_rows):
        ry = fin_top - (i + 1) * ROW_H
        _rect(c, RX,        ry, RL_W, ROW_H)
        _rect(c, RX + RL_W, ry, RV_W, ROW_H)
        _text(c, RX + RL_W / 2,        ry + 2.5, label, "Helvetica", 6.5, "center")
        if value:
            fn = "Helvetica-Bold" if bold else "Helvetica"
            _text(c, RX + RL_W + RV_W / 2, ry + 2.5, value, fn, fnt["valor_size"] - 0.5, "center")

    # ═══════════════════════════════════════════════════════════════════════════
    # 5 · PIE DE PÁGINA
    # ═══════════════════════════════════════════════════════════════════════════
    _rect(c, LM,               FT_Y, F1_W, FT_H, line_width=0.8)
    _rect(c, LM + F1_W,        FT_Y, F2_W, FT_H, line_width=0.8)
    _rect(c, LM + F1_W + F2_W, FT_Y, F3_W, FT_H, line_width=0.8)

    emitio = (orden.get("emitio_la_orden") or "").upper()
    c.setFont("Helvetica", fnt["label_size"])
    lw_emitio = c.stringWidth(pie["texto_izquierda"], "Helvetica", fnt["label_size"]) / mm
    _text(c, LM + 2,                  FT_Y + 3, pie["texto_izquierda"], "Helvetica",     fnt["label_size"])
    _text(c, LM + 2 + lw_emitio + 2,  FT_Y + 3, emitio,                "Helvetica-Bold", 9)

    _text(c, LM + F1_W + F2_W / 2,         FT_Y + 3, pie["texto_centro"],  "Helvetica",     8, "center")
    _text(c, LM + F1_W + F2_W + F3_W / 2,  FT_Y + 3, pie["texto_derecha"], "Helvetica-Bold", 8, "center")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
