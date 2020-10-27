# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 11:38:07 2019

@author: jerome.jacq
"""

import numpy as np

from PyQt5.QtWidgets import QWidget, QGridLayout, QSpacerItem, QSizePolicy
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path


class MplCanvas(FigureCanvas):
    """ Creation de la figure

    """

    def __init__(self):

        fig = Figure()
        self.axes = fig.add_subplot(111)
        FigureCanvas.__init__(self, fig)
        FigureCanvas.updateGeometry(self)


class MplWidget(QWidget):
    """ Creation du widget Mpl
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
#        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.navi_toolbar = CustomToolbar(self.canvas, self)
        self.navi_toolbar.update()
        self.vbl = QGridLayout()
        self.vbl.addWidget(self.navi_toolbar, 0, 1)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.vbl.addItem(spacer, 0, 0)
        self.vbl.addWidget(self.canvas, 1, 0, 1, 2)
        self.setLayout(self.vbl)


class CustomToolbar(NavigationToolbar):
    """ Personnalisation de la toolbar
    """

    def __init__(self, canvas_, parent_):
        self.toolitems = (
            ('Home', 'Initialiser', 'home', 'home'),
            ('Pan', 'Déplacer/Zoomer', 'move', 'pan'),
            ('Zoom', 'Zoom Rect', 'zoom_to_rect', 'zoom'),
            )
        NavigationToolbar.__init__(self, canvas_, parent_)


class SelectFromCollection(object):
    """Select indices from a matplotlib collection using `PolygonSelector`.

    Selected indices are saved in the `ind` attribute. This tool fades out the
    points that are not part of the selection (i.e., reduces their alpha
    values). If your collection has alpha < 1, this tool will permanently
    alter the alpha values.

    Note that this tool selects collection objects based on their *origins*
    (i.e., `offsets`).

    Parameters
    ----------
    ax : :class:`~matplotlib.axes.Axes`
        Axes to interact with.

    collection : :class:`matplotlib.collections.Collection` subclass
        Collection you want to select from.

    alpha_other : 0 <= float <= 1
        To highlight a selection, this tool sets all selected points to an
        alpha value of 1 and non-selected points to `alpha_other`.
    """

    def __init__(self, ax, collection, alpha_other=0.3):
        self.canvas = ax.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other

        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))

        self.poly = PolygonSelector(ax, self.onselect)
        self.ind = []

    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero(path.contains_points(self.xys))[0]
        self.fc[:, -1] = self.alpha_other
        self.fc[self.ind, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def disconnect(self):
        self.poly.disconnect_events()
        self.fc[:, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()


class SnaptoCursor:
    """
    Like Cursor but the crosshair snaps to the nearest x, y point.
    For simplicity, this assumes that *x* is sorted.
    """

    def __init__(self, ax, x, y):
        self.ax = ax
        self.lx = ax.axhline(color='k')  # the horiz line
        self.x = x
        # text location in axes coords
        self.txt = ax.text(0.7, 0.9, '', transform=ax.transAxes)

    def mouse_move(self, event):
        if not event.inaxes:
            return

        x = event.xdata
        indx = min(np.searchsorted(self.x, x), len(self.x) - 1)
        x = self.x[indx]
        # update the line positions
        self.lx.set_xdata(x)

        self.txt.set_text('x=%1.2f' % (x))
        self.ax.figure.canvas.draw()