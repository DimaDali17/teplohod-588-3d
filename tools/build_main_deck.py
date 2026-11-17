"""Теплоход пр. 588 — Главная палуба. Схема расположения помещений (существующее положение).
Геометрия восстановлена по схеме палуб т/х «Святая Русь» (пр. 588), miniflot.ru, с привязкой
к габаритам L=95,8 м, B=14,3 м. Координаты: X — от кормовой оконечности к носу, Y — от ДП (+ левый борт).
"""
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon, box
import ezdxf
from ezdxf.enums import TextEntityAlignment
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle

L, B = 95.8, 14.3

# ---------- корпус (полуширота палубы по X) ----------
hx = [0.0, 0.36, 1.20, 2.39, 4.79, 7.18, 11.97, 14.0, 77.8, 83.8, 88.6, 92.2, 94.6, 95.8]
hy = [0.0, 1.11, 2.10, 3.08, 4.56, 5.67, 7.03, 7.15, 7.15, 5.92, 4.07, 2.34, 0.74, 0.0]
half = PchipInterpolator(hx, hy)
xs = np.linspace(0, L, 400)
hull_pts = [(x, float(half(x))) for x in xs] + [(x, -float(half(x))) for x in xs[::-1]]
hull = Polygon(hull_pts)

# ---------- контур надстройки главной палубы ----------
DH_AFT_C, DH_AFT_A, DH_HALF, DH_FWD = 12.6, 6.6, 6.0, 89.5
pts = []
for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 60):        # кормовая скруглённая стенка
    pts.append((DH_AFT_C + DH_AFT_A * np.cos(t), DH_HALF * np.sin(t)))
for x in np.linspace(DH_AFT_C, DH_FWD, 200):               # правый борт к носу
    pts.append((x, -min(DH_HALF, float(half(x)) - 1.15)))
for x in np.linspace(DH_FWD, DH_AFT_C, 200):               # левый борт к корме
    pts.append((x, min(DH_HALF, float(half(x)) - 1.15)))
deckhouse = Polygon(pts).buffer(0)

# ---------- помещения ----------
rooms = []  # (код, наименование, полигон, категория)
def R(code, name, x0, x1, y0, y1, cat):
    rooms.append((code, name, box(x0, min(y0, y1), x1, max(y0, y1)), cat))

rooms.append(("1", "Кают-компания", deckhouse.intersection(box(0, -6, 12.6, 6)), "pub"))
R("2", "Служебное помещение (ЛБ)", 12.6, 22.7, 2.1, 6.0, "srv")
R("3", "Служебное помещение (ПрБ)", 12.6, 22.7, -2.1, -6.0, "srv")
R("4", "Шахта / трап (уточнить)", 22.7, 32.3, -2.2, 2.2, "tech")
R("5", "Амбулатория", 24.5, 32.9, 3.7, 6.0, "srv")
R("6", "Каюта врача", 32.9, 35.0, 2.4, 6.0, "srv")
R("7", "Служебное помещение (ПрБ)", 24.5, 32.9, -3.2, -6.0, "srv")
R("8", "Санузел М", 32.9, 35.0, 0.0, 1.0, "wc")
R("9", "Санузел Ж", 32.9, 35.0, -1.0, 0.0, "wc")

cab_x = [35.91, 38.24, 40.58, 42.91, 45.25, 47.64, 49.98, 52.31, 54.70]
port_nums = [88, 86, 84, 82, 80, 78, 76, 74]
stb_nums = [89, 87, 85, 83, 81, 79, 77, 75]
for i in range(8):
    R(str(port_nums[i]), f"Каюта 2-местн. №{port_nums[i]}", cab_x[i], cab_x[i + 1], 2.2, 6.0, "cab")
    R(str(stb_nums[i]), f"Каюта 2-местн. №{stb_nums[i]}", cab_x[i], cab_x[i + 1], -2.2, -6.0, "cab")
for x0, x1, p, s in [(57.22, 59.55, 72, 73), (59.55, 61.89, 70, 71)]:
    R(str(p), f"Каюта 2-местн. №{p}", x0, x1, 2.2, 6.0, "cab")
    R(str(s), f"Каюта 2-местн. №{s}", x0, x1, -2.2, -6.0, "cab")

