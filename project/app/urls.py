from django.urls import path
from .views import *

# кастомные урлы для приложения
urlpatterns = [
    path("merge_documents/<int:fos_id>", merge_documents, name="merge_documents")
]
