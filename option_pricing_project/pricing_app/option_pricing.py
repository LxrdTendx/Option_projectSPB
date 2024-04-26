import math
from numpy.polynomial import Polynomial as P
import numpy as np
from scipy.stats import norm


def cnd(x):
    """кумулятивное нормальное распределение через полином. может быть портировано на C"""
    # (a1, a2, a3, a4, a5) = (0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429)
    poly = P([0, 0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429])
    ax = abs(x)
    k = 1.0 / (1.0 + 0.2316419 * ax)
    # w = 1.0 - 1.0 / math.sqrt(2*math.pi) * math.exp(-ax*ax/2.) * (a1*k + a2*k*k + a3*pow(k, 3) + a4*pow(k, 4) + a5*pow(k, 5))
    w = 1.0 - 1.0 / math.sqrt(2 * math.pi) * math.exp(-ax * ax / 2.0) * poly(k)
    if x < 0:
        w = 1.0 - w
    return w


def nd(x):
    """плотность нормального распределения через полином. может быть портирована на C"""
    return 1 / math.sqrt(2 * math.pi) * math.exp(-0.5 * x * x)


def N(x):
    """кумулятивное нормальное распределение, сumulative distribution function"""
    return norm.cdf(x)


def n(x):
    """плотность нормального распределения, probability density function"""
    return norm.pdf(x)


def BlackSholes(callPutFlag, spot_price, strike, t, r, v, min_premium=0.01):
    """цена опциона на акцию по Блэку-Шоулзу"""
    d1 = (np.emath.log(spot_price / strike) + (r + v * v / 2.0) * t) / (
        v * math.sqrt(t)
    )
    d2 = d1 - v * math.sqrt(t)
    if callPutFlag == "Call":
        price = spot_price * N(d1) - strike * math.exp(-r * t) * N(d2)
    else:
        price = strike * math.exp(-r * t) * N(-d2) - spot_price * N(-d1)
    return np.fmax(price, min_premium)


def Bachelier(callPutFlag, spot_price, strike, t, r, v, min_premium=0.01):
    """цена опциона на акцию по Башелье"""
    sqrt = math.sqrt(t)
    d1 = (spot_price - strike) / (v * sqrt)
    if callPutFlag == "Call":
        price = (
            spot_price * N(d1) - strike * math.exp(-r * t) * N(d1) + v * sqrt * n(d1)
        )
    else:
        price = (
            strike * math.exp(-r * t) * N(-d1) - spot_price * N(-d1) + v * sqrt * n(d1)
        )
    return np.fmax(price, min_premium)