R("10", "Санузел М", 37.1, 39.3, -1.0, 1.0, "wc")
R("11", "Санузел Ж", 39.3, 41.5, -1.0, 1.0, "wc")
R("12", "Душевая", 41.5, 44.4, 0.0, 1.0, "wc")
R("13", "Душевая", 44.4, 47.4, 0.0, 1.0, "wc")
R("14", "СП (назначение уточнить)", 47.4, 50.3, 0.0, 1.0, "srv")
R("15", "СП (назначение уточнить)", 41.5, 44.4, -1.0, 0.0, "srv")
R("16", "СП (назначение уточнить)", 44.4, 47.4, -1.0, 0.0, "srv")
R("17", "Душевая", 47.4, 50.3, -1.0, 0.0, "wc")
R("18", "Трап (ЛБ)", 54.70, 57.22, 2.2, 6.0, "tech")
R("19", "Трап (ПрБ)", 54.70, 57.22, -2.2, -6.0, "tech")
R("20", "Вестибюль", 61.89, 66.4, -6.0, 6.0, "pub")
R("21", "Десерт-холл", 66.4, 77.2, 2.1, 6.0, "pub")
R("22", "Камбуз", 66.4, 77.2, -2.1, -6.0, "srv")
rooms.append(("23", "Ресторан «Карелия»", deckhouse.intersection(box(77.8, -7, DH_FWD, 7)), "pub"))
stairs = [box(66.4, 3.0, 68.8, 5.0), box(66.4, -3.0, 68.8, -5.0)]

# ---------- экспликация ----------
expl = {}
for code, name, poly, cat in rooms:
    key = name if cat != "cab" else "Каюта 2-местная"
    e = expl.setdefault(key, {"codes": [], "area": 0.0, "n": 0})
    e["codes"].append(code); e["area"] += poly.area; e["n"] += 1
cab_area = [p.area for c, n, p, k in rooms if k == "cab"]
print("Кают:", len(cab_area), "площадь одной ≈ %.1f м²" % cab_area[0])
for k, v in expl.items():
    print(f"{k:32s} {v['n']:3d}  {v['area']:7.1f}")

CAT_COL = {"cab": "#CFE8D2", "pub": "#F6E3B4", "srv": "#E2E2E2", "wc": "#CFE0F2", "tech": "#BDBDBD"}

# ================= DXF (модель в мм, 1:1) =================
doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
doc.styles.add("GOST", font="isocpeur.ttf")
layers = {"КОРПУС": 7, "НАДСТРОЙКА": 7, "ПЕРЕБОРКИ": 5, "КАЮТЫ": 3, "ОБЩЕСТВ": 30, "СЛУЖЕБН": 8,
          "САНУЗЛЫ": 4, "ТРАПЫ": 6, "ТЕКСТ": 2, "РАЗМЕРЫ": 1, "ОСИ": 1}
for n, c in layers.items():
    doc.layers.add(n, color=c)
doc.layers.get("ОСИ").dxf.linetype = "CENTER"
msp = doc.modelspace()
M = 1000.0
def mm(pts): return [(x * M, y * M) for x, y in pts]
CAT_LAYER = {"cab": "КАЮТЫ", "pub": "ОБЩЕСТВ", "srv": "СЛУЖЕБН", "wc": "САНУЗЛЫ", "tech": "ТРАПЫ"}

msp.add_lwpolyline(mm(list(hull.exterior.coords)), close=True, dxfattribs={"layer": "КОРПУС", "lineweight": 70})
msp.add_lwpolyline(mm(list(deckhouse.exterior.coords)), close=True, dxfattribs={"layer": "НАДСТРОЙКА", "lineweight": 50})
msp.add_line((-2000, 0), ((L + 2) * M, 0), dxfattribs={"layer": "ОСИ"})
msp.add_text("ДП", height=350, dxfattribs={"layer": "ТЕКСТ", "style": "GOST"}).set_placement((-1800, 200))
for code, name, poly, cat in rooms:
    msp.add_lwpolyline(mm(list(poly.exterior.coords)), close=True, dxfattribs={"layer": CAT_LAYER[cat], "lineweight": 35})
    c = poly.representative_point() if cat != "cab" else poly.centroid
    h = 300 if cat == "cab" else 260
    t = msp.add_text(code, height=h, dxfattribs={"layer": "ТЕКСТ", "style": "GOST"})
    t.set_placement((c.x * M, c.y * M), align=TextEntityAlignment.MIDDLE_CENTER)
