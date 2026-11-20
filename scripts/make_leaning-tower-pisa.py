"""Leaning Tower of Pisa at 1:30 (about 1.9 m tall), leaning about 4 degrees. Tour 7565 (Italy)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kit import *

reset()
marble = textured("marble", (0.93, 0.91, 0.86), scale=5, contrast=0.88, rough=0.4)
shadow = flat("arcade_shadow", (0.35, 0.33, 0.30), rough=0.8)
lawn = flat("lawn", (0.30, 0.48, 0.22), rough=0.9)

R = 0.26                       # 15.5 m / 30 / 2
box((1.1, 1.1, 0.015), (0, 0, 0.0075), lawn)
z = 0.015
# ground storey: blind arcade
cyl(R, 0.37, z, marble, verts=48)
ring_of(15, R + 0.006, lambda x, y, a: cyl(0.012, 0.33, z, marble, x=x, y=y, verts=8))
z += 0.37
# six open galleries
for g in range(6):
    h = 0.21
    cyl(R + 0.035, 0.018, z, marble, verts=48)            # gallery floor ledge
    cyl(R - 0.04, h, z, shadow, verts=40)                 # recessed inner wall
    ring_of(30, R + 0.01, lambda x, y, a: cyl(0.009, h - 0.02, z + 0.018, marble, x=x, y=y, verts=8))
    cyl(R + 0.03, 0.022, z + h - 0.022, marble, verts=48)  # arch band
    z += h
# bell chamber
cyl(R + 0.035, 0.018, z, marble, verts=48)
cyl(R * 0.62, 0.16, z, shadow, verts=40)
ring_of(16, R * 0.66, lambda x, y, a: cyl(0.009, 0.14, z + 0.018, marble, x=x, y=y, verts=8))
cyl(R * 0.68, 0.02, z + 0.16, marble, verts=40)
z += 0.18
print("tower height before lean", round(z, 3))

# lean ~4 degrees toward +X, pivoting on the low edge so nothing sinks below the lawn
tilt_all(4.0, 'Y', pivot=(R + 0.035, 0, 0.015))
finish("leaning_tower_pisa_1to30")
