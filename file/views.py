from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse, Http404, FileResponse
import json, os, io, tempfile
from django.contrib import messages
from authentication.models import CustomUser
from .utils import load_pdf_file, load_docx_file, load_sitemap_file, load_youtube_file, text_to_speech, \
    extract_and_save_content, generate_sitemap, loads_urls, load_csv_file, load_xlsx_file
from .langchain_mistral import process_langchain_rag, process_langchain_rag_project
from .tasks import send_simple_download_message, send_simple_share_message
from django.utils.text import get_valid_filename
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
from .models import Document, ChatMessage, Project


def documents_accessible_to(user):
    if user.role == 'admin':
        return Document.objects.filter(organization=user.organization)
    return Document.objects.filter(
        Q(user=user) | Q(shared_with=user),
        organization=user.organization
    ).distinct()


def projects_accessible_to(user):
    if user.role == 'admin':
        return Project.objects.filter(organization=user.organization)
    return Project.objects.filter(
        Q(user=user) | Q(shared_with=user),
        organization=user.organization
    ).distinct()


@login_required
def upload_file(request):
    try:
        if request.method == 'POST':
            # Check file size
            file = request.FILES.get('file')
            if file and file.size > settings.MAX_REQUEST_BODY_SIZE:
                messages.error(request, 'File size exceeds maximum allowed limit.')
                return redirect('upload')

            # Process file
            if file:
                file_name = file.name
                file_type = file_name.split('.')[-1].lower()

                # Validate file type
                allowed_types = ['docx', 'pdf', 'csv', 'xlsx']
                if file_type not in allowed_types:
                    messages.error(request, f'Unsupported file type. Allowed types: {", ".join(allowed_types)}')
                    return redirect('upload')

                # Create document record
                doc = Document.objects.create(
                    file=file,
                    name=file_name,
                    user=request.user,
                    organization=request.user.organization,
                    type=file_type
                )

                # Process file content based on type
                content_loader = {
                    'docx': load_docx_file,
                    'pdf': load_pdf_file,
                    'csv': load_csv_file,
                    'xlsx': load_xlsx_file
                }

                try:
                    # Create a temporary file to store the content for processing
                    # This is needed because remote storages (like Azure) do not support absolute local paths
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
                        for chunk in file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name

                    try:
                        content = content_loader[file_type](temp_file_path)
                        doc.content = content
                        doc.save()
                        messages.success(request, 'File uploaded and processed successfully.')
                    finally:
                        # Ensure the temporary file is deleted from local disk
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                except Exception as e:
                    doc.delete()  # Clean up on failure
                    messages.error(request, f'Error processing file: {str(e)}')
                    return redirect('upload')
            else:
                messages.error(request, 'No file was uploaded.')
                return redirect('upload')

        # RBAC: Admin sees all org files, Member sees only their own or shared with them
        org_members = CustomUser.objects.filter(organization=request.user.organization)
        files = documents_accessible_to(request.user).order_by('-uploaded_at')

        context = {
            'files': files,
            'org_members': org_members,
            'max_file_size': settings.MAX_REQUEST_BODY_SIZE,
            'allowed_types': ['docx', 'pdf', 'csv', 'xlsx'],
            'url': request.build_absolute_uri()
        }
        return render(request, 'file2.html', context)

    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('upload')


@login_required
def delete_document(request, pk):
    if request.method == 'POST':
        doc = get_object_or_404(Document, pk=pk)
        if request.user == doc.user:
            doc.delete()
            messages.success(request, 'Chatbot document deleted successfully.')
        else:
            messages.error(request, 'You do not have permission to delete this document.')
    return redirect('upload')


@login_required
def delete_project(request, pk):
    if request.method == 'POST':
        proj = get_object_or_404(Project, pk=pk)
        if request.user == proj.user:
            proj.delete()
            messages.success(request, 'Project chatbot deleted successfully.')
        else:
            messages.error(request, 'You do not have permission to delete this project.')
    return redirect('new_project')


@login_required
def create_project(request):
    return render(request, 'create_project.html', {})


@login_required
def new_project(request):
    try:
        if request.method == 'POST':
            data_type = request.POST.get('data_type')
            project_name = request.POST.get('name')
            url_input = request.POST.get('url_input')

            if not data_type or not url_input or not project_name:
                messages.error(request, 'Please provide the project type, name, and URL.')
                return redirect('new_project')

            if data_type == 'sitemap':
                content = load_sitemap_file(url_input)
                Project.objects.create(name=project_name, user=request.user, organization=request.user.organization, is_sitemap=True, content=content,
                                       scope='sitemap')
            elif data_type == 'url':
                url_list = url_input.split(';')
                content = loads_urls(url_list)
                if content:
                    Project.objects.create(name=project_name, user=request.user, organization=request.user.organization, is_url=True, content=content,
                                           scope='url')
                else:
                    messages.error(request, 'Failed to fetch content from the URL.')
                    return redirect('new_project')
            elif data_type == 'youtube':
                content = load_youtube_file(url_input)
                Project.objects.create(name=project_name, user=request.user, organization=request.user.organization, is_youtube=True, content=content,
                                       scope='youtube')

            messages.success(request, 'Project created successfully')
            return redirect('new_project')

        projects = projects_accessible_to(request.user).order_by('-uploaded_at')
        context = {"projects": projects}
        return render(request, 'new_project.html', context)
    except Exception as e:
        messages.error(request, f'An unexpected error occurred in new_project: {str(e)}')
        return redirect('new_project')


