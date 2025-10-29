from django import forms
from vendor.models import Vendor

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['image', 'store_name', 'description', 'country']
