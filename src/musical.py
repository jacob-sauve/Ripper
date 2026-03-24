from utils.sound import Sound

rhythm = 2


def victor_jingle():
    tone1 = Sound(duration = rhythm/8, pitch = "A3")

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
