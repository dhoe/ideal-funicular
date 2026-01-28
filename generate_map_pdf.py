#!/usr/bin/env python3
"""Generate an A4 PDF with a schematic map centered on IOM Bangkok office
showing a 30-minute commute radius. Draws roads/landmarks directly with
reportlab - no external tile servers needed."""

import math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen import canvas

# IOM Bangkok Regional Office
CENTER_LAT = 13.7563
CENTER_LON = 100.5855

# A4 page
PAGE_W, PAGE_H = A4
MARGIN = 12 * mm

# Map area on page
MAP_LEFT = MARGIN
MAP_BOTTOM = MARGIN + 10 * mm
MAP_W = PAGE_W - 2 * MARGIN
MAP_H = PAGE_H - MAP_BOTTOM - 35 * mm  # space for header

# Geo bounds: ~12 km across (enough to show 6km radius circle)
KM_SPAN = 14
DEG_LAT_PER_KM = 1 / 111.32
DEG_LON_PER_KM = 1 / (111.32 * math.cos(math.radians(CENTER_LAT)))

LAT_MIN = CENTER_LAT - (KM_SPAN / 2) * DEG_LAT_PER_KM
LAT_MAX = CENTER_LAT + (KM_SPAN / 2) * DEG_LAT_PER_KM
LON_MIN = CENTER_LON - (KM_SPAN / 2) * DEG_LON_PER_KM
LON_MAX = CENTER_LON + (KM_SPAN / 2) * DEG_LON_PER_KM

RADIUS_KM = 6

# Colors
WATER = HexColor("#c6e2ff")
PARK = HexColor("#c8f0c8")
ROAD_MAJOR = HexColor("#f0d060")
ROAD_HIGHWAY = HexColor("#ff9944")
ROAD_MINOR = HexColor("#ffffff")
BG = HexColor("#f2efe9")
CIRCLE_FILL = Color(0.26, 0.52, 0.96, alpha=0.10)
CIRCLE_STROKE = Color(0.26, 0.52, 0.96, alpha=0.7)


def geo_to_page(lat, lon):
    """Convert lat/lon to page coordinates."""
    x = MAP_LEFT + (lon - LON_MIN) / (LON_MAX - LON_MIN) * MAP_W
    y = MAP_BOTTOM + (lat - LAT_MIN) / (LAT_MAX - LAT_MIN) * MAP_H
    return x, y


def draw_road(c, coords, color, width):
    p = c.beginPath()
    x0, y0 = geo_to_page(coords[0][0], coords[0][1])
    p.moveTo(x0, y0)
    for lat, lon in coords[1:]:
        x, y = geo_to_page(lat, lon)
        p.lineTo(x, y)
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setLineCap(1)
    c.setLineJoin(1)
    c.drawPath(p, stroke=1, fill=0)


def draw_area(c, coords, fill_color):
    p = c.beginPath()
    x0, y0 = geo_to_page(coords[0][0], coords[0][1])
    p.moveTo(x0, y0)
    for lat, lon in coords[1:]:
        x, y = geo_to_page(lat, lon)
        p.lineTo(x, y)
    p.close()
    c.setFillColor(fill_color)
    c.setStrokeColor(fill_color)
    c.drawPath(p, stroke=0, fill=1)


def draw_label(c, lat, lon, text, size=6, color=HexColor("#555555"), bold=False):
    x, y = geo_to_page(lat, lon)
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x + 2, y + 2, text)


