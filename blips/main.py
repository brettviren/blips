#!/usr/bin/env python
'''
Main CLI for blips
'''
import click

@click.group()
@click.pass_context
def cli(ctx):
    pass

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
