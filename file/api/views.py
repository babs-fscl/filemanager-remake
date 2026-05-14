from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.http import FileResponse
from django.utils.text import get_valid_filename
import os
from ..models import Document


def accessible_documents_for(user):
    if user.role == 'admin':
        return Document.objects.filter(organization=user.organization)
    return Document.objects.filter(
        Q(user=user) | Q(shared_with=user),
        organization=user.organization
    ).distinct()


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            safe_name = get_valid_filename(os.path.basename(uploaded_file.name))
            file_type = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
            doc = Document.objects.create(
                file=uploaded_file,
                user=request.user,
                organization=request.user.organization,
                name=safe_name,
                type=file_type[:7],
            )
            return Response({
                'message': 'File uploaded successfully',
                'id': doc.pk,
                'name': doc.name,
            }, status=status.HTTP_201_CREATED)
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_name, *args, **kwargs):
        doc = accessible_documents_for(request.user).filter(name=file_name).order_by('-uploaded_at').first()

        if not doc or not doc.file:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            return FileResponse(doc.file.open('rb'), as_attachment=True, filename=doc.name or os.path.basename(doc.file.name))
        except FileNotFoundError:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


class FileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        file_names = list(
            accessible_documents_for(request.user)
            .order_by('-uploaded_at')
            .values_list('name', flat=True)
        )
        return Response({'file_names': file_names}, status=status.HTTP_200_OK)
