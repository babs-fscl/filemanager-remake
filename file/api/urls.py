from django.urls import path
from .views import FileUploadView, FileDownloadView, FileListView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('download/<str:file_name>/', FileDownloadView.as_view(), name='file-download'),
    path('files/', FileListView.as_view(), name='file-list'),
]
