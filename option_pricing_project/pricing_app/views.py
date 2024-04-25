import matplotlib
matplotlib.use('Agg')  # Установка бэкенда
import matplotlib.pyplot as plt
import numpy as np
import math
import scipy.stats as sts
from numpy.polynomial import Polynomial as P
import io
import base64
from django.shortcuts import render
from .forms import OptionSeriesForm
from . import theoretical_prices as tp

norm_rv = sts.norm(loc=0, scale=1)

def create_plot(central_strike, poly):
    spot_price = 190
    opt_type = 'c'
    x = np.arange(spot_price - 100, spot_price + 100, 1)
    R = 22.955656465450307
    theor = tp.TheorPrice(opt_type, spot_price, x, R, poly)
    iv = [max(spot_price - strike if opt_type == 'c' else strike - spot_price, 0) for strike in x]
    m = theor - iv

    plt.figure()
    plt.plot(x, iv, label='Intrinsic Value')
    plt.plot(x, theor, label='Theoretical Price')
    plt.plot(x, m, label='Market Price')
    plt.grid(True)
    plt.legend(loc='best')
    plt.title(f'Spot Price={spot_price}, Option Type={opt_type}, Poly={poly}')
    plt.xlabel('Strike')
    plt.ylabel('Price')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def index(request):
    form = OptionSeriesForm(request.POST or None)
    data = None
    if request.method == 'POST' and form.is_valid():
        central_strike = form.cleaned_data['central_strike']
        polynomial_coefficients = form.cleaned_data['polynomial_coefficients']
        poly = P([float(x) for x in polynomial_coefficients.split(',')])
        data = create_plot(central_strike, poly)

    return render(request, 'index.html', {'form': form, 'data': data})
