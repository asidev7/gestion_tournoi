"""
Designer de Tickets Premium - ADEIB U26
Design unique, moderne et stylé avec bordure rectangulaire
"""
import io
import qrcode
import random
import string
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, Polygon
from reportlab.graphics.charts.textlabels import Label
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFilter


# === PALETTE DE COULEURS PREMIUM ===
COLORS = {
    'primary': HexColor('#0d5c2e'),        # Vert foot
    'primary_light': HexColor('#1a7a3e'),  # Vert clair
    'secondary': HexColor('#1a1a1a'),      # Noir
    'accent': HexColor('#c41e3a'),         # Rouge sport
    'accent_light': HexColor('#e63950'),   # Rouge clair
    'gold': HexColor('#d4af37'),           # Or
    'gold_light': HexColor('#f4d03f'),     # Or clair
    'white': white,
    'black': black,
    'dark_gray': HexColor('#2c3e50'),
    'medium_gray': HexColor('#5d6d7e'),
    'light_gray': HexColor('#ecf0f1'),
    'border_dark': HexColor('#1a252f'),
    'gradient_start': HexColor('#0d5c2e'),
    'gradient_end': HexColor('#145a32'),
    'neon_green': HexColor('#39ff14'),
    'neon_gold': HexColor('#ffd700'),
}


def generate_unique_ticket_number():
    """Génère un numéro de ticket unique au format ADEIB-XXXXXX"""
    timestamp = datetime.now().strftime('%y%m')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ADEIB-{timestamp}{random_part}"


def create_rounded_qr_image(data, size=400, border_radius=20):
    """Crée un QR code avec coins arrondis"""
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Créer l'image QR avec couleurs personnalisées
    qr_img = qr.make_image(fill_color="#0d5c2e", back_color="white")
    qr_img = qr_img.convert('RGBA')

    # Créer un masque avec coins arrondis
    mask = Image.new('L', qr_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, qr_img.size[0], qr_img.size[1]], radius=border_radius, fill=255)

    # Appliquer le masque
    output = Image.new('RGBA', qr_img.size, (255, 255, 255, 0))
    output.paste(qr_img, (0, 0), mask)

    return output


def draw_gradient_background(c, x, y, width, height, color1, color2, direction='vertical'):
    """Dessine un dégradé simple ligne par ligne"""
    steps = int(height)
    for i in range(steps):
        ratio = i / steps
        r = color1.red * (1 - ratio) + color2.red * ratio
        g = color1.green * (1 - ratio) + color2.green * ratio
        b = color1.blue * (1 - ratio) + color2.blue * ratio

        c.setStrokeColor(Color(r, g, b))
        c.setLineWidth(1)
        if direction == 'vertical':
            c.line(x, y + i, x + width, y + i)
        else:
            c.line(x + i, y, x + i, y + height)


def draw_rounded_rect(c, x, y, width, height, radius, fill_color=None, stroke_color=None, stroke_width=1):
    """Dessine un rectangle avec coins arrondis"""
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
    c.setLineWidth(stroke_width)

    # Dessiner le rectangle avec coins arrondis
    c.roundRect(x, y, width, height, radius, fill=1 if fill_color else 0, stroke=1 if stroke_color else 0)


def draw_double_border(c, x, y, width, height, inner_radius=8, outer_radius=12,
                       inner_color=COLORS['gold'], outer_color=COLORS['primary'],
                       inner_width=2, outer_width=4):
    """Dessine une double bordure rectangulaire stylisée"""
    # Bordure extérieure (plus épaisse)
    c.setStrokeColor(outer_color)
    c.setLineWidth(outer_width)
    c.roundRect(x - outer_width/2, y - outer_width/2, width + outer_width, height + outer_width,
                outer_radius, fill=0, stroke=1)

    # Bordure intérieure (plus fine, or)
    c.setStrokeColor(inner_color)
    c.setLineWidth(inner_width)
    c.roundRect(x + inner_width, y + inner_width, width - 2*inner_width, height - 2*inner_width,
                inner_radius, fill=0, stroke=1)


