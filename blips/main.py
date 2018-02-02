#!/usr/bin/env python
'''
Main CLI for blips
'''
import click
import numpy
import matplotlib.pyplot as plt 
from matplotlib.backends.backend_pdf import PdfPages

@click.group()
@click.pass_context
def cli(ctx):
    pass

@cli.command("plot-frames")
@click.option("-o","--output", default="sim-plots.pdf",
              help="Output PDF file.")
@click.argument("npzfile")
@click.pass_context
def plot_frames(ctx, output, npzfile):
    '''
    Plot some basic things from the wire-cell simulation output.
    '''
    from blips import sim
    with PdfPages(output) as pdf:
        for frame in sim.frames(npzfile):

            for plotter in [sim.plot_raw_frame,
                            sim.plot_channels,
                            sim.plot_planes]:
                fig = plotter(frame)
                pdf.savefig(fig)
                plt.close()


@cli.command("plot-primitives")
@click.option("-o","--output", default="sim-plots.pdf",
              help="Output PDF file.")
@click.argument("npzfile")
@click.pass_context
def plot_primitives(ctx, output, npzfile):
    '''
    Plot some things from the output of test_nparray
    '''
    from blips import sim
    arrs = numpy.load(npzfile)

    frame = sim.Frame(arrs['fullframe'], arrs['channels'], None, 0, "")
    with PdfPages(output) as pdf:
        for plotter in [sim.plot_raw_frame,
                        sim.plot_channels,
                        sim.plot_planes]:
            fig = plotter(frame)
            pdf.savefig(fig)
            plt.close()

        def plot_array(arr, tit="", xlab="", ylab=""):
            fig, ax = plt.subplots(nrows=1,ncols=1)
            ax.set_title(tit)
            ax.set_xlabel(xlab)
            ax.set_ylabel(ylab)
            im = ax.imshow(arr, aspect='auto')
            fig.colorbar(im, ax=[ax])
            pdf.savefig(fig)
            plt.close()

        plot_array(arrs['colframe'], "Collection Frame", "tick", "channel index array")

        fig, axes = plt.subplots(nrows=2,ncols=1)
        minadc = 350
        maxadc = 450
        for ind,(ax, name) in enumerate(zip(axes, ['hist', 'cumu'])):
            arr = arrs[name]
            if ind == 0:
                ax.set_title("ADC values -- %s"%name)
            ax.set_xlabel("channel")
            ax.set_ylabel("ADC - %d" % minadc)
            im = ax.imshow(arr[minadc:maxadc,:], aspect='auto')
            fig.colorbar(im, ax=[ax])
        pdf.savefig(fig)
        plt.close()
            
        plot_array(arrs['blipmask'], "Trigger Primitives", "tick", "channel index array")
    

@cli.command("sel-plots")
@click.option("-d","--detector", type=click.Choice(["dune","uboone"]),
              help="Set detector name.")
@click.option("-n","--number", default=0,
              help="The ``event'' number to use.")
@click.option("-t","--tag", default="",
              help="The frame tag to use.")
@click.option("-s","--shape", nargs=2, type=int, default=(3,40),
              help="Set array shape for blip region.")
@click.option("-o","--output", default="plots.pdf",
              help="Output graphics file.")
@click.argument("npzfile")
@click.pass_context
def sel_plots(ctx, detector, number, tag, shape, output, npzfile):
    '''
    Plot some things related to blip selection.
    '''
    import blips
    detmod = getattr(blips, detector)

    from blips import wct, sel
    click.echo("loading")
    fr,ch = wct.load_numpy_saver(npzfile, number, tag)
    click.echo("framing")
    fru,frv,frw = detmod.frame_to_planes(fr, ch)
    click.echo("plotting")
    sel.plots(frw, shape, output)

def main():
    cli(obj=dict())
