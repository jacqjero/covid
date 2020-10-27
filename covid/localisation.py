import pandas as pd

from santepublique.visus import (plotevol, plotnouveauxcas, plotevoltestsreg,
                                 plotevolreg)


def defineplotopt(rbGraph, rbEvol, rbSexe, age):
    """ attribution des options graphiques
    """
    title = list()
    # Coix du type de graph
    if rbEvol.objectName() == 'rbEvol':
        title.append('Evolution du')
    else:
        title.append('Nombre de nouveaux')
    # Choix de la grandeur à afficher
    if rbGraph.objectName() == 'rbRea':
        strdata = 'rea'
        title.append('nombre de patients en réanimation')
        ylabel = 'Nombre de patients'
    elif rbGraph.objectName() == 'rbDeaths':
        strdata = 'dc'
        title.append('nombre de décès')
        ylabel = 'Nombre de décès'
    elif rbGraph.objectName() == 'rbHosp':
        strdata = 'hosp'
        title.append('nombre de patients hospitalisés')
        ylabel = 'Nombre de patients'
    elif rbGraph.objectName() == 'rbTest':
        strdata = 'Tx'
        title.append('taux de positivité')
        ylabel = '%'
    elif rbGraph.objectName() == 'rbIncid':
        strdata = 'Tx'
        title.append('taux d''incidence')
        ylabel = 'Tests positifs / 100000 hab'
    # Choix du Sexe: Homme, Femme, Total (H+F)
    if rbSexe.objectName() == 'rbH':
        title.append('- Hommes')
        if strdata == 'Tx':
            grpsexe = '_h'
        else:
            grpsexe = 1
    elif rbSexe.objectName() == 'rbF':
        title.append('- Femmes')
        if strdata == 'Tx':
            grpsexe = '_f'
        else:
            grpsexe = 2
    else:
        title.append('- Total (H+F)')
        if strdata == 'Tx':
            grpsexe = ''
        else:
            grpsexe = 0

    title = ' '.join(title)

    return strdata, grpsexe, title, ylabel


def calcultauxpositivite(dat):
    """ réalise le calcul du taux d'incidence
    """
    try:
        dat['Tx_h'] = dat['P_h'] / dat['T_h'] * 100
        dat['Tx_f'] = dat['P_f'] / dat['T_f'] * 100
        dat['Tx'] = dat['P'] / dat['T'] * 100
    except KeyError:
        dat['Tx'] = dat['P'] / dat['T'] * 100

    return dat


def calcultauxincidence(dat):
    """ réalise le calcul du taux d'incidence
    """
    try:
        dat['Tx_h'] = dat['P_h'] / dat['pop_h'] * 100000
        dat['Tx_f'] = dat['P_f'] / dat['pop_f'] * 100000
        dat['Tx'] = dat['P'] / dat['pop'] * 100000
    except KeyError:
        dat['Tx'] = dat['P'] / dat['pop'] * 100000

    return dat


