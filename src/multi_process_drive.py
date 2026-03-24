#!/usr/bin/env python3

"""
Ripper driving scripts.
Implemented using multiprocessing.
"""

# imports
import sys, os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick, Motor, EV3ColorSensor, EV3GyroSensor, TouchSensor, wait_ready_sensors
from vision import _read_rgb, is_orange
from math import pi
from time import sleep
from multiprocess import cpu_count, Process, Queue


# constants
R_GRABBER = 1.8
R_WHEEL = 2.2           # wheel radius in cm
R_ROBOT = 7.52          # middle wheel to middle wheel in cm
MIN_SPEED = 270         # wheel rotation speed in degrees.s-1
LEFT = -1               # multiplier for correct rotations of left wheel
RIGHT = -1              # multiplier for correct rotations of right wheel
GRABBER = -1            # multiplier for correct rotations of grabber (should be pickup direction)
MEGAMIND_BUFFER = 0.005 # seconds between Megamind queue parsings
MAX_DRIFT = 0.5         # max degrees of drift acceptable from desired rectilinear trajectory
DRIFT_CORRECTION = 1.05 # percentage (decimal form) of desired speed applied to lagging wheel if drifting


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
    def __init__(self, processor_dict=dict()):
        super().__init__("MEGAMIND")
        self.is_busy = False
        self.active_command = None
        # dictionnary mapping processor (sensor or actuator) name to Processor object
        self.processor_dict = processor_dict
        self.funcdict = {
            "GO": self._go_with_sensors,
            "TURN": self._turn_with_sensors,
            "GRAB": self._grab
        }
        # mapping of Sensor objects to their respective most recent readings
        self.latest_readings = dict()
        self.start()

    def start(self):
        wait_ready_sensors(True)
        super().start()
    
    def addProcessor(self, processor):
        """connect a new processor (sensor/actuator)"""
        if processor is None:
            return False
        self.processor_dict[processor.name] = processor
        print(self.processor_dict)
        return True


    def killProcessor(self, processor):
        """kill processor object passed as arg"""
        if processor is None:
            return False
        processor.process.terminate() # kill active process
        return True

    def killProcessorByName(self, name):
        processor = self.processor_dict.get(name)
        return self.killProcessor(processor)

    def killAll(self):
        for name in self.processor_dict:
            self.killProcessorByName(name)
        # kill itself
        self.process.terminate()


    def clearSensorQueues(self):
        """Empty all sensor queues to have up-to-date data at front of queue"""
        sensors = (self.processor_dict.get("GYRO"),
                   self.processor_dict.get("COLOR"))
        queue_front_dict = dict(zip(sensors, [None]*len(sensors)))
        for sensor in sensors:
            if not (sensor is None):
                try:
                    queue_front = sensor.queue.get_nowait()
                #queue_front = sensor.queue.get()
                except:
                    queue_front = None
                while not (queue_front is None):
                    queue_front_dict[sensor] = queue_front
        return queue_front_dict

    def manage_queue(self):
        """probably should rework --> could easily get stuck in busy mode"""
        while True: 
            instruction, *args = self.queue.get()
            #instruction, *args = self.queue.get()
            if instruction:
                # call function
                self.funcdict.get(instruction)(*args)
            # clear sensor queues to keep them up to date, store newest readings
            self.latest_readings = self.clearSensorQueues()
            sleep(MEGAMIND_BUFFER)

    def _distance_to_iterations(self, distance, speed=MIN_SPEED, radius=R_WHEEL):
        # calculate how much motor rotation is necessary to move distance
        n_rotations = abs(distance / (radius * pi * 2))
        spin_time = (n_rotations * 360) / speed
        # calculate amount of iterations with delay equal to constant buffer are needed
        return int(spin_time / MEGAMIND_BUFFER)

    def _go_with_sensors(self, distance, speed=MIN_SPEED):
        """go a certain distance in a straight line. uses gyro for drift mgmt."""
        granular_iterations = self._distance_to_iterations(distance)
        left, right, touch, gyro = (self.processor_dict.get("LEFT"),
                             self.processor_dict.get("RIGHT"),
                             self.processor_dict.get("TOUCH"),
                             self.processor_dict.get("GYRO"))
        left.queue.put(("GO", speed))
        right.queue.put(("GO", speed))
        # get most recent gyro reading, if existent
        # take it as reference for "straightness"
        initial_angle = gyro.queue.get().get("angle")
        for i in range(granular_iterations):
            gyro_readings = gyro.queue.get()
            if gyro_readings:
                drift =  gyro_readings.get("angle") - initial_angle
                # flip these corrections if they're inverted
                #print(f"{drift=}")
                if drift > MAX_DRIFT:
                    print("right drift. correcting...")
                    # right wheel lagging
                    #right.queue.put(("STOP",))
                    #left.queue.put(("STOP",))
                    right.queue.put(("GO", speed * DRIFT_CORRECTION))
                    left.queue.put(("GO", speed / DRIFT_CORRECTION))
                    #right.queue.put(("GO", speed))
                    #left.queue.put(("STOP",))
                elif drift < -MAX_DRIFT:
                    print("left drift. correcting...")
                    # left wheel lagging
                    #right.queue.put(("STOP",))
                    #left.queue.put(("STOP",))
                    right.queue.put(("GO", speed / DRIFT_CORRECTION))
                    left.queue.put(("GO", speed * DRIFT_CORRECTION))
                    #right.queue.put(("STOP",))
                    #left.queue.put(("GO", speed))
                else:
                    # all good
                    left.queue.put(("GO", speed))
                    right.queue.put(("GO", speed))
            #print("about to sleep, iterating...")
            sleep(MEGAMIND_BUFFER)
        left.queue.put(("STOP",))
        right.queue.put(("STOP",))
        return True

    def _turn_with_sensors(self):
        return True

    def _grab(self, distance, speed=MIN_SPEED):
        granular_iterations = self._distance_to_iterations(distance, radius=R_GRABBER)
        grabber = self.processor_dict.get("GRABBER")

        grabber.queue.put(("GO", speed))

        for i in range(granular_iterations):
            print(f"waiting... iteration {i}")
            sleep(MEGAMIND_BUFFER)

        grabber.queue.put(("STOP",))
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
            raise ValueError(f"Invalid Motor name: '{self.name}'. Should be one of: 'LEFT', 'RIGHT', 'GRABBER'")
        self.min_speed = min_speed * self.direction
        super().__init__(self.name)
        self.start()

    def start(self):
        """Start process, initialise Motor output pin"""
        self.motor_pin = Motor(self.motor_pin_name)
        super().start()

    def _go(self, speed=None):
        """start moving"""
        # set default speed value
        try:
            power = 100*(self.direction * speed)/self.motor_pin.MAX_SPEED if speed is not None else 100*self.min_speed/self.motor_pin.MAX_SPEED
            print(power)
            self.motor_pin.set_power(power)
            self.is_moving = True
           #print(self.name + " moving")
            return True
        except:
            return False

    def _stop(self):
        """stop moving"""
        try:
            print("stopping...")
            self.motor_pin.set_power(0)
            self.is_moving = False
            print("stopped")
            return True
        except:
            return False

    def manage_queue(self):
        while True:
            instruction = self.queue.get()
            if instruction:
                funcname, args = instruction[0], instruction[1:]
                self.funcdict[funcname](*args)


