"""
Color classification script.
Uses 'omega value' calculated according to our formula and checks against saved
standard values.
"""

# imports
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick


# constants
# range of omega values at which colors are classified
OMEGA_THRESHOLDS = [
        (0.15, 0.25, "red"),
        (0.42, 0.60, "orange"),
        (0.68, 0.75, "yellow"),
        # i.e., all omega values 0.91<=w<=1.1 are green
        (0.91, 1.1, "green")
        ]

# (hue_min, hue_max, sat_min, val_min, color_name)
# hue really defines the colour, while saturation and brightness depend on lighting.
# So guards for sat and brightness can be adjusted to a pretty low value
# we just need those two low enough so it takes out outliers
COLOR_THRESHOLDS = [
    (0,    10,  0.65, 0.4, "red"),
    #(340,  360, 0.65, 0.6, "red"),
    (10,   25,  0.65, 0.6, "orange"),
    (25,   55,  0.65, 0.6, "yellow"),
    (55,   165, 0.65, 0.6, "green"),
]

def classify(rgb, debugging = False):
    try:
        h, s, v = rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
        hue = h*360

        for hue_min, hue_max, sat_min, val_min, color in COLOR_THRESHOLDS:
            if hue_min <= hue <= hue_max and s >= sat_min and v >= val_min:
                if debugging:
                    print(f"hsv:{h},{s},{v}")
                    print(color)
                return color
            else:
                if debugging:
                    print(f"hsv:{h},{s},{v}")
        return "ambiguous"

    except Exception:
        return "bad value"






def classify_color(rgb, debugging=True):
    """Classify rgb value as one of the four saved colours
    Keyword arguments:
        rgb         -- list of (R,G,B) values to be classified
        debugging   -- flag to toggle informative printing on/off (default off)
    Outputs:
        color       -- string indicating corresponding colour
    """
    # 1) normalise RGB values
    try:
        mag = math.sqrt(rgb[0]**2 + rgb[1]**2 + rgb[2]**2)
        if mag != 0:
            for i in range(3):
                rgb[i] = rgb[i] / mag
        else:
            return "false color mag = 0"

        # 2) calculate color's 'omega' value
        if rgb[1] != 0:
            omega = math.atan(math.asin(rgb[2]) / math.atan(rgb[0] * rgb[2] / rgb[1]))
        else:
            return "false color rgb[1] = 0"
        # 3) classify color
        for minimum, maximum, color in OMEGA_THRESHOLDS:
            if (minimum <= omega and omega <= maximum):
                if debugging:
                    print(omega)
                    print(color)
                return color
    except Exception:
        return "bad value"

# Very inspired by colorsys
def rgb_to_hsv(r,g,b):
    """TO DO
        """
    maxval = max(r,g,b)
    minval = min(r,g,b)
    rangeval = maxval - minval
    brightness = maxval
    if maxval == minval:
        return 0.0,0.0, brightness
    saturation = rangeval / maxval
    sr = (maxval-r)/ rangeval
    sg = (maxval-g)/ rangeval
    sb = (maxval-b)/ rangeval
    if r == maxval:
        hue = sb - sg
    elif g == maxval:
        hue = 2.0+sr - sb
    else:
        hue = 4.0+sg-sr
    hue = (hue/6.0) % 1.0
    return hue, saturation, brightness

if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
