#!/usr/bin/env python

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


    nticks = frame.shape[1]
    arrs = [
        numpy.zeros((400*2, nticks), dtype='f'), 
        numpy.zeros((400*2, nticks), dtype='f'), 
        numpy.zeros((480*2, nticks), dtype='f'), 
    ]
    for chn, wf in zip(channels, frame):
        chdat = by_chan[chn]
        arrs[chdat['plane']][chdat['wanglobal']] = wf

    return arrs
