"""
Generador de PDF para Orden de Transporte - Formato ADK S.R.L.
"""
import datetime
from io import BytesIO
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fmt_currency(value) -> str:
    """Formatea un valor numérico en pesos argentinos: $ 20.000,00"""
    if value is None:
        return ""
    try:
        val = float(value)
    except (TypeError, ValueError):
        return ""
    # Formato argentino: punto para miles, coma para decimales
    formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {formatted}"


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
    """Escribe una etiqueta y luego su valor en negrita."""
    c.setFont("Helvetica", label_size)
    lw = c.stringWidth(label, "Helvetica", label_size) / mm
    _text(c, x, y, label, "Helvetica", label_size)
    _text(c, x + lw + 1, y, value, "Helvetica-Bold", value_size)


# ─── generador principal ───────────────────────────────────────────────────────

def generar_pdf_orden_transporte(
    orden: Dict[str, Any],
    cliente: Dict[str, Any],
) -> bytes:
    """
    Genera un PDF de Orden de Transporte con el formato ADK S.R.L.

    Args:
        orden:   dict con los campos de la orden (mismos nombres que el modelo).
        cliente: dict con los campos del cliente.

    Returns:
        Bytes del PDF generado.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # ── Constantes de layout (mm desde el borde inferior de la hoja A4=297mm) ──
    LM = 10          # margen izquierdo
    CW = 190         # ancho del contenido
    RM = LM + CW     # borde derecho = 200 mm

    # Secciones (de ARRIBA a ABAJO → coordenadas crecen hacia abajo = decrecen en y)
    H_H  = 25        # header height
    H_Y  = 262       # header bottom  (top = 287 = 297-10)

    DR_H = 36        # datos-rows height  (3 filas × 12 mm)
    DR_Y = H_Y - DR_H          # = 226

    DL_H = 6         # datos-label height
    DL_Y = DR_Y - DL_H         # = 220   ← label bar "Datos del destinatario"

    DC_H = 70        # descripción content height
    DC_Y = DL_Y - DC_H         # = 150

    HL_H = 6         # header-label "Descripción de la Orden:"
    HL_Y = DC_Y - HL_H         # = 144

    ROW_H = 8        # altura de cada fila en sección financiera
    N_ROWS = 5       # 1 cabecera + 4 datos
    FR_H  = ROW_H * N_ROWS     # = 40
    FR_Y  = HL_Y - FR_H        # = 104

    FT_H = 10        # footer height
    FT_Y = FR_Y - FT_H         # = 94

    GRAY = colors.Color(0.87, 0.87, 0.87)

    # ═══════════════════════════════════════════════════════════════════════════
    # 1 · ENCABEZADO
    # ═══════════════════════════════════════════════════════════════════════════
    LOGO_W  = 50
    TITLE_W = 90
    INFO_W  = CW - LOGO_W - TITLE_W   # 50 mm

    _rect(c, LM,                      H_Y, LOGO_W,  H_H, line_width=0.8)
    _rect(c, LM + LOGO_W,             H_Y, TITLE_W, H_H, line_width=0.8)
    _rect(c, LM + LOGO_W + TITLE_W,   H_Y, INFO_W,  H_H, line_width=0.8)

    # Celda logo: "ADK" + líneas horizontales + "MAQUINAS ENVASADORAS"
    _text(c, LM + 2, H_Y + 15, "ADK", "Helvetica-Bold", 17)
    c.saveState()
    c.setLineWidth(1.2)
    for ly in [H_Y + 20, H_Y + 17, H_Y + 14]:
        c.line((LM + 14) * mm, ly * mm, (LM + LOGO_W - 3) * mm, ly * mm)
    c.restoreState()
    _text(c, LM + 2, H_Y + 3, "MAQUINAS ENVASADORAS", "Helvetica", 6.5)

    # Celda título
    cx = LM + LOGO_W + TITLE_W / 2
    _text(c, cx, H_Y + 15, "ORDEN DE TRANSPORTE", "Helvetica-Bold", 11, "center")
    _text(c, cx, H_Y + 8,  "ADK S.R.L.  RG 1.1",  "Helvetica",      8,  "center")

    # Celda info
    ix = LM + LOGO_W + TITLE_W + 2
    _text(c, ix, H_Y + 18, "Revisión: 00",              "Helvetica", 7.5)
    _text(c, ix, H_Y + 12, "Fecha de vigencia: 05/08/03","Helvetica", 7.5)
    _text(c, ix, H_Y + 6,  "Hoja: 1/1",                 "Helvetica", 7.5)

    # ═══════════════════════════════════════════════════════════════════════════
    # 2 · DATOS DEL DESTINATARIO
    # ═══════════════════════════════════════════════════════════════════════════
    # Barra de título de sección
    _rect(c, LM, DL_Y, CW, DL_H, fill_color=GRAY)
    _text(c, LM + 2, DL_Y + 1.8, "Datos del destinatario", "Helvetica-Bold", 8)

    # Caja "Fecha de envío" (derecha, abarca las 3 filas)
    FECHA_W  = 38
    FECHA_X  = RM - FECHA_W
    DATA_W   = CW - FECHA_W   # ancho del área de datos (izquierda)

    _rect(c, FECHA_X, DR_Y, FECHA_W, DR_H, line_width=0.8)
    _text(c, FECHA_X + FECHA_W / 2, DR_Y + DR_H - 6,  "Fecha",     "Helvetica", 7, "center")
    _text(c, FECHA_X + FECHA_W / 2, DR_Y + DR_H - 11, "de envío:", "Helvetica", 7, "center")

    # Cajas de día, mes y año
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
    _text(c, dx + DB_W / 2,  DB_Y + 2.5, day_s,  "Helvetica-Bold", 10, "center")
    _text(c, mx + DB_W / 2,  DB_Y + 2.5, mon_s,  "Helvetica-Bold", 10, "center")
    _text(c, yx + YR_W / 2,  DB_Y + 2.5, year_s, "Helvetica-Bold", 10, "center")

    # Fila 1: Señor/es (70%) + Ciudad (30%)
    R1_Y = H_Y - 12;  R1_H = 12
    SEN_W = DATA_W * 0.70
    CIU_W = DATA_W - SEN_W

    _rect(c, LM,          R1_Y, SEN_W, R1_H)
    _rect(c, LM + SEN_W,  R1_Y, CIU_W, R1_H)

    name  = cliente.get("name", "")
    cuit  = cliente.get("cuit", "")
    city  = cliente.get("ciudad", "")
    label_name = f"{name} (CUIT: {cuit})" if cuit else name
    _label_value(c, LM + 2, R1_Y + 4.5, "Señor/es:", label_name)
    _label_value(c, LM + SEN_W + 2, R1_Y + 4.5, "Ciudad:", city.upper())

    # Fila 2: Domicilio
    R2_Y = R1_Y - 12;  R2_H = 12
    _rect(c, LM, R2_Y, DATA_W, R2_H)
    _label_value(c, LM + 2, R2_Y + 4.5, "Domicilio:", cliente.get("domicilio", ""))

    # Fila 3: Teléfono (50%) + Provincia (50%)
    R3_Y = R2_Y - 12;  R3_H = 12
    TEL_W = DATA_W * 0.50
    PRO_W = DATA_W - TEL_W

    _rect(c, LM,          R3_Y, TEL_W, R3_H)
    _rect(c, LM + TEL_W,  R3_Y, PRO_W, R3_H)
    _label_value(c, LM + 2, R3_Y + 4.5, "Telefono:", cliente.get("telefono", ""))
    _label_value(c, LM + TEL_W + 2, R3_Y + 4.5, "Provincia:", cliente.get("provincia", "").upper())

    # ═══════════════════════════════════════════════════════════════════════════
    # 3 · DESCRIPCIÓN DE LA ORDEN
    # ═══════════════════════════════════════════════════════════════════════════
    _rect(c, LM, HL_Y, CW, HL_H, fill_color=GRAY)
    _text(c, LM + 2, HL_Y + 1.8, "Descripción de la Orden:", "Helvetica-Bold", 8)

    _rect(c, LM, DC_Y, CW, DC_H)

    desc     = orden.get("descripcion", "")
    contacto = orden.get("contacto", "") or ""
    movil    = orden.get("movil", "") or ""

    _text(c, LM + 3, DC_Y + DC_H - 9,  desc,            "Helvetica-Bold", 9)
    _text(c, LM + 3, DC_Y + DC_H - 22, "Contacto:",     "Helvetica",      8)
    if contacto:
        _text(c, LM + 3, DC_Y + DC_H - 30, contacto.upper(), "Helvetica-Bold", 9)
    _text(c, LM + 3, DC_Y + DC_H - 42, "MOVIL:",        "Helvetica",      8)
    if movil:
        _text(c, LM + 3, DC_Y + DC_H - 50, movil,       "Helvetica-Bold", 9)

    # ═══════════════════════════════════════════════════════════════════════════
    # 4 · SECCIÓN FINANCIERA
    # ═══════════════════════════════════════════════════════════════════════════
    FIN_LEFT_W  = CW * 0.60      # ~114 mm
    FIN_RIGHT_W = CW - FIN_LEFT_W

    # Columnas de la tabla izquierda
    C0_W = 27   # "Valores enviados:"
    C1_W = 33   # Banco
    C2_W = 25   # Número
    C3_W = FIN_LEFT_W - C0_W - C1_W - C2_W   # Importe

    fin_top = FR_Y + FR_H   # = 144 mm

    # Fila cabecera de la tabla
    HR_Y = fin_top - ROW_H   # = 136
    _rect(c, LM,                    HR_Y, C0_W, ROW_H)
    _rect(c, LM + C0_W,             HR_Y, C1_W, ROW_H)
    _rect(c, LM + C0_W + C1_W,      HR_Y, C2_W, ROW_H)
    _rect(c, LM + C0_W + C1_W + C2_W, HR_Y, C3_W, ROW_H)

    _text(c, LM + 1.5,                        HR_Y + 2.5, "Valores enviados:", "Helvetica", 6.5)
    _text(c, LM + C0_W + C1_W / 2,            HR_Y + 2.5, "Banco",   "Helvetica", 7, "center")
    _text(c, LM + C0_W + C1_W + C2_W / 2,     HR_Y + 2.5, "Número",  "Helvetica", 7, "center")
    _text(c, LM + C0_W + C1_W + C2_W + C3_W/2, HR_Y + 2.5, "Importe","Helvetica", 7, "center")

    # 4 filas de datos
    valores = orden.get("valores_enviados") or []
    for i in range(4):
        ry = HR_Y - (i + 1) * ROW_H
        _rect(c, LM,                     ry, C0_W, ROW_H)
        _rect(c, LM + C0_W,              ry, C1_W, ROW_H)
        _rect(c, LM + C0_W + C1_W,       ry, C2_W, ROW_H)
        _rect(c, LM + C0_W+C1_W+C2_W,   ry, C3_W, ROW_H)

        if i < len(valores):
            v = valores[i]
            if isinstance(v, dict):
                _text(c, LM + C0_W + C1_W / 2,              ry + 2.5, v.get("banco",  ""), "Helvetica", 7, "center")
                _text(c, LM + C0_W + C1_W + C2_W / 2,       ry + 2.5, v.get("numero", ""), "Helvetica", 7, "center")
                if v.get("importe"):
                    _text(c, LM + C0_W + C1_W + C2_W + C3_W / 2, ry + 2.5,
                          _fmt_currency(v["importe"]), "Helvetica", 7, "center")

    # Columna derecha: 5 cajas de información
    RX = LM + FIN_LEFT_W
    RL_W = FIN_RIGHT_W * 0.55   # label
    RV_W = FIN_RIGHT_W - RL_W   # value

    right_rows = [
        ("Valor Declarado",         _fmt_currency(orden.get("valor_declarado")),   True),
        ("Efectivo enviado:",        _fmt_currency(orden.get("efectivo_enviado")),  True),
        ("Total (Valores + Efvo.):", "",                                             False),
        ("Flete a cargo de:",        (orden.get("flete_a_cargo_de") or "").upper(), True),
        ("Transporte:",              (orden.get("transporte") or "").upper(),        True),
    ]

    for i, (label, value, bold) in enumerate(right_rows):
        ry = fin_top - (i + 1) * ROW_H
        _rect(c, RX,        ry, RL_W, ROW_H)
        _rect(c, RX + RL_W, ry, RV_W, ROW_H)
        _text(c, RX + RL_W / 2,        ry + 2.5, label, "Helvetica", 6.5, "center")
        if value:
            fn = "Helvetica-Bold" if bold else "Helvetica"
            _text(c, RX + RL_W + RV_W / 2, ry + 2.5, value, fn, 8, "center")

    # ═══════════════════════════════════════════════════════════════════════════
    # 5 · PIE DE PÁGINA
    # ═══════════════════════════════════════════════════════════════════════════
    F1_W = CW * 0.30
    F2_W = CW * 0.40
    F3_W = CW * 0.30

    _rect(c, LM,            FT_Y, F1_W, FT_H, line_width=0.8)
    _rect(c, LM + F1_W,     FT_Y, F2_W, FT_H, line_width=0.8)
    _rect(c, LM + F1_W+F2_W, FT_Y, F3_W, FT_H, line_width=0.8)

    emitio = (orden.get("emitio_la_orden") or "").upper()
    c.setFont("Helvetica", 7)
    lw_emitio = c.stringWidth("Emitio la Orden:", "Helvetica", 7) / mm
    _text(c, LM + 2,               FT_Y + 3, "Emitio la Orden:", "Helvetica", 7)
    _text(c, LM + 2 + lw_emitio + 2, FT_Y + 3, emitio, "Helvetica-Bold", 9)

    _text(c, LM + F1_W + F2_W / 2, FT_Y + 3, "Original",          "Helvetica",      8, "center")
    _text(c, LM + F1_W + F2_W + F3_W / 2, FT_Y + 3, "PARA EL TRANSPORTE", "Helvetica-Bold", 8, "center")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
