import numpy


def coalesce(frame, combine=(3,3), step=(2,2), op = numpy.sum):
    '''
    Return a new frame built by rastering over the input frame,
    summing over blocks, returning the sum as one element of the new
    frame.

    The `combine` tuple gives the shape of a rectangle over which the
    input frame is summed to produce one entry in the output frame.

    The `step` tuple gives how far to step in either direction for the
    next combination.
    '''


    ret = numpy.zeros((frame.shape[0]/step[0], frame.shape[1]/step[1]))
    print ret.shape

    for orow, irow in enumerate(range(0, frame.shape[0], step[0])):
        if orow == ret.shape[0]:
            return ret
        for ocol, icol in enumerate(range(0, frame.shape[1], step[1])):
            if ocol == ret.shape[1]:
                break
            rend = min(irow+combine[0], frame.shape[0]-1)
            cend = min(icol+combine[1], frame.shape[1]-1)
            pixel = op(frame[irow:rend, icol:cend])
            ret[orow,ocol] = pixel
    return ret

def convolve(frame, mask):
    '''
    Run mask over frame in a 2D convolution, returning the result.

    See avg_blips() for possible mask.  A step is another likely function.
    '''
    from scipy.signal import convolve2d
    return convolve2d(frame, mask, 'same')

def baseline_subtract(frame):
    '''
    Return a new frame were each channel is has its baseline
    subtracted.
    '''
    # gotta transpose around to get the right shapes to trigger broadcasting.
    return (frame.T - numpy.median(frame, axis=1)).T


def find_blips(frame, threshold, shape=(3,10)):
    '''
    Return blips above threshold and of given shape.

    Frame is probably best first baseline_subtract()'ed.
    '''
    nchans,nticks = frame.shape
    chans, ticks = numpy.meshgrid(numpy.linspace(0, nchans, nchans, endpoint=False),
                                  numpy.linspace(0, nticks, nticks, endpoint=False),
                                  indexing='ij')
    want = frame.flat>threshold
    fvals = frame.flat[want]
    fchans = chans.flat[want]
    fticks = ticks.flat[want]
    qct = numpy.vstack((fvals, fchans, fticks)).T
    ordered_indices = numpy.argsort(qct[:,0]).tolist()

    ret = list()
    while ordered_indices:
        ind = ordered_indices.pop()
        center = (int(qct[ind][1]), int(qct[ind][2]))
        chan_range = (center[0] - shape[0]//2,
                      center[0] - shape[0]//2 + shape[0])
        tick_range = (center[1] - shape[1]//2,
                      center[1] - shape[1]//2 + shape[1])
                      
        #print ind, center, chan_range, tick_range

        # Only save blips that do not hit the edge
        if chan_range[0] >= 0 and chan_range[1] < frame.shape[0] and \
           tick_range[0] >= 0 and tick_range[1] < frame.shape[1]:
            blip = frame[chan_range[0]:chan_range[1], tick_range[0]:tick_range[1]]
            ret.append(blip)

        # remove overlaps for next time
        for_next = list()
        for ind in ordered_indices:
            chan,tick = (int(qct[ind][1]), int(qct[ind][2]))
            if chan >= chan_range[0] and chan < chan_range[1]:
                continue
            if tick >= tick_range[0] and tick < tick_range[1]:
                continue
            for_next.append(ind)

        #print len(ordered_indices),'-->',len(for_next)
        ordered_indices = for_next

    return ret

def avg_blips(blips):
    '''
    Average a list of 2D blips, returning one with unit peak.
    '''
    ret = numpy.zeros_like(blips[0])
    peak = 0;
    for blip in blips:
        peak += numpy.max(blip)
        ret += blip
    return ret / peak

def border_sum(blip, border=1):
    '''
    Return the sum of samples around border of blip.
    '''
    return numpy.sum(blip) - numpy.sum(blip[border:-border, border:-border])
    # tot = 0.0
    # tot += numpy.sum(blip[:,:border]) + numpy.sum(blip[:,-border:])
    # tot += numpy.sum(blip[:border,:]) + numpy.sum(blip[-border:,:])
    # tot -= numpy.sum(blip[ :border, :border]) + numpy.sum(blip[ :border,-border:])
    # tot -= numpy.sum(blip[-border:,-border:]) + numpy.sum(blip[-border:,:border])
    # return tot
