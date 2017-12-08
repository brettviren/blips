#!/usr/bin/env python
'''
Visualize stuff
'''
from wirecell.util.wires import apa, graph
import numpy
from collections import defaultdict

import matplotlib.pyplot as plt




def dune_numpy_saver_to_planes(frame, channels):
    '''
    Make "event display" from a DUNE frame and channel array saved by
    NumpySaver.  Frame should be shaped (nchannels, nticks) which is
    likely transposed from how NumpySaver saves.
    '''

    # fixme: move this out to a function
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

def uboone_numpy_saver_to_planes(frame, channels):
    '''
    Make "event display" from a MicroBooNE frame saved by NumpySaver.
    Frame should be shaped (nchannels, nticks) which is likely
    transposed from how NumpySaver saves.
    '''
    return (frame[channels<2400],
            frame[(channels>=2400) & (channels<4800)],
            frame[channels>=4800])

def threeplanes(planes, threshold=25):
    '''
    Plot three planes, circling samples above baseline by threshold.
    '''
    fig,axes = plt.subplots(nrows=len(planes), ncols=3)

    bls = list()
    subs = list()
    for pl in planes:
        bls.append(numpy.asarray([numpy.median(w) for w in pl]))
        subs.append(numpy.asarray([w-b for w,b in zip(pl, bls[-1])]))

    pcol=0
    for ax,pl in zip(axes[:,pcol], planes):
        bl = [numpy.median(w) for w in pl]
        ax.hist(bl, 100)

    pcol += 1
    for ax,pl in zip(axes[:,pcol], planes):
        bl = [numpy.median(w) for w in pl]
        sub = numpy.asarray([w-b for w,b in zip(pl, bl)])
        ax.hist([max(w) for w in sub], 100, log=True)


    pcol += 1
    for ax,pl,sub in zip(axes[:,pcol], planes, subs):
        img = ax.imshow(pl, aspect='auto')
        fig.colorbar(img, ax=ax)

        # highlight high blips
        nchan, nticks = pl.shape
        xv,yv = numpy.meshgrid(numpy.linspace(0,nticks,nticks), numpy.linspace(0,nchan,nchan))

        xblips = xv[sub>threshold]-0.5
        yblips = yv[sub>threshold]-0.5

        ax.plot(xblips, yblips, 'o', ms=14, markerfacecolor="None",
                markeredgecolor='green', markeredgewidth=5)
    return fig
    
def adc_hists(plw, mask_size=(5,40)):
    '''
    Make some hists of ADC
    '''
    from scipy.signal import convolve2d

    blw = [numpy.median(w) for w in plw]
    subw = numpy.asarray([w-b for w,b in zip(plw,blw)])
    mask=numpy.zeros(mask_size)+1.0
    conw = convolve2d(subw, mask)

    fig,axes = plt.subplots(nrows=2, ncols=1)
    ax0,ax1 = axes

    ax0.hist(subw.reshape((subw.size,)), 100, log=True)
    ax0.set_xlabel('baseline subtracted ADC')
    ax0.set_title('Direct ADC (noise+Ar39)')

    ax1.hist(conw.reshape((conw.size,)), 100, log=True)
    ax1.set_xlabel('baseline subtracted, convolved ADC')
    ax1.set_title('%s-Convolved ADC (noise+Ar39)' % str(mask_size))
    return fig

