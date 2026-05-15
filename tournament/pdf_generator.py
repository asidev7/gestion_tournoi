"""
Generateur de tickets PDF pour les matchs
Design: Premium, A4 paysage, deux parties avec perforation
"""
import io
import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader


# Palette de couleurs - Design premium
COLORS = {
    'primary': HexColor('#0d5c2e'),
    'primary_dark': HexColor('#094a24'),
    'secondary': HexColor('#1a1a1a'),
    'accent': HexColor('#c41e3a'),
    'gold': HexColor('#d4af37'),
    'white': white,
    'black': black,
    'border': HexColor('#333333'),
    'text': HexColor('#1a1a1a'),
    'text_light': HexColor('#666666'),
    'perforation': HexColor('#999999'),
}


def draw_qr_code(c, data, x, y, size=30):
    """Dessine un QR code au centre du ticket"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=4,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Creer une image PIL
    img = qr.make_image(fill_color="#0d5c2e", back_color="white")

    # Convertir en donnees pour reportlab
    from PIL import Image
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Dessiner l'image avec ImageReader
    img_reader = ImageReader(buffer)
    c.drawImage(img_reader, x, y, width=size*mm, height=size*mm)


def draw_logo_placeholder(c, x, y, size, letter, color=COLORS['primary']):
    """Dessine un cercle avec la premiere lettre du nom de l'equipe"""
    c.setFillColor(color)
    c.circle(x + size/2, y + size/2, size/2, fill=1, stroke=0)
    c.setFillColor(COLORS['white'])
    c.setFont("Helvetica-Bold", size * 0.5)
    c.drawCentredString(x + size/2, y + size/2 - size*0.15, letter.upper())


def draw_premium_ticket_landscape(c, x, y, width, height, ticket_data, config, match):
    """
    Dessine un ticket premium en format paysage avec deux parties
    et perforation pointillée au milieu
    """

    # Dimensions
    mid_x = x + width / 2
    part_width = width / 2 - 5*mm  # Espace pour la perforation
    part_height = height - 10*mm
    part_y = y + 5*mm

    # === PARTIE GAUCHE ===
    draw_ticket_part(c, x + 5*mm, part_y, part_width, part_height,
                     ticket_data, config, match, is_left=True)

    # === LIGNE DE PERFORATION POINTILLEE AU CENTRE ===
    c.setDash(3, 3)
    c.setStrokeColor(COLORS['perforation'])
    c.setLineWidth(1)
    c.line(mid_x, y + 8*mm, mid_x, y + height - 8*mm)
    c.setDash()

    # Ciseaux icon au milieu de la ligne de perforation
    c.setFont("Helvetica", 8)
    c.setFillColor(COLORS['perforation'])
    c.drawCentredString(mid_x, y + height/2, "✂")

    # === QR CODE AU CENTRE (sur la ligne de perforation) ===
    qr_size = 25
    qr_x = mid_x - (qr_size*mm)/2
    qr_y = y + height/2 - (qr_size*mm)/2

    # Fond blanc pour le QR
    c.setFillColor(COLORS['white'])
    c.roundRect(qr_x - 2*mm, qr_y - 2*mm, qr_size*mm + 4*mm, qr_size*mm + 4*mm,
                3*mm, fill=1, stroke=1)

    # QR Code
    qr_data = f"TICKET:{ticket_data.get('ticket_number', '000000')}|MATCH:{match.id}|VALID:24H"
    draw_qr_code(c, qr_data, qr_x, qr_y, size=qr_size)

    # === PARTIE DROITE ===
    draw_ticket_part(c, mid_x + 5*mm, part_y, part_width, part_height,
                     ticket_data, config, match, is_left=False)


