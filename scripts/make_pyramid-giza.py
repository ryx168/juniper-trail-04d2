"""Great Pyramid of Giza at 1:150 (0.98 m tall, 1.54 m base) on a sand slab. Tour 7564 (Egypt)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kit import *

reset()
stone = textured("limestone_blocks", (0.78, 0.60, 0.36), scale=40, contrast=0.62)
sand = textured("sand", (0.86, 0.74, 0.52), scale=12, contrast=0.85)

H, B, STEPS = 146.6 / 150, 230.3 / 150, 28
box((B + 0.5, B + 0.5, 0.02), (0, 0, 0.01), sand)
for i in range(STEPS):
    z0 = 0.02 + i * H / STEPS
    w = B * (1 - (i + 0.5) / STEPS)
    box((w, w, H / STEPS), (0, 0, z0 + H / STEPS / 2), stone)
# the missing capstone: a small dark tip marks where it once stood
cone(B / STEPS * 0.75, 0.0, H / STEPS * 1.2, 0.02 + H, flat("tip", (0.55, 0.45, 0.30)), verts=4,
     rot=(0, 0, math.radians(45)), smooth=False)
finish("pyramid_giza_1to150")