def draw_decorative_corners(c, x, y, width, height, corner_size=15, color=COLORS['gold']):
    """Dessine des coins décoratifs aux 4 angles"""
    c.setStrokeColor(color)
    c.setLineWidth(3)

    # Coin supérieur gauche
    c.line(x, y + height - corner_size, x, y + height)
    c.line(x, y + height, x + corner_size, y + height)

    # Coin supérieur droit
    c.line(x + width - corner_size, y + height, x + width, y + height)
    c.line(x + width, y + height, x + width, y + height - corner_size)

    # Coin inférieur gauche
    c.line(x, y + corner_size, x, y)
    c.line(x, y, x + corner_size, y)

    # Coin inférieur droit
    c.line(x + width - corner_size, y, x + width, y)
    c.line(x + width, y, x + width, y + corner_size)


def draw_ornament_pattern(c, x, y, width, height, color=COLORS['gold']):
    """Dessine un motif ornemental subtil"""
    c.setStrokeColor(color)
    c.setLineWidth(0.5)

    # Motif de points subtil
    dot_spacing = 8
    for i in range(int(width / dot_spacing)):
        for j in range(int(height / dot_spacing)):
            if (i + j) % 2 == 0:
                c.setFillColor(color)
                c.circle(x + i * dot_spacing, y + j * dot_spacing, 0.5, fill=1, stroke=0)


def draw_team_logo_placeholder(c, x, y, size, letter, bg_color, text_color=white):
    """Dessine un logo d'équipe circulaire avec la première lettre"""
    # Cercle extérieur doré
    c.setFillColor(COLORS['gold'])
    c.circle(x + size/2, y + size/2, size/2, fill=1, stroke=0)

    # Cercle intérieur coloré
    c.setFillColor(bg_color)
    c.circle(x + size/2, y + size/2, size/2 - 2, fill=1, stroke=0)

    # Lettre
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", size * 0.45)
    c.drawCentredString(x + size/2, y + size/2 - size*0.12, letter.upper())


def draw_vs_badge(c, x, y, size=20):
    """Dessine un badge VS stylisé"""
    # Cercle extérieur
    c.setFillColor(COLORS['accent'])
    c.circle(x, y, size, fill=1, stroke=0)

    # Cercle intérieur
    c.setFillColor(COLORS['white'])
    c.circle(x, y, size - 3, fill=1, stroke=0)

    # Texte VS
    c.setFillColor(COLORS['accent'])
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x, y - 3, "VS")


