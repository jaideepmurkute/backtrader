#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from six.moves import xrange, zip

import matplotlib.collections as mcol
import matplotlib.colors as mcolors
import matplotlib.legend as mlegend
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms

from .utils import shade_color


class CandlestickPlotHandler(object):
    legend_opens = [0.50, 0.50, 0.50]
    legend_highs = [1.00, 1.00, 1.00]
    legend_lows = [0.00, 0.00, 0.00]
    legend_closes = [0.80, 0.00, 1.00]

    def __init__(self,
                 ax, opens, highs, lows, closes,
                 colorup='k', colordown='r',
                 edgeup=None, edgedown=None,
                 tickup=None, tickdown=None,
                 width=1, tickwidth=1,
                 edgeadjust=0.05, edgeshading=-10,
                 alpha=1.0,
                 label='_nolegend',
                 **kwargs):

        # Manager up/down bar colors
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha
        # Manage the edge up/down colors for the bars
        if edgeup:
            r, g, b = colorConverter.to_rgb(edgeup)
            self.edgeup = ((r, g, b, alpha),)
        else:
            self.edgeup = shade_color(self.colorup, edgeshading)

        if edgedown:
            r, g, b = colorConverter.to_rgb(edgedown)
            self.edgedown = ((r, g, b, alpha),)
        else:
            self.edgedown = shade_color(self.colordown, edgeshading)

            # Manage the up/down tick colors
        if tickup:
            r, g, b = colorConverter.to_rgb(tickup)
            self.tickup = ((r, g, b, alpha),)
        else:
            self.tickup = self.edgeup

        if tickdown:
            r, g, b = colorConverter.to_rgb(tickdown)
            self.tickdown = ((r, g, b, alpha),)
        else:
            self.tickdown = self.edgedown

        self.barcol, self.tickcol = self.barcollection(
            xrange(len(opens)),
            opens, highs, lows, closes,
            width, tickwidth, edgeadjust,
            label=label,
            **kwargs)

        # add collections to the axis and return them
        ax.add_collection(self.tickcol)
        ax.add_collection(self.barcol)

        # Update the axis
        ax.update_datalim(((0, min(lows)), (len(opens), max(highs))))
        ax.autoscale_view()

        # Add self as legend handler for this object
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_opens)
        height = handlebox.height

        # Generate the x axis coordinates (handlebox based)
        xs = [x0 + width * (i + 0.5) for i in xrange(len(self.legend_opens))]

        barcol, tickcol = self.barcollection(
            xs,
            self.legend_opens, self.legend_highs,
            self.legend_lows, self.legend_closes,
            width=width, tickwidth=2,
            scaling=height, bot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)
        tickcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(tickcol)

        return barcol, tickcol

    def barcollection(self,
                      xs,
                      opens, highs, lows, closes,
                      width, tickwidth=1, edgeadjust=0,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      **kwargs):

        # Prepack different zips of the series values
        oc = lambda: zip(opens, closes)
        xoc = lambda: zip(xs, opens, closes)
        iohlc = lambda: zip(xs, opens, highs, lows, closes)

        colord = {True: self.colorup, False: self.colordown}
        colors = [colord[o < c] for o, c in oc()]

        edgecolord = {True: self.edgeup, False: self.edgedown}
        edgecolors = [edgecolord[o < c] for o, c in oc()]

        tickcolord = {True: self.tickup, False: self.tickdown}
        tickcolors = [edgecolord[o < c] for o, c in oc()]

        delta = width / 2 - edgeadjust

        def barbox(i, open, close):
            # delta seen as closure
            left, right = i - delta, i + delta
            open = open * scaling + bot
            close = close * scaling + bot
            return (left, open), (left, close), (right, close), (right, open)

        barareas = [barbox(i, o, c) for i, o, c in xoc()]

        def tup(i, open, high, close):
            high = high * scaling + bot
            open = open * scaling + bot
            close = close * scaling + bot

            return (i, high), (i, max(open, close))

        tickrangesup = [tup(i, o, h, c) for i, o, h, l, c in iohlc()]

        def tdown(i, open, low, close):
            low = low * scaling + bot
            open = open * scaling + bot
            close = close * scaling + bot

            return (i, low), (i, min(open, close))

        tickrangesdown = [tdown(i, o, l, c) for i, o, h, l, c in iohlc()]

        # Extra variables for the collections
        useaa = 0,  # use tuple here
        lw = 0.5,   # and here
        tlw = tickwidth,

        # Bar collection for the candles
        barcol = mcol.PolyCollection(
            barareas,
            facecolors=colors,
            edgecolors=edgecolors,
            antialiaseds=useaa,
            linewidths=lw,
            label=label,
            **kwargs)

        # LineCollections have a higher zorder than PolyCollections
        # to ensure the edges of the bars are not overwriten by the Lines
        # we need to put the bars slightly over the LineCollections
        kwargs['zorder'] = barcol.get_zorder() * 0.9999

        # Up/down ticks from the body
        tickcol = mcol.LineCollection(
            tickrangesup + tickrangesdown,
            colors=tickcolors,
            linewidths=tlw,
            antialiaseds=useaa,
            **kwargs)

        # return barcol, tickcol
        return barcol, tickcol


