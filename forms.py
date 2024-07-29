from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CartItem, Profile, Contact, FAQ, Review


class AddToCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        quantity = forms.IntegerField(min_value=1)
        fields = ['quantity']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }
