import matplotlib.pyplot as plt
import numpy as np
import math
import scipy.stats as sts
from numpy.polynomial import Polynomial as P

import theoretical_prices as tp

norm_rv = sts.norm(loc=0, scale=1)

def N(x):
    # ''' кумулятивное нормальное распределение через полином'''
    # (a1, a2, a3, a4, a5) = (0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429)
    # ax = abs(x)
    # k = 1.0 / (1.0 + 0.2316419 * ax)
    # w = 1.0 - 1.0 / math.sqrt(2*math.pi) * math.exp(-ax*ax/2.) * (a1*k + a2*k*k + a3*pow(k, 3) + a4*pow(k, 4) + a5*pow(k, 5))
    # if x < 0:
    #     w = 1.0-w
    # return w
    return norm_rv.cdf(x)

def n(x):
   ''' плотность нормального распределения '''
   return norm_rv.pdf(x)


def get_intrinsic_value(opt_type, strike, spot_price):
  if opt_type == 'c':
    if strike <= spot_price:
      return spot_price - strike
    return 0
  if opt_type == 'p':
    if strike >= spot_price:
      return strike - spot_price
    return 0
 
def get_time_value(opt_type, strike, spot_price, price):
  return price - get_intrinsic_value(opt_type, strike, spot_price)

def BlackSholes_d1(spot_price, strike, t, r, v):
    """цена опциона на акцию по Блэку-Шоулзу"""
    return (math.log(spot_price / strike) + (r + v * v / 2.0) * t) / (
        v * math.sqrt(t)
    )

spot_price = 190
central_strike = 190  #+
opt_type = 'c'

r1 = 43.92987330
poly = P([-1.00000000, -0.38753731, -0.06145558, -0.01789372, -0.02134468, -0.00046039, 0.00486132, 0.00086628, 0.00103907]) # +
print(poly)
x = np.arange(spot_price-100, spot_price+100, 1)
R = 22.955656465450307

theor = tp.TheorPrice(opt_type, spot_price, x, R, poly)
print(theor)
iv = []

for strike in x:
    iv.append(get_intrinsic_value(opt_type=opt_type, strike=strike, spot_price=spot_price))
    # pp.append(Poly(strike, poly))

m = theor - iv
print (m)
# print(y)
plt.plot(x, iv, label='intrinsic value')
plt.plot(x, theor, label='poly')
plt.plot(x, m, label='m')
plt.grid(True)
plt.legend(loc='best', fontsize=12)
# plt.xticks(np.arange(150, 260, step=10))
plt.title(f'spot_price={spot_price}, opt_type={opt_type}, poly={poly}')
plt.show()