def draw_ticket_part(c, x, y, width, height, ticket_data, config, match, is_left=True):
    """Dessine une partie du ticket (gauche ou droite)"""

    # Bordure rectangulaire epaisse
    c.setStrokeColor(COLORS['border'])
    c.setLineWidth(2)
    c.rect(x, y, width, height, fill=0, stroke=1)

    # Bande superieure vert fonce
    header_height = 18*mm
    c.setFillColor(COLORS['primary'])
    c.rect(x, y + height - header_height, width, header_height, fill=1, stroke=0)

    # Logo ADEIB dans le header
    c.setFillColor(COLORS['white'])
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x + width/2, y + height - 12*mm, "ADEIB U26")

    # Sous-titre
    c.setFont("Helvetica", 8)
    c.setFillColor(COLORS['white'])
    c.drawCentredString(x + width/2, y + height - 16*mm, "ILLARA - TOURNOI DE FOOTBALL")

    # === CONTENU PRINCIPAL ===
    content_y = y + height - header_height - 8*mm

    # VS avec logos des equipes
    if is_left:
        # Partie gauche: Equipe domicile
        home_team = ticket_data.get('home_team', 'HOME')
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(COLORS['primary'])
        c.drawCentredString(x + width/2, content_y, home_team[:15])

        # Logo placeholder
        draw_logo_placeholder(c, x + width/2 - 15*mm, content_y - 22*mm, 30*mm,
                              home_team[0] if home_team else 'H', COLORS['primary'])

        # Label HOME
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(COLORS['text_light'])
        c.drawCentredString(x + width/2, content_y - 28*mm, "HOME")

    else:
        # Partie droite: Equipe visiteur
        away_team = ticket_data.get('away_team', 'AWAY')
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(COLORS['accent'])
        c.drawCentredString(x + width/2, content_y, away_team[:15])

        # Logo placeholder
        draw_logo_placeholder(c, x + width/2 - 15*mm, content_y - 22*mm, 30*mm,
                              away_team[0] if away_team else 'A', COLORS['accent'])

        # Label AWAY
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(COLORS['text_light'])
        c.drawCentredString(x + width/2, content_y - 28*mm, "AWAY")

    # === INFOS MATCH ===
    info_y = content_y - 42*mm

    # Date
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLORS['text'])
    match_date = ticket_data.get('match_date', 'DATE A DEFINIR')
    c.drawCentredString(x + width/2, info_y, f"📅 {match_date}")

    # Heure et lieu
    c.setFont("Helvetica", 8)
    c.setFillColor(COLORS['text_light'])
    gate_time = ticket_data.get('gate_opens', '13:00')
    venue = ticket_data.get('venue', 'Terrain ADEIB, Illara')[:20]
    c.drawCentredString(x + width/2, info_y - 5*mm, f"🕐 {gate_time} | 📍 {venue}")

    # === PRIX EN GRAND ===
    price_y = info_y - 18*mm
    c.setFillColor(COLORS['primary'])
    c.roundRect(x + 10*mm, price_y - 8*mm, width - 20*mm, 14*mm, 3*mm, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(COLORS['white'])
    currency = ticket_data.get('currency', 'CFA')
    symbol = '₦' if currency == 'NGN' else 'CFA'
    price = ticket_data.get('price', 500)
    c.drawCentredString(x + width/2, price_y, f"{symbol} {price}")

    # === CONDITIONS ===
    c.setFont("Helvetica", 7)
    c.setFillColor(COLORS['text_light'])
    c.drawCentredString(x + width/2, y + 15*mm, "Valable 24h - Non remboursable")

    # === NUMERO DE TICKET ===
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLORS['secondary'])
    ticket_num = ticket_data.get('ticket_number', '000000')
    c.drawCentredString(x + width/2, y + 8*mm, f"N° {ticket_num}")

    # Siege
    seat = ticket_data.get('seat_number', '')
    if seat:
        c.setFont("Helvetica", 8)
        c.setFillColor(COLORS['primary'])
        c.drawCentredString(x + width/2, y + 22*mm, f"Siège: {seat}")


