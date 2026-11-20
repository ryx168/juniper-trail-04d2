"""Temple of Heaven, Hall of Prayer for Good Harvests (祈年殿), Beijing, at 1:20 (about 1.9 m). Tour 7584."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kit import *

reset()
white = textured("white_marble", (0.93, 0.92, 0.89), scale=8, contrast=0.9, rough=0.5)
red = flat("vermilion", (0.62, 0.08, 0.06), rough=0.55)
blue = flat("glazed_blue", (0.08, 0.20, 0.55), rough=0.3)
gold = flat("gilt", (0.85, 0.62, 0.20), rough=0.3, metal=1.0)
green = flat("eave_green", (0.10, 0.40, 0.30), rough=0.5)

# three-tier white marble terrace (real: 90 m wide, here cut to a 2 m base so it fits a room)
z = 0.0
for r, h in ((1.00, 0.09), (0.86, 0.09), (0.72, 0.09)):
    cyl(r, h, z, white, verts=64)
    ring_of(48, r - 0.02, lambda x, y, a: box((0.012, 0.012, 0.05), (x, y, z + h + 0.025), white))
    z += h
# building: red drum, three blue roofs, gilt finial
drum_r = [0.50, 0.40, 0.30]
roof_r = [0.66, 0.54, 0.42]
for i in range(3):
    h = 0.26 if i == 0 else 0.18
    cyl(drum_r[i], h, z, red, verts=48)
    ring_of(12 if i == 0 else 8, drum_r[i] + 0.02,
            lambda x, y, a: cyl(0.018, h, z, red, x=x, y=y, verts=10))
    cyl(drum_r[i] + 0.03, 0.03, z + h - 0.03, green, verts=48)      # painted bracket band
    z += h
    cone(roof_r[i], drum_r[i] * (0.85 if i < 2 else 0.12), 0.16 if i < 2 else 0.24, z, blue, verts=48)
    z += 0.10 if i < 2 else 0.24
cyl(0.03, 0.10, z, gold, verts=16)
sphere(0.06, (0, 0, z + 0.14), gold)
print("height", round(z + 0.2, 3))
finish("temple_of_heaven_1to20")
