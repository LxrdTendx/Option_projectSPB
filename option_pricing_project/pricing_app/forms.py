from django import forms

class FileUploadForm(forms.Form):
    json_file = forms.FileField(label='Загрузите JSON файл')

class OptionSelectionForm(forms.Form):
    option_id = forms.ChoiceField(label='Выберите опцион', choices=[])
    strike_step = forms.FloatField(label='Шаг страйка', required=False)
    cnt = forms.IntegerField(label='Количество', required=False)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])
        super(OptionSelectionForm, self).__init__(*args, **kwargs)
        self.fields['option_id'].choices = choices
        if choices:
            self.fields['option_id'].widget.attrs.update({'onchange': 'updateFormFields()'})