class Departement:
    def __init__(self):
        # Attributs de l'objet
        self.nom = ''
        self.code = ''
        self.region = ''
        self.coderegion = ''
        self.cheflieu = ''
        self.superficie = 0
        self.population = 0
        # La densité est calculée à partir de la population et de la superficie
        self.densite = 0
        # Attributs calculés à partir des données
        self.nbrea = 0
        self.nbdeaths = 0
        self.nbhosp = 0
        self.txincid7j = 0
        # Données attribuées à l'objet
        self.hosp = None
        self.newcases = None
        self.services = None
        self.tests = None
        self.txincid = None
        # Attributs pour l'IG
        self.checked = False

    @classmethod
    def fromcsv(cls, data):
        departement = cls()
        departement.code = data[0]
        departement.nom = data[1]
        departement.region = data[6]
        departement.cheflieu = data[2]
        departement.superficie = float(data[3])
        departement.population = float(data[4])
        departement.densite = round(float(data[4]) / float(data[3]), 2)
        departement.coderegion = data[5]

        return departement

    @classmethod
    def fromdatabase(cls, db, codedpt):
        departement = cls()
        # Recherche du dpt dans la bdd
        data = db.find_one({'code': codedpt})
        departement.code = data['code']
        departement.nom = data['nom']
        departement.region = data['region']
        departement.cheflieu = data['chef_lieu']
        departement.superficie = data['superficie']
        departement.population = data['population']
        departement.densite = round(float(data['population']) / float(data['superficie']), 2)
        departement.coderegion = data['code_region']

        return departement

    def tocsv(self):
        """ permet d'exporter les données
        """
        return [self.code, self.nom, self.region, self.cheflieu,
                self.superficie, self.population, self.densite, self.coderegion]

    def tobdd(self):
        """ permet d'intégrer l'objet dans la collection de la base de données
        santepublique
        """
        return {'nom': self.nom,
                'code': self.code,
                'chef_lieu': self.cheflieu,
                'region': self.region,
                'code_region': self.coderegion,
                'superficie': self.superficie,
                'population': self.population,
                'densite': self.densite,
                'hosp': self.hosp.to_dict(orient='list'),
                'newcases': self.newcases.to_dict(orient='list'),
                'tests': self.tests.to_dict(orient='list'),
                'txincid': self.txincid.to_dict(orient='list')}

    def attribuerdata(self, tag, dfgrp):
        df = dfgrp.get_group(self.code)
        if tag == 'tests':
            df = calcultauxpositivite(df)
        elif tag == 'txincid':
            df = calcultauxincidence(df)
        self.__setattr__(tag, df.drop(labels='dep', axis=1).reset_index(drop=True))
        # calcul des indicateurs
        if tag == 'hosp':
            self.nbdeaths = int(self.hosp.groupby(by='sexe').get_group(0).iloc[-1, -1])
            self.nbrea = int(self.hosp.groupby(by='sexe').get_group(0).iloc[-1, -3])
            self.nbhosp = int(self.hosp.groupby(by='sexe').get_group(0).iloc[-1, -4])
        if tag == 'txincid':
            testpos7 = self.tests.groupby(by='cl_age90').get_group(0)['P'].iloc[-7:].sum()
            self.txincid7j = int(testpos7 / self.population * 100000)
            

    def visualiser(self, hAx, rbGraph, rbEvol, rbSexe, tagage=None, admin=None):
        """ méthode de visualisation de l'objet
        """
        strdata, grpsexe, title, ylabel = defineplotopt(rbGraph, rbEvol, rbSexe, tagage)
        # Affichage
        if rbEvol.objectName() == 'rbEvol':
            if rbGraph.objectName() == 'rbTest':
                dates = plotevoltestsreg(hAx, self.nom, self.tests, strdata, grpsexe, tagage, title, ylabel)
            elif rbGraph.objectName() == 'rbIncid':
                dates = plotevoltestsreg(hAx, self.nom, self.txincid, strdata, grpsexe, tagage, title, ylabel)
            else:
                dates = plotevol(hAx, self.nom, self.hosp, strdata, grpsexe, title, ylabel)
        else:
            dates = plotnouveauxcas(hAx, self.nom, self.newcases, strdata, title, ylabel)
        hAx.set_xticklabels(dates)


