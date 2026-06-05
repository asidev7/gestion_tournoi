"""
Génération PDF : contrat d'engagement d'équipe + tableau des matchs.
"""
import io
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer, Image)

try:
    from django.contrib.staticfiles import finders
except Exception:  # pragma: no cover
    finders = None

PITCH = colors.HexColor('#0d7a3c')
PITCH_DARK = colors.HexColor('#064d24')
LIGHT = colors.HexColor('#f1f5f2')
LINE = colors.HexColor('#d7ddd9')


def _static_path(rel):
    if finders:
        p = finders.find(rel)
        if p:
            return p
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', rel)
    return p if os.path.exists(p) else None


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle('CLTitle', parent=ss['Title'], textColor=PITCH_DARK, fontSize=20, spaceAfter=2))
    ss.add(ParagraphStyle('CLSub', parent=ss['Normal'], textColor=colors.HexColor('#666'), fontSize=9))
    ss.add(ParagraphStyle('CLH', parent=ss['Heading2'], textColor=PITCH_DARK, fontSize=12, spaceBefore=10, spaceAfter=4))
    ss.add(ParagraphStyle('CLBody', parent=ss['Normal'], fontSize=9.5, leading=14))
    return ss


def _header_flowables(ss, title, subtitle):
    logo_path = _static_path('images/adeib_logo.png')
    elems = []
    if logo_path:
        try:
            img = Image(logo_path, width=22 * mm, height=22 * mm)
            tbl = Table([[img, Paragraph(f'<b>{title}</b><br/><font size=9 color="#666">{subtitle}</font>', ss['CLBody'])]],
                        colWidths=[26 * mm, None])
            tbl.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
            elems.append(tbl)
        except Exception:
            elems.append(Paragraph(title, ss['CLTitle']))
            elems.append(Paragraph(subtitle, ss['CLSub']))
    else:
        elems.append(Paragraph(title, ss['CLTitle']))
        elems.append(Paragraph(subtitle, ss['CLSub']))
    elems.append(Spacer(1, 8))
    return elems


def generate_team_contract_pdf(team):
    """Contrat d'engagement d'une équipe (A4 portrait)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)
    ss = _styles()
    tournament = team.tournament
    story = []

    story += _header_flowables(ss, "Contrat d'engagement", tournament.name if tournament else 'ADEIB U26')

    story.append(Paragraph("Contrat d'engagement de l'équipe", ss['CLTitle']))
    story.append(Spacer(1, 6))

    # Bloc infos équipe
    info_rows = [
        ['Équipe', team.name],
        ['Poule', f'Groupe {team.group.name}' if team.group else '—'],
        ['Entraîneur', team.coach_name or '—'],
        ['Président', team.president_name or '—'],
        ['Effectif', f'{team.player_count} joueur(s)'],
    ]
    t = Table(info_rows, colWidths=[40 * mm, None])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT),
        ('TEXTCOLOR', (0, 0), (0, -1), PITCH_DARK),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('GRID', (0, 0), (-1, -1), 0.5, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    # Effectif
    story.append(Paragraph("Effectif déclaré", ss['CLH']))
    head = ['#', 'Nom', 'Prénom', 'Surnom', 'Poste', 'N°', 'Âge']
    data = [head]
    for i, p in enumerate(team.players.all(), 1):
        data.append([
            str(i), p.last_name, p.first_name, p.nickname or '—',
            p.get_position_display(), str(p.jersey_number or '—'), str(p.age),
        ])
    if len(data) == 1:
        data.append(['—', 'Aucun joueur', '', '', '', '', ''])
    pt = Table(data, colWidths=[10 * mm, None, None, 28 * mm, 24 * mm, 12 * mm, 12 * mm], repeatRows=1)
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PITCH),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, LINE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pt)

    # Engagement
    story.append(Paragraph("Engagement", ss['CLH']))
    engagement = (
        "L'équipe susmentionnée, représentée par son capitaine et/ou son président, "
        "s'engage à participer au tournoi {name} dans le respect du règlement officiel, "
        "de l'esprit sportif et des décisions du comité d'organisation. "
        "Les frais d'inscription s'élèvent à <b>50 000 Naira</b> par équipe et doivent être "
        "réglés avant le début de la compétition. Toute inscription vaut acceptation pleine "
        "et entière du règlement."
    ).format(name=tournament.name if tournament else 'ADEIB U26')
    story.append(Paragraph(engagement, ss['CLBody']))
    story.append(Spacer(1, 24))

    # Signatures
    sign = [
        ['Le Président de l\'équipe', 'Le Capitaine', 'Le Comité d\'organisation'],
        ['\n\n_______________', '\n\n_______________', '\n\n_______________'],
    ]
    st = Table(sign, colWidths=[None, None, None])
    st.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, 0), PITCH_DARK),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(st)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_matches_table_pdf(matches, tournament):
    """Tableau des matchs sélectionnés (A4 paysage)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm)
    ss = _styles()
    story = []
    story += _header_flowables(ss, tournament.name if tournament else 'ADEIB U26', 'Tableau des matchs')

    head = ['Date', 'Phase', 'Poule', 'Domicile', '', 'Extérieur', 'Lieu', 'Statut']
    data = [head]
    for m in matches:
        date = m.match_date.strftime('%d/%m/%Y %H:%M') if m.match_date else '—'
        score = m.score_display
        data.append([
            date, m.get_phase_display(),
            (f'Gr. {m.group.name}' if m.group else '—'),
            m.home_team.name, score, m.away_team.name,
            (m.venue or '—'), m.get_status_display(),
        ])
    if len(data) == 1:
        data.append(['—', 'Aucun match sélectionné', '', '', '', '', '', ''])

    table = Table(data, repeatRows=1,
                  colWidths=[32 * mm, 30 * mm, 18 * mm, None, 20 * mm, None, 45 * mm, 24 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PITCH),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, LINE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('ALIGN', (7, 0), (7, -1), 'CENTER'),
        ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (4, 1), (4, -1), PITCH_DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer
