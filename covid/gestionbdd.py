# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 11:46:36 2020

@author: jerome.jacq
"""

import os
import csv
import json

from santepublique.localisation import Departement, Region, Individu
from santepublique.utilities import ressource_path, readcsv, extrairedata

from pymongo import MongoClient, errors


def creerbdddepartements(path, urldata, db, nomcollection, update=False):
    """ le département est l'entité administrative la plus petite
    """
    # Création de la bd
    try:
        db.create_collection(nomcollection)
        ldepartements = list()
        # Création des objects à mettre en base
        with open(os.path.join(path, 'departements.csv'), 'r',
                  encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', dialect='excel')
            ip = 0
            for row in reader:
                if ip != 0:
                    ldepartements.append(Departement.fromcsv(row))
                ip += 1
        # Attribution des données aux objets
        ldat = [dat for dat in urldata if dat['admin'] == 'dep']
        for dat in ldat:
            readcsv(path, dat, update=update)
            df, dfgrp = extrairedata(dat)
            for dep in ldepartements:
                dep.attribuerdata(dat['code'], dfgrp)
        for dep in ldepartements:
            db[nomcollection].insert_one(dep.tobdd())
    except errors.CollectionInvalid:
        print('Collection already exists')
        pass


def creerbddregions(path, urldata, db, nomcollection, update=False):
    """ les régions sont créées à partir de la base de données des
    départements
    """
    # Création de la bd
    lregions = list()
    try:
        db.create_collection(nomcollection)
        # Création des objects à mettre en base
        with open(os.path.join(path, 'regions.csv'), 'r',
                  encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', dialect='excel')
            ip = 0
            for row in reader:
                if ip != 0:
                    lregions.append(Region.fromdata(row))
                ip += 1
        # Attribution des données aux objets
        ldat = [dat for dat in urldata if dat['admin'] == 'reg']
        for dat in ldat:
            readcsv(path, dat, update=update)
            df, dfgrp = extrairedata(dat, admin='reg')
            for reg in lregions:
                reg.attribuerdata(dat['code'], dfgrp)
        for reg in lregions:
            db[nomcollection].insert_one(reg.tobdd())
    except errors.CollectionInvalid:
        print('Collection already exists')
        pass


def creerbdddeces(path, db, nomcollec):
    """ création de la bdd des décès en france métropolitaine depuis 1990
    """
    files = os.listdir(os.path.join(path, 'deces'))
    # Création de la bd
    try:
        db.create_collection(nomcollec)
        for file in files:
            # Création des objects à mettre en base
            with open(os.path.join(path, 'deces', file), 'r',
                      encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';', dialect='excel')
                ip = 0
                for row in reader:
                    if ip != 0:
                        indiv = Individu.fromdata(row)
                        db[nomcollec].insert_one(indiv.tobdd())
                    ip += 1
    except errors.CollectionInvalid:
        print('Collection already exists')
        pass


def ajouteranneedeces(file, db, nomcollec):
    """ permet d'ajouter une année à la base de données décès
    """
    # Création des objects à mettre en base
    with open(file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', dialect='excel')
        ip = 0
        for row in reader:
            if ip != 0:
                indiv = Individu.fromdata(row)
                db[nomcollec].insert_one(indiv.tobdd())
            ip += 1


def updatedepts(path, db, nomcollecregion, nomcollecdepts):
    """ réalise des opération de mise à jour nécessaires des bdd créées
    """
    for dpt in db[nomcollecdepts].find({}):
        reg = db[nomcollecregion].find_one({'code': dpt['code_region']})
        db[nomcollecdepts].update_one({'_id': dpt.get('_id')}, {'$set': {'id_region': reg.get('_id')}})


def updateregs(db, nomcollecregion, nomcollecdepts):
    """ mise à jour de la bdd région
    """
    for reg in db[nomcollecregion].find({}):
        # ajout de la liste des départements
        cursor = db[nomcollecdepts].find({'code_region': reg['code']})
        lid = [dpt['_id'] for dpt in cursor]
        db[nomcollecregion].update_one({'_id': reg.get('_id')}, {'$set': {'liste_departements': lid}})
        # ajout de la population de la région
        query = {'_id': {'$in': lid}}
        pipe = [{'$match': query}, {'$group': {'_id': 'null', 'sum': {'$sum': '$population'}}}]
        curs = db[nomcollecdepts].aggregate(pipe)
        pop = next(doc['sum'] for doc in curs)
        db[nomcollecregion].update_one({'_id': reg.get('_id')}, {'$set': {'population': pop}})
        # ajout de la superficie de la région
        pipe = [{'$match': query}, {'$group': {'_id': 'null', 'sum': {'$sum': '$superficie'}}}]
        curs = db[nomcollecdepts].aggregate(pipe)
        sup = next(doc['sum'] for doc in curs)
        db[nomcollecregion].update_one({'_id': reg.get('_id')}, {'$set': {'superficie': sup}})
    # ajout de la densité de la population
    db[nomcollecregion].aggregate([{'$addFields': {'densite': {'$round': [{'$divide': ['$population', '$superficie']}, 2]}}},
                                   {'$out': nomcollecregion}])


def connexionbdd(nombdd):
    """permet la connecion à la bdd
    """
    print('toto')


if __name__ == '__main__':
    # Création de la bdd
    mongo_client = MongoClient('mongodb://localhost:27017')
    db = mongo_client.santepublique
    nomdbdeps = 'departements'
    nomdbregs = 'regions'
    nomdbdeces = 'deces'
    # folder
    pathappdata = ressource_path('data')
    # données
    file = os.path.join(pathappdata, 'urls.cfg')
    with open(file, 'r', encoding='utf-8') as fp:
        urlsdata = json.load(fp)
    # Création bdd départements
    creerbdddepartements(pathappdata, urlsdata, db, nomdbdeps)
    # Création bdd régions
    creerbddregions(pathappdata, urlsdata, db, nomdbregs)
    # Mise à jour de la bdd département
    updatedepts(pathappdata, db, nomdbregs, nomdbdeps)
    # Mise à jour de la bdd region
    updateregs(db, nomdbregs, nomdbdeps)
    # Création bdd décès
    creerbdddeces(pathappdata, db, nomdbdeces)
    # Ajout année
    file = 'deces-1991.csv'
    pathfile = os.path.join(pathappdata, 'deces', file)
    ajouteranneedeces(pathfile, db, nomdbdeces)