class Region:
    def __init__(self):
        self.nom = ''
        self.code = ''
        self.ldepartements = list()
        self.superficie = 0
        self.population = 0
        self.densite = 0
        self.nbdeaths = 0
        self.nbrea = 0
        self.nbhosp = 0
        self.nbtests = 0
        self.nbtestspos = 0
        self.txpositivite = 0
        self.txincidence = 0
        self.txincid7j = 0
        self.hosp = None
        self.newcases = None
        self.ages = None
        self.services = None
        self.tests = None
        self.txincid = None
        self.checked = False

    @classmethod
    def fromdata(cls, data):
        region = cls()
        region.nom = data[0]
        region.code = data[1]

        return region

    def tobdd(self):
        """ permet d'intégrer l'objet dans la collection de la base de données
        santepublique
        """
        return {'nom': self.nom,
                'code': self.code,
                'ages': self.ages.to_dict(orient='list'),
                'tests': self.tests.to_dict(orient='list'),
                'txincid': self.txincid.to_dict(orient='list')}

    def getdep(self, departements):
        gen = (dep for dep in departements if dep.coderegion == self.code)
        for dpt in gen:
            self.ldepartements.append(dpt)
        # Attribution des données administratives issues des départements
        self.superficie = sum([x.superficie for x in self.ldepartements])
        self.population = sum([x.population for x in self.ldepartements])
        self.densite = round(self.population / self.superficie, 2)

    def attribuerdata(self, tag, dfgrp, admin='reg'):
        if int(self.code) in range(10):
            code2 = str(int(self.code))
        else:
            code2 = self.code
        df = dfgrp.get_group(code2)
        if tag == 'tests':
            df = calcultauxpositivite(df)
        elif tag == 'txincid':
            df = calcultauxincidence(df)
        self.__setattr__(tag, df.drop(labels=admin, axis=1).reset_index(drop=True))

    def valoriserdata(self):
        """ valorise les données manquantes à partir des données sur les
        départements
        """
        # Valorisation des données hospitalières issues des départements
        df = pd.concat([x.hosp for x in self.ldepartements])
        self.hosp = df.groupby(by=['jour', 'sexe']).sum().reset_index()
        # Valorisation des données hospitalières nouveaux cas issues des dpts
        df = pd.concat([x.newcases for x in self.ldepartements])
        self.newcases = df.groupby(by='jour').sum().reset_index()
        # Valorisation des données des établissements issues des départements
        df = pd.concat([x.services for x in self.ldepartements])
        self.services = df.groupby(by='jour').sum().reset_index()
        # Calcul des indicateurs
        self.calculerindicateurs()

    def calculerindicateurs(self):
        """ permet le calcul d'indicateur pour affichage
        """
        # Calculs réalisés sur les données valorisées
        self.nbdeaths = int(self.hosp.groupby(by='sexe').get_group(0).iloc[-1, -1])
        self.nbrea = int(self.hosp.groupby(by='sexe').get_group(0).iloc[-1, -3])
        self.nbhosp = int(self.hosp.groupby(by='sexe').get_group(0).iloc[-1, -4])
        # Nombre de tests total
        self.nbtests = self.tests.groupby(by='cl_age90').get_group(0)['T'].sum()
        self.nbtestspos = self.tests.groupby(by='cl_age90').get_group(0)['P'].sum()
        testpos7 = self.tests.groupby(by='cl_age90').get_group(0)['P'].iloc[-7:].sum()
        self.txpositivite = testpos7 / self.nbtests * 100
        self.txincidence = testpos7 / self.population * 100000
        self.txincid7j = int(self.txincidence)

    def visualiser(self, hAx, rbGraph, rbEvol, rbSexe, tagage=None, admin=None):
        """ visualisation des régions
        """
        strdata, grpsexe, title, ylabel = defineplotopt(rbGraph, rbEvol, rbSexe, tagage)

        # Affichage
        if rbEvol.objectName() == 'rbEvol':
            if rbGraph.objectName() == 'rbTest':
                dates = plotevoltestsreg(hAx, self.nom, self.tests, strdata, grpsexe, tagage, title, ylabel)
            elif rbGraph.objectName() == 'rbIncid':
                dates = plotevoltestsreg(hAx, self.nom, self.txincid, strdata, grpsexe, tagage, title, ylabel)
            else:
                dates = plotevolreg(hAx, self.nom, self.hosp, self.ages, strdata, grpsexe, tagage, title, ylabel)
        else:
            dates = plotnouveauxcas(hAx, self.nom, self.newcases, strdata, title, ylabel)
        hAx.set_xticklabels(dates)


