from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import Event
import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def upload_excel(request):
    """Страница загрузки Excel-файла с мероприятиями для администраторов."""
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['file']
            df = pd.read_excel(excel_file)
            events = []
            print("Столбцы в файле:", df.columns.tolist())
            for index, row in df.iterrows():
                event = Event(
                    protocol=row['Мероприятие'],
                    description=row.get('Описание', ''),
                    responsible_person=row['Ответственный'],
                    deadline=pd.to_datetime(row['Срок']).to_pydatetime(),
                )
                events.append(event)
            Event.objects.bulk_create(events)
            return redirect('admin:core_event_changelist')
    else:
        form = UploadFileForm()
        return render(request, 'admin/upload_excel.html', {'form': form})
