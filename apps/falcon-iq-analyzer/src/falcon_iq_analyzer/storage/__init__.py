from falcon_iq_analyzer.storage.base import StorageService
from falcon_iq_analyzer.storage.local_storage import LocalStorageService
from falcon_iq_analyzer.storage.s3_storage import S3StorageService


def create_storage_service() -> StorageService:
    """Create the appropriate storage service based on settings."""
    from falcon_iq_analyzer.config import settings

    if settings.storage_type == "s3":
        endpoint_url = None
        access_key_id = None
        secret_access_key = None

        if settings.r2_account_id:
            endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
            access_key_id = settings.r2_access_key_id
            secret_access_key = settings.r2_secret_access_key

        return S3StorageService(
            bucket_name=settings.s3_bucket_name,
            region=settings.aws_region,
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )
    return LocalStorageService(base_dir=settings.results_dir)