for s in stairs:
    msp.add_lwpolyline(mm(list(s.exterior.coords)), close=True, dxfattribs={"layer": "ТРАПЫ"})
    x0, y0, x1, y1 = s.bounds
    for k in range(1, 8):
        xx = x0 + (x1 - x0) * k / 8
        msp.add_line((xx * M, y0 * M), (xx * M, y1 * M), dxfattribs={"layer": "ТРАПЫ"})
# метки длины через 5 м
for x in range(0, 96, 5):
    msp.add_line((x * M, -8200), (x * M, -7800), dxfattribs={"layer": "ОСИ"})
    t = msp.add_text(str(x), height=300, dxfattribs={"layer": "ТЕКСТ", "style": "GOST"})
    t.set_placement((x * M, -8700), align=TextEntityAlignment.MIDDLE_CENTER)
# размеры
dimstyle = "EZDXF"
def dim(p1, p2, base, angle=0):
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, dimstyle=dimstyle,
                           override={"dimlfac": 1, "dimdec": 0, "dimtxt": 350, "dimasz": 250, "dimexe": 150, "dimexo": 150},
                           dxfattribs={"layer": "РАЗМЕРЫ"})
    d.render()
dim((0, 0), (L * M, 0), (0, -10500))
dim((14000, 7150), (14000, -7150), (-4000, 0), angle=90)
dim((cab_x[0] * M, 6000), (cab_x[1] * M, 6000), (0, 9000))
dim((cab_x[0] * M, 6000), (cab_x[0] * M, 2200), (34500, 0), angle=90)
dim((DH_AFT_C * M - DH_AFT_A * M, 0), (DH_FWD * M, 0), (0, 11000))
doc.saveas("/home/claude/out/588_glavnaya_paluba.dxf")

# ================= PDF / PNG, лист A2, М 1:200 =================
W, H = 594, 420
S = 5.0  # мм листа на 1 м (1:200)
OX, OY = 65, 330  # положение кормы/ДП на листе
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
plt.rcParams["font.family"] = "DejaVu Sans"
def P(x, y): return (OX + x * S, OY + y * S)
def poly(p, **kw): ax.add_patch(MPoly([P(*q) for q in p.exterior.coords], closed=True, **kw))

ax.add_patch(Rectangle((20, 5), W - 25, H - 10, fill=False, lw=1.4))
poly(hull, fill=True, fc="#FAFAF7", ec="black", lw=1.4)
poly(deckhouse, fill=False, ec="black", lw=1.0)
for code, name, p, cat in rooms:
    poly(p, fc=CAT_COL[cat], ec="black", lw=0.5)
    c = p.centroid if cat == "cab" else p.representative_point()
    cy = c.y + ((0.5 if code in ("10","11") else 1.0) if abs(c.y) < 0.6 and code in ("1", "4", "10", "11", "20", "23") else 0)
    ax.text(*P(c.x, cy), code, ha="center", va="center", fontsize=5.6 if cat == "cab" else 5.2)
for s in stairs:
    poly(s, fc="white", ec="black", lw=0.5)
    x0, y0, x1, y1 = s.bounds
    for k in range(1, 8):
        xx = x0 + (x1 - x0) * k / 8
        ax.plot(*zip(P(xx, y0), P(xx, y1)), color="black", lw=0.3)