def plot_candlestick(ax,
                     opens, highs, lows, closes,
                     colorup='k', colordown='r',
                     edgeup=None, edgedown=None,
                     tickup=None, tickdown=None,
                     width=1, tickwidth=1.25,
                     edgeadjust=0.05, edgeshading=-10,
                     alpha=1.0,
                     label='_nolegend',
                     **kwargs):

    chandler = CandlestickPlotHandler(
        ax, opens, highs, lows, closes,
        colorup, colordown,
        edgeup, edgedown,
        tickup, tickdown,
        width, tickwidth,
        edgeadjust, edgeshading,
        alpha,
        label,
        **kwargs)

    # Return the collections. the barcol goes first because
    # is the larger,  has the dominant zorder and defines the legend
    return chandler.barcol, chandler.tickcol


class VolumePlotHandler(object):
    legend_vols = [0.5, 1.0, 0.75]
    legend_opens = [0, 1, 0]
    legend_closes = [1, 0, 1]

    def __init__(self,
                 ax, opens, closes, volumes,
                 colorup='k', colordown='r',
                 edgeup=None, edgedown=None,
                 edgeshading=-5, edgeadjust=0.05,
                 overlay=False, overscaling=0.25, overpushup=0.0,
                 width=1, alpha=1.0,
                 **kwargs):

        # Manage the up/down colors
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha

        # Prepare the edge colors
        if not edgeup:
            self.edgeup = shade_color(self.colorup, edgeshading)
        else:
            r, g, b = mcolors.colorConverter.to_rgb(edgeup)
            self.edgeup = r, g, b, alpha

        if not edgedown:
            self.edgedown = shade_color(self.colordown, edgeshading)
        else:
            r, g, b = mcolors.colorConverter.to_rgb(edgedown)
            self.edgedown = r, g, b, alpha

        # Prepare overlay scaling/pushup or manage own axis
        if overlay:
            axbot, axtop = ax.get_ylim()
            if overpushup:
                # push up the existing data by changing the bottom limit
                axbot *= (1.0 - overpushup)
                ax.set_ylim(axbot, axtop)

            vrange = axtop - axbot
            vscaling = overscaling * vrange / max(volumes)
            vbot = axbot
        else:
            vscaling = 1.0
            vbot = 0
            corners = (0, 0), (len(volumes), max(volumes))
            ax.update_datalim(corners)
            ax.autoscale_view()

        self.barcol = self.barcollection(
            xrange(len(volumes)), opens, closes, volumes,
            width=width, edgeadjust=edgeadjust,
            vscaling=vscaling, vbot=vbot,
            **kwargs)

        # add to axes
        ax.add_collection(self.barcol)

        # Add a legend handler for this object
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_vols)
        height = handlebox.height

        # Generate the x axis coordinates (handlebox based)
        xs = [x0 + width * (i + 0.5) for i in xrange(len(self.legend_vols))]

        barcol = self.barcollection(
            xs, self.legend_opens, self.legend_closes, self.legend_vols,
            width=width, vscaling=height, vbot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)

        return barcol

    def barcollection(self,
                      x, opens, closes, vols,
                      width, edgeadjust=0,
                      vscaling=1.0, vbot=0.0,
                      **kwargs):

        # Prepare the data
        openclose = lambda: zip(opens, closes)

        # Calculate bars colors
        colord = {True: self.colorup, False: self.colordown}
        colors = [colord[open < close] for open, close in openclose()]
        edgecolord = {True: self.edgeup, False: self.edgedown}
        edgecolors = [edgecolord[open < close] for open, close in openclose()]

        # bar width to the sides
        delta = width / 2 - edgeadjust

        # small auxiliary func to return the bar coordinates
        def volbar(i, v):
            left, right = i - delta, i + delta
            v = vbot + v * vscaling
            return (left, vbot), (left, v), (right, v), (right, vbot)

        barareas = [volbar(i, v) for i, v in zip(x, vols)]
        barcol = mcol.PolyCollection(
            barareas,
            facecolors=colors,
            edgecolors=edgecolors,
            antialiaseds=(0,),
            linewidths=(0.5,),
            **kwargs)

        return barcol


def plot_volume(ax, opens, closes, volumes,
                colorup='k', colordown='r',
                edgeup=None, edgedown=None,
                edgeshading=-5, edgeadjust=0.05,
                overlay=False, overscaling=0.25, overpushup=0.0,
                width=1, alpha=1.0,
                **kwargs):

    vhandler = VolumePlotHandler(
        ax, opens, closes, volumes,
        colorup, colordown,
        edgeup, edgedown,
        edgeshading, edgeadjust,
        overlay, overscaling, overpushup,
        width, alpha,
        **kwargs)

    return vhandler.barcol,


class OHLCPlotHandler(object):
    legend_opens = [0.50, 0.50, 0.50]
    legend_highs = [1.00, 1.00, 1.00]
    legend_lows = [0.00, 0.00, 0.00]
    legend_closes = [0.80, 0.20, 0.90]

    def __init__(self,
                 ax, opens, highs, lows, closes,
                 colorup='k', colordown='r',
                 width=1, tickwidth=0.5,
                 alpha=1.0,
                 label='_nolegend',
                 **kwargs):

        # Manager up/down bar colors
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha

        bcol, ocol, ccol = self.barcollection(
            xrange(len(opens)),
            opens, highs, lows, closes,
            width=width, tickwidth=tickwidth,
            label=label,
            **kwargs)

        self.barcol = bcol
        self.opencol = ocol
        self.closecol = ccol

        # add collections to the axis and return them
        ax.add_collection(self.barcol)
        ax.add_collection(self.opencol)
        ax.add_collection(self.closecol)

        # Update the axis
        ax.update_datalim(((0, min(lows)), (len(opens), max(highs))))
        ax.autoscale_view()

        # Add self as legend handler for this object
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_opens)
        height = handlebox.height

        # Generate the x axis coordinates (handlebox based)
        xs = [x0 + width * (i + 0.5) for i in xrange(len(self.legend_opens))]

        barcol, opencol, closecol = self.barcollection(
            xs,
            self.legend_opens, self.legend_highs,
            self.legend_lows, self.legend_closes,
            width=1.5, tickwidth=2,
            scaling=height, bot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)
        # opencol.set_transform(handlebox.get_transform())
        handlebox.add_artist(opencol)
        # closecol.set_transform(handlebox.get_transform())
        handlebox.add_artist(closecol)

        return barcol, opencol, closecol

    def barcollection(self,
                      xs,
                      opens, highs, lows, closes,
                      width, tickwidth,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      **kwargs):

        # Prepack different zips of the series values
        ihighlow = lambda: zip(xs, highs, lows)
        iopen = lambda: zip(xs, opens)
        iclose = lambda: zip(xs, closes)
        openclose = lambda: zip(opens, closes)

        colord = {True: self.colorup, False: self.colordown}
        colors = [colord[open < close] for open, close in openclose()]

        # Extra variables for the collections
        useaa = 0,
        lw = width,
        tlw = tickwidth,

        # Calculate the barranges
        def barrange(i, high, low):
            return (i, low * scaling + bot), (i, high * scaling + bot)

        barranges = [barrange(i, high, low) for i, high, low in ihighlow()]

        barcol = mcol.LineCollection(
            barranges,
            colors=colors,
            linewidths=lw,
            antialiaseds=useaa,
            label=label,
            **kwargs)

        def tickopen(i, open):
            open = open * scaling + bot
            return (i - tickwidth, open), (i, open)

        openticks = [tickopen(i, open) for i, open in iopen()]
        opencol = mcol.LineCollection(
            openticks,
            colors=colors,
            antialiaseds=useaa,
            linewidths=lw,
            label='_nolegend',
            **kwargs)

        def tickclose(i, close):
            close = close * scaling + bot
            return (i, close), (i + tickwidth, close)

        closeticks = [tickclose(i, close) for i, close in iclose()]
        closecol = mcol.LineCollection(
            closeticks,
            colors=colors,
            antialiaseds=useaa,
            linewidths=lw,
            label='_nolegend',
            **kwargs)

        # return barcol, tickcol
        return barcol, opencol, closecol


