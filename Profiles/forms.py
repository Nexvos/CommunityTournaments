from django import forms


class NicknameForm(forms.Form):
    nickname = forms.CharField(max_length=20)


class LocationForm(forms.Form):
    location = forms.CharField(max_length=120)


class ImageForm(forms.Form):
    picture_id = forms.IntegerField(required=True)


# TODO: Form validation for colours etc.
class ColourForm(forms.Form):
    colour_string = forms.CharField(max_length=7)
