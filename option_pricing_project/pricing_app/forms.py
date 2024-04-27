from django import forms

class FileUploadForm(forms.Form):
    json_file = forms.FileField(label='')

class OptionSelectionForm(forms.Form):
    option_id = forms.ChoiceField(label='', choices=[])
    strike_step = forms.FloatField(label='Значение шага страйков', required=False)
    cnt = forms.IntegerField(label='Значение количества страйков', required=False)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])
        super(OptionSelectionForm, self).__init__(*args, **kwargs)
        self.fields['option_id'].choices = choices
        if choices:
            self.fields['option_id'].widget.attrs.update({'onchange': 'updateFormFields()'})

