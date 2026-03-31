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


def classify(rgb, debugging=False):
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


if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
