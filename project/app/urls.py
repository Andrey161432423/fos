from django.urls import path
from .views import *

# кастомные урлы для приложения
urlpatterns = [
    path("merge_documents/<int:fos_id>", merge_documents, name="merge_documents"),
    path('export-fos', export_fos, name='export_fos'),
    path('export-disciplines', export_disciplines, name='export_disciplines')
]
