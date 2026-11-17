"""Эскизная 3D-модель теплохода пр. 588 -> web/model588.glb + web/rooms.json
Корабельные координаты: X от кормы (м), Y от ДП (+ЛБ), Z от ОП.
glTF (Y-вверх): x = X - L/2, y = Z, z = -Y.
Имена узлов только ASCII (three.js чистит точки/пробелы в именах) — подписи берутся из rooms.json.
"""
import json, os
import numpy as np
import trimesh
from shapely.geometry import Polygon, box, LineString
from scipy.interpolate import PchipInterpolator

src = open("/home/claude/build_main_deck.py", encoding="utf-8").read()
ns = {}
exec(src.split("# ---------- экспликация")[0], ns)
half, L, main_rooms, main_stairs = ns["half"], ns["L"], ns["rooms"], ns["stairs"]
deckhouse1 = ns["deckhouse"]

Z_WL = 2.4
Z_MAIN = 4.6
SLAB = 0.2
LOW = (1.9, Z_MAIN - 0.05)
T1 = (Z_MAIN, 7.1)
T2 = (7.1 + SLAB, 9.7)
T3 = (9.7 + SLAB, 12.3)
ROOF3 = 12.3
WH = (ROOF3 + SLAB, 14.6)

def sheer(X):
    z = Z_MAIN
    if X > 80:
        z += 2.3 * ((X - 80) / (L - 80)) ** 2
    if X < 6:
        z += 0.35 * (1 - X / 6)
    return z

def keel(X):
    if X < 9:
        return 2.8 * (1 - X / 9) ** 1.6
    if X > 91.3:
        return (X - 91.3) / (L - 91.3) * sheer(L) * 0.97
    return 0.0

def hb(X):
    return max(float(half(min(max(X, 0), L))), 0.0)

def sec(t):
    tb = 0.28
    return np.sqrt(max(0.0, 1 - (1 - t / tb) ** 2)) if t < tb else 1.0

def endf(X, t):
    return (0.75 + 0.25 * t) if (X < 12 or X > 84) else 1.0

def hull_half_at(X, z):
    zb, zd = keel(X), sheer(X)
    if z <= zb or zd - zb < 1e-6:
        return 0.0
    t = min(1.0, (z - zb) / (zd - zb))
    return hb(X) * sec(t) * endf(X, t)

def build_hull():
    NX, NT = 180, 28
    Xs = np.linspace(0.0, L, NX)
    ts = np.linspace(0, 1, NT)
    verts = []
    ring_n = 2 * NT + 1
    for X in Xs:
        zb, zd, b = keel(X), sheer(X), hb(X)
        ring = [(X, -b * sec(t) * endf(X, t), zb + (zd - zb) * t) for t in ts[::-1]]
        ring += [(X, b * sec(t) * endf(X, t), zb + (zd - zb) * t) for t in ts]
        ring.append((X, 0.0, zd + 0.15))
        verts.extend(ring)
    faces = []
    for i in range(NX - 1):
        a0, b0 = i * ring_n, (i + 1) * ring_n
        for j in range(ring_n):
            j2 = (j + 1) % ring_n
            faces.append([a0 + j, b0 + j, b0 + j2])
            faces.append([a0 + j, b0 + j2, a0 + j2])
    cols = []
    for (X, Y, Z) in verts:
        if Z < Z_WL - 0.05:
            cols.append([150, 45, 35, 255])
        elif Z < Z_WL + 0.35:
            cols.append([40, 40, 44, 255])
        elif Z > sheer(X) - 0.05 and abs(Y) < hb(X) - 0.05:
            cols.append([196, 178, 150, 255])
        else:
            cols.append([246, 246, 242, 255])
    return trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces),
                           vertex_colors=np.array(cols, dtype=np.uint8), process=False)

meshes = []        # (node_name, mesh)
parts_meta = []    # подписи для не-помещений
rooms_meta = []

