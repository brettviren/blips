#!/usr/bin/env python
'''
Uboone specific stuff
'''

def frame_to_planes(frame, channels):
    '''
    Make "event display" from a MicroBooNE frame saved by NumpySaver.
    Frame should be shaped (nchannels, nticks) which is likely
    transposed from how NumpySaver saves.
    '''
    return (frame[channels<2400],
            frame[(channels>=2400) & (channels<4800)],
            frame[channels>=4800])



