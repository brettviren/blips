#!/usr/bin/env python
'''
Interface to WCT
'''
import numpy
def load_numpy_saver(filename, count=0, tag=""):
    '''
    Load and return full WCT frame and its channel array from the
    given file matching the count (aka, "event number") and the tag,
    if any.

    See {dune,uboone}.frame_to_planes() to split up the result by plane
    '''
    # these match patterns in NumpySaver WCT component used to make the file
    frame_key = 'frame_%s_%d' % (tag, count)
    chan_key = 'channels_%s_%d' % (tag, count)
    f = numpy.load(filename)
    fr = f[frame_key].T
    ch = f[chan_key]
    return fr,ch


