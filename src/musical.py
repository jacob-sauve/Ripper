"""
All things musical
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick
import array

from utils.sound import Sound, Song

def make_sounds_victor():
    # duration of a full note (float possible)
    rhythm = 0.75

    chord_dur = 4*rhythm
    chord_tones = ["G#3", "C4", "D#4", "G4", "A#4"]
    chord_sounds = [Sound(duration=chord_dur, pitch=p, volume=80) for p in chord_tones]

# mix them by summing the audio arrays
    mixed = array.array('h', [0] * len(chord_sounds[0].audio))
    for s in chord_sounds:
        for i in range(len(mixed)):
            mixed[i] = max(-32768, min(32767, mixed[i] + s.audio[i]*1))

    chord = Sound(duration=chord_dur, pitch="A4", volume=100)
    chord.audio = mixed
    
    notes = [
            ("A3", rhythm/8), ("B3", rhythm/8), ("C4", rhythm*3/8),
            ("A3", rhythm*3/8), ("F3", rhythm/4), ("G3", rhythm/2),
            ("C4", rhythm/8), ("D4", rhythm/8), ("Eb4", rhythm*3/8),
            ("C4", rhythm*3/8), ("G#3", rhythm/4), ("Bb3", rhythm/2),
            ("Eb4", rhythm/2), ("F4", rhythm/2), ("F#4", rhythm*3/8),
            ("Eb4", rhythm*3/8), ("B3", rhythm/4), ("Db4", rhythm*3/8),
            ("F#4", rhythm*3/8), ("G#4", rhythm)
        ]

    sounds = [Sound(duration=dur, pitch=pitch, volume=100) for pitch, dur in notes] 
    sounds.append(chord)

    song = Song(sounds)
    song.compile()  # merges everything into one buffer
    return song

def make_sounds_delivery():
    # duration of a full note (float possible)
    rhythm = 0.75

    notes = [
        ("D3", rhythm / 8), ("E3", rhythm / 8), ("F3", rhythm / 8),
        ("E3", rhythm * 3 / 8), ("D3", rhythm *3/ 8), ("C3", rhythm *3/ 8),
        ("G3", rhythm)
    ]
    sounds = [Sound(duration=dur, pitch=pitch, volume=100) for pitch, dur in notes]
    song = Song(sounds)
    song.compile()
    return song

song1 = make_sounds_victor()
song2 = make_sounds_delivery()

def delivery_jingle():
    song2.play()
    song2.wait_done()

def victor_jingle():
    song1.play()
    song1.wait_done()

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
