from django import forms

from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'users']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'users': forms.SelectMultiple(attrs={'class': 'form-control'})
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Plik jest zbyt duży. Maksymalny rozmiar to 10MB.")
        return file
