from django import forms


class UploadFileForm(forms.Form):
    """Форма для загрузки Excel файлов с мероприятиями."""
    file = forms.FileField(label='Выберите Excel-файл')
