import matplotlib
matplotlib.use('Agg')  # Установка бэкенда
import matplotlib.pyplot as plt
import numpy as np
import math
import scipy.stats as sts
from numpy.polynomial import Polynomial as P
import io
import base64
from . import theoretical_prices as tp
from django.shortcuts import render
from .forms import FileUploadForm, OptionSelectionForm
import json
from django.http import JsonResponse


norm_rv = sts.norm(loc=0, scale=1)


def get_option_data(request, id):
    json_data = request.session.get('json_data', {})
    selected_option = next((item for item in json_data['group'] if item['idOptionGroupParams'] == int(id)), None)
    if selected_option:
        return JsonResponse({
            'spot_price': selected_option['spot_price'],
            'type': selected_option['type'],
            'coef': selected_option['coef'],
            'r': selected_option['r'],
            'external_strikes': selected_option['external_strike'],
            'count': selected_option['count'],
            'step': selected_option['step']
        })
    else:
        return JsonResponse({'error': 'Option not found'}, status=404)

def create_plot(strike_step, cnt, spot_price, opt_type, coef, r, external_strikes):

    # spot_price = 16
    # opt_type = 'c'
    x = np.arange(spot_price-10, spot_price+10, 1)
    poly = P(coef)
    R = r
    # external_strikes = [8.75, 9, 9.25, 9.5, 9.75, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 15.5, 16, 16.5,
    #                     17, 17.5, 18, 18.5, 19, 19.5, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]


    theor = tp.TheorPrice(opt_type, spot_price, x, R, poly)
    iv = [max(spot_price - strike if opt_type == 'Call' else strike - spot_price, 0) for strike in x]
    m = theor - iv

    plt.plot(x, iv, label='intrinsic value')
    plt.plot(x, theor, label='poly')
    plt.plot(x, m, label='m')

    left_bound = spot_price - (cnt // 2) * strike_step
    right_bound = spot_price + (cnt // 2) * strike_step

    # Добавление вертикальных линий и закрашивание промежутка
    for i in range(1, cnt // 2 + 1):
        plt.axvline(x=spot_price + i * strike_step, color='red', linestyle='--')
        plt.axvline(x=spot_price - i * strike_step, color='red', linestyle='--')

    plt.axvspan(left_bound, right_bound, color='red', alpha=0.1)  # Прозрачное красное закрашивание

    plt.grid(True, axis='x')
    plt.legend(loc='best', fontsize=12)
    plt.axvline(x=spot_price, color='red')
    plt.xticks(np.unique(np.concatenate((external_strikes, x))),
               rotation=90)  # Adjusting tick locations and adding rotation for clarity
    plt.title(f'Spot Price={spot_price}, Option Type={opt_type}, Polynomial={poly}')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')


def index(request):
    file_form = FileUploadForm()
    options_form = None
    graph_data = None
    selected_data = None  # Для хранения выбранных данных

    if request.method == 'POST':
        if 'json_file' in request.FILES:
            file_form = FileUploadForm(request.POST, request.FILES)
            if file_form.is_valid():
                json_file = request.FILES['json_file']
                json_data = json.load(json_file)
                choices = [(item['idOptionGroupParams'], item['idOptionGroupParams']) for item in json_data['group']]
                initial_option = json_data['group'][0]
                options_form = OptionSelectionForm(initial={
                    'option_id': initial_option['idOptionGroupParams'],
                    'strike_step': initial_option.get('step', 1),
                    'cnt': initial_option.get('count', 10)
                }, choices=choices)
                request.session['json_data'] = json_data
                return render(request, 'index.html', {'file_form': file_form, 'options_form': options_form})

        elif 'option_id' in request.POST:
            json_data = request.session['json_data']
            selected_id = int(request.POST['option_id'])
            selected_option = next(item for item in json_data['group'] if item['idOptionGroupParams'] == selected_id)
            spot_price = selected_option['spot_price']
            opt_type = selected_option['type']
            coef = selected_option['coef']
            r = selected_option['r']
            external_strikes = selected_option['external_strike']
            cnt = int(request.POST.get('cnt', selected_option.get('count', 10)))
            strike_step = float(request.POST.get('strike_step', selected_option.get('step', 1)))

            graph_data = create_plot(strike_step, cnt, spot_price, opt_type, coef, r, external_strikes)
            selected_data = {
                'spot_price': spot_price,
                'type': opt_type,
                'coef': coef,
                'r': r,
                'external_strikes': external_strikes,
                'count': cnt,
                'step': strike_step
            }
            options_form = OptionSelectionForm(request.POST, choices=[(item['idOptionGroupParams'], item['idOptionGroupParams']) for item in json_data['group']])
            return render(request, 'index.html', {'options_form': options_form, 'graph_data': graph_data, 'selected_data': selected_data, 'file_form': file_form})

    return render(request, 'index.html', {'file_form': file_form, 'options_form': options_form, 'graph_data': graph_data})