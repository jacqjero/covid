# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 16:17:05 2019

@author: jerome.jacq
"""

import os
import json
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as tkr
import numpy as np
import pandas as pd

from itertools import chain
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Rectangle

from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QApplication, qApp, QHeaderView
from PyQt5.QtWidgets import QAction, QSizePolicy, QAbstractItemView, QRadioButton
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPalette
from PyQt5.QtCore import Qt

from santepublique.tablemodel import ModeleTab
from santepublique.localisation import Departement, Region, Pays
from santepublique.utilities import (ressource_path, readcsv, extrairedata,
                                     dateformat)


class CovidVisu(QMainWindow):
    def __init__(self, ):
        super(CovidVisu, self).__init__()
        self.pathapp = os.path.dirname(ressource_path(''))
        self.pathicones = ressource_path('icones')
        self.pathappdata = ressource_path('data')
        loadUi(ressource_path('.\\UICovid19.ui'), self)

        # Read the file urls.cfg which provides infos on data
        self.data = self.__lireurl(os.path.join(self.pathappdata,
                                                'urls.cfg'))
        # Read the data which are in the app data dir
        # Création des objets
        self.createobjects()
        # IG
        self.icone = QIcon(QPixmap(os.path.join(self.pathicones, 'hygrometer_64px.png')))
        self.setWindowIcon(self.icone)
        # MENU MAIN WINDOW
        # activation du menu de la fenêtre princiale
        menubar = self.menuBar()
        # Ajout du menu Fichier
        filemenu = menubar.addMenu('Fichier')
        # Définition des différentes actions du menu Fichier
        actionUpdateData = QAction('Update data', self)
        actionUpdateData.setShortcut('Ctrl+U')
        actionSaveData = QAction('Save data', self)
        actionSaveData.setShortcut('Ctrl+S')
        actionExportData = QAction('Export data', self)
        actionExportData.setShortcut('Ctrl+E')
        actionQuitter = QAction('Quitter', self)
        actionQuitter.setShortcut('Ctrl+Q')

        # Ajout des actions au menu Fichier
        filemenu.addAction(actionUpdateData)
        filemenu.addAction(actionSaveData)
        filemenu.addAction(actionQuitter)
        filemenu.addAction(actionExportData)

        # SIGNAUX SLOT du menu
        actionUpdateData.triggered.connect(self.updateData)
        actionExportData.triggered.connect(self.exportData)
        actionSaveData.triggered.connect(self.saveData)
        actionQuitter.triggered.connect(self.quitter)
        # %% DEFINITION ZONE TRACE MPL
        # Canvas Matplotlib
        self.FIG_Visu = plt.figure()
        self.CAN_Visu = FigureCanvas(self.FIG_Visu)
        self.layMpl.addWidget(self.CAN_Visu)
        self.TBN_Visu = NavigationToolbar(self.CAN_Visu, self)
        self.layMpl.addWidget(self.TBN_Visu)
        self.AX_Visu = self.FIG_Visu.subplots()
        sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.CAN_Visu.setSizePolicy(sizepolicy)
        # self.CAN_Visu.mpl_connect('motion_notify_event', self.mouse_move)
        # self.CAN_Visu.mpl_connect('pick_event', self.onpick)
        # self.annot = self.AX_Visu.annotate('toto', xy=(0, 0))
        # self.annot.set_visible(True)
        # Groupbox affichage
        self.cbRegions.setChecked(False)
        self.cbDeps.setChecked(True)
        self.cbRegions.stateChanged.connect(self.displayregs)
        self.cbDeps.stateChanged.connect(self.displaydeps)
        self.ldata = self.ldepartements
        self.gbAge.setEnabled(False)
        # Gestion des RB du GB GraphOpt
        self.rbRea.setChecked(True)
        self.rbRea.toggled.connect(self.updaterbaffichage)
        self.rbDeaths.toggled.connect(self.updaterbaffichage)
        self.rbHosp.toggled.connect(self.updaterbaffichage)
        self.rbTest.toggled.connect(self.updaterbaffichage)
        self.rbIncid.toggled.connect(self.updaterbaffichage)
        # Groupbox Sexe, gestion des rb
        self.rbTot.setChecked(True)
        self.rbH.setChecked(False)
        self.rbF.setChecked(False)
        self.rbTot.toggled.connect(self.updaterb)
        self.rbH.toggled.connect(self.updaterb)
        self.rbF.toggled.connect(self.updaterb)
        # GroupBox Evolution / Nouveaux cas
        self.rbEvol.setChecked(True)
        self.rbEvol.toggled.connect(self.updaterbevol)
        self.rbNew.toggled.connect(self.updaterbevol)
        # Rb Classes d'ages
        self.rbAll.setChecked(True)
        self.rb0.setChecked(False)
        self.rb1.setChecked(False)
        self.rb2.setChecked(False)
        self.rb3.setChecked(False)
        self.rb4.setChecked(False)
        self.rb5.setChecked(False)
        self.rb6.setChecked(False)
        self.rb7.setChecked(False)
        self.rb8.setChecked(False)
        self.rb9.setChecked(False)
        # Callbacks
        self.rbAll.toggled.connect(self.updaterb)
        self.rb0.toggled.connect(self.updaterb)
        self.rb1.toggled.connect(self.updaterb)
        self.rb2.toggled.connect(self.updaterb)
        self.rb3.toggled.connect(self.updaterb)
        self.rb4.toggled.connect(self.updaterb)
        self.rb5.toggled.connect(self.updaterb)
        self.rb6.toggled.connect(self.updaterb)
        self.rb7.toggled.connect(self.updaterb)
        self.rb8.toggled.connect(self.updaterb)
        self.rb9.toggled.connect(self.updaterb)
        # LCD Number
        palette = QPalette()
        palette.setColor(palette.WindowText, QColor('red'))
        palette.setColor(palette.Light, QColor('black'))
        self.lcdHospi.setPalette(palette)
        self.lcdRea.setPalette(palette)
        self.lcdDeaths.setPalette(palette)
        self.lcdTests.setPalette(palette)
        self.lcdTestPos.setPalette(palette)
        self.lcdPos.setPalette(palette)
        self.lcdIncid.setPalette(palette)
        # affichage des lcd
        self.displaylcd()
        # Définition des modeles
        self.modeletable = ModeleTab(self, self.ldata)
        self.tabData.setModel(self.modeletable)
        self.tabData.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabData.setSortingEnabled(True)
        self.tabData.setAlternatingRowColors(True)
        # resize header width
        head = self.tabData.horizontalHeader()
        head.setSectionResizeMode(QHeaderView.ResizeToContents)
        head.setSectionResizeMode(1, QHeaderView.Stretch)
        # Signal Sélection
        self.tabData.selectionModel().selectionChanged.connect(self.afficher)
        self.tabData.model().dataChanged.connect(self.afficher)

    def displaylcd(self):
        """permet de mettre à jour l'affichage des lcd number
        """
        self.lcdHospi.display(self.ldepartements[0].nbhosp)
        self.lcdRea.display(self.ldepartements[0].nbrea)
        self.lcdDeaths.display(self.ldepartements[0].nbdeaths)
        self.lcdTests.display(self.pays.nbtests)
        self.lcdTestPos.display(self.pays.nbtestspos)
        self.lcdPos.display(self.pays.txpositivite)
        self.lcdIncid.display(self.pays.txincidence)

    def createobjects(self, update=False):
        """ réalise l'initialisation et la création des objets
        """
        # Set objects
        self.ldepartements = list()
        self.lregions = list()
        # Création des départements, des régions et du pays
        self.creerdepartements(update=update)
        self.creerregions(update=update)
        self.creerpays(update=update)
        # Valorisation des objets
        self.valoriserreg()
        self.valoriserpays()
        # Ajout du pays dans les listes des données administratives
        self.ldepartements.insert(0, self.pays)
        self.lregions.insert(0, self.pays)

    def creerdepartements(self, update=False):
        """ le département est l'entité administrative la plus petite
        Il n'est pas possible de déterminer les données manquantes des régions
        ou du pays
        Il n'y a pas de valorisation à faire sur les départements
        """
        with open(os.path.join(self.pathappdata, 'departements.csv'), 'r',
                  encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', dialect='excel')
            ip = 0
            for row in reader:
                if ip != 0:
                    self.ldepartements.append(Departement.fromcsv(row))
                ip += 1
        # Attribution des données aux objets
        ldat = [dat for dat in self.data if dat['admin'] == 'dep']
        for dat in ldat:
            readcsv(self.pathappdata, dat, update=update)
            df, dfgrp = extrairedata(dat)
            for dep in self.ldepartements:
                dep.attribuerdata(dat['code'], dfgrp)

    def creerregions(self, update=False):
        """ les régions sont créées à partir des départements
        """
        lpo = [(x.region, x.coderegion) for x in self.ldepartements]
        lreg = np.unique(np.array(lpo), axis=0).tolist()
        for data in lreg:
            reg = Region.fromdata(data)
            reg.getdep(self.ldepartements)
            self.lregions.append(reg)
        # Attribution des données aux objets
        ldat = [dat for dat in self.data if dat['admin'] == 'reg']
        for dat in ldat:
            readcsv(self.pathappdata, dat, update=update)
            df, dfgrp = extrairedata(dat, admin='reg')
            for reg in self.lregions:
                reg.attribuerdata(dat['code'], dfgrp)

    def valoriserreg(self):
        """ valorise les données manquantes à partir des données sur les
        départements
        """
        for reg in self.lregions:
            reg.valoriserdata()

    def creerpays(self, update=False):
        """ permet de définir les différents attributs du pays à partir des
        département et des régions
        """
        self.pays = Pays('France', 'FR', self.ldepartements, self.lregions)
        ldat = [dat for dat in self.data if dat['admin'] == 'fra']
        for dat in ldat:
            readcsv(self.pathappdata, dat, update=update)
            df, dfgrp = extrairedata(dat, admin='fra')
            self.pays.attribuerdata(dat['code'], dfgrp)

    def valoriserpays(self):
        self.pays.valoriserdata()

    def __lireurl(self, file):
        with open(file, 'r', encoding='utf-8') as fp:
            return json.load(fp)

    def displaydeps(self, event):
        bcheck = event == Qt.Checked
        if bcheck:
            self.modeletable.beginResetModel()
            self.cbRegions.setChecked(False)
            self.modeletable.lDep = self.ldepartements
            self.ldata = self.ldepartements
            self.modeletable.endResetModel()
            _, rbchecked = self.getselectedrb(self.gbGraphOpt)
            if rbchecked.objectName() in ['rbTest', 'rbIncid']:
                self.gbAge.setEnabled(True)
                self.rbH.setEnabled(False)
                self.rbF.setEnabled(False)
            else:
                self.gbAge.setEnabled(False)
                self.rbH.setEnabled(True)
                self.rbH.setEnabled(True)
            self.rbTot.setChecked(True)
            self.rbAll.setChecked(True)

    def displayregs(self, event):
        bcheck = event == Qt.Checked
        if bcheck:
            self.modeletable.beginResetModel()
            self.cbDeps.setChecked(False)
            self.modeletable.lDep = self.lregions
            self.ldata = self.lregions
            self.modeletable.endResetModel()
            _, rbchecked = self.getselectedrb(self.gbSexe)
            if rbchecked.text() != 'Total':
                self.gbAge.setEnabled(False)
            else:
                self.gbAge.setEnabled(True)

    def updaterbevol(self):
        """callback associé au RB présents dans le GB Evolution
        """
        ind, rb = self.getselectedrb(self.gbEvol)
        if rb.objectName() == 'rbNew':
            self.rbH.setEnabled(False)
            self.rbF.setEnabled(False)
            self.rbTot.setChecked(True)
            self.gbAge.setEnabled(False)
            self.rbTest.setEnabled(False)
            self.rbIncid.setEnabled(False)
        else:
            self.rbH.setEnabled(True)
            self.rbF.setEnabled(True)
            self.rbTest.setEnabled(True)
            self.rbIncid.setEnabled(True)
            if self.rbTot.isChecked():
                if self.cbRegions.isChecked():
                    self.gbAge.setEnabled(True)
                else:
                    self.gbAge.setEnabled(False)
            else:
                self.gbAge.setEnabled(False)
        self.afficher()

    def updaterbaffichage(self):
        """callback associé au RB présents dans le GB Affichage
        """
        ind, rb = self.getselectedrb(self.gbGraphOpt)
        if rb.objectName() in ['rbTest', 'rbIncid']:
            self.gbAge.setEnabled(True)
            self.rbNew.setEnabled(False)
            if self.cbDeps.isChecked():
                self.rbTot.setChecked(True)
                self.rbH.setEnabled(False)
                self.rbF.setEnabled(False)
            else:
                self.rbH.setEnabled(True)
                self.rbF.setEnabled(True)
        else:
            if self.cbDeps.isChecked():
                self.rbTot.setChecked(True)
                self.gbAge.setEnabled(False)
            else:
                self.gbAge.setEnabled(True)
            self.rbNew.setEnabled(True)
        self.afficher()

    def updaterb(self):
        """ callback associé aux RB présents dans le GB Evolution
        """
        cb = self.getselectedcb()
        _, rb = self.getselectedrb(self.gbGraphOpt)
        if cb.objectName() == 'cbDeps':
            if rb.objectName() in ['rbTest', 'rbIncid']:
                self.gbAge.setEnabled(True)
                self.rbH.setEnabled(False)
                self.rbF.setEnabled(False)
            else:
                self.gbAge.setEnabled(False)
        else:
            if rb.objectName() in ['rbTest', 'rbIncid']:
                self.gbAge.setEnabled(True)
            else:
                self.gbAge.setEnabled(False)
        self.afficher()

    def getselectedrb(self, gb):
        lrb = gb.findChildren(QRadioButton)
        ind, rbchecked = next((x, y) for x, y in enumerate(lrb) if y.isChecked())
        return ind, rbchecked

    def getselectedcb(self):
        if self.cbRegions.isChecked():
            return self.cbRegions
        else:
            return self.cbDeps

    def afficher(self):
        # affichage
        index = self.tabData.selectionModel().currentIndex().row()
        dat = self.ldata[index]
        indG, rbGraphOpt = self.getselectedrb(self.gbGraphOpt)
        indS, rbSexe = self.getselectedrb(self.gbSexe)
        indA, rbAge = self.getselectedrb(self.gbAge)
        indEvol, rbEvol = self.getselectedrb(self.gbEvol)
        cbchecked = self.getselectedcb()
        ld = [x for x in self.ldata if x.checked and x != dat]
        ld.append(dat)
        self.AX_Visu.cla()
        for p in ld:
            p.visualiser(self.AX_Visu, rbGraphOpt,
                         rbEvol, rbSexe, tagage=indA,
                         admin=cbchecked)
        self.AX_Visu.set_xlabel('Dates')
        self.AX_Visu.tick_params(axis='x', rotation=70)
        self.AX_Visu.xaxis.set_major_formatter(tkr.FuncFormatter(dateformat))
        self.AX_Visu.xaxis.set_major_locator(mdates.DayLocator(interval=4))
        self.AX_Visu.xaxis.set_minor_locator(mdates.DayLocator())
        self.AX_Visu.yaxis.set_major_locator(tkr.MaxNLocator(integer=True))
        self.CAN_Visu.draw()

    def update_annot(self, bar):
        x = bar.get_x()
        y = bar.get_y() + bar.get_height()
        self.annot.set_text('tt')
        self.annot.set_x(x)
        self.annot.set_y(y)

    def mouse_move(self, event):
        if not event.inaxes:
            return
        for rect in list(chain.from_iterable(self.artists)):
            if isinstance(rect, Rectangle):
                if rect.contains(event)[0]:
                    self.update_annot(rect)
                    self.annot.set_visible(True)
                    print(self.annot.get_x(), self.annot.get_y())
                else:
                    self.annot.set_visible(False)
                    pass
                self.AX_Visu.figure.canvas.draw_idle()
            else:
                pass

    def onpick(self, event):
        if isinstance(event.artist, Rectangle):
            print(event.artist.get_height(), event.artist.get_y())
        else:
            print('tata')
            pass
        # self.AX_Visu.figure.canvas.draw_idle()

    def updateData(self):
        # Réinitialisation des objets
        self.createobjects(update=True)
        # IG
        self.modeletable.beginResetModel()
        self.modeletable.lDep = self.ldepartements
        self.modeletable.endResetModel()
        self.cbRegions.setChecked(False)
        self.cbDeps.setChecked(True)
        # affichage
        self.displaylcd()

    def exportData(self):
        """ permet d'exporter le csv contenant toutes les données administatives
        des départements
        """
        cols = ['Numéro', 'Nom', 'Région', 'Chef lieu', 'Superficie (km²)',
                'Population', 'Densité (hab/km²)', 'Code région']
        ind = [i for i in range(len(self.ldepartements) - 1)]
        dpts = pd.DataFrame(index=ind, columns=cols)
        ip = 0
        for dpt in self.ldepartements[1:]:
            dpts.iloc[ip] = dpt.tocsv()
            ip += 1

        dpts.to_csv(os.path.join(self.pathappdata, 'toto.csv'), index=False,
                    sep=';')

    def saveData(self):
        for csvdat in self.data:
            df = csvdat['data']
            dfm = csvdat['metadata']
            savefilenamedata = os.path.join(self.pathappdata, 'bak', csvdat['name_csv'])
            savefilenamemeta = os.path.join(self.pathappdata, 'bak', csvdat['name_csv_meta'])
            df.to_csv(savefilenamedata, sep=';', index=False)
            dfm.to_csv(savefilenamemeta, sep=';', index=False)

    def quitter(self):

        qApp.quit()


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    ui = CovidVisu()
    ui.show()
    sys.exit(app.exec_())
