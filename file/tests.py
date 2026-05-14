from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document
from authentication.models import CustomUser

User = get_user_model()


class FileSharingAppTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            company_name='Test Co',
            personal_telephone='N/A',
            office_telephone='N/A',
            address='N/A',
        )
        self.client.login(email='test@example.com', password='testpassword')
        self.file = Document.objects.create(
            name='file.txt',
            user=self.user,
            file=SimpleUploadedFile('file.txt', b'test content'),
        )

    def test_upload_file_view(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file2.html')

        file_data = SimpleUploadedFile('file.txt', b'test content')
        response = self.client.post(reverse('upload'), {'file': file_data})

        self.assertEqual(response.status_code, 302)  # Check if the file upload redirects to 'files' page

    def test_list_files_view(self):
        response = self.client.get(reverse('files'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file2.html')
        self.assertContains(response, 'file.txt')

    def test_filter_documents_view(self):
        response = self.client.post(reverse('search_file'), {'company': 'testcompany', 'name': 'file.txt'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file2.html')
        self.assertContains(response, 'file.txt')

    def test_download_file_view(self):
        response = self.client.get(reverse('download', args=[self.file.pk]))
        self.assertEqual(response.status_code, 200)

    # def test_share_file_view(self):  # awaiting for email services so can configure the email settings. response =
    # self.client.post(reverse('share_file', args=[self.file.id]), {'recipient_email': 'test@example.com'})
    # self.assertEqual(response.status_code, 200)

    def test_all_shared_files_view(self):
        self.file.is_shared = True
        self.file.save()
        response = self.client.get(reverse('all_shared_files'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file2.html')
