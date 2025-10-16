from django import forms
from .models import ProductImage, ProductVariant, InventoryLog

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True 

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': MultiFileInput(attrs={'multiple': True}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['variant_name', 'value', 'price_difference']
        widgets = {
            'variant_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Size'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. XL'}),
            'price_difference': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class InventoryLogForm(forms.ModelForm):
    class Meta:
        model = InventoryLog
        fields = ['change_type', 'quantity', 'remarks']
        widgets = {
            'change_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }