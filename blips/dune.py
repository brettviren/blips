#!/usr/bin/env python
import numpy
from wirecell.util.wires import apa, graph

def frame_to_planes(frame, channels):
    '''
    Make "event display" from a DUNE frame and channel array saved by
    NumpySaver.  Frame should be shaped (nchannels, nticks) which is
    likely transposed from how NumpySaver saves.
    '''

    # This needs to assume a lot of details to untagle the channels.
    det_params = apa.Description()
    G,P = apa.graph(det_params)
    flat = graph.flatten_to_conductor(G)
    by_chan = {one['channel']:one for one in flat}


    print "input frame shape:", frame.shape
    nticks = frame.shape[1]
    arrs = [
        numpy.zeros((400*2, nticks), dtype='f'), 
        numpy.zeros((400*2, nticks), dtype='f'), 
        numpy.zeros((480, nticks), dtype='f'), # warning, maybe simulation populates both collection planes
    ]
    all_chans = [list(), list(), list()]
    for chn, wf in zip(channels, frame):
        chdat = by_chan[chn]
        arrs[chdat['plane']][chdat['wanglobal']] = wf
        all_chans[chdat['plane']].append(chdat['wanglobal'])




    for letter, arr, chlst in zip("uvw",arrs,all_chans):
        chlst.sort()
        print "output %s frame shape: %s, nch=%d, ch:[%d,%d]" % (letter, arr.shape, len(chlst), chlst[0], chlst[-1])
    return arrs
