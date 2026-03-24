"""
All things musical
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick

from utils.sound import Sound

# duration of a full note (float possible)
rhythm = 0.5


def victor_jingle():
    tone1 = Sound(duration = rhythm/8, pitch = "A3", volume=100)

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("B3")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("C4")
    tone1.update_duration(rhythm*3/8) 
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("A3")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("F3")
    tone1.update_duration(rhythm/4)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("G3")
    tone1.update_duration(rhythm/2)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()



    tone1.set_pitch("C4")
    tone1.update_duration(rhythm/8)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("D4")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("Eb4")
    tone1.update_duration(rhythm*3/8)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("C4")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("G#3")
    tone1.update_duration(rhythm/4)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("Bb3")
    tone1.update_duration(rhythm/2)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()




    tone1.set_pitch("Eb4")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("F4")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("F#4")
    tone1.update_duration(rhythm*3/8)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("Eb4")
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("B3")
    tone1.update_duration(rhythm/4)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("Db4")
    tone1.update_duration(rhythm*3/8)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()

    tone1.set_pitch("F#4")
    tone1.update_duration(rhythm*3/8)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()


    tone1.set_pitch("G#4")
    tone1.update_duration(rhythm)
    tone1.update_audio()

    tone1.play()
    tone1.wait_done()
#!/usr/bin/env python3



# main loop
if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
        victor_jingle()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