class Vision(Processor):
    """One Vision object per sensor; worker class for process management"""
    def __init__(self, name, sensor_pin_number, poll_period=MEGAMIND_BUFFER):
        self.sensor_pin_number = sensor_pin_number
        self.name = name.upper()
        # seconds between sensor polls
        self.poll_period = poll_period
        # set port initialisation and polling functions
        if self.name == "GYRO":
            self.setup_function = EV3GyroSensor
            self.read = self.gyro_measure
        elif self.name == "TOUCH":
            self.setup_function = TouchSensor
            self.read = self.touch_measure
        elif self.name == "COLOR":
            self.setup_function = EV3ColorSensor
            self.read = self.color_measure
        else:
            raise ValueError(f"Invalid Sensor name: '{self.name}'. Should be one of: 'GYRO', 'TOUCH', 'COLOR'")
        super().__init__(self.name)
        self.start()

    def start(self):
        # setup sensor pin
        self.sensor_pin = self.setup_function(self.sensor_pin_number)
        super().start()

    def gyro_measure(self, *args):
        if self.name != "GYRO":
            return False
        data = self.sensor_pin.get_both_measure()
        if data is None:
            return None
        output = dict()
        for mode in args:
            if mode == "angle":
                output["angle"] = data[0]
            if mode == "dps":
                output["dps"] = data[1]
        return output

    def touch_measure(self, *args):
        if self.name != "TOUCH":
            return False
        is_pressed = self.sensor_pin.is_pressed()
        if is_pressed:
                return {"press":is_pressed}

    def color_measure(self, *args):
        if self.name != "COLOR":
            return False
        return True

    def manage_queue(self):
        while True:
            args = []
            if self.name == "GYRO":
                args.append("angle")
            measurement = self.read(*args)
            # put new reading to output queue
            if measurement:
                #if self.name == "GYRO":
                    #print("I'm alive!!!")
                self.queue.put(measurement)
                time.sleep(self.poll_period)

# main loop
if __name__ == "__main__":
    processors = {
            "GYRO": Vision("GYRO", 3),
            "LEFT": Driver("LEFT", "A"),
            "RIGHT": Driver("RIGHT", "D"),
            "GRABBER": Driver("GRABBER", "B")
        }
    brain = Megamind(processors)
    stop = TouchSensor(1)
    try:
        import titlecard
        titlecard.show()
        print(f"{cpu_count()=}\n\n")
        #brain.queue.put(("GO", 10))
        brain.queue.put(("GRAB", 50, 500))
        while not stop.is_pressed():
            sleep(0.01)
        raise Exception()
    except Exception as e:
        print(e)
    finally:
        print("killing...")
        brain.killAll()
        print("killed.")
        reset_brick()
