from utils.brick import BP, Motor, reset_brick
import time

right = Motor("C")
left = Motor("B")

try:
    right.set_dps(20)
    left.set_dps(20)
    time.sleep(5)
except:
    print("error")

reset_brick()
