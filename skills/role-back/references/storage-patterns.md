# Storage Patterns

## Overview

Object/blob storage for uploads, exports, static assets. Signed URLs; never trust client Content-Type alone.

## Patterns

### Direct Upload (Signed URL)

```python
# Server generates signed PUT URL
async def get_upload_url(filename: str, content_type: str, max_size: int) -> str:
    key = f"uploads/{uuid4()}/{sanitize(filename)}"
    url = await storage.presigned_put(key, content_type, max_size, expires=3600)
    return {"url": url, "key": key, "headers": {"Content-Type": content_type}}

# Client uploads directly to storage
# Server verifies on webhook/callback
```

### Download with Signed URL

```python
async def get_download_url(key: str, filename: str | None = None) -> str:
    disposition = f'attachment; filename="{filename or key.split("/")[-1]}"'
    return await storage.presigned_get(key, expires=3600, response_headers={"Content-Disposition": disposition})
```

### Multipart Upload (Large Files)

```python
async def initiate_multipart(key: str, content_type: str) -> str:
    return await storage.create_multipart_upload(key, content_type)

async def sign_part(key: str, upload_id: str, part_number: int) -> str:
    return await storage.presigned_upload_part(key, upload_id, part_number, expires=3600)

async def complete_multipart(key: str, upload_id: str, parts: list[Part]) -> Object:
    return await storage.complete_multipart_upload(key, upload_id, parts)
```

### Export / Batch Download

```python
async def create_export(job_id: str, query: Query) -> str:
    key = f"exports/{job_id}.csv"
    # Stream query results to storage
    await storage.stream_upload(key, stream_query_results(query))
    return await get_download_url(key, f"export-{job_id}.csv")
```

## Content-Type Handling

```python
# ALWAYS validate on server side
ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
    "text/csv", "application/json",
}

async def verify_upload(key: str, expected_type: str) -> bool:
    obj = await storage.head(key)
    return obj.content_type in ALLOWED_TYPES and obj.content_type == expected_type
```

## Lifecycle Policies

| Prefix | Retention | Transition |
|--------|-----------|------------|
| uploads/ | 7 days | Delete incomplete |
| exports/ | 30 days | Glacier after 7d |
| static/ | Permanent | CDN cached |
| backups/ | 1 year | Glacier after 30d |

## Providers

| Provider | SDK | Signed URLs | Multipart |
|----------|-----|-------------|-----------|
| AWS S3 | boto3 | ✓ | ✓ |
| GCS | google-cloud-storage | ✓ | ✓ |
| Azure Blob | azure-storage-blob | ✓ | ✓ |
| Upstash S3-compatible | boto3 | ✓ | ✓ |
| Cloudflare R2 | boto3 | ✓ | ✓ |

## References

- [AWS S3 Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html)
- [S3 Multipart Upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)
- [Content-Type security](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)