@login_required
def list_files(request):
    org_members = CustomUser.objects.filter(organization=request.user.organization)
    files = documents_accessible_to(request.user).order_by('-uploaded_at')
    context = {
        'files': files,
        'org_members': org_members
    }
    return render(request, 'file2.html', context)


@login_required
def list_projects(request):
    org_members = CustomUser.objects.filter(organization=request.user.organization)
    projects = projects_accessible_to(request.user).order_by('-uploaded_at')
    context = {
        'projects': projects,
        'org_members': org_members
    }
    return render(request, 'my_projects.html', context)


@login_required
def filter_documents(request):
    try:
        file_name = request.POST['name']
    except KeyError:
        return HttpResponse('Invalid parameters', status=400)

    files = documents_accessible_to(request.user).filter(name=file_name).select_related('user')

    context = {
        'files': files,
        'org_members': CustomUser.objects.filter(organization=request.user.organization),
    }
    return render(request, 'file2.html', context)


@login_required
def my_documents(request):
    docs = documents_accessible_to(request.user)
    context = {
        'docs': docs,
        'org_members': CustomUser.objects.filter(organization=request.user.organization),
    }
    return render(request, 'my_documents.html', context)


@login_required
def download_file(request, pk):
    doc = get_object_or_404(documents_accessible_to(request.user), pk=pk)
    if not doc.file:
        raise Http404("File not found")

    try:
        return FileResponse(doc.file.open('rb'), as_attachment=True, filename=doc.name or os.path.basename(doc.file.name))
    except FileNotFoundError:
        raise Http404("File not found")


@login_required
def share_file(request, pk):
    if request.method == 'POST':
        # Ensure user has access to share this file (owner or admin)
        if request.user.role == 'admin':
            doc = get_object_or_404(Document, pk=pk, organization=request.user.organization)
        else:
            doc = get_object_or_404(Document, pk=pk, user=request.user)

        doc.is_shared = True
        doc.save()

        recipient_email = request.POST.get('recipient_email')
        if recipient_email:
            try:
                recipient = CustomUser.objects.get(email=recipient_email, organization=request.user.organization)
                doc.shared_with.add(recipient)

                context_data = {
                    'doc_name': doc.name or doc.file.name,
                    'file_url': request.build_absolute_uri(reverse('shared_file', args=[doc.pk])),
                    'sender_name': request.user.get_full_name().strip() or request.user.email,
                    'company_name': getattr(request.user.organization, 'name', ''),
                }
                context_json = json.dumps(context_data, cls=DjangoJSONEncoder)
                task = send_simple_share_message.delay(request.user.pk, recipient_email, context_json)
                return JsonResponse({'success': True, 'message': f'File shared with {recipient.get_full_name()}'})
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found in your organization'})
        else:
            return JsonResponse({'success': False, 'message': 'Recipient email is required'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def share_project(request, pk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        email = data.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Recipient email is required'}, status=400)

        if request.user.role == 'admin':
            project = get_object_or_404(Project, pk=pk, organization=request.user.organization)
        else:
            project = get_object_or_404(Project, pk=pk, user=request.user, organization=request.user.organization)

        # Restriction: Only share with users in the same organization
        try:
            user_to_share = CustomUser.objects.get(email=email, organization=request.user.organization)
            project.shared_with.add(user_to_share)
            return JsonResponse({'status': 'success'})
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found in your organization'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def all_shared_files(request):
    files = documents_accessible_to(request.user).filter(is_shared=True).select_related('user')
    context = {
        'files': files,
        'org_members': CustomUser.objects.filter(organization=request.user.organization),
    }
    return render(request, 'file2.html', context)


@login_required
def shared_file(request, pk):
    if request.method == 'GET':
        file = get_object_or_404(documents_accessible_to(request.user), pk=pk)
        context = {
            'file': file,
        }
        return render(request, 'shared_file.html', context)
    raise PermissionDenied


@login_required
def chatbot(request, uuid=None):
    if request.method == 'POST':
        query = request.POST.get('query')
        if not query:
            return HttpResponseBadRequest("Query is required")

        uuid = request.POST.get('document_uuid')
        doc = get_object_or_404(documents_accessible_to(request.user), uuid=uuid)

        chat_history = ChatMessage.objects.filter(document=doc, user=request.user).order_by('timestamp')
        user_message = ChatMessage.objects.create(document=doc, user=request.user, message=query, is_bot_response=False)
        try:
            response = process_langchain_rag(doc.pk, query, chat_history=chat_history)
        except ValueError as e:
            response = str(e)
        except Exception as e:
            response = f"An error occurred while processing your question. Please try again. ({str(e)[:200]})"
        bot_message = ChatMessage.objects.create(document=doc, user=request.user, message=response,
                                                 is_bot_response=True)

        context = {
            'document': doc,
            'chat_history': [user_message, bot_message]
        }

        if request.headers.get('HX-Request'):
            context['chat_history'] = [bot_message]
            return render(request, 'chatbot_response_partial.html', context)
        else:
            return render(request, 'chatbot.html', context=context)
    else:
        if uuid is None:
            return HttpResponse("Document not found", status=404)

        doc = get_object_or_404(documents_accessible_to(request.user), uuid=uuid)

        chat_history = ChatMessage.objects.filter(document=doc, user=request.user).order_by('timestamp')
        context = {
            'document': doc,
            'chat_history': chat_history
        }
        return render(request, 'chatbot.html', context=context)


@login_required
def proj_chatbot(request, uuid=None):
    if request.method == 'POST':
        query = request.POST.get('query')
        if not query:
            return HttpResponseBadRequest("Query is required")

        uuid = request.POST.get('project_uuid')
        proj = get_object_or_404(projects_accessible_to(request.user), uuid=uuid)

        chat_history = ChatMessage.objects.filter(project=proj, user=request.user).order_by('timestamp')
        user_message = ChatMessage.objects.create(project=proj, user=request.user, message=query, is_bot_response=False)
        try:
            response = process_langchain_rag_project(proj.pk, query, chat_history=chat_history)
        except ValueError as e:
            response = str(e)
        except Exception as e:
            response = f"An error occurred while processing your question. Please try again. ({str(e)[:200]})"
        bot_message = ChatMessage.objects.create(project=proj, user=request.user, message=response,
                                                 is_bot_response=True)

        context = {
            'project': proj,
            'chat_history': [user_message, bot_message]
        }

        if request.headers.get('HX-Request'):
            context['chat_history'] = [bot_message]
            return render(request, 'proj_chatbot_response_partial.html', context)
        else:
            return render(request, 'proj_chatbot.html', context=context)
    else:
        if uuid is None:
            return HttpResponse("Project not found", status=404)

        proj = get_object_or_404(projects_accessible_to(request.user), uuid=uuid)

        chat_history = ChatMessage.objects.filter(project=proj, user=request.user).order_by('timestamp')
        context = {
            'project': proj,
            'chat_history': chat_history
        }
        return render(request, 'proj_chatbot.html', context=context)


@login_required
def process_sitemap_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('sitemap')
        if not uploaded_file:
            messages.error(request, "Please upload a sitemap file.")
            return redirect('create_sitemap')

        try:
            file_name = get_valid_filename(os.path.basename(uploaded_file.name))
            project = Project.objects.create(
                user=request.user,
                organization=request.user.organization,
                scope='Auto-Gen of Sitemap',
                is_sitemap=True,
                name=file_name
            )

            sitemap_xml_content = b''.join(uploaded_file.chunks()).decode('utf-8')

            extract_and_save_content(sitemap_xml_content, project.pk)
            messages.success(request, 'Project created successfully')

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        return redirect('gen_sitemap')
    return render(request, 'create-sitemap.html', {})


@login_required
def gen_sitemap(request):
    if request.method == 'POST':
        url = request.POST.get('url_input')
        try:
            sitemap_path = generate_sitemap(url)
            if sitemap_path:
                return render(request, 'sitemap_result.html', {'success': True})
            else:
                return render(request, 'sitemap_result.html', {'success': False, 'error_message': 'Failed to generate or save the sitemap.'})
        except Exception as e:
            return render(request, 'sitemap_result.html', {'success': False, 'error_message': str(e)})

    return render(request, 'create-sitemap.html', {})


@login_required
def get_messages(request, uuid):
    doc = get_object_or_404(documents_accessible_to(request.user), uuid=uuid)
    chat_history = ChatMessage.objects.filter(document=doc, user=request.user).order_by('timestamp')
    response = {
        "messages": list(chat_history.values('message', 'timestamp', 'is_bot_response'))
    }
    return JsonResponse(response)


@login_required
def get_proj_messages(request, uuid):
    proj = get_object_or_404(projects_accessible_to(request.user), uuid=uuid)
    chat_history = ChatMessage.objects.filter(project=proj, user=request.user).order_by('timestamp')
    response = {
        "messages": list(chat_history.values('message', 'timestamp', 'is_bot_response'))
    }
    return JsonResponse(response)


@login_required
def stream_chat_audio(request, pk):
    message = get_object_or_404(ChatMessage, pk=pk, user=request.user)
    if not message.is_bot_response:
        raise Http404("Audio only available for bot responses")

    try:
        # Save to MEDIA_ROOT cache for proper Content-Length handling
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'chat_audio')
        os.makedirs(audio_dir, exist_ok=True)
        audio_file_path = os.path.join(audio_dir, f'message_{pk}.mp3')

        if not os.path.exists(audio_file_path):
            from gtts import gTTS
            tts = gTTS(text=message.message, lang='en')
            tts.save(audio_file_path)

        return FileResponse(open(audio_file_path, 'rb'), content_type='audio/mpeg')
    except Exception as e:
        return HttpResponse(f'An unexpected error occurred: {str(e)}', status=500)
