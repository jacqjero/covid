# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 19:07:03 2020

@author: jerome.jacq
"""
import datetime as dt


LABELAGE = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60',
            '60-70', '70-80', '80-90', '90+']


def plotevol(ax, nom, df, tagdata, tagsx, title, ylabel):
    dates = [dt.datetime.strptime(i, '%Y-%m-%d')
             for i in df['jour'].unique().tolist()]
    if tagsx != 0:
        ax.plot(dates, df.groupby(by='sexe').get_group(tagsx)[tagdata].values,
                label='Homme-' + nom if tagsx == 1 else 'Femme-' + nom)
    else:
        ax.bar(dates, df.groupby(by='sexe').get_group(1)[tagdata].values,
               label='H-' + nom, alpha=0.7, picker=True)
        ax.bar(dates, df.groupby(by='sexe').get_group(2)[tagdata].values,
               label='F-' + nom, alpha=0.7, picker=True,
               bottom=df.groupby(by='sexe').get_group(1)[tagdata].values)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    return dates


def plotnouveauxcas(ax, nom, df, tagdata, title, ylabel):
    dates = [dt.datetime.strptime(i, '%Y-%m-%d')
             for i in df['jour'].unique().tolist()]
    ax.bar(dates, df['incid_' + tagdata].values, alpha=0.7,
           label=tagdata + '-' + nom)
    ax.legend()
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    return dates


def plotevolreg(ax, nom, df1, df2, tagdata, tagsx, age, title, ylabel):
    if tagsx == 0:
        if age == 0:
            dates = [dt.datetime.strptime(i, '%Y-%m-%d')
                     for i in df2['jour'].unique().tolist()]
            xx = df2.groupby(by='cl_age90')
            ff = df2.drop(xx.get_group(0).index)
            dff = ff.groupby(by='cl_age90')
            dfsum = ff.groupby(by='jour').sum()[tagdata].values / 100
            groups = list(dff.groups.keys())
            ax.bar(dates, dff.get_group(groups[0])[tagdata].values / dfsum,
                   label=LABELAGE[0])
            bot = dff.get_group(groups[0])[tagdata].values / dfsum
            for ind, grp in enumerate(groups[1:]):
                ax.bar(dates, dff.get_group(grp)[tagdata].values / dfsum,
                       bottom=bot, label=LABELAGE[ind + 1])
                bot += dff.get_group(groups[ind + 1])[tagdata].values / dfsum
        else:
            df = df2.groupby(by='cl_age90')
            dates = [dt.datetime.strptime(i, '%Y-%m-%d')
                     for i in df2['jour'].unique().tolist()]
            try:
                ax.bar(dates, df.get_group(age * 10 - 1)[tagdata].values,
                       label=nom, alpha=0.7)
            except KeyError:
                ax.bar(dates, df.get_group(90)[tagdata].values)
    else:
        dates = [dt.datetime.strptime(i, '%Y-%m-%d')
                 for i in df1['jour'].unique().tolist()]
        ax.plot(dates, df1.groupby(by='sexe').get_group(tagsx)[tagdata].values,
                label='Homme-' + nom if tagsx == 1 else 'Femme-' + nom)
    ax.legend()
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    return dates


def plotevoltestsreg(ax, nom, df, tagdata, tagsx, age, title, ylabel):
    grp = df.groupby(by='cl_age90')
    if age == 0:
        dates = [dt.datetime.strptime(i, '%Y-%m-%d')
                 for i in df['jour'].unique().tolist()]
        groups = list(grp.groups.keys())
        ax.bar(dates, grp.get_group(groups[0])[tagdata + tagsx].values,
               label='Total')
    else:
        dates = [dt.datetime.strptime(i, '%Y-%m-%d')
                 for i in df['jour'].unique().tolist()]
        try:
            ax.bar(dates, grp.get_group(age * 10 - 1)[tagdata + tagsx].values,
                   label=nom, alpha=0.7)
        except KeyError:
            ax.bar(dates, grp.get_group(90)[tagdata + tagsx].values)
    ax.legend()
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    return dates
