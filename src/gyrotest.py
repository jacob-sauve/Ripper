#!/usr/bin/env python3
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import * 
# EV3 gyro works best (less drift and less error results) if you hold it still in setup.
GYRO = EV3GyroSensor(3)
wait_ready_sensors(True)

if __name__ == "__main__":
    while True:
        print(GYRO.get_abs_measure())
        time.sleep(0.1)