def draw_ticket_unique_design(c, x, y, width, height, ticket_data, match, config):
    """
    Dessine un ticket avec un design UNIQUE et COOL
    Bordure rectangulaire stylisée avec QR code central
    """
    # === FOND AVEC DÉGRADÉ SUBTIL ===
    draw_gradient_background(c, x, y, width, height,
                            COLORS['light_gray'], white, direction='vertical')

    # === BORDURE RECTANGULAIRE STYLISÉE ===
    margin = 8
    inner_x = x + margin
    inner_y = y + margin
    inner_width = width - 2 * margin
    inner_height = height - 2 * margin

    # Double bordure avec coins décoratifs
    draw_double_border(c, inner_x, inner_y, inner_width, inner_height,
                       inner_radius=5, outer_radius=8,
                       inner_color=COLORS['gold'], outer_color=COLORS['primary'])

    # Coins décoratifs
    draw_decorative_corners(c, inner_x, inner_y, inner_width, inner_height,
                           corner_size=12, color=COLORS['gold'])

    # === EN-TÊTE AVEC BANDE VERTE ===
    header_height = 22
    header_y = inner_y + inner_height - header_height

    # Bande verte principale
    c.setFillColor(COLORS['primary'])
    c.roundRect(inner_x + 4, header_y, inner_width - 8, header_height - 4, 4, fill=1, stroke=0)

    # Bande dorée décorative en haut
    c.setFillColor(COLORS['gold'])
    c.roundRect(inner_x + 4, header_y + header_height - 8, inner_width - 8, 4, 2, fill=1, stroke=0)

    # Logo ADEIB
    c.setFillColor(COLORS['white'])
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(inner_x + inner_width/2, header_y + 9, "⚽ ADEIB U26 ILLARA")

    # === SECTION DES ÉQUIPES ===
    teams_y = header_y - 28

    home_team = ticket_data.get('home_team', 'HOME')
    away_team = ticket_data.get('away_team', 'AWAY')

    # Logo équipe domicile (à gauche)
    logo_size = 18
    home_x = inner_x + 20
    draw_team_logo_placeholder(c, home_x, teams_y - logo_size/2, logo_size,
                               home_team[0] if home_team else 'H', COLORS['primary'])

    # Nom équipe domicile
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLORS['primary'])
    c.drawCentredString(home_x + logo_size/2, teams_y - logo_size/2 - 8, home_team[:10])

    # Badge VS au centre
    vs_x = inner_x + inner_width/2
    draw_vs_badge(c, vs_x, teams_y, size=12)

    # Logo équipe visiteur (à droite)
    away_x = inner_x + inner_width - 20 - logo_size
    draw_team_logo_placeholder(c, away_x, teams_y - logo_size/2, logo_size,
                               away_team[0] if away_team else 'A', COLORS['accent'])

    # Nom équipe visiteur
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLORS['accent'])
    c.drawCentredString(away_x + logo_size/2, teams_y - logo_size/2 - 8, away_team[:10])

    # === QR CODE CENTRAL (POINT FORT DU DESIGN) ===
    qr_size = 32
    qr_x = inner_x + (inner_width - qr_size) / 2
    qr_y = teams_y - logo_size/2 - 45

    # Fond blanc arrondi pour le QR
    c.setFillColor(white)
    c.roundRect(qr_x - 3, qr_y - 3, qr_size + 6, qr_size + 6, 5, fill=1, stroke=0)

    # Bordure dorée autour du QR
    c.setStrokeColor(COLORS['gold'])
    c.setLineWidth(2)
    c.roundRect(qr_x - 3, qr_y - 3, qr_size + 6, qr_size + 6, 5, fill=0, stroke=1)

    # Générer et dessiner le QR code
    qr_data = f"TICKET:{ticket_data.get('ticket_number', '000000')}|MATCH:{match.id}|VALID:ADEIB-U26|{datetime.now().strftime('%Y%m%d')}"

    try:
        qr_img = create_rounded_qr_image(qr_data, size=400, border_radius=20)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        img_reader = ImageReader(qr_buffer)
        c.drawImage(img_reader, qr_x, qr_y, width=qr_size, height=qr_size)
    except Exception:
        # Fallback simple
        draw_simple_qr(c, qr_data, qr_x, qr_y, qr_size)

    # === INFORMATIONS DU MATCH ===
    info_y = qr_y - 15

    # Date avec icône
    match_date = ticket_data.get('match_date', 'DATE À DÉFINIR')
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(COLORS['dark_gray'])
    c.drawCentredString(inner_x + inner_width/2, info_y, f"📅 {match_date}")

    # Heure et lieu
    c.setFont("Helvetica", 7)
    c.setFillColor(COLORS['medium_gray'])
    gate_time = ticket_data.get('gate_opens', '13:00')
    venue = ticket_data.get('venue', 'Terrain ADEIB, Illara')[:25]
    c.drawCentredString(inner_x + inner_width/2, info_y - 6, f"🕐 {gate_time}  |  📍 {venue}")

    # === PRIX EN BADGE ===
    price_y = info_y - 22
    badge_width = 35
    badge_height = 14
    badge_x = inner_x + (inner_width - badge_width) / 2

    # Fond du badge prix
    c.setFillColor(COLORS['gold'])
    c.roundRect(badge_x, price_y - badge_height/2, badge_width, badge_height, 7, fill=1, stroke=0)

    # Bordure
    c.setStrokeColor(COLORS['primary'])
    c.setLineWidth(1)
    c.roundRect(badge_x, price_y - badge_height/2, badge_width, badge_height, 7, fill=0, stroke=1)

    # Prix
    c.setFillColor(COLORS['primary'])
    c.setFont("Helvetica-Bold", 11)
    price = ticket_data.get('price', 500)
    currency = ticket_data.get('currency', 'XOF')
    symbol = '₦' if currency == 'NGN' else 'CFA'
    c.drawCentredString(inner_x + inner_width/2, price_y - 2, f"{symbol} {price}")

    # === NUMÉRO DE TICKET (BAS) ===
    ticket_num = ticket_data.get('ticket_number', '000000')
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(COLORS['secondary'])
    c.drawCentredString(inner_x + inner_width/2, inner_y + 12, f"N° {ticket_num}")

    # Code-barres stylisé (lignes verticales)
    barcode_y = inner_y + 5
    barcode_x = inner_x + inner_width/2 - 20
    c.setStrokeColor(COLORS['medium_gray'])
    c.setLineWidth(0.5)
    for i in range(40):
        line_height = 4 if i % 5 == 0 else 2
        c.line(barcode_x + i, barcode_y, barcode_x + i, barcode_y + line_height)

    # === SÉPARATEUR POINTILLÉ (pour découpe) ===
    c.setDash(2, 2)
    c.setStrokeColor(COLORS['medium_gray'])
    c.setLineWidth(0.5)
    c.line(inner_x + inner_width - 15, inner_y + 10, inner_x + inner_width - 15, inner_y + inner_height - 10)
    c.setDash()

    # Petite paire de ciseaux
    c.setFont("Helvetica", 6)
    c.setFillColor(COLORS['medium_gray'])
    c.drawCentredString(inner_x + inner_width - 15, inner_y + inner_height/2, "✂")

    # === BANDE VERTICALE DÉCORATIVE (droite) ===
    c.setFillColor(COLORS['primary'])
    c.roundRect(inner_x + inner_width - 8, inner_y + 5, 4, inner_height - 10, 2, fill=1, stroke=0)


