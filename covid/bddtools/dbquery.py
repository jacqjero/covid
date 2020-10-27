# -*- coding: utf-8 -*-
"""
Created on Sat Feb 22 09:12:59 2020

@author: jerome.jacq
"""

def querydpt(db):
    # recherche simple
    query = {'region': '0106'}

def analyseproduits(db, dbcat):
    # recherche simple: category
    query = {'category2': '0106'}
    curs = db.produits.find(query)
    lp = list(curs)
    # recherche pipeline: regrouper les produits par category 1
    stage1 = {'$lookup': {'from': 'categories',
                          'localField': 'category1',
                          'foreignField': 'code',
                          'as': 'test'}}

    stage2 = {'$group': {'_id': '$test.name', 'produit': {'$push': '$$ROOT'},
                         'nombre': {'$sum': 1}}}

    pipe = [stage1, stage2]
    lp = list(db.produits.aggregate(pipe))
    # regrouper les produits par facettes
    linclude = ["A0806"]
    land = []
    lexclude = []
    url = 'https://ico.iate.inra.fr/meatylab/origin_databases/2/foods/'
    lnumexclude = []
    lnumexclude = [url + x for x in lnumexclude]
    lnuminclude = []
    lnuminclude = [url + x for x in lnuminclude]
    query = dbcat.createquery(linclude, land, lexclude, lnuminclude, lnumexclude) # analysis:ignore
    curs = db.produits.find(query, {'name': 1, 'facettes':1, '_id': 0, 'url':1}) # analysis:ignore
    curs.sort('name', 1)
    lp = list(curs)
    # %% V1
    # Créer une requette permettant de trouver toutes les entrées ayant plus de
    # x% de lipides
    stage1 = {'$match': {'category2': 'a0'}}
    stage2 = {'$unwind': '$composition'}
    stage3 = {'$lookup': {'from': 'composants',
                          'localField': 'composition.composant',
                          'foreignField': '_id',
                          'as': 'test'}}
    stage4 = {'$group': {'_id': '$test.code', 'produit': {'$push': '$$ROOT'},
                         'nombre': {'$sum': 1}}}
    pipe = [stage1, stage2, stage3, stage4]

    cursor = db.produits.aggregate(pipe)
    lp = list(cursor)
    # %% V2
    # Créer une requette permettant de trouver toutes les entrées ayant plus de
    # x% de lipides
    # 1er étage de sélection: tous les produits ayant la catégorie a0
    category = 'a0'
    stage1 = {'$match': {'category2': category}}
    # expr utilisée dans le pipeline sur la bdd composants --> récupère l'id du
    # composant
    composant = 'CHO'
    expression = {'$and': [{'$in': ['$_id', '$$compid']},
                           {'$eq': ['$code', composant]}]}
    pipeline = [{'$match': {'$expr': expression}},
                {'$project': {'code': 1}}]

    stage2 = {'$lookup': {'from': 'composants',
                          'let': {'compid': '$composition.composant'},
                          'pipeline': pipeline,
                          'as': 'result'}}

    pipe = [stage1, stage2]

    cursor = db.produits.aggregate(pipe)
    lp = list(cursor)

    # %% V3
    # Créer une requette permettant de trouver toutes les entrées ayant plus de
    # x% de lipides
    # 1er étage de sélection: tous les produits ayant la catégorie a0
    category = 'a0'
    stage1 = {'$match': {'category2': category}}
    unwindcompos = {'$unwind': '$composition'}
    # expr utilisée dans le pipeline sur la bdd composants --> récupère l'id du
    # composant
    expression = {'$eq': ['$_id', '$$compid']}
    pipeline = [{'$match': {'$expr': expression}},
                {'$addFields': {'value': '$$compvalue',
                                'unit': '$$compunit'}}]

    stage2 = {'$lookup': {'from': 'composants',
                          'let': {'compid': '$composition.composant',
                                  'compvalue': '$composition.value',
                                  'compunit': '$composition.unit.code'},
                          'pipeline': pipeline,
                          'as': 'result'}}

    group = {'$group': {'_id': '$_id', 'result': {'$push': '$result'}}}
    pipe = [stage1, unwindcompos, stage2]

    cursor = db.produits.aggregate(pipe)
    lp = list(cursor)

    # %% V4
    # Créer une requette permettant de trouver toutes les entrées ayant plus de
    # x% de lipides
    # 1er étage de sélection: tous les produits ayant la catégorie a0
    composant = 'FAT'
    value = 15

    comp = db.composants.find_one({'code': composant})
    stage1 = {'entrees': {'$exists': True}}
    stage2 = {'composition': {'$elemMatch': {'composant': comp.get('_id'),
                                             'value': {'$gt': value}}}}
    query = {'$and': [stage1, stage2]}

    cursor = db.produits.find(query)
    lp = list(cursor)

    # %% V5
    # Créer une requette permettant de trouver toutes les entrées ayant plus de
    # x% de lipides
    # 1er étage de sélection: tous les produits ayant la catégorie a0
    cat = list(db.categories.find({'name': {'$regex': 'lég', '$options': 'i'}}))
    catcode = [x['code'] for x in cat]
    catname = [x['name'] for x in cat]
    category = 'a1'
    value = 15
    composant = 'FAT'

    comp = db.composants.find_one({'code': composant})
    stage1 = {'$match': {'entrees': {'$exists': True}}}
    filtre = {'$filter': {'input': '$composition',
                          'as': 'compos',
                          'cond': {'$and': [{'$eq': ['$$compos.composant', comp.get('_id')]},
                                            {'$gt': ['$$compos.value', value]}]}}}
    stage2 = {'$project': {'name': '$name', 'result': filtre}} 
    pipe = [stage1, stage2]
    cursor = db.produits.aggregate(pipe)
    lp = list(cursor)
    # %% V6
    # Récupérer tous les produits ayant le composant COMP
    composant = 'CA'
    comp = db.composants.find_one({'code': composant})

    stage1 = {'$unwind': '$composition'}
    stage2 = {'$match': {'composition.composant': comp.get('_id')}}
    pipe = [stage1, stage2]
    cursor = db.produits.aggregate(pipe)
    lp = list(cursor)
    # %% V6b
    composant = 'FIBT'
    comp = db.composants.find_one({'code': composant})
    cursor = db.produits.find({'composition.composant': {'$eq': comp.get('_id')}}, {'_id': 0, 'composition.$':1})
    lp = list(cursor)
    
    stage1 = {'contrainte7': {'$exists': True}}
    stage2 = {'composition.composant': {'$eq': comp.get('_id')}}
    query = {'$and': [stage1, stage2]}
    cursor = db.produits.find(query, {'_id': 0, 'composition.$':1})
    lp = list(cursor)
    # %% V7
    # Récupérer tous les produits n'ayant pas le composant COMP
    composant = 'FIBT'
    comp = db.composants.find_one({'code': composant})
    cursor = db.produits.find({'composition.composant': {'$ne': comp.get('_id')}})
    lp = list(cursor)
    # %% V8
    # Ajouter le rapport FASAT / FAT à chaque produit si FAT > 0
    composant1 = 'PROT'
    composant2 = 'FAT'
    comp1 = db.composants.find_one({'code': composant1})
    comp2 = db.composants.find_one({'code': composant2})
    
    stage1 = {'$match': {'$and': [{'composition.composant': comp1.get('_id')},
                                  {'composition.composant': comp2.get('_id')}]}}
    pipe = [stage1]
    cursor = db.produits.aggregate(pipe)
    lp = list(cursor)
    
    expression = {'$and': [{'$in': [comp1.get('_id'),'$composition.composant']},
                           {'$in': [comp2.get('_id'),'$composition.composant']}]}
    query = {'$and': [{'$expr': expression}, {'plats': 1}]}
    cursor = db.produits.find(query)
    lp = list(cursor)

    return lp