ax.plot(*zip(P(-9, 0), P(L + 2, 0)), color="black", lw=0.4, dashes=(8, 2, 1, 2))
ax.text(*P(-10, 0.4), "ДП", fontsize=6)
ax.text(*P(1.0, 0), "Корма\n(откр.)", fontsize=5, ha="left", va="center")
ax.text(*P(91.0, 0), "Бак", fontsize=5, ha="left", va="center")
ax.text(*P(40, 6.6), "Наружный прогулочный проход ЛБ", fontsize=5, ha="center", va="center", style="italic")
ax.text(*P(40, -6.6), "Наружный прогулочный проход ПрБ", fontsize=5, ha="center", va="center", style="italic")
ax.text(*P(45, 1.6), "коридор", fontsize=4.6, ha="center", va="center", style="italic")
ax.text(*P(45, -1.6), "коридор", fontsize=4.6, ha="center", va="center", style="italic")
# шкала длины
for x in range(0, 96, 5):
    ax.plot(*zip(P(x, -8.0), P(x, -8.6)), color="black", lw=0.5)
    ax.text(*P(x, -9.3), str(x), fontsize=5, ha="center", va="top")
ax.plot(*zip(P(0, -8.3), P(L, -8.3)), color="black", lw=0.5)
ax.text(*P(L / 2, -11.0), "Длина наибольшая 95 800 (отсчёт, м, от кормовой оконечности)", fontsize=6, ha="center", va="top")
# ширина
for yy in (7.15, -7.15):
    ax.plot(*zip(P(14, yy), P(-7, yy)), color="black", lw=0.3)
ax.annotate("", xy=P(-6, 7.15), xytext=P(-6, -7.15), arrowprops=dict(arrowstyle="<->", lw=0.5))
ax.text(*P(-6.6, -3.5), "14 300", fontsize=5.5, rotation=90, va="center", ha="right")
ax.text(OX + L * S / 2, OY + 9.5 * S, "ГЛАВНАЯ ПАЛУБА   М 1:200", ha="center", fontsize=11, weight="bold")
ax.text(OX + L * S + 4, OY + 7.4 * S, "ЛБ", fontsize=7); ax.text(OX + L * S + 4, OY - 7.9 * S, "ПрБ", fontsize=7)
ax.annotate("", xy=(OX + L * S + 15, OY + 50), xytext=(OX + L * S - 10, OY + 50), arrowprops=dict(arrowstyle="->", lw=0.8))
ax.text(OX + L * S - 10, OY + 53, "В нос", fontsize=6)

# условные обозначения
lx, ly = 30, 245
ax.text(lx, ly + 10, "Условные обозначения", fontsize=7, weight="bold")
for i, (cat, lab) in enumerate([("cab", "Пассажирские каюты"), ("pub", "Общественные помещения"),
                                ("srv", "Служебные помещения"), ("wc", "Санузлы, душевые"), ("tech", "Трапы, шахты")]):
    ax.add_patch(Rectangle((lx, ly - i * 7), 10, 4.5, fc=CAT_COL[cat], ec="black", lw=0.5))
    ax.text(lx + 13, ly - i * 7 + 2.2, lab, fontsize=6, va="center")

# экспликация
tx, ty = 150, 262
cols = [(0, 14, "Поз."), (14, 80, "Наименование"), (94, 14, "Кол."), (108, 22, "Площадь, м²")]
rowh = 5.2
ax.text(tx, ty + 4, "Экспликация помещений", fontsize=7, weight="bold")
def row(i, vals, bold=False):
    y = ty - i * rowh
    for (cx, cw, _), v in zip(cols, vals):
        ax.add_patch(Rectangle((tx + cx, y - rowh), cw, rowh, fill=False, lw=0.5))
        ax.text(tx + cx + (1.5 if cw > 20 else cw / 2), y - rowh / 2, v, fontsize=5.3,
                ha="left" if cw > 20 else "center", va="center", weight="bold" if bold else "normal")
row(0, [c[2] for c in cols], True)
order = ["Кают-компания", "Ресторан «Карелия»", "Десерт-холл", "Вестибюль", "Каюта 2-местная", "Каюта врача",
         "Амбулатория", "Камбуз", "Служебное помещение (ЛБ)", "Служебное помещение (ПрБ)", "СП (назначение уточнить)",
         "Санузел М", "Санузел Ж", "Душевая", "Трап (ЛБ)", "Трап (ПрБ)", "Шахта / трап (уточнить)"]