def generate_tickets_pdf_premium(match, config, tickets_data):
    """
    Genere un PDF avec les tickets premium en format A4 paysage
    Deux tickets par page (côte à côte)
    """
    buffer = io.BytesIO()

    # Format A4 paysage
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Dimensions d'un ticket (2 tickets par page en hauteur)
    ticket_width = page_width - 30*mm  # Marges
    ticket_height = 120*mm
    margin_x = 15*mm
    margin_y = 20*mm

    gap_y = 15*mm

    ticket_idx = 0
    total_tickets = len(tickets_data)

    while ticket_idx < total_tickets:
        # En-tete de page
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(COLORS['primary'])
        c.drawString(margin_x, page_height - 12*mm,
                    f"TICKETS PREMIUM - {match.home_team.name} vs {match.away_team.name}")

        c.setFont("Helvetica", 9)
        c.setFillColor(COLORS['text_light'])
        page_num = (ticket_idx // 2) + 1
        total_pages = (total_tickets + 1) // 2
        c.drawRightString(page_width - margin_x, page_height - 12*mm,
                         f"Page {page_num}/{total_pages}")

        # Ligne sous l'en-tete
        c.setStrokeColor(COLORS['border'])
        c.setLineWidth(0.5)
        c.line(margin_x, page_height - 15*mm, page_width - margin_x, page_height - 15*mm)

        # Dessiner jusqu'a 2 tickets par page
        for row in range(2):
            if ticket_idx >= total_tickets:
                break

            ticket_data = tickets_data[ticket_idx]

            y_pos = page_height - margin_y - (row + 1) * ticket_height - row * gap_y

            draw_premium_ticket_landscape(c, margin_x, y_pos, ticket_width, ticket_height,
                                         ticket_data, config, match)

            ticket_idx += 1

        # Nouvelle page si necessaire
        if ticket_idx < total_tickets:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


def generate_ticket_preview_premium(match, config):
    """Genere un PDF de previsualisation d'un ticket premium"""
    buffer = io.BytesIO()
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    ticket_data = {
        'ticket_number': 'DEMO-001',
        'home_team': match.home_team.name,
        'away_team': match.away_team.name,
        'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE',
        'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
        'venue': match.venue or 'Terrain ADEIB, Illara',
        'price': 500,
        'seat_number': 'A01',
    }

    # Dimensions
    ticket_width = page_width - 60*mm
    ticket_height = 120*mm
    x = (page_width - ticket_width) / 2
    y = (page_height - ticket_height) / 2

    # Titre de previsualisation
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(COLORS['primary'])
    c.drawCentredString(page_width/2, page_height - 15*mm, "APERÇU DU TICKET PREMIUM")

    c.setFont("Helvetica", 10)
    c.setFillColor(COLORS['text_light'])
    c.drawCentredString(page_width/2, page_height - 22*mm,
                       "Format A4 Paysage - Deux parties avec perforation")

    # Dessiner le ticket
    draw_premium_ticket_landscape(c, x, y, ticket_width, ticket_height,
                                 ticket_data, config, match)

    c.save()
    buffer.seek(0)
    return buffer


# === Fonctions existantes pour compatibilite ===

def draw_ticket_small(c, x, y, width, height, ticket_data, config):
    """Dessine un petit ticket (10 par page A4) - version standard"""

    c.setFillColor(COLORS['white'])
    c.rect(x, y, width, height, fill=1, stroke=0)

    c.setStrokeColor(COLORS['border'])
    c.setLineWidth(0.5)
    c.rect(x, y, width, height, fill=0, stroke=1)

    c.setFillColor(COLORS['primary'])
    c.rect(x, y, 4*mm, height, fill=1, stroke=0)

    c.setDash(2, 2)
    c.setStrokeColor(COLORS['border'])
    c.line(x + width - 12*mm, y + 2*mm, x + width - 12*mm, y + height - 2*mm)
    c.setDash()

    content_x = x + 6*mm
    content_y = y + height - 5*mm

    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(COLORS['primary'])
    c.drawString(content_x, content_y - 4*mm, "ADEIB U26")

    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(COLORS['secondary'])
    home_team = ticket_data.get('home_team', 'HOME')[:12]
    away_team = ticket_data.get('away_team', 'AWAY')[:12]
    c.drawString(content_x, content_y - 12*mm, f"{home_team}")
    c.setFont("Helvetica", 5)
    c.setFillColor(COLORS['text_light'])
    c.drawString(content_x, content_y - 15*mm, "VS")
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(COLORS['secondary'])
    c.drawString(content_x, content_y - 18*mm, f"{away_team}")

    c.setFont("Helvetica", 5)
    c.setFillColor(COLORS['text'])
    match_date = ticket_data.get('match_date', 'DATE')
    c.drawString(content_x, content_y - 22*mm, match_date)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(COLORS['accent'])
    currency = ticket_data.get('currency', 'CFA')
    symbol = '₦' if currency == 'NGN' else 'CFA'
    price = ticket_data.get('price', 500)
    c.drawString(content_x, y + 4*mm, f"{symbol} {price}")

    ticket_num = ticket_data.get('ticket_number', '000000')
    c.setFont("Helvetica", 5)
    c.setFillColor(COLORS['text'])
    c.drawCentredString(x + width - 6*mm, y + 2*mm, ticket_num, direction=90)


def generate_tickets_pdf(match, config, tickets_data):
    """
    Genere un PDF avec les tickets bulk (version standard ou premium)
    Si config.ticket_size == 'premium', utilise le format paysage
    """
    if config.ticket_size == 'premium':
        return generate_tickets_pdf_premium(match, config, tickets_data)

    # Version standard existante
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    ticket_size = config.ticket_size

    if ticket_size == 'small':
        ticket_w = 90*mm
        ticket_h = 52*mm
        cols = 2
        rows = 5
        margin_x = 10*mm
        margin_y = 15*mm
    elif ticket_size == 'medium':
        ticket_w = 90*mm
        ticket_h = 85*mm
        cols = 2
        rows = 3
        margin_x = 10*mm
        margin_y = 10*mm
    else:  # large
        ticket_w = 90*mm
        ticket_h = 130*mm
        cols = 2
        rows = 2
        margin_x = 10*mm
        margin_y = 10*mm

    gap_x = (width - 2*margin_x - cols*ticket_w) / (cols - 1) if cols > 1 else 0
    gap_y = (height - 2*margin_y - rows*ticket_h) / (rows - 1) if rows > 1 else 0

    ticket_idx = 0
    total_tickets = len(tickets_data)

    while ticket_idx < total_tickets:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(COLORS['primary'])
        c.drawString(margin_x, height - 10*mm,
                    f"TICKETS - {match.home_team.name} vs {match.away_team.name}")
        c.setFont("Helvetica", 8)
        c.setFillColor(COLORS['text_light'])
        page_num = (ticket_idx // (cols * rows)) + 1
        total_pages = (total_tickets + cols * rows - 1) // (cols * rows)
        c.drawRightString(width - margin_x, height - 10*mm, f"Page {page_num}/{total_pages}")

        c.setStrokeColor(COLORS['border'])
        c.line(margin_x, height - 12*mm, width - margin_x, height - 12*mm)

        for row in range(rows):
            for col in range(cols):
                if ticket_idx >= total_tickets:
                    break

                ticket_data = tickets_data[ticket_idx]
                x = margin_x + col * (ticket_w + gap_x)
                y = height - margin_y - (row + 1) * ticket_h - row * gap_y - 5*mm

                draw_ticket_small(c, x, y, ticket_w, ticket_h, ticket_data, config)
                ticket_idx += 1

            if ticket_idx >= total_tickets:
                break

        if ticket_idx < total_tickets:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


def generate_ticket_preview(match, config):
    """Genere un PDF de previsualisation"""
    if config.ticket_size == 'premium':
        return generate_ticket_preview_premium(match, config)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    ticket_data = {
        'ticket_number': 'DEMO-001',
        'home_team': match.home_team.name,
        'away_team': match.away_team.name,
        'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE',
        'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
        'gate_closes': str(config.gate_closes)[:5] if config.gate_closes else '19:00',
        'venue': match.venue or 'Terrain ADEIB, Illara',
        'price': 500,
        'seat_number': 'A01',
    }

    if config.ticket_size == 'small':
        ticket_w, ticket_h = 90*mm, 52*mm
    elif config.ticket_size == 'medium':
        ticket_w, ticket_h = 90*mm, 85*mm
    else:
        ticket_w, ticket_h = 90*mm, 130*mm

    x = (width - ticket_w) / 2
    y = (height - ticket_h) / 2

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(COLORS['primary'])
    c.drawCentredString(width/2, height - 20*mm, "APERÇU DU TICKET")

    draw_ticket_small(c, x, y, ticket_w, ticket_h, ticket_data, config)

    c.save()
    buffer.seek(0)
    return buffer
