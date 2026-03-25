"""
All things musical
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick

from utils.sound import Sound, Song

# duration of a full note (float possible)
rhythm = 0.5

def victor_jingle():
    notes = [
        ("A3", rhythm/8), ("B3", rhythm/8), ("C4", rhythm*3/8),
        ("A3", rhythm*3/8), ("F3", rhythm/4), ("G3", rhythm/2),
        ("C4", rhythm/8), ("D4", rhythm/8), ("Eb4", rhythm*3/8),
        ("C4", rhythm*3/8), ("G#3", rhythm/4), ("Bb3", rhythm/2),
        ("Eb4", rhythm/2), ("F4", rhythm/2), ("F#4", rhythm*3/8),
        ("Eb4", rhythm*3/8), ("B3", rhythm/4), ("Db4", rhythm*3/8),
        ("F#4", rhythm*3/8), ("G#4", rhythm),
    ]

    sounds = [Sound(duration=dur, pitch=pitch, volume=100) for pitch, dur in notes]

    song = Song(sounds)
    song.compile()  # merges everything into one buffer
    song.play()
    song.wait_done()

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
