import matplotlib.pyplot as plt
import numpy as np
import csv
import os


def lecture(path, file):

    lres = list()
    with open(os.path.join(path, file), 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            lres.append(row)

    return lres

def creatematrice(result):
    return np.array(result)


def plotdata(mat, pays):
    index = np.where(mat[:, 1] == pays)
    plt.plot(mat[0, 4:], mat[index[0][0], 4:])
    plt.show()
    print('todo')


if __name__ == '__main__':
    datadir = 'csse_covid_19_data'
    tsdir = 'csse_covid_19_time_series'
    path = os.path.join(os.path.dirname(os.getcwd()), datadir, tsdir)
    lfiles = [x for x in os.listdir(path) if x.endswith('.csv')]
    res = lecture(path, lfiles[0])
    matrice = creatematrice(res)
    plotdata(matrice, 'Italy')
    print('todo')
