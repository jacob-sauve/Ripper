#!/usr/bin/env python3

"""
Ripper scripts.
"""

# imports
from utils.brick import BP, Motor, reset_brick

# constants
ORANGE_R_MIN = 100
ORANGE_G_MAX = 160
ORANGE_RG_RATIO = 1.4
ORANGE_B_MAX = 60

# main loop

def _read_rgb(sensor):
    rgb = sensor.get_rgb()
    if rgb is None or None in rgb:
        return (0,0,0)
    print(rgb)
    return rgb[0], rgb[1], rgb[2]

def is_orange(r,g,b):
    return (
        r > ORANGE_R_MIN
        and g < ORANGE_G_MAX
        and b < ORANGE_B_MAX
        and g > 0
        and (r/g) > ORANGE_RG_RATIO
    )

if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
