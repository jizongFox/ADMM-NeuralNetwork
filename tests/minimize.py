from cmath import sqrt

import pytest

import numpy as np
import scipy as sp
import numpy.matlib
import scipy.optimize
import time

import auxiliaries

__author__ = "Lorenzo Rutigliano, lnz.rutigliano@gmail.com"


def _minimize(a, m, alpha, beta):
    if a <= 0 and m <= 0:
        return m
    sol = ((alpha * a) + (beta * m)) / (alpha + beta)
    if a >= 0 and m >= 0:
        return sol
    if m < 0 < a:
        if sol / (a ** 2) > 1:
            return sol
        else:
            return m
    if a < 0 < m:
        return sol


def argminz(z, a, w, a_in, gamma, beta):
    m = np.dot(w, a_in)
    x = z.shape[0]
    y = z.shape[1]
    #z = np.zeros((x, y))
    for i in range(x):
        for j in range(y):
            z[i, j] = _minimize(a[i, j], m[i, j], gamma, beta)
    return z


def comp(z, a, w, a_in, gamma, beta):
    m = np.dot(w, a_in)
    m1 = gamma * (np.linalg.norm(a - np.maximum(0, z))) ** 2
    m2 = beta * (np.linalg.norm(z - m)) ** 2
    return m1 + m2


def test_1():
    print()
    n = 3
    indim = 400
    outdim = 3
    w = np.matlib.randn(outdim, indim)
    z = np.matlib.randn(outdim, n)
    a = np.matlib.randn(outdim, n)
    a_in = np.matlib.randn(indim, n)
    m = np.dot(w, a_in)
    res = comp(z, a, w, a_in, 10, 1)
    print("=======")
    print(a)
    print("----------------------------------------------")
    print(m)
    print("=======")
    print("Original score: %s" % str(res))
    print("=======")
    z = argminz(z, a, w, a_in, 10, 1)
    res = comp(z, a, w, a_in, 10, 1)
    print(res)
    print(z)


def test_2():
    print()
    res = _minimize(2.5, -41.5, 10, 1)
    res1 = 10 * (2.5) ** 2
    sol = np.abs(((10 * 2.5) + (1 * -41.5)) / (11))
    res2 = 10 * (2.5 - np.maximum(0, sol)) ** 2 + 1 * (sol + 41.5) ** 2
    print(res1)
    print(res2)

"""
LAST LAYER
"""
def loss(z, y):
    if y == 1:
        return np.maximum(0, 1 - z)
    return np.maximum(0, z)


def compscalar(z, y, eps, m, beta):
    return loss(z, y) + (z * eps) + (beta * ((z - m) ** 2))


def lastmin(y, eps, m, beta):
    if y == 0:
        if m > (eps + 1) / (2 * beta):
            return m - ((eps + 1) / (2 * beta))
        else:
            return m - (eps / (2 * beta))
    else:
        if m < 1 + ((eps - 1) / (2 * beta)):
            return m - ((eps - 1) / (2 * beta))
        else:
            return m - (eps / (2 * beta))


def bot(z, y, eps, m, beta):
    m1 = auxiliaries.binary_loss_sum(z, y)
    m2 = np.dot(z.T, eps)
    m3 = beta * (np.linalg.norm(z - m) ** 2)
    return m1 + m2[0, 0] + m3


def top(z, y, eps, w, a_in, beta):
    m = np.dot(w, a_in)
    for j in range(z.shape[1]):
        tmp = sp.optimize.minimize(bot, z[:, j], args=(y[:, j], eps[:, j], m[:, j], beta))
        z[:, j] = np.reshape(tmp.x, (10, 1))
    return z


def compall(z, y, eps, w, a_in, beta):
    m = np.dot(w, a_in)
    c = 0
    for j in range(z.shape[1]):
        c += bot(z[:, j], y[:, j], eps[:, j], m[:, j], beta)
    return c


def test_3():
    print()
    print()
    n = 3
    indim = 400
    outdim = 10
    w = np.matlib.randn(outdim, indim)
    z = np.matlib.randn(outdim, n)
    a = np.matlib.randn(outdim, n)
    a_in = np.matlib.randn(indim, n)
    samples, targets = auxiliaries.data_gen(indim, outdim, n)
    eps = np.matlib.randn(outdim, n)
    m = np.dot(w, a_in)

    print(compall(z, targets, eps, w, a_in, 1.))
    z1 = top(z, targets, eps, w, a_in, 1.)
    print(compall(z1, targets, eps, w, a_in, 1.))

    c = 0
    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            z[i, j] = lastmin(targets[i, j], eps[i, j], m[i, j], 1.)
            c += compscalar(z[i, j], targets[i, j], eps[i, j], m[i, j], 1.)
    #print(c)
    print(compall(z, targets, eps, w, a_in, 1.))