#!/usr/bin/env python3

"""
Ripper driving scripts.
Implemented using multiprocessing.
"""

# imports
import sys, os

from sympy.physics.units.definitions.dimension_definitions import information

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick, Motor
from vision import _read_rgb, is_orange
import math
from time import sleep
from multiprocess import cpu_count, Process, Queue


# constants
R_WHEEL = 2.2           # wheel radius in cm
R_ROBOT = 7.60          # middle wheel to middle wheel in cm
MIN_SPEED = 270         # wheel rotation speed in degrees.s-1
LEFT = 1                # multiplier for correct rotations of left wheel
RIGHT = -1              # multiplier for correct rotations of right wheel
GRABBER = 1             # multiplier for correct rotations of grabber (should be pickup direction)
MEGAMIND_BUFFER = 0.01  # seconds between Megamind queue parsings


class Processor:
    """Parent class for all process wrapper classes"""
    def __init__(self, name):
        self.queue = Queue()                                # queue for interprocess comms through Megamind
        self.name = name
        self.process = Process(target=self.manage_queue)    # start process with queue parsing loop

    def start(self):
        self.process.start()

    def manage_queue(self):
        # implemented differently for actuators (get from queue) and sensors (put)
        pass


class Megamind(Processor):
    """
    Dispatcher/controller
    Reads main instruction queue and
        L-> sends instructions to motors
        L-> polls sensors
    ⢘⣾⣾⣿⣾⣽⣯⣼⣿⣿⣴⣽⣿⣽⣭⣿⣿⣿⣿⣿⣧
⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⠀⠀⠠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⠀⠀⣰⣯⣾⣿⣿⡼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿
⠀⠀⠛⠛⠋⠁⣠⡼⡙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁
⠀⠀⠀⠤⣶⣾⣿⣿⣿⣦⡈⠉⠉⠉⠙⠻⣿⣿⣿⣿⣿⠿⠁⠀
⠀⠀⠀⠀⠈⠟⠻⢛⣿⣿⣿⣷⣶⣦⣄⠀⠸⣿⣿⣿⠗⠀⠀⠀
⠀⠀⠀⠀⠀⣼⠀⠄⣿⡿⠋⣉⠈⠙⢿⣿⣦⣿⠏⡠⠂⠀⠀⠀
⠀⠀⠀⠀⢰⡌⠀⢠⠏⠇⢸⡇⠐⠀⡄⣿⣿⣃⠈⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠈⣻⣿⢫⢻⡆⡀⠁⠀⢈⣾⣿⠏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣿⣻⣷⣾⣿⣿⣷⢾⣽⢭⣍⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣿⣿⣿⣿⡿⠈⣹⣾⣿⡞⠐⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠨⣟⣿⢟⣯⣶⣿⣆⣘⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡆⠀⠐⠶⠮⡹⣸⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """
    def __init__(self, processor_dict):
        super().__init__("MEGAMIND")
        self.is_busy = False
        self.active_command = None
        # dictionnary mapping processor (sensor or actuator) name to Processor object
        self.processor_dict = processor_dict
        self.funcdict = {
            "GO": self._go_with_sensors,
            "TURN": self._turn_with_sensors
        }
        super().start()

    def addProcessor(self, processor):
        """connect a new processor (sensor/actuator)"""
        if processor is None:
            return False
        self.processor_dict[processor.name] = processor
        return True


    def killProcessor(self, processor):
        """kill processor object passed as arg"""
        if processor is None:
            return False
        del self.processor_dict[processor.name]
        processor.process.join() # kill active process
        del processor
        return True

    def killProcessorByName(self, name):
        processor = self.processor_dict.get(name)
        return self.killProcessor(processor)

    def killAll(self):
        for name in self.processor_dict:
            self.killProcessorByName(name)

    def manage_queue(self):
        while True:
            if not self.is_busy:
                instruction, *args = self.queue.get()
                if instruction:
                    self.is_busy
                    # call function
                    self.is_busy = not self.funcdict.get(instruction)(*args)
            else:
                pass
            sleep(MEGAMIND_BUFFER)

    def _go_with_sensors(self, speed=MIN_SPEED):
        """go a certain distance in a straight line. uses gyro for drift mgmt."""
        left, right, gyro = (self.processor_dict.get("LEFT"),
                             self.processor_dict.get("RIGHT"),
                             self.processor_dict.get("GYRO"))
        left.queue.put(("GO", speed))
        return True

    def _turn_with_sensors(self):
        return True


class Driver(Processor):
    """One driver per motor; worker class for process management"""
    def __init__(self, name, motor_pin_name, min_speed=MIN_SPEED):
        self.motor_pin_name = motor_pin_name
        self.is_moving = False
        # dict mapping funcnames to funcs for safe pickling
        self.funcdict = {
                "GO": self._go,
                "STOP": self._stop
                }
        self.name = name.upper()
        if self.name == "LEFT":
            self.direction = LEFT
        elif self.name == "RIGHT":
            self.direction = RIGHT
        elif self.name == "GRABBER":
            # grabber
            self.direction = GRABBER
        else:
            raise ValueError(f"Invalid Motor name: {self.name}. Should be one of: 'LEFT', 'RIGHT', 'GRABBER'")
        self.min_speed = min_speed * self.direction
        super().__init__(self.name)
        self.start()

    def start(self):
        """Start process, initialise Motor output pin"""
        self.motor_pin = Motor(self.motor_pin_name)
        super.start()

    def _go(self, speed=None):
        """start moving"""
        # set default speed value
        try:
            speed = self.direction * speed if speed is not None else self.min_speed
            self.motor_pin.set_dps(speed)
            self.is_moving = True
            return True
        except:
            return False

    def _stop(self):
        """stop moving"""
        try:
            self.motor_pin.set_dps(0)
            self.is_moving = False
            return True
        except:
            return False

    def manage_queue(self):
        while True:
            instruction = self.queue.get()
            if instruction:
                funcname, *args = instruction
                self.funcdict[funcname](*args)


# main loop
# REWORK THIS
if __name__ == "__main__":
    try:
        processors = dict()
        brain = Megamind(processors)
    except Exception as e:
        print(e)
        killall(brain, left, right)
        raise Exception("unable to launch driver processes")
    try:
        import titlecard
        titlecard.show()
        print(f"{cpu_count()=}\n\n")
        brain.move(20)
        brain.rotate_in_place(180)
        brain.move(20)
        brain.rotate_in_place(180)
        killall(brain, left, right)
    except BaseException as e:
        print(e)
    finally:
        killall(brain, left, right)
        reset_brick()
