# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 16:17:05 2019

@author: jerome.jacq
"""

import os
import sys
import pandas as pd

import matplotlib.dates as mdates

pd.options.mode.chained_assignment = None


# Translate asset paths to useable format for PyInstaller
def ressource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def checkdate(data):
    """ vérifie le format des dates dans les fichiers de données
    """
    if 'jour' in data.columns:
        dfdate = pd.to_datetime(data['jour'])
        dates = [x.strftime('%Y-%m-%d') for x in dfdate]
        data['jour'] = dates


def downloadData(pathappdata, url, nomsauvegarde):
    """ télécharge et sauvegarde les données de santé publique france
    """
    # téléchargement des fichiers
    try:
        df = pd.read_csv(url, delimiter=';')
    except pd.errors.ParserError:
        df = pd.read_excel(url)
    df.drop_duplicates(keep='last', ignore_index=True, inplace=True)
    # sauvegarde des données
    savefilenamedata = os.path.join(pathappdata, nomsauvegarde)
    df.to_csv(savefilenamedata, sep=';', index=False)

    return df


def readcsv(pathappdata, urldata, update=False, fieldcsv='name_csv',
            fieldcsvmeta='name_csv_meta',
            fielddata='data', fieldmeta='metadata', urlcsv='url',
            urlcsvmeta='url_metadata'):
    if update:
        df = downloadData(pathappdata, urldata[urlcsv], urldata[fieldcsv])
        dfmeta = downloadData(pathappdata, urldata[urlcsvmeta], urldata[fieldcsvmeta])
    else:
        try:
            file = urldata[fieldcsv]
            df = pd.read_csv(os.path.join(pathappdata, file),
                             delimiter=';')
        except FileNotFoundError:
            df = downloadData(urldata[urlcsv], urldata[fieldcsv])
        try:
            filemeta = urldata[fieldcsvmeta]
            dfmeta = pd.read_csv(os.path.join(pathappdata, filemeta),
                                 delimiter=';')
        except FileNotFoundError:
            dfmeta = downloadData(urldata[urlcsvmeta], urldata[fieldcsvmeta])
    checkdate(df)
    # mise à jour des données
    urldata.update({fielddata: df})
    urldata.update({fieldmeta: dfmeta})


def extrairedata(dat, admin='dep'):
    df = dat['data']
    col = df.columns
    df[col[0]] = df[col[0]].apply(str)
    dfm = dat['metadata']
    dfm.dropna(axis=0, how='all', inplace=True)
    dfm.dropna(axis=1, how='all', inplace=True)
    dfgrp = df.groupby(by=admin)

    return df, dfgrp


def dateformat(x, pos=None):
    x = mdates.num2date(x)
    label = x.strftime('%m/%d')
    label = label.lstrip('0')
    return label