total = 0
for i, k in enumerate(order, 1):
    v = expl[k]; total += v["area"]
    codes = v["codes"]
    pos = "70–89" if k == "Каюта 2-местная" else ", ".join(codes)
    row(i, [pos, k, str(v["n"]), f"{v['area']:.1f}"])
row(len(order) + 1, ["", "Итого внутри надстройки (по помещениям)", "", f"{total:.1f}"], True)

# примечания
nx, ny = 30, 195
notes = [
    "Примечания",
    "1. Схема восстановлена по плану палуб т/х «Святая Русь» (пр. 588) с сайта miniflot.ru",
    "    и привязана к габаритам L = 95,8 м, B = 14,3 м. Точность ±0,3–0,5 м.",
    "2. Это НЕ рабочий чертёж: положение переборок, шпангоутов, шахт и трапов",
    "    подлежит уточнению обмерами на судне.",
    "3. Нумерация кают — по схеме т/х «Святая Русь» (20 двухместных кают).",
    "4. Площади даны по осям переборок, без учёта толщины стенок и мебели.",
    "5. Отсчёт по длине — от кормовой оконечности, по ширине — от ДП.",
]
for i, t in enumerate(notes):
    ax.text(nx, ny - i * 5.5, t, fontsize=6.3 if i else 7, weight="bold" if i == 0 else "normal")

# штамп (упрощённо по ГОСТ 2.104, форма 1)
sx, sy = W - 5 - 185, 5
ax.add_patch(Rectangle((sx, sy), 185, 55, fill=False, lw=1.2))
for yy in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
    ax.plot([sx, sx + 65], [sy + yy, sy + yy], color="black", lw=0.4)
for xx in [7, 17, 40, 55, 65]:
    ax.plot([sx + xx, sx + xx], [sy, sy + 55], color="black", lw=0.4 if xx != 65 else 1.0)
ax.plot([sx + 65, sx + 185], [sy + 40, sy + 40], color="black", lw=1.0)
ax.plot([sx + 65, sx + 185], [sy + 15, sy + 15], color="black", lw=1.0)
ax.plot([sx + 135, sx + 135], [sy, sy + 40], color="black", lw=1.0)
ax.plot([sx + 135, sx + 185], [sy + 20, sy + 20], color="black", lw=0.6)
ax.plot([sx + 135, sx + 185], [sy + 35, sy + 35], color="black", lw=0.6)
for xx in [152, 170]:
    ax.plot([sx + xx, sx + xx], [sy + 20, sy + 40], color="black", lw=0.6)
for i, lab in enumerate(["Разраб.", "Пров.", "Т.контр.", "", "Н.контр.", "Утв."]):
    ax.text(sx + 1, sy + 27.5 - i * 5, lab, fontsize=4.6, va="center")
ax.text(sx + 125, sy + 47.5, "588-РК-01-ГП", ha="center", va="center", fontsize=11, weight="bold")
ax.text(sx + 100, sy + 27.5, "Теплоход проекта 588\nГлавная палуба\nСхема расположения помещений\n(существующее положение)",
        ha="center", va="center", fontsize=6.3)
ax.text(sx + 143.5, sy + 37.5, "Лит.", ha="center", va="center", fontsize=4.8)
ax.text(sx + 161, sy + 37.5, "Масса", ha="center", va="center", fontsize=4.8)
ax.text(sx + 177.5, sy + 37.5, "Масштаб", ha="center", va="center", fontsize=4.8)
ax.text(sx + 143.5, sy + 27.5, "Э", ha="center", va="center", fontsize=8)
ax.text(sx + 177.5, sy + 27.5, "1:200", ha="center", va="center", fontsize=8)
ax.text(sx + 160, sy + 17.5, "Лист 1      Листов 1", ha="center", va="center", fontsize=5.5)
ax.text(sx + 160, sy + 7.5, "Концептуальная проработка", ha="center", va="center", fontsize=5.5)
ax.text(sx + 100, sy + 7.5, "Эскизный вариант", ha="center", va="center", fontsize=6)
fig.savefig("/home/claude/out/588_glavnaya_paluba.pdf")
fig.savefig("/home/claude/out/588_glavnaya_paluba_preview.png", dpi=110)
print("done")