# %%


def analyserecettes(db):
    query = {'results.1.properties': {'$elemMatch':
                                      {'code': 'PROT', 'value': {'$lte': 200}}}} # analysis:ignore
    lp = list(db.recettes.find(query))
    # regrouper les résultats des recettes
    pipe = [{'$unwind': '$results'},
            {'$group': {'_id': '$results.code',
                        'res': {'$addToSet': '$results.properties'}}},
            {'$match': {'_id': 2}},
            {'$unwind': '$res'},
            {'$match': {'code': 'ENERKJ'}}
            ]
    lp = list(db.recettes.aggregate(pipe))
    # regrouper les recettes par catégories
    pipe = [{'$group': {'_id': '$category', 'recette': {'$push': '$$ROOT'},
                        'nombre': {'$sum': 1}}}]
    lp = list(db.recettes.aggregate(pipe))

    pipe = [{'$lookup': {'from': 'produits',
                         'localField': 'ingredients.produit',
                         'foreignField': '_id',
                         'as': 'test'}},
            {'$group': {'_id': '$test.name', 'produit': {'$push': '$$ROOT'},
                        'nombre': {'$sum': 1}}}
            ]
    lp = list(db.produits.aggregate(pipe))

    pipe = [{'$unwind': 'results'},
            {'$eq': ['results.code', 2]}]

    curs = db.recettes.aggregate(pipe)
    lp = list(curs)

    lp = list(db.recettes.find({'results.1.properties': {'$elemMatch': {'code':'ENERKJ', # analysis:ignore
                                                                        'value':{'$lte':1000}}}})) # analysis:ignore

    pipe = [
            {'$lookup': {'from': 'produits',
                         'localField': 'ingredients.produit',
                         'foreignField': '_id',
                         'as': 'test'}},
            {'$match': {'test.category1': 'b'}}
            ] # analysis:ignore

    pipe = [{'$lookup': {'from': 'produits',
                         'let': {'produit': '$ingredients.produit'},
                         'pipeline': [{'$match': {'$expr': {'$and': [{'$eq': ['$_id', '$$produit']},  # analysis:ignore
                                                                     {'$eq': ['$category1', 'f']}]}}},  # analysis:ignore
                                      {'$project': {'category1': 1, '_id': 0}}],  # analysis:ignore
                         'as': 'cat'}}
            ] # analysis:ignore

    pipe = [{'$lookup': {'from': 'produits',
                         'let': {'cat': '$ingredients.produit.category1'},
                         'pipeline': [{'$match': {'$expr': {'$$cat': 'f'}}},
                                      {'$project': {'category1': 1, '_id': 0}}],  # analysis:ignore
                         'as': 'cat'}}
            ] # analysis:ignore
    cursor = db.recettes.aggregate(pipe)
    lp = list(cursor)

    pipe = [{'$match': {'category1': 'd'}}]

    curs = db.produits.aggregate(pipe)
    lp = list(curs)

    return lp
