"""
Générateur de tickets PDF — format unique.
10 tickets par page A4 (portrait, 2 colonnes x 5 lignes).
Filigrane logo ADEIB, logos d'équipes (ou ballon par défaut),
fond « tournoi-adeib.site ». Prix dynamique.
"""
import io
import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.utils import ImageReader

try:
    from django.contrib.staticfiles import finders
except Exception:  # pragma: no cover
    finders = None


COLORS = {
    'primary': HexColor('#0d7a3c'),
    'primary_dark': HexColor('#064d24'),
    'secondary': HexColor('#1a1a1a'),
    'gold': HexColor('#e7b84b'),
    'white': white,
    'black': black,
    'border': HexColor('#c9c9c9'),
    'text': HexColor('#1a1a1a'),
    'text_light': HexColor('#6b6b6b'),
    'perforation': HexColor('#9a9a9a'),
}

TICKETS_PER_PAGE = 10
COLS = 2
ROWS = 5
SITE_URL = 'tournoi-adeib.site'
SITE_BASE = 'https://tournoi-adeib.site'


def _static_path(rel):
    if finders:
        p = finders.find(rel)
        if p:
            return p
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', rel)
    return p if os.path.exists(p) else None


def _adeib_logo():
    return _static_path('images/adeib_logo.png')


def _image_reader(path):
    try:
        if path and os.path.exists(path):
            return ImageReader(path)
    except Exception:
        pass
    return None


def _currency_symbol(currency):
    return '₦' if currency == 'NGN' else 'CFA'


def _currency_word(currency):
    return 'Naira' if currency == 'NGN' else 'CFA'


def _draw_qr(c, data, x, y, size_mm):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=3, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d7a3c", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    c.drawImage(ImageReader(buf), x, y, width=size_mm * mm, height=size_mm * mm)


def _draw_team_badge(c, reader, x, y, d, letter):
    """Logo d'équipe (cercle) ou ballon par défaut."""
    r = d / 2
    cx, cy = x + r, y + r
    if reader:
        c.saveState()
        p = c.beginPath()
        p.circle(cx, cy, r)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(reader, x, y, width=d, height=d, mask='auto', preserveAspectRatio=True)
        c.restoreState()
        c.setStrokeColor(COLORS['border'])
        c.setLineWidth(0.5)
        c.circle(cx, cy, r, stroke=1, fill=0)
    else:
        c.setFillColor(COLORS['primary'])
        c.circle(cx, cy, r, fill=1, stroke=0)
        c.setFillColor(COLORS['white'])
        c.setFont("Helvetica-Bold", d * 0.5)
        c.drawCentredString(cx, cy - d * 0.18, '⚽')