class Pays:
    def __init__(self, nom, code, ldpt, lreg):
        """objet pays
        """
        self.nom = nom
        self.code = code
        self.ldepartements = ldpt
        self.lregions = lreg
        # autres attributs
        self.nbdeaths = 0
        self.nbrea = 0
        self.nbhosp = 0
        self.nbtests = 0
        self.nbtestspos = 0
        self.txpositivite = 0
        self.txincidence = 0
        self.txincid7j = 0
        self.superficie = 0
        self.population = 0
        self.densite = 0
        # Data
        self.hosp = None
        self.newcases = None
        self.ages = None
        self.services = None
        self.tests = None
        self.txincid = None
        # autre
        self.checked = False

    def attribuerdata(self, tag, dfgrp, admin='fra'):
        df = dfgrp.get_group(self.code)
        if tag == 'tests':
            df = calcultauxpositivite(df)
        elif tag == 'txincid':
            df = calcultauxincidence(df)
        self.__setattr__(tag, df.drop(labels=admin, axis=1).reset_index(drop=True))

    def valoriserdata(self):
        # Valorisation des données hospitalières issues des départements
        df = pd.concat([x.hosp for x in self.ldepartements])
        self.hosp = df.groupby(by=['jour', 'sexe']).sum().reset_index()
        # Valorisation des données hospitalières issues des départements
        df = pd.concat([x.newcases for x in self.ldepartements])
        self.newcases = df.groupby(by='jour').sum().reset_index()
        # Valorisation des données issus des services hospitaliers issues des dpts
        df = pd.concat([x.services for x in self.ldepartements])
        self.services = df.groupby(by='jour').sum().reset_index()
        # Valorisation des données hospitalières par tranches d'age issues des régions
        df = pd.concat([x.ages for x in self.lregions])
        self.ages = df.groupby(by=['cl_age90', 'jour']).sum().reset_index()
        # Propriété du pays
        self.superficie = sum([x.superficie for x in self.lregions])
        self.population = sum([x.population for x in self.lregions])
        self.densite = self.population / self.superficie
        # Calcul des indicateurs
        self.calculerindicateurs()

    def calculerindicateurs(self):
        """ permet le calcul d'indicateur pour affichage
        """
        # Calculs réalisés sur les données valorisées
        self.nbrea = sum([x.nbrea for x in self.ldepartements])
        self.nbhosp = sum([x.nbhosp for x in self.ldepartements])
        self.nbdeaths = sum([x.nbdeaths for x in self.ldepartements])
        # Nombre de tests total
        self.nbtests = self.tests.groupby(by='cl_age90').get_group(0)['T'].sum()
        self.nbtestspos = self.tests.groupby(by='cl_age90').get_group(0)['P'].sum()
        testpos7 = self.tests.groupby(by='cl_age90').get_group(0)['P'].iloc[-7:].sum()
        tests7 = self.tests.groupby(by='cl_age90').get_group(0)['T'].iloc[-7:].sum()
        self.txpositivite = testpos7 / tests7 * 100
        self.txincidence = testpos7 / self.population * 100000
        self.txincid7j = int(self.txincidence)

    def visualiser(self, hAx, rbGraph, rbEvol, rbSexe, tagage=None, admin=None):
        """ visualisation des régions
        """
        strdata, grpsexe, title, ylabel = defineplotopt(rbGraph, rbEvol, rbSexe, tagage)

        # Affichage
        if rbEvol.objectName() == 'rbEvol':
            if rbGraph.objectName() == 'rbTest':
                dates = plotevoltestsreg(hAx, self.nom, self.tests, strdata, grpsexe, tagage, title, ylabel)
            elif rbGraph.objectName() == 'rbIncid':
                dates = plotevoltestsreg(hAx, self.nom, self.txincid, strdata, grpsexe, tagage, title, ylabel)
            else:
                if admin.objectName() == 'cbRegions':
                    dates = plotevolreg(hAx, self.nom, self.hosp, self.ages, strdata, grpsexe, tagage, title, ylabel)
                else:
                    dates = plotevol(hAx, self.nom, self.hosp, strdata, grpsexe, title, ylabel)
        else:
            dates = plotnouveauxcas(hAx, self.nom, self.newcases, strdata, title, ylabel)
        hAx.set_xticklabels(dates)


class Individu:
    def __init__(self):
        self.nom = ''
        self.prenom = ''
        self.sexe = ''
        self.datenaissance = ''
        self.datedeces = ''
        self.codelieunaissance = ''
        self.codelieudeces = ''
        self.communenaissance = ''
        self.paysnaissance = ''

    @classmethod
    def fromdata(cls, data):
        indiv = cls()
        try:
            indiv.nom = data[0].split(sep='*')[0]
            indiv.prenom = data[0].split(sep='*')[1][:-1]
        except IndexError:
            indiv.nom = ''
            indiv.prenom = data[0][:-1]
        indiv.sexe = data[1]
        indiv.datenaissance = data[2]
        indiv.datedeces = data[6]
        indiv.codelieunaissance = data[3]
        indiv.codelieudeces = data[7]
        indiv.communenaissance = data[4]
        indiv.paysnaissance = data[5]

        return indiv

    def tobdd(self):
        """ permet d'intégrer l'objet dans la collection de la base de données
        santepublique
        """
        return {'nom': self.nom,
                'prenom': self.prenom,
                'sexe': self.sexe,
                'date_naissance': self.datenaissance,
                'date_deces': self.datedeces,
                'code_lieu_naissance': self.codelieunaissance,
                'code_lieu_deces': self.codelieudeces,
                'commune_naissance': self.communenaissance,
                'pays_naissance': self.paysnaissance}