def plot_ohlc(ax, opens, highs, lows, closes,
              colorup='k', colordown='r',
              width=1.5, tickwidth=0.5,
              alpha=1.0,
              label='_nolegend',
              **kwargs):

    handler = OHLCPlotHandler(
        ax, opens, highs, lows, closes,
        colorup, colordown,
        width, tickwidth,
        alpha,
        label,
        **kwargs)

    return handler.barcol, handler.opencol, handler.closecol


class LineOnClosePlotHandler(object):
    legend_closes = [0.00, 0.66, 0.33, 1.00]

    def __init__(self,
                 ax, x, closes, color='k',
                 width=1, alpha=1.0,
                 label='_nolegend',
                 **kwargs):

        self.color = color
        self.alpha = alpha

        self.loc, = self.barcollection(
            x, closes,
            width=width,
            label=label,
            **kwargs)

        # add collections to the axis and return them
        ax.add_line(self.loc)

        # Update the axis
        ax.update_datalim(((0, min(closes)), (len(closes), max(closes))))
        ax.autoscale_view()

        # Add self as legend handler for this object
        mlegend.Legend.update_default_handler_map({self.loc: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_closes)
        height = handlebox.height

        # Generate the x axis coordinates (handlebox based)
        xs = [x0 + width * (i + 0.5) for i in xrange(len(self.legend_closes))]

        linecol, = self.barcollection(
            xs, self.legend_closes,
            width=1.5,
            scaling=height, bot=y0)

        linecol.set_transform(handlebox.get_transform())
        handlebox.add_artist(linecol)

        return linecol,

    def barcollection(self,
                      xs, closes,
                      width,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      **kwargs):

        # Prepack different zips of the series values
        scaled = [close * scaling + bot for close in closes]

        loc = mlines.Line2D(
            xs, scaled,
            color=self.color,
            lw=width,
            label=label,
            alpha=self.alpha,
            **kwargs)

        # return barcol, tickcol
        return loc,


def plot_lineonclose(ax, x, closes,
                     color='k',
                     width=1.5,
                     alpha=1.0,
                     label='_nolegend',
                     **kwargs):

    handler = LineOnClosePlotHandler(
        ax, x, closes,
        color=color, width=width,
        alpha=alpha, label=label,
        **kwargs)

    return handler.loc,