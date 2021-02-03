from django import forms
from .models import Vlan

# Los Formularios Simples no trabajan con un modelo en particular
class VlanForm(forms.Form):
    
    ssh_user = forms.CharField(
        max_length=30,
        required = True
    )
    
    ssh_pass = forms.CharField(
        max_length=30,
        required = True
    )

# Creamos un formulario que dependa en un modelo 'Model Form'
class NewVlanForm(forms.ModelForm):
    class Meta:
        model = Vlan
        fields = (
            'name',
            'network',
            'mask',
            'number',
            'interfaces'   
        )

        # Si queremos personalizar un campo de un formulario debemos utilizar widgets
        widgets = {
            'interfaces': forms.CheckboxSelectMultiple()
        }