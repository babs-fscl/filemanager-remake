from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
                  path('home/', views.upload_file, name='upload'),
                  path('download/<int:pk>/', views.download_file, name='download'),
                  path('share/<int:pk>/', views.share_file, name='share_file'),
                  path('share-project/<int:pk>/', views.share_project, name='share_project'),
                  path('shared_files/', views.all_shared_files, name='all_shared_files'),
                  path('search/', views.filter_documents, name='search_file'),
                  path('files/', views.list_files, name='files'),
                  path('projects/', views.create_project, name='create_project'),
                  path('documents/', views.my_documents, name='my_documents'),
                  path('shared/<int:pk>/', views.shared_file, name='shared_file'),
                  # path('analyze/<int:pk>/', views.analyze, name='analyze'),
                  path('chat/<uuid:uuid>/', views.chatbot, name='chatbot'),
                  path('get-messages/<uuid:uuid>/', views.get_messages, name='messages'),
                  path('get-proj-messages/<uuid:uuid>/', views.get_proj_messages, name='proj_messages'),
                  path('create-project/', views.new_project, name='new_project'),
                  path('project-chat/<uuid:uuid>/', views.proj_chatbot, name='proj_chatbot'),
                  path('audio/<int:pk>/', views.stream_chat_audio, name='stream_chat_audio'),
                  path('create-sitemap/', views.process_sitemap_view, name='create_sitemap'),
                  path('generate-sitemap/', views.gen_sitemap, name='gen_sitemap'),
                  path('delete-document/<int:pk>/', views.delete_document, name='delete_document'),
                  path('delete-project/<int:pk>/', views.delete_project, name='delete_project'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
