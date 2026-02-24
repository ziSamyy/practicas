from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from config.database import get_db
from middlewares.jwt_bearer import JWTBearer
from models.Client import Client as ClientModel
from models.Documento import Documento as DocumentoModel, DocumentoItem as DocumentoItemModel
from models.User import User as UserModel
from routers.Users import require_admin
from schemas.Documento import DocumentoCreate, DocumentoResponse

documento_route = APIRouter()


def _generar_numero(db: Session) -> str:
    ultimo = db.query(func.max(DocumentoModel.numero)).scalar()
    if not ultimo:
        return "FAC-0001"
    n = int(ultimo.split("-")[1]) + 1
    return f"FAC-{n:04d}"


# ── CRUD ────────────────────────────────────────────────────────────────────

@documento_route.post(
    "/documentos",
    tags=["Documentos"],
    response_model=DocumentoResponse,
    dependencies=[Depends(JWTBearer())],
)
def crear_documento(
    doc: DocumentoCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    cliente = db.query(ClientModel).filter(ClientModel.id == doc.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    usuario_id = token_data.get("id")
    usuario = db.query(UserModel).filter(UserModel.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    numero = _generar_numero(db)

    items_db = []
    total = 0
    for item in doc.items:
        subtotal = item.cantidad * item.precio_unitario
        total += subtotal
        items_db.append(
            DocumentoItemModel(
                descripcion=item.descripcion,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=subtotal,
            )
        )

    nuevo_doc = DocumentoModel(
        numero=numero,
        cliente_id=doc.cliente_id,
        usuario_id=usuario_id,
        empresa_transporte=doc.empresa_transporte,
        a_cargo_de=doc.a_cargo_de,
        total=total,
        items=items_db,
    )
    db.add(nuevo_doc)
    db.commit()
    db.refresh(nuevo_doc)
    return nuevo_doc


@documento_route.get(
    "/documentos",
    tags=["Documentos"],
    response_model=List[DocumentoResponse],
    dependencies=[Depends(JWTBearer())],
)
def listar_documentos(db: Session = Depends(get_db)):
    return db.query(DocumentoModel).all()


@documento_route.get(
    "/documentos/{documento_id}",
    tags=["Documentos"],
    response_model=DocumentoResponse,
    dependencies=[Depends(JWTBearer())],
)
def obtener_documento(documento_id: int, db: Session = Depends(get_db)):
    doc = db.query(DocumentoModel).filter(DocumentoModel.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@documento_route.delete(
    "/documentos/{documento_id}",
    tags=["Documentos"],
    dependencies=[Depends(require_admin)],
)
def eliminar_documento(documento_id: int, db: Session = Depends(get_db)):
    doc = db.query(DocumentoModel).filter(DocumentoModel.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    db.delete(doc)
    db.commit()
    return {"msg": "Documento eliminado correctamente"}


# ── PDF ─────────────────────────────────────────────────────────────────────

@documento_route.get(
    "/documentos/{documento_id}/pdf",
    tags=["Documentos"],
    dependencies=[Depends(JWTBearer())],
)
def descargar_pdf(documento_id: int, db: Session = Depends(get_db)):
    doc = db.query(DocumentoModel).filter(DocumentoModel.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    pdf_bytes = _generar_pdf(doc)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc.numero}.pdf"'},
    )


def _generar_pdf(doc: DocumentoModel) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )

    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold")
    title_style = ParagraphStyle(
        "title", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=20
    )
    section_style = ParagraphStyle(
        "section", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10, textColor=colors.white,
    )

    fecha = doc.fecha_emision.strftime("%d/%m/%Y")
    elements = []

    # ── Encabezado ──────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f"FACTURA  {doc.numero}", title_style),
        Paragraph(f"Fecha de emisión: {fecha}", styles["Normal"]),
    ]]
    header_table = Table(header_data, colWidths=["60%", "40%"])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#2c3e50")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Sección: Datos del cliente y usuario ───────────────────────────
    section_header = Table(
        [[Paragraph("DATOS DEL CLIENTE", section_style),
          Paragraph("CREADO POR", section_style)]],
        colWidths=["50%", "50%"],
    )
    section_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(section_header)

    c = doc.cliente
    u = doc.usuario
    info_data = [
        [
            Paragraph(f"<b>Nombre:</b> {c.name}", styles["Normal"]),
            Paragraph(f"<b>Nombre:</b> {u.name}", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>CUIT:</b> {c.cuit}", styles["Normal"]),
            Paragraph(f"<b>Email:</b> {u.email}", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>Email:</b> {c.email}", styles["Normal"]),
            Paragraph(f"<b>Rol:</b> {u.rol}", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>Teléfono:</b> {c.telefono}", styles["Normal"]),
            Paragraph("", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>Domicilio:</b> {c.domicilio}", styles["Normal"]),
            Paragraph("", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>Ciudad:</b> {c.ciudad} — <b>Provincia:</b> {c.provincia}", styles["Normal"]),
            Paragraph("", styles["Normal"]),
        ],
    ]
    info_table = Table(info_data, colWidths=["50%", "50%"])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f9f9f9"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#eeeeee")),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Sección: Transporte ────────────────────────────────────────────
    transport_header = Table(
        [[Paragraph("DATOS DE TRANSPORTE", section_style)]],
        colWidths=["100%"],
    )
    transport_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(transport_header)

    transport_data = [[
        Paragraph(f"<b>Empresa:</b> {doc.empresa_transporte}", styles["Normal"]),
        Paragraph(f"<b>A cargo de:</b> {doc.a_cargo_de}", styles["Normal"]),
    ]]
    transport_table = Table(transport_data, colWidths=["50%", "50%"])
    transport_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ]))
    elements.append(transport_table)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Sección: Detalle de items ──────────────────────────────────────
    detail_header = Table(
        [[Paragraph("DETALLE", section_style)]],
        colWidths=["100%"],
    )
    detail_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(detail_header)

    col_headers = [
        Paragraph("<b>Descripción</b>", bold),
        Paragraph("<b>Cant.</b>", bold),
        Paragraph("<b>P. Unit.</b>", bold),
        Paragraph("<b>Subtotal</b>", bold),
    ]
    rows = [col_headers]
    for item in doc.items:
        rows.append([
            Paragraph(item.descripcion, styles["Normal"]),
            Paragraph(f"{item.cantidad:.2f}", styles["Normal"]),
            Paragraph(f"$ {item.precio_unitario:.2f}", styles["Normal"]),
            Paragraph(f"$ {item.subtotal:.2f}", styles["Normal"]),
        ])

    rows.append([
        Paragraph("", styles["Normal"]),
        Paragraph("", styles["Normal"]),
        Paragraph("<b>TOTAL</b>", bold),
        Paragraph(f"<b>$ {doc.total:.2f}</b>", bold),
    ])

    detail_table = Table(rows, colWidths=["55%", "12%", "17%", "16%"])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecf0f1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9f9f9")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#eeeeee")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#2c3e50")),
    ]))
    elements.append(detail_table)

    pdf.build(elements)
    return buffer.getvalue()
