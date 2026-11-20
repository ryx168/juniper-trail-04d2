"""Gastown Steam Clock, Vancouver - life-size stylised stand-in (~4.9 m). Tour 7554 stops here."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kit import *

reset()
granite = textured("granite", (0.48, 0.47, 0.46), scale=18, contrast=0.6)
bronze = flat("bronze", (0.32, 0.20, 0.10), rough=0.45, metal=0.8)
dark = flat("cast_iron", (0.10, 0.09, 0.08), rough=0.5, metal=0.6)
glass = flat("glass_glow", (0.95, 0.80, 0.45), rough=0.2, emit=1.2)
face = flat("clock_face", (0.95, 0.93, 0.86), rough=0.4)
gold = flat("gold", (0.85, 0.65, 0.25), rough=0.3, metal=1.0)

# granite plinth (two steps)
box((1.25, 1.25, 0.25), (0, 0, 0.125), granite, bevel=0.02)
box((1.05, 1.05, 0.35), (0, 0, 0.25 + 0.175), granite, bevel=0.02)
# lower cabinet with corner posts
box((0.78, 0.78, 1.35), (0, 0, 0.60 + 0.675), bronze, bevel=0.015)
for sx in (-1, 1):
    for sy in (-1, 1):
        cyl(0.055, 2.55, 0.60, dark, x=sx * 0.40, y=sy * 0.40, verts=16)
# glass works section (lit)
box((0.66, 0.66, 0.85), (0, 0, 1.95 + 0.425), glass)
box((0.84, 0.84, 0.08), (0, 0, 1.95), dark)
box((0.84, 0.84, 0.08), (0, 0, 2.80), dark)
# clock head: block with a dial on each side
box((0.92, 0.92, 0.80), (0, 0, 2.84 + 0.40), bronze, bevel=0.02)
for ang in range(4):
    a = math.radians(90 * ang)
    nx, ny = math.sin(a), -math.cos(a)  # first dial faces -Y (the front)
    rot = (math.radians(90), 0, a)
    cyl(0.30, 0.03, 0, face, x=nx * 0.46, y=ny * 0.46, verts=40, rot=rot).location.z = 3.24
    cyl(0.33, 0.02, 0, gold, x=nx * 0.455, y=ny * 0.455, verts=40, rot=rot).location.z = 3.24
    # hands: 10 past 10
    for length, tilt in ((0.22, 60), (0.16, -60)):
        h = box((0.025, 0.012, length), (0, 0, 0), dark)
        h.rotation_euler = (0, 0, 0)
        import mathutils
        M = (mathutils.Matrix.Translation((nx * 0.48, ny * 0.48, 3.24))
             @ mathutils.Matrix.Rotation(a, 4, 'Z')
             @ mathutils.Matrix.Rotation(math.radians(tilt), 4, 'Y')
             @ mathutils.Matrix.Translation((0, 0, length / 2)))
        h.matrix_world = M
# cornice, roof, whistles
box((1.02, 1.02, 0.10), (0, 0, 3.64 + 0.05), dark)
cone(0.70, 0.10, 0.55, 3.74, bronze, verts=4, rot=(0, 0, math.radians(45)), smooth=False)
for i, (dx, dy) in enumerate(((0, 0), (0.18, 0.18), (-0.18, 0.18), (0.18, -0.18), (-0.18, -0.18))):
    hgt = 0.55 if i == 0 else 0.35
    cyl(0.045, hgt, 4.10, gold, x=dx, y=dy, verts=16)
    sphere(0.06, (dx, dy, 4.10 + hgt), gold)

finish("steam_clock_gastown")
