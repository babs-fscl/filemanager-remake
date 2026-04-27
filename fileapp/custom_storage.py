from storages.backends.azure_storage import AzureStorage
import os

class AzureStaticStorage(AzureStorage):
    account_name = os.getenv('AZURE_ACCOUNT_NAME', 'dummy_azure_name_account')
    account_key = os.getenv('AZURE_ACCOUNT_KEY', 'dummy_azure_account_key')
    azure_container = os.getenv('AZURE_STATIC_CONTAINER', 'static')
    expiration_secs = None

class AzureMediaStorage(AzureStorage):
    account_name = os.getenv('AZURE_ACCOUNT_NAME', 'dummy_azure_name_account')
    account_key = os.getenv('AZURE_ACCOUNT_KEY', 'dummy_azure_account_key')
    azure_container = os.getenv('AZURE_MEDIA_CONTAINER', 'media')
    expiration_secs = None
