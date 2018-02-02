#!/usr/bin/env python
'''
Do stuff with wire-cell sim output
'''
import numpy
import matplotlib.pyplot as plt 
from collections import namedtuple

Frame = namedtuple("Frame","frame channels ticks number tag")

def frames(npzfile):
    '''
    A generator that loads results frames from the numpy file.

    It yields Frame tuple (frame, channels, tickinfo, framenum, tag)
    '''
    datf = numpy.load(npzfile)
    
    # invert thing_tag_number:arr to [{tag:{thing:arr,...}, ...}, ...]
    
    for name, arr in datf.items():
        if not name.startswith("frame_"):
            continue
        _,tag,num = name.split("_")
        chanarr = datf["channels_%s_%s"%(tag,num)]
        tickarr = datf["tickinfo_%s_%s"%(tag,num)]
        yield Frame(arr, chanarr, tickarr, int(num), tag)

        
def index_columns(arr, indices):
    '''
    Return a list of arrays created based on the indices.

    Each element of list will be an array composed of columns matched
    by their associated index.  Column order as set by indices is
    preserved.  Returned list is ordered by increasing index number.
    '''
    want = list(set(indices))
    want.sort()
    return [arr[:,indices==i] for i in want]
    

def frame_to_planes(frame):
    # fixme: big assumption right here!!!
    from wirecell.util.wires.apa import channel_unhash, chip_channel_layer

    layers = list()
    for chid in frame.channels:
        iconn, islot, ichip, iaddr = channel_unhash(chid)
        layer = chip_channel_layer[ichip, iaddr]
        layers.append(layer)

    return index_columns(frame.frame, layers)
    

Depos = namedtuple("Depos", "data info number")
def depos(npzfile):
    '''
    A generator that returns deposition data and info records.

    It yields a Depos tuple (data, info, number)
    '''
    for name, arr in datf.items():
        if not name.startswith("depo_data_"):
            continue
        _,_,num = name.split("_")
        infoarr = datf['depo_info_%s'%num]
        yield Depos(arr, infoarr, int(num))

def plot_raw_frame(frame):
    '''
    Plot a frame as returned by sim.frames().
    '''
    fig, ax = plt.subplots(nrows=1,ncols=1)
    ax.set_title("ADC Frame %d %s" % (frame.number, frame.tag))
    ax.set_xlabel("tick")
    ax.set_ylabel("channel array index")
    im = ax.imshow(frame.frame.T, aspect='auto')
    fig.colorbar(im, ax=[ax])
    return fig
    
def plot_channels(frame):
    '''
    Plot the channel identity numbers
    '''
    fig, ax = plt.subplots(nrows=1,ncols=1)
    ax.set_title("Channel Identity Numbers for frame %d %s" % (frame.number, frame.tag))
    ax.set_xlabel("channel array index")
    ax.set_ylabel("channel ident")
    ax.plot(frame.channels)
    return fig
    
def plot_planes(frame):
    planes = frame_to_planes(frame)
    fig, axes = plt.subplots(nrows=len(planes),ncols=1)
    for iplane,(ax,plane) in enumerate(zip(axes, planes)):
        ax.set_title("%s-Plane  ADC Frame %d %s" % ("UVW"[iplane], frame.number, frame.tag))
        ax.set_xlabel("tick")
        ax.set_ylabel("array index")
        im = ax.imshow(plane.T, aspect='auto')
        fig.colorbar(im, ax=[ax])
    return fig