def draw_simple_qr(c, data, x, y, size):
    """Dessine un QR code simple en fallback"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0d5c2e", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_reader = ImageReader(buffer)
    c.drawImage(img_reader, x, y, width=size, height=size)


def generate_cool_ticket_pdf(match, config, ticket_data=None, is_preview=True):
    """
    Génère un PDF avec un ticket au design unique et cool
    Format: Ticket individuel stylisé
    """
    buffer = io.BytesIO()
    page_width, page_height = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    # Si c'est une prévisualisation, générer des données de démo
    if ticket_data is None:
        ticket_data = {
            'ticket_number': generate_unique_ticket_number() if not is_preview else 'ADEIB-DEMO-001',
            'home_team': match.home_team.name if match.home_team else 'HOME',
            'away_team': match.away_team.name if match.away_team else 'AWAY',
            'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE À DÉFINIR',
            'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
            'venue': match.venue or 'Terrain ADEIB, Illara',
            'price': config.price if config else 500,
            'currency': config.currency if config else 'XOF',
            'seat_number': 'A-12',
        }

    # Dimensions du ticket
    ticket_width = 100 * mm
    ticket_height = 160 * mm

    # Centrer le ticket sur la page
    x = (page_width - ticket_width) / 2
    y = (page_height - ticket_height) / 2 + 20 * mm

    # Titre de prévisualisation
    if is_preview:
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(COLORS['primary'])
        c.drawCentredString(page_width/2, page_height - 25*mm, "🎫 TICKET PREMIUM ADEIB U26")

        c.setFont("Helvetica", 10)
        c.setFillColor(COLORS['medium_gray'])
        c.drawCentredString(page_width/2, page_height - 32*mm, "Design unique avec QR code et bordure rectangulaire")

    # Dessiner le ticket
    draw_ticket_unique_design(c, x, y, ticket_width, ticket_height, ticket_data, match, config)

    # Informations en bas de page
    c.setFont("Helvetica", 8)
    c.setFillColor(COLORS['medium_gray'])
    c.drawCentredString(page_width/2, 20*mm, "Ce ticket est unique et valable pour une seule entrée")
    c.drawCentredString(page_width/2, 15*mm, "ADEIB U26 Illara - Tournoi de Football")

    c.save()
    buffer.seek(0)
    return buffer


def generate_bulk_cool_tickets(match, config, quantity=10):
    """
    Génère plusieurs tickets cool sur une page A4
    Format: 2 colonnes x 4 rangées = 8 tickets par page
    """
    buffer = io.BytesIO()
    page_width, page_height = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    # Dimensions d'un ticket (plus petit pour tenir sur la page)
    ticket_width = 85 * mm
    ticket_height = 65 * mm

    # Marges et espacements
    margin_x = 15 * mm
    margin_y = 20 * mm
    gap_x = 10 * mm
    gap_y = 8 * mm

    cols = 2
    rows = 4

    tickets_per_page = cols * rows
    total_pages = (quantity + tickets_per_page - 1) // tickets_per_page

    ticket_idx = 0

    while ticket_idx < quantity:
        # En-tête de page
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(COLORS['primary'])
        c.drawString(margin_x, page_height - 12*mm,
                    f"TICKETS {match.home_team.name} vs {match.away_team.name}")

        c.setFont("Helvetica", 9)
        c.setFillColor(COLORS['medium_gray'])
        page_num = (ticket_idx // tickets_per_page) + 1
        c.drawRightString(page_width - margin_x, page_height - 12*mm,
                         f"Page {page_num}/{total_pages}")

        # Ligne de séparation
        c.setStrokeColor(COLORS['gold'])
        c.setLineWidth(1)
        c.line(margin_x, page_height - 15*mm, page_width - margin_x, page_height - 15*mm)

        # Dessiner les tickets
        for row in range(rows):
            for col in range(cols):
                if ticket_idx >= quantity:
                    break

                # Position du ticket
                x = margin_x + col * (ticket_width + gap_x)
                y = page_height - margin_y - (row + 1) * ticket_height - row * gap_y - 10*mm

                # Générer les données du ticket
                ticket_data = {
                    'ticket_number': generate_unique_ticket_number(),
                    'home_team': match.home_team.name if match.home_team else 'HOME',
                    'away_team': match.away_team.name if match.away_team else 'AWAY',
                    'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE',
                    'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
                    'venue': match.venue or 'Terrain ADEIB, Illara',
                    'price': config.price if config else 500,
                    'currency': config.currency if config else 'XOF',
                    'seat_number': f"{chr(65 + row)}{col + 1}",
                }

                # Dessiner le ticket (version compacte)
                draw_compact_cool_ticket(c, x, y, ticket_width, ticket_height, ticket_data, match, config)

                ticket_idx += 1

            if ticket_idx >= quantity:
                break

        # Nouvelle page si nécessaire
        if ticket_idx < quantity:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


def draw_compact_cool_ticket(c, x, y, width, height, ticket_data, match, config):
    """Version compacte du ticket cool pour impression en masse"""

    # Fond
    c.setFillColor(COLORS['light_gray'])
    c.roundRect(x, y, width, height, 5, fill=1, stroke=0)

    # Bordure double
    draw_double_border(c, x, y, width, height,
                       inner_radius=3, outer_radius=5,
                       inner_color=COLORS['gold'], outer_color=COLORS['primary'],
                       inner_width=1, outer_width=2)

    # Header
    header_height = 12
    c.setFillColor(COLORS['primary'])
    c.roundRect(x + 3, y + height - header_height - 3, width - 6, header_height, 3, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x + width/2, y + height - 10, "ADEIB U26 ILLARA ⚽")

    # Équipes
    teams_y = y + height - 22
    home_team = ticket_data.get('home_team', 'HOME')[:8]
    away_team = ticket_data.get('away_team', 'AWAY')[:8]

    # Logo et nom domicile (gauche)
    draw_team_logo_placeholder(c, x + 8, teams_y - 10, 12, home_team[0] if home_team else 'H', COLORS['primary'])
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(COLORS['primary'])
    c.drawCentredString(x + 14, teams_y - 14, home_team)

    # VS au centre
    c.setFillColor(COLORS['accent'])
    c.circle(x + width/2, teams_y - 4, 6, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 5)
    c.drawCentredString(x + width/2, teams_y - 5, "VS")

    # Logo et nom visiteur (droite)
    draw_team_logo_placeholder(c, x + width - 20, teams_y - 10, 12, away_team[0] if away_team else 'A', COLORS['accent'])
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(COLORS['accent'])
    c.drawCentredString(x + width - 14, teams_y - 14, away_team)

    # QR Code (petit)
    qr_size = 18
    qr_x = x + (width - qr_size) / 2
    qr_y = teams_y - 30

    c.setFillColor(white)
    c.roundRect(qr_x - 2, qr_y - 2, qr_size + 4, qr_size + 4, 3, fill=1, stroke=0)
    c.setStrokeColor(COLORS['gold'])
    c.setLineWidth(1)
    c.roundRect(qr_x - 2, qr_y - 2, qr_size + 4, qr_size + 4, 3, fill=0, stroke=1)

    qr_data = f"TICKET:{ticket_data.get('ticket_number', '000000')}|MATCH:{match.id}"
    draw_simple_qr(c, qr_data, qr_x, qr_y, qr_size)

    # Infos
    c.setFont("Helvetica", 5)
    c.setFillColor(COLORS['dark_gray'])
    match_date = ticket_data.get('match_date', 'DATE')
    c.drawCentredString(x + width/2, qr_y - 6, f"📅 {match_date}")

    # Prix
    c.setFillColor(COLORS['gold'])
    c.roundRect(x + width/2 - 12, y + 10, 24, 8, 4, fill=1, stroke=0)
    c.setFillColor(COLORS['primary'])
    c.setFont("Helvetica-Bold", 7)
    price = ticket_data.get('price', 500)
    currency = ticket_data.get('currency', 'XOF')
    symbol = '₦' if currency == 'NGN' else 'CFA'
    c.drawCentredString(x + width/2, y + 13, f"{symbol}{price}")

    # Numéro de ticket
    c.setFont("Helvetica", 6)
    c.setFillColor(COLORS['secondary'])
    ticket_num = ticket_data.get('ticket_number', '000000')
    c.drawCentredString(x + width/2, y + 4, ticket_num[-12:])


def generate_ticket_from_model(ticket_instance):
    """
    Génère un ticket PDF à partir d'une instance Ticket du modèle
    """
    from .models import Match, TicketConfig

    config = ticket_instance.config
    match = config.match

    ticket_data = {
        'ticket_number': ticket_instance.ticket_number,
        'home_team': match.home_team.name if match.home_team else 'HOME',
        'away_team': match.away_team.name if match.away_team else 'AWAY',
        'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE À DÉFINIR',
        'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
        'venue': match.venue or 'Terrain ADEIB, Illara',
        'price': config.price,
        'currency': config.currency,
        'seat_number': ticket_instance.seat_number or 'LIBRE',
    }

    return generate_cool_ticket_pdf(match, config, ticket_data, is_preview=False)
