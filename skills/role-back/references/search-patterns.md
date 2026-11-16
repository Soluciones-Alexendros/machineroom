# Search Patterns

## Overview

Full-text and filtered retrieval. Index as derived data; source of truth stays in primary DB.

## Patterns

### Basic Full-Text Search

```python
# Index on write
async def index_document(doc: Document):
    await search.index(
        index="documents",
        id=doc.id,
        body={
            "title": doc.title,
            "content": doc.content,
            "tags": doc.tags,
            "created_at": doc.created_at.isoformat(),
        },
    )


# Search
async def search_documents(query: str, filters: dict = None) -> SearchResults:
    body = {
        "query": {
            "bool": {
                "must": [{"multi_match": {"query": query, "fields": ["title^2", "content"]}}],
                "filter": [{"term": {k: v}} for k, v in (filters or {}).items()],
            }
        },
        "highlight": {"fields": {"title": {}, "content": {}}},
    }
    return await search.search(index="documents", body=body)
```

### Filtered / Faceted Search

```python
async def search_with_facets(query: str, filters: dict, facets: list[str]) -> SearchResults:
    body = {
        "query": {...},
        "aggs": {facet: {"terms": {"field": facet, "size": 20}} for facet in facets},
    }
    return await search.search(index="documents", body=body)
```

### Autocomplete / Suggest

```python
async def suggest(prefix: str) -> list[str]:
    body = {
        "suggest": {
            "title_suggest": {
                "prefix": prefix,
                "completion": {"field": "title_suggest", "size": 10},
            }
        }
    }
    return await search.search(index="documents", body=body)
```

### Sync Strategy

| Strategy | When | Consistency |
|----------|------|-------------|
| Synchronous | Critical, low volume | Strong |
| Async (queue) | High volume | Eventual (ms–s) |
| Batch (cron) | Analytics, large datasets | Hours |

```python
# Async indexing via queue
async def on_document_change(doc: Document, action: str):
    if action == "delete":
        await queue.enqueue("search:delete", {"index": "documents", "id": doc.id})
    else:
        await queue.enqueue("search:index", {"index": "documents", "id": doc.id, "action": action})
```

## Schema Design

```json
{
  "mappings": {
    "properties": {
      "title": {"type": "text", "analyzer": "standard", "fields": {"suggest": {"type": "completion"}}},
      "content": {"type": "text", "analyzer": "standard"},
      "tags": {"type": "keyword"},
      "category": {"type": "keyword"},
      "created_at": {"type": "date"},
      "author_id": {"type": "keyword"}
    }
  }
}
```

## Providers

| Provider | Type | Features |
|----------|------|----------|
| Elasticsearch / OpenSearch | Full-text, analytics | SQL, aggregations, ML |
| Meilisearch | Fast, typo-tolerant | Facets, synonyms |
| Typesense | Fast, in-memory | Facets, geo |
| Algolia | Hosted, managed | InstantSearch UI |
| PostgreSQL tsvector | Built-in | Simple, no extra infra |

## References

- [Elasticsearch Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Meilisearch](https://www.meilisearch.com/docs/)
- [PostgreSQL Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)