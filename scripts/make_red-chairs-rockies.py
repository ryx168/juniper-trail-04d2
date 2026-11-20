"""Parks Canada red chairs - a life-size pair of Adirondack chairs. Tour 7616 (Rockies, Lake Louise)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kit import *
import mathutils

reset()
red = flat("parks_red", (0.70, 0.06, 0.05), rough=0.55)


def place(o, M):
    o.matrix_world = M @ o.matrix_world


def chair(ox, turn):
    parts = []
    W = 0.70
    # legs
    for sx in (-1, 1):
        parts.append(box((0.05, 0.05, 0.42), (sx * W / 2, -0.30, 0.21), red))   # front legs
        parts.append(box((0.05, 0.06, 0.24), (sx * W / 2, 0.30, 0.12), red))    # back legs
        parts.append(box((0.05, 0.70, 0.06), (sx * W / 2, 0.02, 0.30), red,      # side rail, sloping
                         rot=(math.radians(-12), 0, 0)))
    # seat slats sloping back
    for i in range(6):
        y = -0.28 + i * 0.10
        parts.append(box((W - 0.04, 0.08, 0.025), (0, y, 0.40 - i * 0.022), red, rot=(math.radians(-12), 0, 0)))
    # wide arms
    for sx in (-1, 1):
        parts.append(box((0.14, 0.62, 0.025), (sx * (W / 2 + 0.04), -0.05, 0.62), red))
        parts.append(box((0.05, 0.05, 0.22), (sx * W / 2, -0.30, 0.51), red))
    # fanned, reclined back slats
    for i in range(7):
        x = (i - 3) * 0.085
        s = box((0.075, 0.02, 0.80 - abs(i - 3) * 0.04), (x * 1.08, 0.34, 0.82), red,
                rot=(math.radians(-20), math.radians(-(i - 3) * 2.5), 0))
        parts.append(s)
    parts.append(box((W - 0.06, 0.03, 0.06), (0, 0.27, 0.55), red, rot=(math.radians(-20), 0, 0)))
    parts.append(box((W + 0.04, 0.03, 0.06), (0, 0.44, 1.05), red, rot=(math.radians(-20), 0, 0)))
    M = mathutils.Matrix.Translation((ox, 0, 0)) @ mathutils.Matrix.Rotation(math.radians(turn), 4, 'Z')
    for p in parts:
        place(p, M)


chair(-0.55, 10)
chair(0.55, -10)
finish("red_chairs_rockies")
