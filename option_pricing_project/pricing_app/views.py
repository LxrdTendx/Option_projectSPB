from django.shortcuts import render
from django.shortcuts import render
from .forms import OptionSeriesForm
from . import theoretical_prices
import matplotlib.pyplot as plt
import io
import urllib, base64
import matplotlib.pyplot as plt
import io
import base64
from . import theoretical_prices
from . import option_pricing
import numpy as np


def plot_graph(data):
    plt.figure()
    plt.plot(data)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri




def option_series_view(request):
    if request.method == 'POST':
        form = OptionSeriesForm(request.POST)
        if form.is_valid():
            central_strike = form.cleaned_data['central_strike']
            strikes_count = form.cleaned_data['strikes_count']
            strike_step = form.cleaned_data['strike_step']
            # Выполните необходимые расчеты и генерацию графика
            # Предположим, что функция generate_graph возвращает URL сгенерированного изображения
            graph_url = generate_graph(central_strike, strikes_count, strike_step)
            return render(request, 'results.html', {'form': form, 'graph_url': graph_url})
    else:
        form = OptionSeriesForm()
    return render(request, 'index.html', {'form': form})



def generate_graph(central_strike, strikes_count, strike_step, opt_type='c', spot_price=10000):
    # Инициализация входных данных для расчета
    strikes = np.linspace(central_strike - strike_step * strikes_count, central_strike + strike_step * strikes_count,
                          2 * strikes_count + 1)
    premiums = option_pricing.BlackSholes(opt_type, spot_price, strikes, 0.5, 0.05,
                                          0.2)  # Пример использования BlackSholes для генерации премий

    # Используем функции из кода для расчета теоретических цен
    r = theoretical_prices.CalcR_v2(opt_type, strikes, premiums, spot_price)
    _, _, poly, _ = theoretical_prices.CalcTheorParams2(opt_type, strikes, premiums, spot_price, r)

    # Генерация данных для графика
    values = theoretical_prices.TheorPrice(opt_type, spot_price, strikes, r, poly)
    values = np.real(values)
    print("Values:", values)
    # Построение графика
    plt.figure()
    plt.plot(strikes, values, label='Theoretical Price')
    plt.scatter(strikes, premiums, color='red', label='Market Price')  # Демонстрация рыночных цен для сравнения
    plt.legend()
    plt.xlabel('Strike Price')
    plt.ylabel('Option Price')

    # Сохранение и возвращение изображения
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return image_url