def ext(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m

def colored(m, rgba):
    rgba = list(rgba) + [255] if len(rgba) == 3 else list(rgba)
    m.visual = trimesh.visual.ColorVisuals(m, face_colors=np.tile(rgba, (len(m.faces), 1)).astype(np.uint8))
    return m

def add(deck, kind, label, m, rgba=None):
    if rgba is not None:
        colored(m, rgba)
    pid = len(parts_meta)
    parts_meta.append({"deck": deck, "kind": kind, "name": label})
    meshes.append((f"{deck}-{kind}-p{pid}", m))

def bar(p0, p1, w=0.05, h=None):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    ln = np.linalg.norm(d)
    if ln < 1e-6:
        return None
    m = trimesh.creation.box(extents=[ln, w, h or w])
    m.apply_transform(trimesh.geometry.align_vectors([1.0, 0, 0], d / ln))
    m.apply_translation((p0 + p1) / 2)
    return m

def cat_(lst):
    return trimesh.util.concatenate([p for p in lst if p is not None])

def offset_outline(off, x0, x1, cap=7.2, n=160):
    xs = np.linspace(x0, x1, n)
    top = [(x, max(0.05, min(cap, hb(x) - off))) for x in xs]
    return Polygon(top + [(x, -y) for x, y in top[::-1]])

def rounded_house(x0, x1, w, ra, rf):
    pts = [(x0 + ra + ra * np.cos(t), w * np.sin(t)) for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 30)]
    pts += [(x1 - rf + rf * np.cos(t), w * np.sin(t)) for t in np.linspace(-np.pi / 2, np.pi / 2, 30)]
    return Polygon(pts)

COL = {"cab": (120, 200, 135), "cab4": (95, 190, 190), "lux": (240, 150, 150), "suite": (245, 150, 60),
       "pub": (240, 205, 120), "srv": (185, 185, 185), "wc": (130, 180, 230), "tech": (110, 110, 115),
       "mech": (95, 105, 125)}
SHELL = (250, 250, 247); DECKC = (200, 185, 160); WIN = (35, 50, 65); RAIL = (240, 240, 236)
DARK = (45, 45, 48); BED = (250, 250, 250); SOFA = (120, 140, 175)

def mix(c, k=0.55):
    return tuple(int(v + (255 - v) * k) for v in c)

def to3(X, Y, Z):
    return [round(X - L / 2, 3), round(Z, 3), round(-Y, 3)]

def furniture(poly, cat, z0):
    out = []
    x0, y0, x1, y1 = poly.bounds
    w, d = x1 - x0, y1 - y0
    port = (y0 + y1) / 2 > 0
    yout = y1 if port else y0
    sgn = 1 if port else -1
    def bed(xa, xb, z, h=0.45, depth=1.9):
        ya, yb = yout - sgn * depth, yout - sgn * 0.02
        b = trimesh.creation.box(extents=[xb - xa, abs(yb - ya), h])
        b.apply_translation([(xa + xb) / 2, (ya + yb) / 2, z + h / 2])
        return b
    if cat in ("cab", "cab4") and w < 3.0 and d > 2.5:
        bw = min(0.78, (w - 0.6) / 2)
        out += [(bed(x0 + 0.06, x0 + 0.06 + bw, z0), BED), (bed(x1 - 0.06 - bw, x1 - 0.06, z0), BED)]
        if cat == "cab4":
            out += [(bed(x0 + 0.06, x0 + 0.06 + bw, z0 + 1.15, 0.12), BED), (bed(x1 - 0.06 - bw, x1 - 0.06, z0 + 1.15, 0.12), BED)]
        tb = trimesh.creation.box(extents=[0.5, 0.45, 0.7])
        tb.apply_translation([(x0 + x1) / 2, yout - sgn * 0.3, z0 + 0.35])
        out.append((tb, (200, 170, 130)))
        yin = y0 if port else y1
        wd = trimesh.creation.box(extents=[0.6, 0.55, 1.9])
        wd.apply_translation([x0 + 0.38, yin + sgn * 0.33, z0 + 0.95])
        out.append((wd, (190, 160, 120)))
        wb = trimesh.creation.box(extents=[0.45, 0.35, 0.85])
        wb.apply_translation([x1 - 0.3, yin + sgn * 0.25, z0 + 0.42])
        out.append((wb, (235, 240, 245)))
    elif cat in ("lux", "suite"):
        bw = min(1.6, w * 0.45)
        out.append((bed(x0 + 0.1, x0 + 0.1 + bw, z0, depth=min(2.0, d - 0.6)), BED))
        s = trimesh.creation.box(extents=[0.8, max(0.8, min(1.8, d - 1.0)), 0.5])
        s.apply_translation([x1 - 0.5, (y0 + y1) / 2, z0 + 0.25])
        out.append((s, SOFA))
    return out

