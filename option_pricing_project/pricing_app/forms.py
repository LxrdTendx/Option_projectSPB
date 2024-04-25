from django import forms

class OptionSeriesForm(forms.Form):
    central_strike = forms.FloatField(label='Центральный страйк')
    polynomial_coefficients = forms.CharField(label='Коэффициенты полинома')
