from django import forms


def validate_not_empty(value):
    if value == '':
        raise forms.ValidationError(
            'Заполните форму',
            params={'value': value},
        )
