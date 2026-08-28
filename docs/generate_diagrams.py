"""
Generate teaching diagrams (PNG) for the Smart eCommerce Platform project.

Run:  python docs/generate_diagrams.py
Output: docs/*.png

Everything drawn here was read from the real code in this repo:
  backend/app.py, backend/test.sql, frontend/main/*, frontend/<service>/*
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# drawing helpers
# ----------------------------------------------------------------------------

S = 2  # supersample factor, final image is downscaled by S for smooth edges
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

_FONT_CACHE = {}


def _font(name, size):
    key = (name, size)
    if key not in _FONT_CACHE:
        path = os.path.join(FONT_DIR, name)
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, int(size * S))
        except OSError:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def reg(size):
    return _font("arial.ttf", size)


def bd(size):
    return _font("arialbd.ttf", size)


def mono(size):
    return _font("consola.ttf", size)


def wrap(text, font, max_px):
    """Wrap text (device px width)."""
    out = []
    for para in str(text).split("\n"):
        words = para.split()
        if not words:
            out.append("")
            continue
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if font.getlength(t) <= max_px or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


# palette
INK = "#202124"
MUTED = "#5F6368"
LINE = "#DADCE0"
BLUE = ("#E8F0FE", "#1A73E8")
GREEN = ("#E6F4EA", "#188038")
YELLOW = ("#FEF7E0", "#F29900")
RED = ("#FCE8E6", "#D93025")
PURPLE = ("#F3E8FD", "#8E24AA")
GREY = ("#F1F3F4", "#80868B")
TEAL = ("#E4F7FB", "#00838F")
ORANGE = ("#FFF0E1", "#E8710A")


class Canvas:
    def __init__(self, w, h, bg="#FFFFFF"):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.img)

    # -- primitives ---------------------------------------------------------
    def rect(self, x, y, w, h, fill=None, outline=None, r=10, width=2):
        self.d.rounded_rectangle(
            [x * S, y * S, (x + w) * S, (y + h) * S],
            radius=r * S, fill=fill, outline=outline, width=int(width * S),
        )

    def line(self, x1, y1, x2, y2, fill=MUTED, width=2):
        self.d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=fill, width=int(width * S))

    def dashed(self, x1, y1, x2, y2, fill=MUTED, width=2, dash=8, gap=6):
        import math
        total = math.hypot(x2 - x1, y2 - y1)
        if total == 0:
            return
        ux, uy = (x2 - x1) / total, (y2 - y1) / total
        pos = 0.0
        while pos < total:
            seg = min(dash, total - pos)
            self.line(x1 + ux * pos, y1 + uy * pos,
                      x1 + ux * (pos + seg), y1 + uy * (pos + seg), fill, width)
            pos += dash + gap

    def text(self, x, y, s, font, fill=INK, anchor="la"):
        self.d.text((x * S, y * S), s, font=font, fill=fill, anchor=anchor)

    def para(self, x, y, s, font, max_w, fill=INK, lh=None, anchor="la"):
        lh = lh or (font.size / S) + 6
        yy = y
        for ln in wrap(s, font, max_w * S):
            self.text(x, yy, ln, font, fill, anchor)
            yy += lh
        return yy

    def arrow(self, x1, y1, x2, y2, color=MUTED, width=2, label=None,
              label_font=None, dash=False, head=9, label_off=8, label_side="above"):
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        if dash:
            self.dashed(x1, y1, bx, by, color, width)
        else:
            self.line(x1, y1, bx, by, color, width)
        left = (bx + head * 0.5 * math.cos(ang + 2.3), by + head * 0.5 * math.sin(ang + 2.3))
        right = (bx + head * 0.5 * math.cos(ang - 2.3), by + head * 0.5 * math.sin(ang - 2.3))
        self.d.polygon([(x2 * S, y2 * S), (left[0] * S, left[1] * S),
                        (right[0] * S, right[1] * S)], fill=color)
        if label:
            f = label_font or reg(11)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if abs(y2 - y1) < abs(x2 - x1):  # horizontal-ish
                lines = wrap(label, f, max(abs(x2 - x1) * S, 120 * S))
                yy = my - label_off - len(lines) * ((f.size / S) + 3)
                if label_side == "below":
                    yy = my + label_off
                for ln in lines:
                    self.text(mx, yy, ln, f, MUTED, anchor="ma")
                    yy += (f.size / S) + 3
            else:  # vertical-ish
                lines = wrap(label, f, 190 * S)
                yy = my - len(lines) * ((f.size / S) + 3) / 2
                for ln in lines:
                    self.text(mx + label_off, yy, ln, f, MUTED, anchor="la")
                    yy += (f.size / S) + 3

    # -- composites ---------------------------------------------------------
    def box(self, x, y, w, h, title=None, lines=(), fill="#FFFFFF", outline=MUTED,
            title_size=15, line_size=12, center=False, mono_lines=False,
            title_fill=None, pad=12, badge=None, r=10):
        tf = bd(title_size)
        title_rows = str(title).split("\n") if title else []
        if h is None:  # auto height
            lf = mono(line_size) if mono_lines else reg(line_size)
            hh = pad
            hh += len(title_rows) * ((tf.size / S) + 4)
            if title_rows:
                hh += 4
            for ln in lines:
                hh += ((line_size) + 6) * len(wrap(ln, lf, (w - 2 * pad) * S))
            h = hh + pad - 2
        self.rect(x, y, w, h, fill=fill, outline=outline, r=r)
        lf = mono(line_size) if mono_lines else reg(line_size)
        # a very light outline would make the title unreadable
        tcol = title_fill or (INK if outline in (LINE, GREY[1]) else outline)
        yy = y + pad
        for trow in title_rows:
            if center:
                self.text(x + w / 2, yy, trow, tf, tcol, anchor="ma")
            else:
                self.text(x + pad, yy, trow, tf, tcol)
            yy += (tf.size / S) + 4
        if title_rows:
            yy += 4
        for ln in lines:
            for piece in wrap(ln, lf, (w - 2 * pad) * S):
                if center:
                    self.text(x + w / 2, yy, piece, lf, INK, anchor="ma")
                else:
                    self.text(x + pad, yy, piece, lf, INK)
                yy += line_size + 6
        if badge:
            btxt, bfill, bink = badge
            bf = bd(10)
            bw = bf.getlength(btxt) / S + 16
            self.rect(x + w - bw - 8, y + 8, bw, 20, fill=bfill, outline=bfill, r=8)
            self.text(x + w - bw / 2 - 8, y + 12, btxt, bf, bink, anchor="ma")
        return h

    def header(self, title, subtitle=None, kicker="Smart eCommerce Platform - Multicloud DevOps by Veera Sir"):
        self.rect(0, 0, self.w, 96, fill="#0B1220", outline="#0B1220", r=0)
        self.text(40, 18, title, bd(26), "#FFFFFF")
        if subtitle:
            self.text(40, 56, subtitle, reg(14), "#9AA7BD")
        self.text(self.w - 40, 40, kicker, reg(12), "#6B7A93", anchor="ra")

    def footer(self, text):
        self.line(40, self.h - 46, self.w - 40, self.h - 46, LINE, 1)
        self.text(40, self.h - 36, text, reg(11), MUTED)

    def elbow(self, points, color=MUTED, width=2, label=None, label_at=None):
        """Orthogonal polyline with an arrowhead on the last segment."""
        for i in range(len(points) - 2):
            (x1, y1), (x2, y2) = points[i], points[i + 1]
            self.line(x1, y1, x2, y2, color, width)
        (x1, y1), (x2, y2) = points[-2], points[-1]
        self.arrow(x1, y1, x2, y2, color, width)
        if label:
            lx, ly = label_at or ((points[0][0] + points[-1][0]) / 2, (points[0][1] + points[-1][1]) / 2)
            self.text(lx, ly, label, reg(11), MUTED)

    def finish(self, content_bottom, footer_text, name):
        """Crop the canvas to the real content height, then footer + save."""
        h = int(content_bottom + 72)
        self.img = self.img.crop((0, 0, self.w * S, h * S))
        self.h = h
        self.d = ImageDraw.Draw(self.img)
        self.footer(footer_text)
        self.save(name)

    def save(self, name):
        path = os.path.join(OUT_DIR, name)
        self.img.resize((self.w, self.h), Image.LANCZOS).save(path)
        print("wrote", path)


# ----------------------------------------------------------------------------
# sequence diagram helper
# ----------------------------------------------------------------------------

def sequence(c, x0, y0, width, actors, steps, actor_h=72):
    n = len(actors)
    slot = width / n
    xs = [x0 + slot * (i + 0.5) for i in range(n)]
    bw = slot - 26

    # measure steps
    heights = []
    for st in steps:
        kind = st[0]
        txt = st[-1]
        f = reg(12)
        if kind == "note":
            hh = 14 + 18 * len(wrap(txt, f, (width - 40) * S))
        elif kind == "self":
            hh = 20 + 17 * len(wrap(txt, f, 300 * S))
        else:
            a, b = st[1], st[2]
            span = max(abs(xs[b] - xs[a]), 200)
            hh = 26 + 17 * len(wrap(txt, f, span * S))
        heights.append(hh)
    total = sum(heights)

    lifeline_top = y0 + actor_h
    lifeline_bottom = lifeline_top + 24 + total + 16

    for i, (name, sub, col) in enumerate(actors):
        c.dashed(xs[i], lifeline_top, xs[i], lifeline_bottom, col[1], 2, dash=7, gap=7)

    for i, (name, sub, col) in enumerate(actors):
        c.box(xs[i] - bw / 2, y0, bw, actor_h, name, [sub] if sub else (), fill=col[0],
              outline=col[1], title_size=14, line_size=11, center=True, pad=10)

    y = lifeline_top + 24
    num = 0
    for st, hh in zip(steps, heights):
        kind = st[0]
        txt = st[-1]
        if kind == "note":
            c.box(x0 + 10, y - 4, width - 20, None, None, [txt], fill="#FFFDE7",
                  outline="#F9A825", line_size=12, pad=10, r=8)
        elif kind == "self":
            a = st[1]
            num += 1
            col = actors[a][2]
            x = xs[a]
            c.line(x, y + 4, x + 26, y + 4, col[1], 2)
            c.line(x + 26, y + 4, x + 26, y + hh - 12, col[1], 2)
            c.arrow(x + 26, y + hh - 12, x + 2, y + hh - 12, col[1], 2)
            c.para(x + 36, y - 2, "%d. %s" % (num, txt), reg(12), 320, INK, lh=17)
        else:
            a, b = st[1], st[2]
            num += 1
            col = actors[a][2] if kind == "call" else actors[b][2]
            color = col[1] if kind == "call" else "#5F6368"
            x1, x2 = xs[a], xs[b]
            pad = 6 if x2 > x1 else -6
            f = reg(12)
            lines = wrap("%d. %s" % (num, txt), f, max(abs(x2 - x1), 200) * S)
            ty = y - 4
            for ln in lines:
                c.text((x1 + x2) / 2, ty, ln, f, INK if kind == "call" else MUTED, anchor="ma")
                ty += 17
            c.arrow(x1 + pad, ty + 6, x2 - pad, ty + 6, color, 2, dash=(kind == "return"))
        y += hh
    return lifeline_bottom


# ----------------------------------------------------------------------------
# table helper
# ----------------------------------------------------------------------------

def table(c, x, y, col_w, headers, rows, row_h=None, head_fill="#0B1220",
          head_ink="#FFFFFF", size=12, zebra="#F8F9FA", mono_cols=()):
    total_w = sum(col_w)
    hf, rf = bd(size), reg(size)
    mf = mono(size - 1)
    hh = 34
    c.rect(x, y, total_w, hh, fill=head_fill, outline=head_fill, r=6)
    cx = x
    for w, htxt in zip(col_w, headers):
        c.text(cx + 10, y + 9, htxt, hf, head_ink)
        cx += w
    yy = y + hh
    for i, row in enumerate(rows):
        cells = []
        max_lines = 1
        for j, (w, cell) in enumerate(zip(col_w, row)):
            f = mf if j in mono_cols else rf
            ls = wrap(cell, f, (w - 20) * S)
            cells.append((ls, f))
            max_lines = max(max_lines, len(ls))
        rh = row_h or (10 + max_lines * (size + 6))
        if i % 2 == 1:
            c.rect(x, yy, total_w, rh, fill=zebra, outline=zebra, r=0, width=1)
        cx = x
        for (ls, f), w in zip(cells, col_w):
            ty = yy + 6
            for ln in ls:
                c.text(cx + 10, ty, ln, f, INK)
                ty += size + 6
            cx += w
        c.line(x, yy + rh, x + total_w, yy + rh, LINE, 1)
        yy += rh
    return yy


# ============================================================================
# 01 - AWS architecture
# ============================================================================

def d01():
    c = Canvas(1820, 1400)
    c.header("01 - AWS Architecture: how a request reaches the database",
             "2 EC2 instances + 1 RDS MySQL + Gmail SMTP. One Nginx origin serves 9 'services' as folders.")

    # browser
    c.box(50, 150, 360, 250, "1) Student / Customer Browser", [
        "Chrome / mobile browser",
        "",
        "Session = localStorage key",
        "  googleStoreUser  (plain JSON)",
        "No cookie, no JWT, no server session",
    ], fill=BLUE[0], outline=BLUE[1], line_size=12)

    # nginx
    c.box(530, 150, 530, 460, "2) EC2 #1  Frontend\n(Amazon Linux + Nginx :80)", [
        "root = /usr/share/nginx/html",
        "config = /etc/nginx/conf.d/google-store.conf",
        "",
        "STATIC (location / -> try_files):",
        "   /               main/index.html  (portal + login)",
        "   /phones         /computers      /earphones",
        "   /electronics    /googleclothes  /googlegrocery",
        "   /googlemusic    /googlepay",
        "",
        "PROXY:",
        "   location = /api   -> backend:5000/api",
        "   location   /api/  -> backend:5000/api/",
    ], fill=GREEN[0], outline=GREEN[1], line_size=12)

    # flask
    c.box(1230, 150, 540, 460, "3) EC2 #2  Backend\n(Flask app.py :5000)", [
        "python3 -m venv venv ; python3 app.py",
        "host 0.0.0.0  port from .env PORT=5000",
        "",
        "ONE process, ONE file, ~20 routes, all /api/*",
        "",
        "@after_request adds:",
        "   Access-Control-Allow-Origin: *",
        "",
        "Reads .env: DB_HOST DB_USER DB_PASSWORD DB_NAME",
        "            MAIL_SERVER MAIL_PORT MAIL_USERNAME",
        "            MAIL_PASSWORD",
        "",
        "Emails for orders + recharges are sent from",
        "background threads (fire and forget).",
    ], fill=YELLOW[0], outline=YELLOW[1], line_size=12)

    # rds + smtp
    c.box(1230, 700, 255, 200, "4) Amazon RDS MySQL", [
        "engine MySQL, db name  cloud",
        "port 3306 (SG allows backend SG only)",
        "8 tables",
        "driver: pymysql, DictCursor,",
        "autocommit = False",
    ], fill=RED[0], outline=RED[1], line_size=11)

    c.box(1515, 700, 255, 200, "5) Gmail SMTP", [
        "smtp.gmail.com : 587  TLS",
        "flask-mail",
        "sends: signup OTP, login OTP,",
        "order receipt, recharge receipt",
        "needs a Gmail App Password",
    ], fill=PURPLE[0], outline=PURPLE[1], line_size=11)

    # external
    c.box(50, 470, 400, 250, "X) Hardcoded external endpoints", [
        "Called DIRECTLY by the browser, NOT via Nginx,",
        "and NOT part of this repo:",
        "",
        "phones        -> 18.181.35.96/upload_receipt",
        "electronics   -> 18.181.35.96/upload_receipt",
        "computers     -> 18.181.35.96:5001/save-receipts",
        "earphones     -> 18.181.35.96:5002/save-receipts",
        "googleclothes -> ipinfo.io , cloudflare trace",
    ], fill=RED[0], outline=RED[1], line_size=11,
        badge=("WILL BREAK", "#D93025", "#FFFFFF"))

    c.arrow(410, 250, 525, 250, BLUE[1], 3, "HTTP :80\npublic", reg(12))
    c.arrow(1060, 300, 1225, 300, GREEN[1], 3, "HTTP :5000\nprivate IP\nsame VPC", reg(12))
    c.arrow(1360, 610, 1360, 695, RED[1], 3, "pymysql\n3306", reg(12))
    c.arrow(1650, 610, 1650, 695, PURPLE[1], 3, "SMTP\n587", reg(12))
    c.arrow(230, 400, 230, 465, RED[1], 2, "plain HTTP,\nno proxy rule", reg(11), dash=True)

    b = c.box(50, 780, 1140, None, "What students must notice", [
        "1. This is NOT microservices. 'Services' are only folders behind one Nginx server_name _; there is a single Flask",
        "    process and a single database. Path = folder, not a separate deployment.",
        "2. The frontend never talks to MySQL. Browser -> /api/... -> Nginx proxy -> Flask -> RDS. Nothing else.",
        "3. Login state lives in the browser (localStorage). The backend does not verify it. Every API call simply carries",
        "    an  email  value in the JSON body or query string, and Flask trusts it.",
        "4. Security groups do the network isolation: EC2#1 SG allows :80 from the internet, EC2#2 SG allows :5000 from",
        "    the EC2#1 SG, RDS SG allows :3306 from the EC2#2 SG. Outbound :587 is needed for e-mail.",
        "5. orders, order_items and service_activity are also created at runtime by CREATE TABLE IF NOT EXISTS inside",
        "    the request handlers, so the app can self-heal a missing schema.",
    ], fill="#FFFFFF", outline=LINE, line_size=12)

    c.finish(max(900, 780 + b),
             "Source: frontend/main/google-store.conf, backend/app.py, backend/.env, README.md",
             "01-aws-architecture.png")



# ============================================================================
# 02 - frontend services map
# ============================================================================

def d02():
    c = Canvas(1820, 1400)
    c.header("02 - The 9 frontend 'services' and what each one calls",
             "All are static folders copied into /usr/share/nginx/html on the SAME EC2 instance.")

    cards = [
        ("/  (main portal)", GREEN, "main/index.html\nmain/session-watchdog.js", "Issues login/signup OTP. The only page that can create a session.",
         "/api/login/request  /api/login/verify\n/api/signup/request  /api/signup/verify\n/api/cart  /api/cart/items\n/api/orders  /api/history\n/api/service-activity",
         "cart: in-memory JS + DB"),
        ("/phones", BLUE, "index.html + script.js", "Product grid, quick view, QR/UPI popup, receipt text.",
         "GET/POST/PUT/DELETE /api/cart/items\nGET /api/cart\nPOST /api/orders\n+ 18.181.35.96/upload_receipt",
         "cart: RDS via /api/cart"),
        ("/computers", BLUE, "index.html + script.js", "Same template as phones, different product list.",
         "GET/POST/PUT/DELETE /api/cart/items\nGET /api/cart\nPOST /api/orders\n+ 18.181.35.96:5001/save-receipts",
         "cart: RDS via /api/cart"),
        ("/earphones", BLUE, "index.html + script.js", "Same template as phones.",
         "GET/POST/PUT/DELETE /api/cart/items\nGET /api/cart\nPOST /api/orders\n+ 18.181.35.96:5002/save-receipts",
         "cart: RDS via /api/cart"),
        ("/electronics", BLUE, "index.html + script.js", "Same template. Portal also links 'Home' here.",
         "GET/POST/PUT/DELETE /api/cart/items\nGET /api/cart\nPOST /api/orders\n+ 18.181.35.96/upload_receipt",
         "cart: RDS via /api/cart"),
        ("/googleclothes  (Fashion)", ORANGE, "single index.html (~2900 lines)", "jQuery storefront, own checkout modal, geo lookup.",
         "POST /api/orders  with explicit items[]\nfetch ipinfo.io + cloudflare trace",
         "cart: localStorage 'cart'"),
        ("/googlegrocery", TEAL, "single index.html\n+ /session-watchdog.js", "Only page that loads the watchdog, so only page auto-logged-out when backend dies.",
         "POST /api/orders  with explicit items[]\nGET /api  every 10s (watchdog)",
         "cart: localStorage 'mooncart_cart'"),
        ("/googlemusic", PURPLE, "single index.html", "Pure static player. Login gate only.",
         "NO backend calls at all",
         "no cart"),
        ("/googlepay", RED, "single index.html", "Mobile recharge wizard. NOT linked from the portal - reachable only by typing the URL.",
         "POST /api/recharges",
         "no cart"),
    ]

    x0, y0, cw, ch, gx, gy = 50, 140, 560, 300, 30, 30
    for i, (path, col, files, what, apis, cart) in enumerate(cards):
        cx = x0 + (i % 3) * (cw + gx)
        cy = y0 + (i // 3) * (ch + gy)
        c.rect(cx, cy, cw, ch, fill=col[0], outline=col[1], r=12)
        c.text(cx + 14, cy + 12, path, bd(17), col[1])
        yy = cy + 42
        yy = c.para(cx + 14, yy, "files: " + files, reg(11), cw - 28, MUTED, lh=16)
        yy = c.para(cx + 14, yy + 4, what, reg(12), cw - 28, INK, lh=17)
        c.line(cx + 14, yy + 6, cx + cw - 14, yy + 6, col[1], 1)
        yy += 14
        c.text(cx + 14, yy, "calls:", bd(11), col[1])
        yy = c.para(cx + 60, yy, apis, mono(11), cw - 80, INK, lh=16)
        c.rect(cx + 14, cy + ch - 40, cw - 28, 28, fill="#FFFFFF", outline=col[1], r=8, width=1)
        c.text(cx + 24, cy + ch - 34, cart, bd(11), col[1])

    b = c.box(50, 1120, 1720, None, "Login gate on every service page (copy-pasted, client side only)", [
        "Each service index.html starts with:  if (!JSON.parse(localStorage.getItem('googleStoreUser'))) "
        "window.location.replace('/?auth=login&redirect=' + path)",
        "That is a UI redirect, nothing more. curl / Postman can hit every /api route without ever logging in.",
    ], fill="#FFFDE7", outline="#F9A825", line_size=12)

    c.finish(1120 + b,
             "Source: frontend/*/index.html, frontend/*/script.js, frontend/main/index.html",
             "02-frontend-services-map.png")


# ============================================================================
# 03 - signup OTP flow
# ============================================================================

def d03():
    c = Canvas(1820, 1500)
    c.header("03 - Signup flow (2 requests, e-mail OTP)",
             "POST /api/signup/request  then  POST /api/signup/verify. Password is hashed before it is stored.")

    actors = [
        ("Browser", "portal /  + localStorage", BLUE),
        ("Nginx :80", "proxy /api/", GREEN),
        ("Flask :5000", "app.py", YELLOW),
        ("RDS MySQL", "pending_signups / users", RED),
        ("Gmail SMTP :587", "flask-mail", PURPLE),
    ]

    steps = [
        ("call", 0, 1, "POST /api/signup/request\n{username, email, password, full_name}"),
        ("call", 1, 2, "proxy_pass http://BACKEND_PRIVATE_IP:5000/api/signup/request"),
        ("self", 2, "require_fields() then validate_password_strength():\nmin 8 chars + upper + lower + digit + special, else 400"),
        ("call", 2, 3, "SELECT id FROM users WHERE email=%s OR username=%s"),
        ("return", 3, 2, "row found -> respond 409 'User already exists'"),
        ("self", 2, "generate_password_hash(password)\notp = random 6 digits, expiry = now + 10 minutes"),
        ("call", 2, 3, "INSERT INTO pending_signups (...) ON DUPLICATE KEY UPDATE\n(re-requesting an OTP overwrites the old row)"),
        ("call", 2, 4, "mail.send('Google Store - Verify Registration', otp)\nSYNCHRONOUS - the HTTP response waits for SMTP"),
        ("return", 2, 0, "200 {\"message\": \"OTP sent to email!\"}"),
        ("note", "Browser saves  localStorage['googleStorePendingAuthEmail'] = email  and shows the OTP input box."),
        ("call", 0, 2, "POST /api/signup/verify  {email, otp}   (through Nginx)"),
        ("call", 2, 3, "SELECT * FROM pending_signups WHERE email=%s"),
        ("self", 2, "otp mismatch or now() >= otp_expiry -> 401 'Invalid or expired OTP'\nno row -> 404 'Signup request not found'"),
        ("call", 2, 3, "INSERT INTO users (username, full_name, email, password=hash)\nDELETE FROM pending_signups WHERE email=%s   then COMMIT"),
        ("return", 2, 0, "201 {\"message\": \"Account created successfully!\", user{...}}"),
    ]

    end = sequence(c, 50, 140, 1720, actors, steps)

    b = c.box(50, end + 20, 1720, None, "Teaching points", [
        "Two-table trick: an unverified user lives in  pending_signups , and is only promoted into  users  after the OTP matches. "
        "So a half-finished signup can never log in.",
        "The password never reaches MySQL in clear text - werkzeug  generate_password_hash  is called before the INSERT.",
        "Weakness: the OTP e-mail is sent inside the request, so a slow SMTP handshake makes signup look 'hung'. Orders and recharges "
        "were fixed to use background threads, signup and login were not.",
    ], fill="#FFFFFF", outline=LINE, line_size=12)

    c.finish(end + 20 + b,
             "Source: backend/app.py signup_request() / signup_verify(), backend/test.sql",
             "03-signup-otp-flow.png")


# ============================================================================
# 04 - login OTP flow
# ============================================================================

def d04():
    c = Canvas(1820, 1500)
    c.header("04 - Login flow: OTP is asked ONCE PER CALENDAR DAY",
             "should_require_daily_login_otp() compares last_login_otp_verified_at.date() with today.")

    actors = [
        ("Browser", "localStorage", BLUE),
        ("Nginx :80", "proxy /api/", GREEN),
        ("Flask :5000", "app.py", YELLOW),
        ("RDS MySQL", "users table", RED),
        ("Gmail SMTP :587", "flask-mail", PURPLE),
    ]

    steps = [
        ("call", 0, 1, "POST /api/login/request  {email, password}"),
        ("call", 1, 2, "proxy_pass -> :5000"),
        ("call", 2, 3, "SELECT * FROM users WHERE email=%s"),
        ("self", 2, "check_password_hash(user.password, password)\nwrong -> 401 'Invalid credentials'"),
        ("self", 2, "DECISION: should_require_daily_login_otp(user)\nlast_login_otp_verified_at is TODAY ?"),
        ("return", 2, 0, "PATH A (same day): clear otp columns, 200 {otp_required:false, user{...}} -> logged in with NO OTP"),
        ("call", 2, 3, "PATH B (new day / first ever): UPDATE users SET otp_code=%s, otp_expiry=now+5min"),
        ("call", 2, 4, "mail.send('Google Store - Login OTP', otp)   (synchronous)"),
        ("return", 2, 0, "200 {\"message\":\"OTP sent to email\", otp_required:true}"),
        ("call", 0, 2, "POST /api/login/verify  {email, otp}"),
        ("call", 2, 3, "SELECT * FROM users WHERE email=%s AND otp_code=%s\nthen check now() < otp_expiry  (else 401)"),
        ("call", 2, 3, "UPDATE users SET otp_code=NULL, otp_expiry=NULL,\nlast_login_otp_verified_at = now()   <-- starts the 1-day window"),
        ("return", 2, 0, "200 {user: {id, username, full_name, email, address, phone}}"),
        ("self", 0, "localStorage['googleStoreUser'] = JSON.stringify(user)\nremove pending-auth email, then redirect to ?redirect= target"),
    ]

    end = sequence(c, 50, 140, 1720, actors, steps)

    b1 = c.box(50, end + 20, 840, None, "Why some logins skip the OTP", [
        "last_login_otp_verified_at stores the moment of the last successful OTP.",
        "Comparison is by DATE, not by elapsed hours: an OTP verified at 23:59 stops",
        "being valid at 00:00, and one verified at 00:01 covers the whole day.",
    ], fill=GREEN[0], outline=GREEN[1], line_size=12)

    b2 = c.box(930, end + 20, 840, None, "The session is just a JSON blob in the browser", [
        "There is no token. Anyone can open DevTools and run",
        "localStorage.setItem('googleStoreUser', '{\"email\":\"victim@x.com\"}')",
        "and every page + every /api call will treat them as that user.",
    ], fill=RED[0], outline=RED[1], line_size=12)

    c.finish(end + 20 + max(b1, b2),
             "Source: backend/app.py login_request() / login_verify() / should_require_daily_login_otp()",
             "04-login-otp-flow.png")


# ============================================================================
# 05 - cart + checkout flow
# ============================================================================

def d05():
    c = Canvas(1820, 1700)
    c.header("05 - Cart and checkout: what POST /api/orders really does",
             "One transaction writes orders + order_items + payments, clears the cart, updates the profile, then e-mails the receipt.")

    actors = [
        ("Browser /phones", "script.js", BLUE),
        ("Nginx :80", "proxy /api/", GREEN),
        ("Flask :5000", "app.py", YELLOW),
        ("RDS MySQL", "cart / orders / payments", RED),
        ("Gmail SMTP :587", "background thread", PURPLE),
    ]

    steps = [
        ("call", 0, 2, "'Add' clicked: POST /api/cart/items {email, product_id, name, image, desc, price, quantity}"),
        ("call", 2, 3, "INSERT INTO cart_items ... ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)\n(works because of UNIQUE KEY (user_id, product_id))"),
        ("call", 0, 2, "qty +/- : PUT /api/cart/items {quantity}   -> UPDATE, and quantity<=0 DELETES the row"),
        ("call", 0, 2, "page load: GET /api/cart?email=...   -> {items[], total} (total computed on the server)"),
        ("note", "Only phones / computers / earphones / electronics use this DB cart. googleclothes uses localStorage 'cart' and "
                 "googlegrocery uses localStorage 'mooncart_cart' - they skip /api/cart and post items[] at checkout instead."),
        ("call", 0, 2, "Pay: POST /api/orders {email, shipping_name, shipping_address, shipping_phone,\npayment_method, payment_status, transaction_reference, payment_notes, items[]?}"),
        ("self", 2, "ensure_order_tables(): CREATE TABLE IF NOT EXISTS orders / order_items\n(DDL on the request path)"),
        ("call", 2, 3, "fetch_cart(user_id) -> order_items = DB cart if not empty ELSE request items[]\nempty both -> 400 'Cart is empty'"),
        ("call", 2, 3, "INSERT INTO orders (...)  -> order_id = cursor.lastrowid"),
        ("call", 2, 3, "INSERT INTO order_items (...) once per line item"),
        ("call", 2, 3, "DELETE FROM cart_items WHERE user_id=%s      (cart emptied)"),
        ("call", 2, 3, "UPDATE users SET full_name, address, phone     (checkout form overwrites the profile)"),
        ("call", 2, 3, "INSERT INTO payments (payment_type='order', ...) if payment_method was sent\nthen conn.commit()  - all of the above is one transaction"),
        ("call", 2, 4, "threading.Thread(send_order_receipt_email) - HTML + text receipt, does NOT block"),
        ("return", 2, 0, "201 {order_id, total_amount, email_queued, email_message, order{...}}"),
        ("self", 0, "clear local cart, render receipt, some pages then POST the receipt text to 18.181.35.96 (external, unreliable)"),
    ]

    end = sequence(c, 50, 140, 1720, actors, steps)

    b = c.box(50, end + 16, 1720, None, "Failure behaviour students should test", [
        "Any exception inside the try block -> conn.rollback() and 500 {error}. Because the e-mail is sent AFTER commit, "
        "an order can exist with no receipt e-mail (check email_queued / email_message in the response).",
        "If MAIL_USERNAME or MAIL_PASSWORD is missing, the order still succeeds and the API says so instead of failing.",
        "4 different cart implementations exist, so a cart filled on /googleclothes is invisible on /phones.",
    ], fill="#FFFFFF", outline=LINE, line_size=12)

    c.finish(end + 16 + b,
             "Source: backend/app.py add_cart_item()/update_cart_item()/create_order(), frontend/phones/script.js",
             "05-cart-checkout-flow.png")


# ============================================================================
# 06 - API endpoints
# ============================================================================

def d06():
    c = Canvas(1820, 1440)
    c.header("06 - Complete API surface (every route in backend/app.py)",
             "All routes are registered twice, with and without a trailing slash. AUTH column = what the server actually verifies.")

    rows = [
        ("GET", "/api", "Health check. Also polled every 10s by session-watchdog.js", "none", "-"),
        ("POST", "/api/signup/request", "Validate password, store pending signup, e-mail OTP", "none", "pending_signups, users"),
        ("POST", "/api/signup/verify", "Promote pending_signups row into users", "OTP", "users, pending_signups"),
        ("POST", "/api/login/request", "Verify password, then send OTP only if not verified today", "password", "users"),
        ("POST", "/api/login/verify", "Check OTP, set last_login_otp_verified_at, return user", "OTP", "users"),
        ("GET", "/api/users/<email>", "Read a profile. UNUSED by the frontend", "NONE - email in URL", "users"),
        ("PUT", "/api/users/<email>", "Update full_name / address / phone. UNUSED by the frontend", "NONE - anyone can edit any profile", "users"),
        ("GET", "/api/cart?email=", "Cart items + server-computed total", "NONE - email in query", "cart_items"),
        ("POST", "/api/cart/items", "Add item, quantity accumulates via ON DUPLICATE KEY", "NONE - email in body", "cart_items"),
        ("PUT", "/api/cart/items", "Set quantity, <=0 deletes the row", "NONE - email in body", "cart_items"),
        ("DELETE", "/api/cart/items", "Remove one product from the cart", "NONE - email in body", "cart_items"),
        ("POST", "/api/orders", "Create order + items + payment, clear cart, e-mail receipt", "NONE - email in body", "orders, order_items, payments, cart_items, users"),
        ("GET", "/api/orders?email=", "Orders with nested items (1 extra query per order = N+1)", "NONE - email in query", "orders, order_items"),
        ("POST", "/api/payments", "Standalone payment record. UNUSED by the frontend", "NONE", "payments"),
        ("GET", "/api/payments?email=", "Payment history", "NONE", "payments"),
        ("POST", "/api/recharges", "Google Pay recharge: recharges + payments row + receipt e-mail", "NONE", "recharges, payments"),
        ("GET", "/api/recharges?email=", "Recharge history", "NONE", "recharges"),
        ("POST", "/api/service-activity", "Log 'user opened service X' before the redirect", "NONE", "service_activity"),
        ("GET", "/api/service-activity?email=", "Service visit log", "NONE", "service_activity"),
        ("GET", "/api/history?email=", "Portal 'Orders' tile: orders + payments + recharges + service_activity in one response", "NONE", "all 5 tables"),
    ]
    end = table(c, 50, 140, [110, 300, 610, 380, 320],
                ["METHOD", "PATH", "WHAT IT DOES", "AUTH ENFORCED BY SERVER", "TABLES TOUCHED"],
                rows, mono_cols=(1,))

    b = c.box(50, end + 24, 1720, None, "Reproduce the missing-auth problem in class (safe, read-only, on YOUR OWN test data)", [
        "curl \"http://FRONTEND_IP/api/history?email=someone@example.com\"        -> full order + payment history, no login",
        "curl -X PUT http://FRONTEND_IP/api/users/someone@example.com -H \"Content-Type: application/json\" -d \"{\\\"address\\\":\\\"changed\\\"}\"",
        "Add  Access-Control-Allow-Origin: *  from @after_request and any third-party website can do the same from a victim's browser.",
        "Fix direction: issue a signed token (JWT or server-side session) at /api/login/verify, require it on every route, and derive",
        "user_id from the token instead of from an email supplied by the client.",
    ], fill=RED[0], outline=RED[1], line_size=12, mono_lines=False)

    c.finish(end + 24 + b,
             "Source: backend/app.py (all @app.route declarations)",
             "06-api-endpoints.png")


# ============================================================================
# 07 - database schema
# ============================================================================

def d07():
    c = Canvas(1820, 1240)
    c.header("07 - Database schema (RDS MySQL, database 'cloud')",
             "8 tables. Every child table cascades from users, so deleting a user erases their whole history.")

    users = ["id INT PK AUTO_INCREMENT", "username VARCHAR(100) UNIQUE", "full_name VARCHAR(150)",
             "email VARCHAR(150) UNIQUE", "password VARCHAR(255)  <- hash", "phone VARCHAR(20)",
             "address TEXT", "otp_code VARCHAR(6)", "otp_expiry DATETIME",
             "last_login_otp_verified_at DATETIME", "created_at / updated_at TIMESTAMP"]
    c.box(660, 150, 470, None, "users  (the hub)", users, fill=BLUE[0], outline=BLUE[1],
          line_size=12, mono_lines=True)

    c.box(60, 150, 540, None, "pending_signups  (staging, pre-verification)",
          ["id PK", "email UNIQUE", "username UNIQUE", "full_name", "password_hash VARCHAR(255)",
           "otp_code VARCHAR(6) NOT NULL", "otp_expiry DATETIME NOT NULL", "created_at / updated_at"],
          fill=GREY[0], outline=GREY[1], line_size=12, mono_lines=True)

    c.box(60, 470, 540, None, "cart_items",
          ["id PK", "user_id FK -> users(id) ON DELETE CASCADE", "product_id VARCHAR(100)",
           "product_name / product_image / product_description", "price DECIMAL(10,2)",
           "quantity INT DEFAULT 1", "UNIQUE KEY (user_id, product_id)  <- makes the",
           "   ON DUPLICATE KEY quantity increment work", "created_at / updated_at"],
          fill=GREEN[0], outline=GREEN[1], line_size=12, mono_lines=True)

    c.box(1190, 150, 570, None, "orders",
          ["id PK", "user_id FK -> users(id) CASCADE", "shipping_name / shipping_email",
           "shipping_address TEXT / shipping_phone", "total_amount DECIMAL(10,2)",
           "status VARCHAR(50) DEFAULT 'placed'", "created_at / updated_at"],
          fill=YELLOW[0], outline=YELLOW[1], line_size=12, mono_lines=True)

    c.box(1190, 400, 570, None, "order_items",
          ["id PK", "order_id FK -> orders(id) CASCADE", "product_id VARCHAR(100)",
           "product_name / product_image", "price DECIMAL(10,2)", "quantity INT DEFAULT 1"],
          fill=YELLOW[0], outline=YELLOW[1], line_size=12, mono_lines=True)

    c.box(1190, 620, 570, None, "payments",
          ["id PK", "user_id FK -> users(id) CASCADE",
           "order_id FK -> orders(id) ON DELETE SET NULL  (NULL for recharges)",
           "payment_type 'order' | 'recharge' | 'payment'",
           "payment_method / status / transaction_reference / notes",
           "amount DECIMAL(10,2)", "created_at / updated_at"],
          fill=PURPLE[0], outline=PURPLE[1], line_size=12, mono_lines=True)

    c.box(660, 620, 470, None, "recharges  (Google Pay)",
          ["id PK", "user_id FK -> users(id) CASCADE", "mobile_number / operator_name",
           "plan_name", "amount DECIMAL(10,2)", "payment_method / status",
           "transaction_reference", "created_at / updated_at"],
          fill=TEAL[0], outline=TEAL[1], line_size=12, mono_lines=True)

    c.box(60, 780, 540, None, "service_activity  (click tracking)",
          ["id PK", "user_id FK -> users(id) CASCADE", "service_name VARCHAR(100)",
           "service_path VARCHAR(255)", "activity_type DEFAULT 'open'", "note", "created_at / updated_at"],
          fill=ORANGE[0], outline=ORANGE[1], line_size=12, mono_lines=True)

    # relations
    c.arrow(600, 240, 652, 240, GREY[1], 2, "OTP ok", reg(11))
    c.elbow([(660, 300), (636, 300), (636, 545), (604, 545)], GREEN[1], 2,
            "1 : N", (612, 500))
    c.elbow([(660, 355), (620, 355), (620, 830), (604, 830)], ORANGE[1], 2,
            "1 : N", (626, 760))
    c.arrow(1130, 240, 1185, 240, YELLOW[1], 2, "1 : N", reg(11))
    c.arrow(1470, 355, 1470, 395, YELLOW[1], 2, "1 : N", reg(11))
    c.arrow(1300, 570, 1300, 615, PURPLE[1], 2, "order_id (nullable)", reg(11))
    c.arrow(950, 430, 950, 615, TEAL[1], 2, "1 : N", reg(11))

    b = c.box(660, 900, 1100, None, "Runtime DDL + gotchas", [
        "orders, order_items and service_activity exist in backend/test.sql AND are re-created at runtime by "
        "ensure_order_tables() / ensure_service_activity_table(), which run inside create_order(), get_orders(), "
        "get_user_history() and the service-activity routes.",
        "test.sql starts with DROP TABLE for all 8 tables - running it again on a live database DELETES all data.",
        "Price columns are DECIMAL(10,2) in MySQL but float() in Python, so display rounding is done in the app layer.",
    ], fill="#FFFDE7", outline="#F9A825", line_size=12)

    c.finish(max(1000, 900 + b),
             "Source: backend/test.sql, backend/app.py ensure_order_tables() / ensure_service_activity_table()",
             "07-database-schema.png")


# ============================================================================
# 08 - security findings
# ============================================================================

def d08():
    c = Canvas(1820, 1600)
    c.header("08 - Security and reliability findings (fix list, worst first)",
             "Read from the code. Nothing here is theoretical - each item names the file that causes it.")

    items = [
        ("CRITICAL", "No authentication on the API",
         "Identity = the  email  string in the JSON body or ?email= query. There is no token, cookie or session. "
         "Every route (cart, orders, payments, recharges, history, PUT /api/users/<email>) can be called by anyone with curl.",
         "backend/app.py - every handler calls fetch_user_by_email(cursor, email_from_client)", RED),
        ("CRITICAL", "Credentials committed to git",
         "backend/.env is in the repo with the live RDS endpoint, DB_USER, plaintext DB_PASSWORD and the mail account "
         "password. Anyone who clones the repo owns the database.",
         "Rotate DB + Gmail app password, git rm --cached backend/.env, add .gitignore, move secrets to SSM Parameter Store / Secrets Manager", RED),
        ("HIGH", "CORS wide open with credentials in the URL",
         "@after_request sets Access-Control-Allow-Origin: * for every response, so any website can read another user's "
         "orders and payment history from the victim's browser (their e-mail is all that is needed).",
         "backend/app.py add_cors_headers()", RED),
        ("HIGH", "Auth gate is client-side only",
         "data-auth-required attributes and the localStorage check at the top of each service page only redirect the UI. "
         "Setting one localStorage key in DevTools bypasses all of it.",
         "frontend/*/index.html head script, frontend/main/index.html ensureLoggedInForService()", ORANGE),
        ("HIGH", "Hardcoded third-party receipt endpoints",
         "phones/electronics POST receipts to http://18.181.35.96/upload_receipt, computers to :5001/save-receipts, "
         "earphones to :5002/save-receipts. Not in this repo, not proxied, plain HTTP - they break on CORS, on HTTPS "
         "(mixed content) and when that IP changes.",
         "frontend/phones|electronics|computers|earphones/index.html uploadReceiptToS3()", ORANGE),
        ("MEDIUM", "No TLS anywhere",
         "Nginx listens on :80 only, and the proxy hop to Flask is plain HTTP. OTPs and addresses travel in clear text.",
         "frontend/main/google-store.conf - add ACM + ALB or certbot", YELLOW),
        ("MEDIUM", "Flask development server in production",
         "app.run(host='0.0.0.0') with no gunicorn, no systemd unit, no restart policy, single instance, single AZ. "
         "SSH session ends -> site is down.",
         "backend/app.py __main__ - use gunicorn + systemd behind an ALB", YELLOW),
        ("MEDIUM", "Blocking SMTP inside signup and login",
         "mail.send() runs inside the request for OTPs, so login latency = Gmail latency. Orders and recharges already "
         "use threads; the auth routes were never converted.",
         "backend/app.py signup_request(), login_request()", YELLOW),
        ("LOW", "DDL and N+1 queries on the request path",
         "CREATE TABLE IF NOT EXISTS runs on order/history requests, and GET /api/history issues one extra query per "
         "order to fetch its items.",
         "backend/app.py ensure_order_tables(), get_user_history()", GREY),
        ("LOW", "Four different cart stores + dead code",
         "DB cart, localStorage 'cart', localStorage 'mooncart_cart', in-memory portal cart. /googlepay is not linked "
         "from the portal, POST /api/payments and /api/users/<email> are never called by any page, and "
         "session-watchdog.js is loaded only by /googlegrocery.",
         "frontend/googleclothes, frontend/googlegrocery, frontend/main/index.html", GREY),
    ]

    y = 140
    for sev, title, body, where, col in items:
        h = c.box(50, y, 1720, None, title, [body, "WHERE: " + where], fill=col[0],
                  outline=col[1], line_size=12, pad=12,
                  badge=(sev, col[1], "#FFFFFF"))
        y += h + 14

    c.finish(y - 14,
             "Priority order for a class exercise: 1) real auth tokens  2) rotate + remove .env  3) lock CORS  4) TLS  5) gunicorn + systemd",
             "08-security-findings.png")


# ============================================================================
# 09 - deployment order
# ============================================================================

def d09():
    c = Canvas(1820, 1150)
    c.header("09 - Deployment order on AWS (what to build first and why)",
             "RDS first, then backend, then frontend: each step needs the address of the previous one.")

    steps = [
        ("STEP 1", "Amazon RDS MySQL", GREEN, [
            "Engine MySQL, free tier template",
            "DB name: cloud   user: admin",
            "Public access: No if backend is in the same VPC",
            "Inbound SG rule: 3306 FROM the backend EC2 SG",
            "",
            "Copy the endpoint:",
            "  xxx.rds.amazonaws.com",
        ]),
        ("STEP 2", "Backend EC2 (Flask)", YELLOW, [
            "sudo yum install -y git python3-pip mariadb105-server",
            "git clone <repo> ; cd backend",
            "mysql -h <rds-endpoint> -u admin -p < test.sql",
            "python3 -m venv venv ; source venv/bin/activate",
            "pip install -r requirements.txt",
            "vi .env   (PORT, DB_*, MAIL_*)",
            "python3 app.py",
            "curl http://127.0.0.1:5000/api  -> API is running",
        ]),
        ("STEP 3", "Frontend EC2 (Nginx)", BLUE, [
            "sudo yum install -y git nginx",
            "sudo systemctl enable --now nginx",
            "git clone <repo> ; cd frontend",
            "sudo cp -r * /usr/share/nginx/html/",
            "sudo cp -r main/* /usr/share/nginx/html/   <- portal at /",
            "cp main/google-store.conf /etc/nginx/conf.d/",
            "replace BACKEND_PRIVATE_IP with EC2#2 private IP",
            "sudo rm -f /etc/nginx/conf.d/default.conf",
            "sudo nginx -t ; sudo systemctl restart nginx",
        ]),
        ("STEP 4", "Verify end to end", PURPLE, [
            "http://FRONTEND_PUBLIC_IP/        portal loads",
            "curl http://FRONTEND_PUBLIC_IP/api   proxy works",
            "Sign up -> OTP mail arrives (check Gmail app password)",
            "Login -> open /phones -> Add -> Pay",
            "Portal 'Orders' tile shows the order",
            "SELECT * FROM orders; in MySQL shows the same row",
            "Receipt e-mail arrives from the background thread",
        ]),
    ]

    max_lines = max(len(lines) for _, _, _, lines in steps)
    card_h = 100 + max_lines * 17
    x = 50
    for tag, title, col, lines in steps:
        c.rect(x, 150, 400, card_h, fill=col[0], outline=col[1], r=12)
        c.rect(x + 14, 164, 84, 26, fill=col[1], outline=col[1], r=8)
        c.text(x + 56, 168, tag, bd(12), "#FFFFFF", anchor="ma")
        c.text(x + 14, 202, title, bd(17), col[1])
        yy = 236
        for ln in lines:
            for piece in wrap(ln, mono(11), (400 - 28) * S):
                c.text(x + 14, yy, piece, mono(11), INK)
                yy += 17
        if x < 1300:
            c.arrow(x + 405, 150 + card_h / 2, x + 445, 150 + card_h / 2, MUTED, 3)
        x += 440

    ny = 150 + card_h + 30
    n1 = c.box(50, ny, 860, None, "Two things that break every class demo", [
        "1. BACKEND_PRIVATE_IP left unreplaced in google-store.conf -> /api returns 502. The portal then looks logged out, "
        "because session-watchdog.js logs the user out when GET /api fails.",
        "2. Gmail normal password instead of an App Password -> signup returns 500 and no OTP arrives.",
    ], fill=RED[0], outline=RED[1], line_size=12)

    n2 = c.box(930, ny, 840, None, "Ports to remember", [
        "80    browser -> Nginx (public)",
        "5000  Nginx -> Flask (private, EC2#1 SG only)",
        "3306  Flask -> RDS  (private, EC2#2 SG only)",
        "587   Flask -> smtp.gmail.com (outbound TLS)",
    ], fill=GREEN[0], outline=GREEN[1], line_size=12, mono_lines=True)

    dy = ny + max(n1, n2) + 24
    b = c.box(50, dy, 1720, None, "Order of dependencies", [
        "RDS endpoint is needed by the backend .env  ->  backend private IP is needed by the Nginx proxy_pass  ->  "
        "the Nginx public IP is what students actually open. Build in that order and nothing has to be redone.",
    ], fill="#FFFFFF", outline=LINE, line_size=13)

    c.finish(dy + b,
             "Source: README.md deployment steps, frontend/main/google-store.conf, backend/.env keys",
             "09-deployment-order.png")


# ============================================================================
# 10 - single request cheat sheet
# ============================================================================

def d10():
    c = Canvas(1820, 1120)
    c.header("10 - Cheat sheet: follow ONE click through all 5 layers",
             "Example: a logged-in student on /phones presses 'Pay' with UPI.")

    hops = [
        ("1", "Browser", BLUE, "frontend/phones/script.js", [
            "placeOrderInDb('UPI') builds the payload from",
            "localStorage['googleStoreUser'] + the cart, then:",
            "fetch('/api/orders', {method:'POST', body: JSON})",
            "Relative URL - same origin, so no CORS needed.",
        ]),
        ("2", "Nginx", GREEN, "/etc/nginx/conf.d/google-store.conf", [
            "URL starts with /api/ -> matches  location /api/",
            "proxy_pass http://BACKEND_PRIVATE_IP:5000/api/;",
            "adds X-Real-IP, X-Forwarded-For, X-Forwarded-Proto",
            "Anything else falls to  try_files -> static file.",
        ]),
        ("3", "Flask", YELLOW, "backend/app.py create_order()", [
            "route /api/orders POST -> require_fields(email,",
            "shipping_name, shipping_address)",
            "ensure_order_tables(); fetch_user_by_email(email)",
            "cart items or request items[] -> compute total",
        ]),
        ("4", "MySQL", RED, "RDS database 'cloud'", [
            "INSERT orders -> INSERT order_items (loop)",
            "DELETE cart_items ; UPDATE users profile",
            "INSERT payments ; conn.commit()",
            "One transaction, rollback on any error.",
        ]),
        ("5", "SMTP", PURPLE, "background thread", [
            "threading.Thread -> send_order_receipt_email()",
            "build_order_receipt() renders text + HTML",
            "mail.send() to smtp.gmail.com:587",
            "Response already returned 201 to the browser.",
        ]),
    ]

    max_rows = max(sum(len(wrap(ln, reg(11), (320 - 28) * S)) for ln in lines)
                   for _, _, _, _, lines in hops)
    card_h = 112 + max_rows * 16
    x = 50
    for tag, title, col, src, lines in hops:
        c.rect(x, 150, 320, card_h, fill=col[0], outline=col[1], r=12)
        c.rect(x + 14, 164, 34, 34, fill=col[1], outline=col[1], r=17)
        c.text(x + 31, 170, tag, bd(15), "#FFFFFF", anchor="ma")
        c.text(x + 58, 172, title, bd(18), col[1])
        c.para(x + 14, 210, src, mono(10), 292, MUTED, lh=15)
        yy = 246
        for ln in lines:
            for piece in wrap(ln, reg(11), (320 - 28) * S):
                c.text(x + 14, yy, piece, reg(11), INK)
                yy += 16
        if x < 1400:
            c.arrow(x + 325, 150 + card_h / 2, x + 365, 150 + card_h / 2, col[1], 3)
        x += 350

    dy = 150 + card_h + 30
    b0 = c.box(50, dy, 1720, None, "Read it backwards to debug", [
        "Receipt e-mail missing but the order is in MySQL  ->  layer 5 (MAIL_* values / Gmail App Password). "
        "Check email_queued and email_message in the 201 response.",
        "500 with a MySQL error text  ->  layer 4 (SG on 3306, wrong DB_HOST, schema never imported).",
        "404 'User not found'  ->  layer 3: the email in the request does not exist in users (localStorage holds a stale user).",
        "502 Bad Gateway on /api  ->  layer 2: BACKEND_PRIVATE_IP wrong, Flask not running, or SG blocking 5000.",
        "Page redirects to / and looks logged out  ->  layer 1: session-watchdog.js saw GET /api fail and cleared localStorage "
        "(only /googlegrocery loads it), or the head-script gate found no googleStoreUser.",
    ], fill="#FFFFFF", outline=LINE, line_size=13)

    by = dy + b0 + 24
    b1 = c.box(50, by, 840, None, "What is really 'multi service' here", [
        "9 URL paths, 1 Nginx, 1 Flask process, 1 database.",
        "To make it genuinely microservices you would split app.py into",
        "auth / cart / orders / payments / recharge services, give each its",
        "own schema, and put an ALB or API Gateway in front with one",
        "auth service issuing tokens the others validate.",
    ], fill=TEAL[0], outline=TEAL[1], line_size=12)

    b2 = c.box(930, by, 840, None, "Minimum homework to make it production-shaped", [
        "1. JWT (or server session) issued at /api/login/verify, required everywhere.",
        "2. Secrets out of git, into SSM / Secrets Manager.",
        "3. gunicorn + systemd, ALB + ACM certificate, HTTPS only.",
        "4. Lock CORS to the site origin. Delete the 18.181.35.96 calls.",
        "5. One cart implementation, backed by the database.",
    ], fill=GREEN[0], outline=GREEN[1], line_size=12)

    c.finish(by + max(b1, b2),
             "Source: whole repo - frontend/phones/script.js, google-store.conf, backend/app.py, backend/test.sql",
             "10-request-cheatsheet.png")


# ============================================================================
# 11 - end to end communication map (all services -> backend -> database)
# ============================================================================

def d11():
    c = Canvas(2200, 1400)
    c.header("11 - End-to-end communication map: every service -> Nginx -> Flask -> MySQL",
             "9 browser paths fan into ONE proxy, ONE Flask process and ONE database. Follow any line left to right.")

    # ---- column 1: the 9 browser pages -------------------------------------
    services = [
        ("/  main portal", GREEN, "auth + cart + orders + history + activity"),
        ("/phones", BLUE, "cart + orders  (+ external receipt)"),
        ("/computers", BLUE, "cart + orders  (+ external receipt)"),
        ("/earphones", BLUE, "cart + orders  (+ external receipt)"),
        ("/electronics", BLUE, "cart + orders  (+ external receipt)"),
        ("/googleclothes", ORANGE, "orders only (cart kept in localStorage)"),
        ("/googlegrocery", TEAL, "orders + GET /api watchdog every 10s"),
        ("/googlemusic", PURPLE, "nothing - static page, login gate only"),
        ("/googlepay", RED, "recharges only"),
    ]
    sy0, sh, sgap = 160, 66, 10
    centers = []
    for i, (path, col, tags) in enumerate(services):
        y = sy0 + i * (sh + sgap)
        c.box(40, y, 290, sh, path, [tags], fill=col[0], outline=col[1],
              title_size=14, line_size=10, pad=10)
        centers.append(y + sh / 2)
    services_bottom = sy0 + len(services) * (sh + sgap) - sgap

    # ---- column 2: nginx ----------------------------------------------------
    c.box(380, 160, 170, services_bottom - 160, "Nginx :80", [
        "", "ONE origin,", "ONE server block", "", "location /",
        "  -> static file", "", "location = /api",
        "location /api/", "  -> proxy_pass", "  backend:5000", "",
        "Same origin, so",
        "the browser sends",
        "no CORS preflight",
        "for /api calls.",
    ], fill=GREEN[0], outline=GREEN[1], title_size=15, line_size=11, pad=10)

    for i, (path, col, tags) in enumerate(services):
        style_dash = (path == "/googlemusic")
        c.arrow(334, centers[i], 376, centers[i], col[1], 2, dash=style_dash)

    # spine: nginx -> flask router
    c.arrow(554, (160 + services_bottom) / 2, 596, (160 + services_bottom) / 2, GREEN[1], 3)

    # ---- column 3: flask route groups --------------------------------------
    groups = [
        ("AUTH routes", YELLOW, [
            "POST /api/signup/request  -> pending_signups + OTP mail",
            "POST /api/signup/verify   -> users (promote), delete pending",
            "POST /api/login/request   -> password check, daily OTP mail",
            "POST /api/login/verify    -> users (last_login_otp_verified_at)",
        ]),
        ("CART routes", GREEN, [
            "GET    /api/cart?email=      -> items + total",
            "POST   /api/cart/items       -> insert / quantity += ",
            "PUT    /api/cart/items       -> set quantity (0 deletes)",
            "DELETE /api/cart/items       -> remove one product",
        ]),
        ("ORDER routes", ORANGE, [
            "POST /api/orders  -> orders + order_items + payments,",
            "                     DELETE cart_items, UPDATE users,",
            "                     then receipt e-mail in a thread",
            "GET  /api/orders?email=  -> orders + nested items",
        ]),
        ("PAYMENT + RECHARGE routes", PURPLE, [
            "POST /api/recharges  -> recharges + payments + e-mail",
            "GET  /api/recharges?email=",
            "POST /api/payments   (unused by the frontend)",
            "GET  /api/payments?email=",
        ]),
        ("ACTIVITY + HISTORY routes", TEAL, [
            "POST /api/service-activity -> service_activity",
            "GET  /api/service-activity?email=",
            "GET  /api/history?email=   -> also SELECTs orders,",
            "        order_items, payments, recharges in one response",
        ]),
        ("HEALTH route", GREY, [
            "GET /api  -> {\"message\":\"API is running successfully\"}",
            "no database access, polled by session-watchdog.js",
        ]),
    ]
    gy = 160
    gcenters = []
    for title, col, lines in groups:
        h = c.box(650, gy, 560, None, title, lines, fill=col[0], outline=col[1],
                  title_size=14, line_size=11, pad=11, mono_lines=True)
        gcenters.append(gy + h / 2)
        c.arrow(600, gy + h / 2, 646, gy + h / 2, col[1], 2)
        gy += h + 18
    groups_bottom = gy - 18
    c.line(600, gcenters[0], 600, gcenters[-1], GREEN[1], 3)
    c.box(650, 120, 560, 30, None, [], fill="#FFFFFF", outline="#FFFFFF", r=0)
    c.text(650, 126, "Flask app.py :5000  -  one process, routes grouped by purpose",
           bd(13), YELLOW[1])

    # ---- column 4: RDS container + tables ----------------------------------
    tables = [
        ("users", BLUE, "profile + password hash + OTP state"),
        ("pending_signups", GREY, "unverified signups only"),
        ("cart_items", GREEN, "UNIQUE(user_id, product_id)"),
        ("orders  +  order_items", ORANGE, "1 : N, cascade delete"),
        ("payments", PURPLE, "order_id NULL for recharges"),
        ("recharges", TEAL, "Google Pay history"),
        ("service_activity", RED, "which service was opened"),
    ]
    tsy, tsh, tsgap = 190, 68, 14
    tcenters = []
    for i, (name, col, sub) in enumerate(tables):
        y = tsy + i * (tsh + tsgap)
        c.box(1288, y, 334, tsh, name, [sub], fill=col[0], outline=col[1],
              title_size=13, line_size=10, pad=9)
        tcenters.append(y + tsh / 2)
    cont_bottom = tsy + len(tables) * (tsh + tsgap) - tsgap + 16
    c.rect(1270, 150, 370, cont_bottom - 150, fill=None, outline=RED[1], r=12, width=2)
    c.text(1278, 158, "Amazon RDS MySQL   database 'cloud'   port 3306", bd(12), RED[1])

    # group -> table wiring (corridor x per group so lines never overlap)
    wiring = {0: [1, 0], 1: [2], 2: [3, 4, 2, 0], 3: [4, 5], 4: [6]}
    corridor = {0: 1232, 1: 1240, 2: 1248, 3: 1256, 4: 1264}
    for gi, tlist in wiring.items():
        col = groups[gi][1]
        for ti in tlist:
            c.elbow([(1214, gcenters[gi]), (corridor[gi], gcenters[gi]),
                     (corridor[gi], tcenters[ti]), (1284, tcenters[ti])],
                    col[1], 2)

    # ---- Gmail SMTP below the database ------------------------------------
    smtp_y = cont_bottom + 26
    c.box(1270, smtp_y, 370, None, "Gmail SMTP  smtp.gmail.com:587", [
        "signup OTP + login OTP  -> sent inside the request",
        "order receipt + recharge receipt -> background thread",
        "flask-mail, needs a Gmail App Password",
    ], fill=PURPLE[0], outline=PURPLE[1], title_size=13, line_size=11)
    for gi in (0, 2, 3):
        col = groups[gi][1]
        c.elbow([(1214, gcenters[gi] + 8), (1224, gcenters[gi] + 8),
                 (1224, smtp_y + 34), (1266, smtp_y + 34)], col[1], 2, )

    # ---- external endpoints (bypass Nginx) ---------------------------------
    ext_y = services_bottom + 30
    c.box(40, ext_y, 560, None, "Bypasses Nginx completely (browser -> public IP)", [
        "phones, electronics -> http://18.181.35.96/upload_receipt",
        "computers           -> http://18.181.35.96:5001/save-receipts",
        "earphones           -> http://18.181.35.96:5002/save-receipts",
        "googleclothes       -> ipinfo.io + cloudflare cdn-cgi/trace",
        "These never touch this backend or this database.",
    ], fill=RED[0], outline=RED[1], title_size=13, line_size=11,
        badge=("NOT IN REPO", "#D93025", "#FFFFFF"))
    for i in (1, 2, 3, 4):
        c.dashed(334, centers[i] + 22, 356, centers[i] + 22, RED[1], 2)
    c.dashed(356, centers[1] + 22, 356, ext_y - 22, RED[1], 2)
    c.arrow(356, ext_y - 22, 356, ext_y - 3, RED[1], 2)

    # ---- right column: rules / legend --------------------------------------
    ry = 150
    r1 = c.box(1690, ry, 470, None, "Legend", [
        "solid coloured arrow  = HTTP request (browser -> Nginx -> Flask)",
        "arrow into RDS box    = SQL executed by pymysql on port 3306",
        "dashed arrow          = no traffic / bypasses the proxy",
        "every line is one process hop, not a separate service",
    ], fill="#FFFFFF", outline=LINE, line_size=11)

    ry2 = ry + r1 + 20
    r2 = c.box(1690, ry2, 470, None, "Where 'who am I' comes from", [
        "1. Browser keeps localStorage['googleStoreUser'] = {email, ...}",
        "2. Every service page reads that object and copies user.email",
        "   into the JSON body or the ?email= query string.",
        "3. Flask calls fetch_user_by_email(cursor, email) and trusts it,",
        "   then uses users.id as the foreign key for every write.",
        "So identity travels as data, never as a credential. No token is",
        "issued at login and no route verifies one.",
    ], fill=RED[0], outline=RED[1], line_size=11)

    ry3 = ry2 + r2 + 20
    r3 = c.box(1690, ry3, 470, None, "The 3 hops that never change", [
        "browser  --HTTP :80-->  Nginx        (public subnet)",
        "Nginx    --HTTP :5000-> Flask        (private IP, same VPC)",
        "Flask    --TCP :3306--> RDS MySQL    (private, SG restricted)",
        "",
        "The browser can never reach :5000 or :3306 directly, which is",
        "why /api works through the site but not from a laptop.",
    ], fill=GREEN[0], outline=GREEN[1], line_size=11, mono_lines=False)

    ry4 = ry3 + r3 + 20
    r4 = c.box(1690, ry4, 470, None, "Why the pages share data", [
        "Add an item on /phones, open the portal cart: the same row is",
        "read back, because both call /api/cart with the same email.",
        "",
        "/googleclothes and /googlegrocery break that: their carts live in",
        "localStorage, so items only reach MySQL at checkout, inside the",
        "items[] array of POST /api/orders.",
    ], fill=YELLOW[0], outline=YELLOW[1], line_size=11)

    bottom = max(groups_bottom, cont_bottom, smtp_y + 100, ext_y + 150, ry4 + r4)
    c.finish(bottom,
             "Source: frontend/main/google-store.conf, frontend/*/script.js + index.html, backend/app.py, backend/test.sql",
             "11-service-communication-map.png")


if __name__ == "__main__":
    d01(); d02(); d03(); d04(); d05(); d06(); d07(); d08(); d09(); d10(); d11()
    print("done")