def draw_ticket(c, x, y, width, height, data, config, logos):
    """Ticket compact pour une grille 2 colonnes."""
    pad = 4 * mm

    # Cadre
    c.setLineWidth(0.8)
    c.setStrokeColor(COLORS['border'])
    c.roundRect(x, y, width, height, 2.5 * mm, fill=0, stroke=1)

    # Filigrane logo ADEIB (centré, très clair)
    if logos.get('adeib'):
        c.saveState()
        try:
            c.setFillAlpha(0.06)
            c.setStrokeAlpha(0.06)
        except Exception:
            pass
        wm = min(width, height) * 0.7
        c.drawImage(logos['adeib'], x + (width - wm) / 2, y + (height - wm) / 2,
                    width=wm, height=wm, mask='auto', preserveAspectRatio=True)
        c.restoreState()

    # Bande gauche verte
    c.setFillColor(COLORS['primary'])
    c.rect(x, y, 2.5 * mm, height, fill=1, stroke=0)

    inner_x = x + pad + 1.5 * mm
    top = y + height

    # En-tête
    c.setFillColor(COLORS['primary_dark'])
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(inner_x, top - 6 * mm, "CUP LEGENDS · ADEIB U26")

    # Logos + VS
    badge = 9 * mm
    badge_y = top - 19 * mm
    _draw_team_badge(c, logos.get('home'), inner_x, badge_y, badge,
                     str(data.get('home_team', 'H'))[:1])
    _draw_team_badge(c, logos.get('away'), inner_x + badge + 16 * mm, badge_y, badge,
                     str(data.get('away_team', 'A'))[:1])
    c.setFillColor(COLORS['text'])
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(inner_x + badge + 8 * mm, badge_y + badge / 2 - 2, "VS")

    # Noms d'équipes
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(COLORS['text'])
    c.drawString(inner_x, badge_y - 4 * mm,
                 f"{str(data.get('home_team',''))[:14]}  -  {str(data.get('away_team',''))[:14]}")

    # Date / lieu
    c.setFont("Helvetica", 6)
    c.setFillColor(COLORS['text_light'])
    c.drawString(inner_x, y + 11 * mm,
                 f"{data.get('match_date','Date')}  ·  {data.get('gate_opens','13:00')}")
    c.drawString(inner_x, y + 8 * mm, str(data.get('venue', 'Stade Cup Legends'))[:30])

    # N° ticket + validité (l'URL n'apparaît plus qu'en filigrane)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(COLORS['secondary'])
    c.drawString(inner_x, y + 4.5 * mm, f"N° {data.get('ticket_number','000000')}")
    c.setFont("Helvetica", 5.5)
    c.setFillColor(COLORS['text_light'])
    c.drawString(inner_x, y + 2 * mm, "Valable 24h · Non remboursable")

    # Talon droit : prix + QR
    stub_w = 26 * mm
    perf_x = x + width - stub_w
    c.setDash(1.5, 1.5)
    c.setStrokeColor(COLORS['perforation'])
    c.line(perf_x, y + 2.5 * mm, perf_x, y + height - 2.5 * mm)
    c.setDash()
    cx = perf_x + stub_w / 2

    currency = data.get('currency', 'NGN')
    word = _currency_word(currency)
    price = data.get('price', 200)
    c.setFillColor(COLORS['primary'])
    c.roundRect(perf_x + 2 * mm, top - 9 * mm, stub_w - 4 * mm, 6 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(COLORS['white'])
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(cx, top - 7.3 * mm, f"{price} {word}")

    # Le QR redirige vers la page du match (suivi en direct)
    match_url = f"{SITE_BASE}/matches/{data.get('match_id','')}/"
    _draw_qr(c, match_url, cx - (13 * mm) / 2, y + 6 * mm, 13)

    seat = data.get('seat_number', '')
    c.setFont("Helvetica", 5)
    c.setFillColor(COLORS['text_light'])
    if seat:
        c.drawCentredString(cx, y + 3 * mm, f"Siège {seat}")
    c.drawCentredString(cx, y + 0.8 * mm, "Valable 24h")


def _load_logos(match):
    logos = {'adeib': _image_reader(_adeib_logo())}
    for key, team in (('home', match.home_team), ('away', match.away_team)):
        reader = None
        try:
            if getattr(team, 'logo', None) and team.logo:
                reader = _image_reader(team.logo.path)
        except Exception:
            reader = None
        logos[key] = reader
    return logos


def _draw_cut_guides(c, margin_x, margin_top, ticket_w, ticket_h, gap_x, gap_y,
                     page_height, page_width, rows_filled):
    """Lignes pointillées + ciseaux pour découper les tickets."""
    if rows_filled <= 0:
        return

    x_left = margin_x
    x_mid = margin_x + ticket_w + gap_x / 2
    x_right = margin_x + 2 * ticket_w + gap_x
    y_top = page_height - margin_top
    y_bottom = page_height - margin_top - rows_filled * ticket_h - (rows_filled - 1) * gap_y

    c.saveState()
    c.setDash(3, 3)
    c.setLineWidth(0.6)
    c.setStrokeColor(COLORS['perforation'])

    # Lignes verticales : bords + gouttière centrale
    for x in (x_left, x_mid, x_right):
        c.line(x, y_bottom, x, y_top)

    # Lignes horizontales : haut, gouttières entre lignes, bas
    y_lines = [y_top]
    for r in range(1, rows_filled):
        y = page_height - margin_top - r * ticket_h - (r - 1) * gap_y - gap_y / 2
        y_lines.append(y)
    y_lines.append(y_bottom)
    for y in y_lines:
        c.line(x_left, y, x_right, y)

    c.setDash()

    # Ciseaux sur la gouttière verticale et au bord des lignes horizontales
    c.setFillColor(COLORS['perforation'])
    c.setFont("Helvetica", 7)
    for y in y_lines:
        c.drawCentredString(x_left - 3 * mm, y - 2, "✂")
    for r in range(1, rows_filled):
        y = page_height - margin_top - r * ticket_h - (r - 1) * gap_y - gap_y / 2
        c.drawCentredString(x_mid, y - 2, "✂")
    c.restoreState()


def generate_tickets_pdf(match, config, tickets_data):
    """PDF : 10 tickets par page A4 (2 colonnes x 5 lignes)."""
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    logos = _load_logos(match)

    margin_x = 9 * mm
    margin_top = 15 * mm
    margin_bottom = 9 * mm
    gap_x = 5 * mm
    gap_y = 4 * mm

    ticket_w = (width - 2 * margin_x - (COLS - 1) * gap_x) / COLS
    usable_h = height - margin_top - margin_bottom - (ROWS - 1) * gap_y
    ticket_h = usable_h / ROWS

    total = len(tickets_data)
    idx = 0
    while idx < total:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(COLORS['primary_dark'])
        c.drawString(margin_x, height - 10 * mm,
                     f"TICKETS · {match.home_team.name} vs {match.away_team.name}")
        c.setFont("Helvetica", 7.5)
        c.setFillColor(COLORS['text_light'])
        page_num = idx // TICKETS_PER_PAGE + 1
        total_pages = (total + TICKETS_PER_PAGE - 1) // TICKETS_PER_PAGE
        c.drawRightString(width - margin_x, height - 10 * mm,
                          f"Page {page_num}/{total_pages}")

        for row in range(ROWS):
            for col in range(COLS):
                if idx >= total:
                    break
                tx = margin_x + col * (ticket_w + gap_x)
                ty = height - margin_top - (row + 1) * ticket_h - row * gap_y
                draw_ticket(c, tx, ty, ticket_w, ticket_h, tickets_data[idx], config, logos)
                idx += 1
            if idx >= total:
                break

        if idx < total:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


def generate_ticket_preview(match, config):
    """Aperçu : une page A4 remplie d'exemplaires de démonstration."""
    demo = {
        'ticket_number': 'DEMO-001',
        'match_id': match.id,
        'home_team': match.home_team.name,
        'away_team': match.away_team.name,
        'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'Date à définir',
        'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
        'venue': match.venue or 'Stade Cup Legends',
        'price': config.price,
        'currency': config.currency,
        'seat_number': 'A01',
    }
    return generate_tickets_pdf(match, config, [demo] * TICKETS_PER_PAGE)
