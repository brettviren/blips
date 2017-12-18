#!/usr/bin/env python
'''
Selection related.

from blips import wct, uboone, sel
fr,ch = wct.load_numpy_saver("uboone-wctsim-fullrate-adc-noise.npz")
fru,frv,frw = uboone.frame_to_planes(fr,ch)
sel.plots(fru)

'''

import frame
import numpy
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

def plots(frw, blip_shape = (3,40), pdffile="blips_sel_plots.pdf"):
    
    with PdfPages(pdffile) as pdf:

        bl = numpy.median(frw, axis=1).T

        plt.title("Median Baselines")
        plt.hist(bl,20, log=True)
        plt.xlabel('ADC')
        pdf.savefig()
        plt.close()

        plt.title("Median Baseline vs Channel")
        plt.plot(bl,'o')
        plt.xlabel('channel')
        plt.ylabel('Baseline [ADC]')
        pdf.savefig()
        plt.close()


        sub = frame.baseline_subtract(frw)
        # plot ADC hist
        plt.title("Baseline subtracted (all samples)")
        plt.hist(numpy.asarray(sub.flat), 100, log=True)
        plt.xlabel('(sample - baseline) [ADC]')
        pdf.savefig()
        plt.close()

        # figure out threshold
        thresholds = [5, 10,15,20,25]
        blips = frame.find_blips(sub, thresholds[0], blip_shape)

        # loop over thresholds:
        plt.title("Blip summed ADC vs peak sample thresholds")
        for threshold in thresholds:
            qtot = list()
            for blip in blips:
                if numpy.max(blip) < threshold:
                    continue
                qtot.append(numpy.sum(blip))
            plt.hist(qtot,20, label="%d ADC"%threshold);
        plt.xlabel('total sample value near blip [ADC]')
        plt.legend(title='Threshold')
        pdf.savefig()
        plt.close()


        