SEATS = []

def chair(cx, cy, ang, z0):
    c = trimesh.creation.box(extents=[0.42, 0.42, 0.45]); c.apply_translation([0, 0, 0.225])
    b = trimesh.creation.box(extents=[0.06, 0.42, 0.45]); b.apply_translation([-0.18, 0, 0.67])
    m = trimesh.util.concatenate([c, b])
    m.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
    m.apply_translation([cx, cy, z0])
    return m

def pub_furniture(deck, name, poly, z0):
    out = []
    inner = poly.buffer(-0.9)
    if inner.is_empty:
        return out
    x0, y0, x1, y1 = inner.bounds
    bar_x = None
    if "Бар" in name:
        bar_x = x1 - 0.6
        cnt = trimesh.creation.box(extents=[0.6, 5.0, 1.1]); cnt.apply_translation([bar_x, 0, z0 + 0.55])
        out.append((cnt, (120, 80, 50)))
        for yy in (-1.6, -0.5, 0.6, 1.7):
            st = trimesh.creation.cylinder(radius=0.18, height=0.75, sections=10); st.apply_translation([bar_x - 0.75, yy, z0 + 0.375])
            out.append((st, (60, 60, 60)))
            SEATS.append({"deck": deck, "pos": to3(bar_x - 0.75, yy, z0 + 0.3), "rot": 0.0, "room": name, "stool": True})
        SEATS.append({"deck": deck, "pos": to3(bar_x + 0.6, 0.3, z0), "rot": 3.1416, "room": name, "staff": "Бармен"})
        x1 = bar_x - 1.6
    step = 2.4
    xs_ = np.arange(x0 + 0.6, x1 - 0.3, step)
    ys_ = np.arange(-((y1 - y0) // step) * step / 2, (y1 - y0) / 2, step)
    from shapely.geometry import Point
    for xx in xs_:
        for yy in ys_:
            if not inner.contains(Point(xx, yy).buffer(0.9)):
                continue
            top = trimesh.creation.cylinder(radius=0.45, height=0.05, sections=16); top.apply_translation([xx, yy, z0 + 0.74])
            leg = trimesh.creation.cylinder(radius=0.06, height=0.72, sections=8); leg.apply_translation([xx, yy, z0 + 0.36])
            out.append((top, (250, 250, 250))); out.append((leg, (90, 90, 90)))
            for k, (dx, dy) in enumerate(((0.75, 0), (-0.75, 0), (0, 0.75), (0, -0.75))):
                ang = np.arctan2(-dy, -dx)
                out.append((chair(xx + dx, yy + dy, ang + np.pi, z0), (150, 60, 50)))
                SEATS.append({"deck": deck, "pos": to3(xx + dx, yy + dy, z0), "rot": round(float(np.arctan2(dy, dx)), 3), "room": name, "table": to3(xx, yy, z0)})
    return out

def room(deck, label, short, poly, cat, z, beds=True):
    z0, z1 = z[0] + 0.02, z[1] - 0.35
    parts = [colored(ext(poly, z0, z0 + 0.06), COL[cat])]
    ring = poly.difference(poly.buffer(-0.08))
    if not ring.is_empty:
        parts.append(colored(ext(ring, z0, z1), mix(COL[cat])))
    if beds:
        for f, c in furniture(poly, cat, z0 + 0.06):
            parts.append(colored(f, c))
    if cat == "pub" and "Вестибюль" not in label:
        for f, c in pub_furniture(deck, label, poly, z0 + 0.06):
            parts.append(colored(f, c))

    idx = len(rooms_meta)
    meshes.append((f"{deck}-room-r{idx}", trimesh.util.concatenate(parts)))
    x0, y0, x1, y1 = poly.bounds
    c = poly.representative_point()
    rooms_meta.append({"id": idx, "deck": deck, "name": label, "short": short, "cat": cat,
                       "area": round(poly.area, 1), "lx": round(x1 - x0, 2), "ly": round(y1 - y0, 2),
                       "xa": round(x0, 1), "xb": round(x1, 1), "pos": to3(c.x, c.y, z0 + 0.1)})

def cab_row(nums, xa, xb, y0, y1, cat, label, shortfmt="{}"):
    w = (xb - xa) / len(nums)
    return [(label.format(n), shortfmt.format(n), box(xa + i * w, min(y0, y1), xa + (i + 1) * w, max(y0, y1)), cat)
            for i, n in enumerate(nums)]

sx = 0.1197
def X(px): return px * sx

# ================= НИЖНЯЯ ПАЛУБА =================
D0 = "lower"
zc = LOW[0] + 0.3
low_out = Polygon([(x, hull_half_at(x, zc) - 0.35) for x in np.linspace(10, 84, 120)] +
                  [(x, -(hull_half_at(x, zc) - 0.35)) for x in np.linspace(84, 10, 120)]).buffer(0)
add(D0, "slab", "Настил нижней палубы", ext(low_out, LOW[0] - 0.12, LOW[0]), DECKC)
lower = [
    ("Служебное помещение (ЛБ)", "", low_out.intersection(box(12.6, 2.9, 22.1, 8)), "srv"),
    ("Служебное помещение (ПрБ)", "", low_out.intersection(box(12.6, -8, 22.1, -2.9)), "srv"),
    ("Машинное отделение", "МО", low_out.intersection(box(22.1, -8, 44.9, 8)), "mech"),
    ("Душевая", "", box(45.2, 0.3, 46.7, 1.8), "wc"),
    ("Душевая", "", box(45.2, -1.6, 46.7, -0.1), "wc"),
    ("Кладовые / шахта (уточнить)", "", box(46.8, -1.5, 65.8, 1.5), "srv"),
    ("Трап", "", box(69.1, -1.5, 71.5, 1.5), "tech"),
    ("Кладовые, форпик (уточнить)", "", low_out.intersection(box(71.6, -8, 84, 8)), "srv"),
]
lower += cab_row(list(range(124, 101, -2)), X(376), X(577), 2.9, 6.8, "cab4", "Каюта №{} (4-местн., 2-ярусн.)")
lower += cab_row(list(range(125, 102, -2)), X(377), X(577), -2.9, -6.8, "cab4", "Каюта №{} (4-местн., 2-ярусн.)")
for name, short, p, cat in lower:
    if cat == "cab4":
        p = p.intersection(low_out)
    room(D0, name, short, p, cat, LOW)

# ================= ГЛАВНАЯ =================
D1 = "main"
add(D1, "shell", "Надстройка главной палубы", ext(deckhouse1, *T1), SHELL)
for code, name, p, cat in main_rooms:
    if cat == "cab":
        room(D1, f"Каюта №{code} (2-местн.)", code, p, cat, T1)
    else:
        room(D1, name, "", p, cat, T1)
for s in main_stairs:
    room(D1, "Трап", "", s, "tech", (T1[0], T1[1] - 0.2), beds=False)

# ================= СРЕДНЯЯ =================
D2 = "mid"
slab2 = offset_outline(0.15, 0.6, L - 1.2)
add(D2, "slab", "Настил средней палубы", ext(slab2, T1[1], T1[1] + SLAB), DECKC)
house2 = offset_outline(1.6, 3.0, 92.0, cap=4.7)
add(D2, "shell", "Надстройка средней палубы", ext(house2, *T2), SHELL)
mid = [
    ("Бар «Буян»", "Бар", house2.intersection(box(0, -5, 12.6, 5)), "pub"),
    ("Каюта №61 (1-местн.)", "61", box(X(108), -4.5, X(125), -0.98), "cab"),
    ("Санузлы М/Ж", "", box(34.7, 0.9, 37.1, 4.5), "wc"),
    ("Душевая", "", box(34.7, -4.5, 37.1, -1.0), "wc"),
    ("СП (назначение уточнить)", "", box(X(458), 0.9, X(475), 4.5), "srv"),
    ("СП (назначение уточнить)", "", box(X(458), -4.5, X(475), -1.0), "srv"),
    ("Трап", "", box(X(533), 0.9, X(557), 4.5), "tech"),
    ("Служебная каюта (С/К)", "С/К", box(X(555), -4.5, X(593), -1.0), "srv"),
    ("Музыкальный салон", "Салон", house2.intersection(box(78.4, -5, 95, 5)), "pub"),
]
mid += cab_row([11, 12, 13], X(125), X(240), 0.9, 4.56, "lux", "Полулюкс №{}")
mid += cab_row([10, 9, 8, 7], X(125), X(277), -4.5, -0.98, "lux", "Полулюкс №{}")
for nums, xa, xb in [([46, 44, 42, 40, 38, 36], 340, 458), ([34, 32, 30], 475, 533), ([28, 26], 557, 593), ([22, 20], 613, 649)]:
    mid += cab_row(nums, X(xa), X(xb), 0.9, 4.56, "cab", "Каюта №{} (2-местн.)")
for nums, xa, xb in [([43, 41, 39, 37, 35, 33], 340, 458), ([31, 29, 27], 475, 533), ([25, 23, 21], 594, 649)]:
    mid += cab_row(nums, X(xa), X(xb), -4.5, -0.98, "cab", "Каюта №{} (2-местн.)")
for name, short, p, cat in mid:
    room(D2, name, short, p, cat, T2)

# ================= ШЛЮПОЧНАЯ =================
D3 = "boat"
bx = [62, 65, 70, 100, 200, 600, 700, 730, 742]
bh = [0.0, 3.4, 3.9, 5.7, 6.2, 6.2, 5.7, 3.3, 0.0]
bfun = PchipInterpolator([x * sx for x in bx], bh)
xs = np.linspace(bx[0] * sx, bx[-1] * sx, 140)
slab3 = Polygon([(x, float(bfun(x))) for x in xs] + [(x, -float(bfun(x))) for x in xs[::-1]]).buffer(0)
add(D3, "slab", "Настил шлюпочной палубы", ext(slab3, T2[1], T2[1] + SLAB), DECKC)
house3 = rounded_house(16.8, 76.6, 4.6, 2.5, 3.5)
add(D3, "shell", "Надстройка шлюпочной палубы", ext(house3, *T3), SHELL)
roof3 = rounded_house(16.3, 77.2, 4.85, 2.6, 3.6)
add(D3, "roof", "Солнечная палуба (крыша)", ext(roof3, ROOF3, ROOF3 + SLAB), DECKC)
boat = [
    ("Дискозал «Параллель»", "Дискозал", house3.intersection(box(0, -5, X(270), 5)), "pub"),
    ("Люкс Б", "Люкс Б", box(X(486), 0.55, X(540), 4.5), "suite"),
    ("Люкс А", "Люкс А", box(X(486), -4.5, X(540), -0.93), "suite"),
    ("Служебное помещение", "", box(X(436), -4.5, X(486), -0.93), "srv"),
    ("Ресторан «Панорама»", "Ресторан", house3.intersection(box(67.6, -5, 80, 5)), "pub"),
]
boat += cab_row([4, 3, 2, 1], X(310), X(486), 0.55, 4.5, "lux", "Полулюкс №{}")
boat += cab_row([5, 6], X(333), X(436), -3.64, -0.93, "lux", "Полулюкс №{}")
for name, short, p, cat in boat:
    room(D3, name, short, p, cat, T3)

# рубка и верх
wh = rounded_house(70.0, 76.4, 3.2, 0.6, 2.4)
add(D3, "top", "Рулевая рубка", ext(wh, *WH), SHELL)
add(D3, "top", "Крыша рубки", ext(rounded_house(69.8, 76.7, 3.4, 0.6, 2.5), WH[1], WH[1] + 0.15), DECKC)
wglass = rounded_house(70.3, 76.55, 3.25, 0.5, 2.45).difference(box(0, -5, 73.0, 5))
add(D3, "topwin", "Окна рубки", ext(wglass, WH[0] + 1.05, WH[0] + 1.75), WIN)
pj = trimesh.creation.cylinder(radius=0.22, height=0.5, sections=12); pj.apply_translation([75.2, 0, WH[1] + 0.4])
add(D3, "top", "Прожектор", pj, DARK)

def funnel(x0, x1, w, h, name):
    pts = [(x0 + w + w * np.cos(t), w * np.sin(t)) for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 16)]
    pts += [(x1 - w * 0.4 + w * 0.4 * np.cos(t), w * 0.55 * np.sin(t)) for t in np.linspace(-np.pi / 2, np.pi / 2, 16)]
    base = Polygon(pts).convex_hull
    body = ext(base, ROOF3 + SLAB, ROOF3 + SLAB + h)
    v = body.vertices
    top = v[:, 2] > ROOF3 + SLAB + h - 0.01
    v[top, 2] = ROOF3 + SLAB + h * (0.55 + 0.45 * (v[top, 0] - x0) / (x1 - x0))
    body.vertices = v
    cap = ext(base.buffer(0.04), 0, 0.35)
    vv = cap.vertices
    vv[:, 2] = ROOF3 + SLAB + h * (0.55 + 0.45 * (vv[:, 0] - x0) / (x1 - x0)) - 0.3 + vv[:, 2]
    cap.vertices = vv
    add(D3, "top", name, trimesh.util.concatenate([colored(body, SHELL), colored(cap, (30, 30, 32))]))
funnel(36.3, 43.2, 1.25, 3.4, "Дымовая труба")
funnel(59.4, 65.7, 1.25, 3.1, "Дымовая труба (вентиляционная)")

def mast(x, z0, z1, name):
    m = trimesh.creation.cylinder(radius=0.12, height=z1 - z0, sections=10)
    m.apply_translation([x, 0, (z0 + z1) / 2])
    return m
add(D3, "top", "Грот-мачта", cat_([mast(30.7, ROOF3, 18.0, ""), bar((30.7, -1.6, 16.4), (30.7, 1.6, 16.4), 0.08)]), (230, 230, 225))
add(D3, "top", "Фок-мачта", cat_([mast(72.5, WH[1], 18.6, ""), bar((72.5, -1.6, 17.2), (72.5, 1.6, 17.2), 0.08)]), (230, 230, 225))
add(D3, "top", "Штаги", cat_([bar((30.7, 0, 17.8), (2.0, 0, 7.7), 0.03), bar((30.7, 0, 17.8), (72.5, 0, 18.4), 0.03),
                              bar((72.5, 0, 18.4), (94.6, 0, 7.6), 0.03)]), (90, 90, 90))
fs = []
for xf, hh in ((0.9, 3.5), (94.6, 3.0)):
    m = trimesh.creation.cylinder(radius=0.07, height=hh, sections=8); m.apply_translation([xf, 0, sheer(xf) + hh / 2]); fs.append(m)
add("hull", "ext", "Флагшток / гюйсшток", cat_(fs), (230, 230, 225))

for xb in (19.0, 24.6, 30.2):
    for sgn in (1, -1):
        b = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        b.apply_scale([2.2, 0.75, 0.5]); b.apply_translation([xb, sgn * 5.5, T2[1] + SLAB + 1.4])
        add(D3, "ext", "Спасательная шлюпка", b, (245, 130, 40))
        dav = []
        for dx in (-1.6, 1.6):
            dav.append(bar((xb + dx, sgn * 4.75, T2[1] + SLAB), (xb + dx, sgn * 4.75, T2[1] + SLAB + 2.4), 0.12))
            dav.append(bar((xb + dx, sgn * 4.75, T2[1] + SLAB + 2.4), (xb + dx, sgn * 5.6, T2[1] + SLAB + 2.1), 0.1))
        add(D3, "ext", "Шлюпбалки", cat_(dav), (225, 225, 220))
for xr in (46.0, 49.0, 52.0):
    for sgn in (1, -1):
        c = trimesh.creation.cylinder(radius=0.32, height=1.2, sections=12)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        c.apply_translation([xr, sgn * 3.9, ROOF3 + SLAB + 0.35])
        add(D3, "top", "Спасательный плот (контейнер)", c, (235, 235, 230))

def railing(deck, kind, pts_xyz, h=1.0, post=1.5):
    pts = list(pts_xyz) + [pts_xyz[0]]
    dense = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.array(a), np.array(b)
        n = max(1, int(np.linalg.norm(b - a) / post))
        for k in range(1, n + 1):
            dense.append(tuple(a + (b - a) * k / n))
    ps = [bar(p, (p[0], p[1], p[2] + h), 0.05) for p in dense]
    for a, b in zip(dense[:-1], dense[1:]):
        for dz in (h, h * 0.5):
            ps.append(bar((a[0], a[1], a[2] + dz), (b[0], b[1], b[2] + dz), 0.045))
    add(deck, kind, "Леерное ограждение", cat_(ps), RAIL)

def outline_pts(poly, z_of, step=1.5):
    ring = LineString(poly.exterior.coords)
    return [(p.x, p.y, z_of(p.x)) for p in (ring.interpolate(k * step) for k in range(int(ring.length / step)))]

hull_edge = Polygon([(x, hb(x) - 0.12) for x in np.linspace(0.8, L - 1.5, 150)] +
                    [(x, -(hb(x) - 0.12)) for x in np.linspace(L - 1.5, 0.8, 150)])
railing("hull", "ext", outline_pts(hull_edge, sheer))
railing(D2, "ext", outline_pts(slab2.buffer(-0.08), lambda x: T1[1] + SLAB))
railing(D3, "ext", outline_pts(slab3.buffer(-0.08), lambda x: T2[1] + SLAB))
railing(D3, "top", outline_pts(roof3.buffer(-0.08), lambda x: ROOF3 + SLAB), h=0.9)

pil = []
for x in np.arange(8.0, 89.0, 4.66):
    for sgn in (1, -1):
        y = hb(x) - 0.45
        if y > 6.2:
            pil.append(bar((x, sgn * y, sheer(x)), (x, sgn * y, T1[1]), 0.14))
add(D1, "ext", "Пиллерсы прогулочной галереи", cat_(pil), RAIL)
pil = []
for x in np.arange(10.0, 86.0, 4.66):
    for sgn in (1, -1):
        y = float(bfun(x)) - 0.3
        if y > 5.0:
            pil.append(bar((x, sgn * y, T1[1] + SLAB), (x, sgn * y, T2[1]), 0.14))
add(D3, "ext", "Пиллерсы прогулочной галереи", cat_(pil), RAIL)

def windows(deck, x0, x1, yfun, z0, z1, pitch=2.33, w=1.1):
    ps = []
    x = x0
    while x + w < x1:
        for sgn in (1, -1):
            bb = trimesh.creation.box(extents=[w, 0.06, z1 - z0])
            bb.apply_translation([x + w / 2, sgn * (yfun(x + w / 2) + 0.01), (z0 + z1) / 2])
            ps.append(bb)
        x += pitch
    add(deck, "win", "Окна", cat_(ps), WIN)
windows(D1, 14.0, 77.0, lambda x: 6.0, T1[0] + 0.9, T1[0] + 1.9)
windows(D2, 6.0, 88.0, lambda x: min(4.7, hb(x) - 1.6), T2[0] + 0.85, T2[0] + 1.85)
windows(D3, 20.0, 74.0, lambda x: 4.6, T3[0] + 0.85, T3[0] + 1.85, pitch=2.6, w=1.4)
ps = []
for x in np.arange(12.0, 82.0, 2.33):
    for sgn in (1, -1):
        c = trimesh.creation.cylinder(radius=0.22, height=0.08, sections=12)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        c.apply_translation([x, sgn * (hull_half_at(x, 3.55) + 0.02), 3.55])
        ps.append(c)
add("hull", "win", "Иллюминаторы нижней палубы", cat_(ps), WIN)

under = []
for yy in (-2.6, 0.0, 2.6):
    xp, zp = 5.6, 0.95
    under.append(bar((xp, yy, zp), (13.0, yy, zp + 0.15), 0.18))
    hub = trimesh.creation.cylinder(radius=0.17, height=0.45, sections=12)
    hub.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    hub.apply_translation([xp, yy, zp]); under.append(hub)
    for k in range(3):
        bl = trimesh.creation.box(extents=[0.08, 0.32, 0.62]); bl.apply_translation([0, 0, 0.36])
        bl.apply_transform(trimesh.transformations.rotation_matrix(2 * np.pi * k / 3 + 0.3, [1, 0, 0]))
        bl.apply_translation([xp, yy, zp]); under.append(bl)
    rd = trimesh.creation.box(extents=[1.1, 0.12, 1.5]); rd.apply_translation([4.1, yy, 1.05]); under.append(rd)
add("hull", "ext", "Гребные винты (3), валы, рули", cat_(under), (170, 130, 60))
anc = []
for sgn in (1, -1):
    a = trimesh.creation.box(extents=[0.9, 0.12, 1.1]); a.apply_translation([88.5, sgn * (hull_half_at(88.5, 5.4) + 0.06), 5.4]); anc.append(a)
add("hull", "ext", "Якоря в клюзах", cat_(anc), DARK)
br = trimesh.creation.box(extents=[1.2, 2.2, 0.7]); br.apply_translation([91.0, 0, sheer(91.0) + 0.35])
add("hull", "ext", "Брашпиль", br, (90, 95, 100))

# ================= сборка =================
scene = trimesh.Scene()
def yup(m):
    v = m.vertices.copy()
    m.vertices = np.column_stack([v[:, 0] - L / 2, v[:, 2], -v[:, 1]])
    return m
parts_meta.append({"deck": "hull", "kind": "hull", "name": "Корпус"})
scene.add_geometry(yup(build_hull()), node_name=f"hull-hull-p{len(parts_meta) - 1}", geom_name="hull")
for name, m in meshes:
    scene.add_geometry(yup(m.copy()), node_name=name, geom_name=name)
os.makedirs("/home/claude/web", exist_ok=True)
scene.export("/home/claude/web/model588.glb")

summary = {}
for r in rooms_meta:
    d = summary.setdefault(r["deck"], {"cab": 0, "berths": 0})
    if r["cat"] in ("cab", "cab4", "lux", "suite"):
        d["cab"] += 1
        d["berths"] += 4 if r["cat"] == "cab4" else (1 if "1-местн" in r["name"] else 2)
json.dump({"rooms": rooms_meta, "parts": parts_meta, "summary": summary, "seats": SEATS},
          open("/home/claude/web/rooms.json", "w"), ensure_ascii=False)
print("meshes", len(meshes) + 1, "rooms", len(rooms_meta), os.path.getsize("/home/claude/web/model588.glb") // 1024, "KB")
print(summary)
print("seats", len(SEATS))