def main():
    output = "iom-bangkok-map.pdf"
    c = canvas.Canvas(output, pagesize=A4)

    # --- Header ---
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 22 * mm,
                        "IOM Bangkok Office — 30 Min Commute Radius")
    c.setFont("Helvetica", 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 27 * mm,
                        "120 Soi Soonvijai 4, Bangkapi, Huai Khwang, Bangkok 10310")

    # --- Map background ---
    c.saveState()
    p = c.beginPath()
    p.rect(MAP_LEFT, MAP_BOTTOM, MAP_W, MAP_H)
    c.clipPath(p, stroke=0)
    c.setFillColor(BG)
    c.rect(MAP_LEFT, MAP_BOTTOM, MAP_W, MAP_H, stroke=0, fill=1)

    # --- Water features ---
    # Chao Phraya River (simplified path through Bangkok)
    river_coords = [
        (13.82, 100.51), (13.80, 100.50), (13.78, 100.505),
        (13.77, 100.50), (13.76, 100.505), (13.75, 100.50),
        (13.74, 100.505), (13.73, 100.51), (13.72, 100.505),
        (13.71, 100.50), (13.70, 100.505), (13.69, 100.51),
    ]
    c.setStrokeColor(WATER)
    c.setLineWidth(6)
    c.setLineCap(1)
    p = c.beginPath()
    x0, y0 = geo_to_page(river_coords[0][0], river_coords[0][1])
    p.moveTo(x0, y0)
    for lat, lon in river_coords[1:]:
        x, y = geo_to_page(lat, lon)
        p.lineTo(x, y)
    c.drawPath(p, stroke=1, fill=0)

    # Khlong Saen Saep canal
    canal = [
        (13.755, 100.49), (13.755, 100.51), (13.756, 100.53),
        (13.757, 100.55), (13.758, 100.57), (13.759, 100.59),
        (13.760, 100.61), (13.761, 100.63), (13.762, 100.65),
    ]
    c.setLineWidth(2)
    p = c.beginPath()
    x0, y0 = geo_to_page(canal[0][0], canal[0][1])
    p.moveTo(x0, y0)
    for lat, lon in canal[1:]:
        x, y = geo_to_page(lat, lon)
        p.lineTo(x, y)
    c.drawPath(p, stroke=1, fill=0)

    # --- Parks ---
    # Lumphini Park
    draw_area(c, [
        (13.728, 100.538), (13.728, 100.548), (13.735, 100.548), (13.735, 100.538)
    ], PARK)
    # Benjakitti Park
    draw_area(c, [
        (13.726, 100.555), (13.726, 100.565), (13.732, 100.565), (13.732, 100.555)
    ], PARK)
    # Chatuchak Park / Rod Fai Park
    draw_area(c, [
        (13.798, 100.550), (13.798, 100.560), (13.810, 100.560), (13.810, 100.550)
    ], PARK)
    # Rama IX Park
    draw_area(c, [
        (13.725, 100.592), (13.725, 100.607), (13.735, 100.607), (13.735, 100.592)
    ], PARK)

    # --- Major highways / expressways ---
    # Expressway (elevated) - Chalerm Maha Nakhon / Si Rat
    draw_road(c, [
        (13.82, 100.535), (13.80, 100.535), (13.78, 100.535),
        (13.76, 100.53), (13.74, 100.525), (13.72, 100.525),
        (13.70, 100.530),
    ], ROAD_HIGHWAY, 3)

    # Motorway - Ramindra-At Narong
    draw_road(c, [
        (13.82, 100.575), (13.80, 100.580), (13.78, 100.585),
        (13.76, 100.585), (13.74, 100.582), (13.72, 100.580),
        (13.70, 100.578),
    ], ROAD_HIGHWAY, 3)

    # --- Major roads ---
    # Sukhumvit Road (roughly east-west through center-south)
    draw_road(c, [
        (13.725, 100.49), (13.725, 100.52), (13.723, 100.55),
        (13.722, 100.58), (13.720, 100.61), (13.718, 100.65),
    ], ROAD_MAJOR, 2.5)

    # Rama IV Road
    draw_road(c, [
        (13.720, 100.50), (13.722, 100.52), (13.725, 100.535),
        (13.728, 100.555), (13.730, 100.575),
    ], ROAD_MAJOR, 2)

    # Phetchaburi Road
    draw_road(c, [
        (13.748, 100.49), (13.748, 100.52), (13.750, 100.55),
        (13.752, 100.58), (13.753, 100.61), (13.754, 100.65),
    ], ROAD_MAJOR, 2.5)

    # Ratchadaphisek Road (roughly circular, N-S on east side)
    draw_road(c, [
        (13.82, 100.56), (13.80, 100.565), (13.78, 100.57),
        (13.76, 100.575), (13.74, 100.57), (13.72, 100.56),
        (13.71, 100.545), (13.70, 100.535),
    ], ROAD_MAJOR, 2.5)

    # Lat Phrao Road
    draw_road(c, [
        (13.78, 100.555), (13.77, 100.575), (13.76, 100.59),
        (13.755, 100.61), (13.75, 100.63), (13.745, 100.65),
    ], ROAD_MAJOR, 2)

    # Ramkhamhaeng Road
    draw_road(c, [
        (13.755, 100.58), (13.750, 100.60), (13.748, 100.62),
        (13.745, 100.64), (13.742, 100.66),
    ], ROAD_MAJOR, 2)

    # Vibhavadi Rangsit Road (N-S main artery)
    draw_road(c, [
        (13.82, 100.555), (13.80, 100.555), (13.78, 100.555),
        (13.76, 100.555), (13.74, 100.545), (13.72, 100.540),
    ], ROAD_MAJOR, 2.5)

    # Asoke / Ratchadaphisek intersection area - Soonvijai area roads
    # Soi Soonvijai (near IOM office)
    draw_road(c, [
        (13.762, 100.582), (13.756, 100.585), (13.752, 100.586),
    ], ROAD_MINOR, 1.5)

    # Phahon Yothin Road (N-S)
    draw_road(c, [
        (13.82, 100.545), (13.80, 100.545), (13.78, 100.545),
        (13.76, 100.54), (13.74, 100.535),
    ], ROAD_MAJOR, 2)

    # --- BTS/MRT lines ---
    # BTS Sukhumvit Line (green)
    bts_color = HexColor("#4CAF50")
    draw_road(c, [
        (13.82, 100.555), (13.80, 100.555), (13.78, 100.56),
        (13.76, 100.565), (13.74, 100.56), (13.73, 100.555),
        (13.725, 100.55), (13.72, 100.54),
    ], bts_color, 1.5)

    # MRT Blue Line
    mrt_color = HexColor("#1565C0")
    draw_road(c, [
        (13.81, 100.565), (13.80, 100.565), (13.78, 100.57),
        (13.76, 100.575), (13.74, 100.57), (13.73, 100.555),
        (13.72, 100.54), (13.71, 100.535),
    ], mrt_color, 1.5)

    # MRT Yellow Line (near IOM office!)
    draw_road(c, [
        (13.78, 100.585), (13.77, 100.585), (13.76, 100.585),
        (13.75, 100.59), (13.74, 100.595), (13.73, 100.60),
    ], HexColor("#FFC107"), 1.5)

    # Airport Rail Link
    draw_road(c, [
        (13.75, 100.555), (13.748, 100.57), (13.746, 100.585),
        (13.744, 100.60), (13.742, 100.62), (13.74, 100.65),
    ], HexColor("#e91e63"), 1.5)

    # --- 30 min commute radius circle ---
    cx, cy = geo_to_page(CENTER_LAT, CENTER_LON)
    # Radius in page units
    r_lat = RADIUS_KM * DEG_LAT_PER_KM
    _, y_r = geo_to_page(CENTER_LAT + r_lat, CENTER_LON)
    r_page = y_r - cy

    c.setFillColor(CIRCLE_FILL)
    c.setStrokeColor(CIRCLE_STROKE)
    c.setLineWidth(2)
    c.setDash([6, 3])
    c.circle(cx, cy, r_page, stroke=1, fill=1)
    c.setDash([])

    # --- IOM Office marker ---
    c.setFillColor(HexColor("#e53935"))
    c.setStrokeColor(HexColor("#b71c1c"))
    c.setLineWidth(2)
    c.circle(cx, cy, 5, stroke=1, fill=1)
    # White inner dot
    c.setFillColor(HexColor("#ffffff"))
    c.circle(cx, cy, 2, stroke=0, fill=1)

    # --- Labels ---
    draw_label(c, CENTER_LAT + 0.003, CENTER_LON + 0.003, "IOM Bangkok Office", 7, HexColor("#b71c1c"), bold=True)

    # Landmark labels
    draw_label(c, 13.732, 100.539, "Lumphini Park", 5.5, HexColor("#2e7d32"))
    draw_label(c, 13.728, 100.556, "Benjakitti Park", 5, HexColor("#2e7d32"))
    draw_label(c, 13.802, 100.551, "Chatuchak Park", 5, HexColor("#2e7d32"))
    draw_label(c, 13.727, 100.594, "Rama IX Park", 5, HexColor("#2e7d32"))

    # Road labels
    draw_label(c, 13.724, 100.60, "Sukhumvit Rd", 5, HexColor("#666"))
    draw_label(c, 13.749, 100.60, "Phetchaburi Rd", 5, HexColor("#666"))
    draw_label(c, 13.77, 100.60, "Lat Phrao Rd", 5, HexColor("#666"))
    draw_label(c, 13.79, 100.545, "Phahon Yothin", 5, HexColor("#666"))
    draw_label(c, 13.79, 100.558, "Vibhavadi", 5, HexColor("#666"))
    draw_label(c, 13.77, 100.577, "Ratchadaphisek", 5, HexColor("#666"))
    draw_label(c, 13.745, 100.635, "Ramkhamhaeng", 5, HexColor("#666"))

    # River
    draw_label(c, 13.76, 100.497, "Chao Phraya", 5, HexColor("#1565C0"))

    # Canal
    draw_label(c, 13.757, 100.51, "Kh. Saen Saep", 4.5, HexColor("#4A90C0"))

    # Transit labels
    draw_label(c, 13.815, 100.556, "BTS", 4.5, HexColor("#4CAF50"), bold=True)
    draw_label(c, 13.808, 100.567, "MRT Blue", 4.5, HexColor("#1565C0"), bold=True)
    draw_label(c, 13.778, 100.587, "MRT Yellow", 4.5, HexColor("#E6A800"), bold=True)
    draw_label(c, 13.742, 100.605, "ARL", 4.5, HexColor("#e91e63"), bold=True)

    # Area names
    draw_label(c, 13.745, 100.535, "Silom / Sathorn", 6, HexColor("#888"))
    draw_label(c, 13.76, 100.555, "Asoke", 6, HexColor("#888"))
    draw_label(c, 13.77, 100.545, "Din Daeng", 6, HexColor("#888"))
    draw_label(c, 13.745, 100.565, "Khlong Toei", 6, HexColor("#888"))
    draw_label(c, 13.765, 100.61, "Bangkapi", 6, HexColor("#888"))
    draw_label(c, 13.79, 100.575, "Huai Khwang", 6, HexColor("#888"))
    draw_label(c, 13.74, 100.61, "Suan Luang", 6, HexColor("#888"))

    c.restoreState()

    # Map border
    c.setStrokeColor(HexColor("#999999"))
    c.setLineWidth(0.5)
    c.rect(MAP_LEFT, MAP_BOTTOM, MAP_W, MAP_H, stroke=1, fill=0)

    # --- Legend ---
    leg_y = MARGIN + 2 * mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(HexColor("#555555"))

    items = [
        (HexColor("#e53935"), "IOM Office"),
        (CIRCLE_STROKE, "~6 km / ~30 min commute"),
        (ROAD_HIGHWAY, "Expressway"),
        (ROAD_MAJOR, "Major road"),
        (HexColor("#4CAF50"), "BTS"),
        (HexColor("#1565C0"), "MRT Blue"),
        (HexColor("#FFC107"), "MRT Yellow"),
        (HexColor("#e91e63"), "Airport Rail Link"),
        (WATER, "Water"),
        (PARK, "Park"),
    ]
    x_pos = MARGIN
    for color, label in items:
        c.setFillColor(color)
        c.rect(x_pos, leg_y, 8, 5, stroke=0, fill=1)
        c.setFillColor(HexColor("#333333"))
        c.drawString(x_pos + 10, leg_y + 0.5, label)
        x_pos += c.stringWidth(label, "Helvetica", 6.5) + 18

    # --- Footer ---
    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#999999"))
    c.drawRightString(PAGE_W - MARGIN, MARGIN, "Schematic map — not to exact scale")

    c.save()
    print(f"PDF saved to {output}")


if __name__ == "__main__":
    main()
