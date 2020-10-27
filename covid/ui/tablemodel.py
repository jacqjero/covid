# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 11:33:54 2019

@author: jerome.jacq
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant
from PyQt5.QtGui import QColor, QBrush

class ModeleTab(QAbstractTableModel):
    """ Modèle de Table Profils
    """

    header = ['', 'Admin', 'Réa', 'Nb Morts', 'Tx Incid']

    def __init__(self, parent, lDep,  *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.lDep = lDep

    def rowCount(self, parent):
        return len(self.lDep)

    def columnCount(self, parent):
        return 5

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return QAbstractTableModel.headerData(self, col, orientation, role)

    def data(self, index, role):
        row = index.row()
        column = index.column()
        dep = self.lDep[row]
        value = QVariant()
        if not index.isValid():
            return value
        if column == 0:
            if role == Qt.CheckStateRole:
                if dep.checked:
                    value = Qt.Checked
                else:
                    value = Qt.Unchecked
        elif column == 1:
            if role == Qt.DisplayRole:
                value = dep.nom
        elif column == 2:
            if role == Qt.DisplayRole:
                value = dep.nbrea
        elif column == 3:
            if role == Qt.DisplayRole:
                value = dep.nbdeaths
        elif column == 4:
            if role == Qt.DisplayRole:
                value = dep.txincid7j
        if role == Qt.BackgroundRole and dep.checked:
            value = QBrush(QColor(0, 50, 0, 100))

        return value

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Checked:
                self.lDep[index.row()].checked = True
            else:
                self.lDep[index.row()].checked = False
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            return True

    def flags(self, index):
        if not index.isValid():
            return None
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        if order == Qt.DescendingOrder:
            if Ncol == 2:
                self.lDep.sort(key=lambda x: x.nbrea, reverse=True)
            elif Ncol == 3:
                self.lDep.sort(key=lambda x: x.nbdeaths, reverse=True)
            elif Ncol == 4:
                self.lDep.sort(key=lambda x: x.txincid7j, reverse=True)
            elif Ncol == 1:
                self.lDep.sort(key=lambda x: x.nom, reverse=True)
        elif order == Qt.AscendingOrder:
            if Ncol == 2:
                self.lDep.sort(key=lambda x: x.nbrea)
            elif Ncol == 3:
                self.lDep.sort(key=lambda x: x.nbdeaths)
            elif Ncol == 4:
                self.lDep.sort(key=lambda x: x.txincid7j)
            elif Ncol == 1:
                self.lDep.sort(key=lambda x: x.nom)
        self.layoutChanged.emit()
