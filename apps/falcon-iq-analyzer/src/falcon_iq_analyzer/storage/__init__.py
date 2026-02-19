from falcon_iq_analyzer.storage.base import StorageService
from falcon_iq_analyzer.storage.local_storage import LocalStorageService
from falcon_iq_analyzer.storage.s3_storage import S3StorageService


def create_storage_service() -> StorageService:
    """Create the appropriate storage service based on settings."""
    from falcon_iq_analyzer.config import settings

    if settings.storage_type == "s3":
        return S3StorageService(
            bucket_name=settings.s3_bucket_name,
            region=settings.aws_region,
        )
    return LocalStorageService(base_dir=settings.results_dir)
