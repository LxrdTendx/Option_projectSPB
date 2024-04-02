from django import forms

class OptionSeriesForm(forms.Form):
    central_strike = forms.FloatField(label='Центральный страйк')
    strikes_count = forms.IntegerField(label='Количество страйков')
    strike_step = forms.FloatField(label='Шаг страйка')
    # Дополните форму другими необходимыми полями