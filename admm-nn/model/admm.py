import numpy as np

#from memory_profiler import profile

import warnings
warnings.filterwarnings("error")

__author__ = "Lorenzo Rutigliano, lnz.rutigliano@gmail.com"


"""
The idea behind this method is to decouple the weights from the non-linear
link functions using a splitting technique. We wish to solve the following problem:

    minimize l(z_L, y) + <z_L, lambda> + beta||z_L - W_L a_L-1||^2

             + sum{from 1 to L-1} of [gamma||a_l - h(z_l)||^2 + beta||z_l - W_l a_l-1||^2]


For a complete reading:

    'Training Neural Networks Without Gradients: A Scalable ADMM Approach', 2016
    Gavin Taylor, Ryan Burmeister, Zheng Xu, Bharat Singh, Ankit Patel, Tom Goldstein

"""


@profile
def weight_update(layer_output, activation_input):
    """
    Consider it now the minimization of the problem with respect to W_l.
    For each layer l, the optimal solution minimizes ||z_l - W_l a_l-1||^2. This is simply
    a least square problem, and the solution is given by W_l = z_l p_l-1, where p_l-1
    represents the pseudoinverse of the rectangular acivation matrix a_l-1.

    :param layer_output:        output matrix z_l
    :param activation_input:    activation matrix a_l-1
    :return:    weight matrix W_l
    """
    ap_ps = np.linalg.pinv(activation_input)
    return np.dot(layer_output, ap_ps)


def _activation_inverse(next_weight, beta, gamma):
    m1 = beta * (np.dot(next_weight.T, next_weight))
    m2 = (np.identity(next_weight.shape[1], dtype='float64')) * gamma
    return np.linalg.inv(m1 + m2)


def _activation_formulate(next_weight, next_layer_output, layer_nl_output, beta, gamma):
    m1 = beta * (np.dot(next_weight.T, next_layer_output))
    m2 = gamma * layer_nl_output
    return m1 + m2


@profile
def activation_update(next_weight, next_layer_output, layer_nl_output, beta, gamma):
    """
    Minimization for a_l is a simple least squares problem similar to the weight update.
    However, in this case the matrix appears in two penalty terms in the problem, and so
    we must minimize:

        beta ||z_l+1 - W_l+1 a_l||^2 + gamma ||a_l - h(z_l)||^2

    :param next_weight:         weight matrix W_l+1
    :param next_layer_output:   output matrix z_l+1
    :param layer_nl_output:     activate output matrix h(z_l)
    :return:    activation matrix a_l
    """
    m1 = _activation_inverse(next_weight, beta, gamma)
    m2 = _activation_formulate(next_weight, next_layer_output,
                               layer_nl_output, beta, gamma)
    return np.dot(m1, m2)


def _minimize(a, m, alpha, beta):
    """
    Minimization of z_l using ReLUs:

               | x, if x > 0
        h(x) = |
               | 0, otherwise
    """
    if a <= 0 and m <= 0:
        return m
    sol = ((alpha * a) + (beta * m)) / (alpha + beta)
    if a >= 0 and m >= 0:
        return sol
    if m < 0 < a:
        try:
            t = a ** 2
        except RuntimeWarning:
            return sol
        if sol > t:
            return sol
        else:
            return m
    if a < 0 < m:
        return sol


@profile
def argminz(a, w, a_in, gamma, beta):
    """
    This problem is non-convex and non-quadratic (because of the non-linear term h).
    Fortunately, because the non-linearity h works entry-wise on its argument, the entries
    in z_l are decoupled. This is particularly easy when h is piecewise linear, as it can
    be solved in closed form; common piecewise linear choices for h include rectified
    linear units (ReLUs), that its used here, and non-differentiable sigmoid functions.

    :param a:   activation matrix a_l
    :param w:   weight matrix W_l
    :param a_in:activation matrix a_l-1
    :return: output matrix z_l
    """
    m = np.dot(w, a_in)
    x = a.shape[0]
    y = a.shape[1]
    z = np.mat(np.zeros((x, y), dtype='float64'))
    for i in range(x):
        for j in range(y):
            z[i, j] = _minimize(a[i, j], m[i, j], gamma, beta)
    return z


def _minimizelast(y, eps, m, beta):
    """
    Minimization of z_L using the following loss function:

                  | max{1 - z, 0}, when y = 1
        l(z, y) = |
                  | max{z, 0}, when y = 0
    """
    if y == 0:
        if m >= ((1 + eps) / (2 * beta)):
            return m - ((1 + eps) / (2 * beta))
        else:
            return m - (eps / (2 * beta))
    else:
        sol = m + ((1 - eps) / (2 * beta))
        if sol <= 1:
            return sol
        else:
            return m - (eps / (2 * beta))


@profile
def argminlastz(targets, eps, w, a_in, beta):
    m = np.dot(w, a_in)
    x = targets.shape[0]
    y = targets.shape[1]
    z = np.mat(np.zeros((x, y), dtype='float64'))
    for i in range(x):
        for j in range(y):
            z[i, j] = _minimizelast(targets[i, j], eps[i, j], m[i, j], beta)
    return z


@profile
def lambda_update(zl, w, a_in, beta):
    mpt = np.dot(w, a_in)
    return beta * (zl - mpt)
