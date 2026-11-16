# Vector / RAG Patterns

## Overview

Embeddings retrieval for semantic search, RAG (Retrieval-Augmented Generation). Separate ingest from query; cite sources in answers.

## Patterns

### Ingest Pipeline

```python
async def ingest_document(doc: Document, chunk_size: int = 512, overlap: int = 50):
    chunks = chunk_text(doc.content, chunk_size, overlap)
    embeddings = await embedder.embed([c.text for c in chunks])

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        await vector_db.upsert(
            collection="documents",
            id=f"{doc.id}#chunk{i}",
            vector=emb,
            payload={
                "doc_id": doc.id,
                "chunk_index": i,
                "text": chunk.text,
                "title": doc.title,
                "source_url": doc.url,
            }
        )
```

### Query Pipeline (RAG)

```python
async def rag_query(question: str, top_k: int = 5) -> RAGResponse:
    # 1. Embed query
    query_emb = await embedder.embed([question])

    # 2. Retrieve
    results = await vector_db.query(
        collection="documents",
        vector=query_emb[0],
        top_k=top_k,
        with_payload=True,
    )

    # 3. Build context with citations
    context = "\n\n".join(
        f"[{i+1}] {r.payload['title']}: {r.payload['text'][:500]}"
        for i, r in enumerate(results)
    )

    # 4. Generate answer
    prompt = f"""Answer using only the context. Cite sources as [1], [2], etc.
Context:
{context}

Question: {question}
Answer:"""
    answer = await llm.generate(prompt)

    return RAGResponse(answer=answer, citations=[r.payload for r in results])
```

### Hybrid Search (Vector + Keyword)

```python
async def hybrid_search(query: str, top_k: int = 10) -> list[Result]:
    # Vector search
    query_emb = await embedder.embed([query])
    vector_results = await vector_db.query(collection="docs", vector=query_emb[0], top_k=top_k*2)

    # Keyword search (BM25)
    keyword_results = await search.search(index="docs", body={"query": {"match": {"content": query}}}, size=top_k*2)

    # Reciprocal Rank Fusion
    fused = rrf_fusion(vector_results, keyword_results, k=60)
    return fused[:top_k]
```

## Embedding Models

| Model | Dimensions | Max Tokens | Use Case |
|-------|------------|------------|----------|
| text-embedding-3-small | 1536 | 8191 | General, cost-effective |
| text-embedding-3-large | 3072 | 8191 | High quality |
| bge-large-en-v1.5 | 1024 | 512 | Open source, strong |
| e5-base-v2 | 768 | 512 | Multilingual |
| nomic-embed-text | 768 | 8192 | Long context |

## Chunking Strategies

| Strategy | Chunk Size | Overlap | Best For |
|----------|------------|---------|----------|
| Fixed | 512 tokens | 50 tokens | General |
| Semantic | Variable | N/A | Structured docs |
| Recursive | 1000 chars | 200 chars | Code, markdown |
| Sentence | 3-5 sentences | 1 sentence | Narrative |

## Vector DB Providers

| Provider | Type | Filtering | Hybrid |
|----------|------|-----------|--------|
| Pinecone | Managed | Metadata | ✓ |
| Weaviate | Managed / Self | GraphQL | ✓ |
| Qdrant | Self / Managed | Payload | ✓ |
| Chroma | Self / Managed | Metadata | ✓ |
| pgvector | PostgreSQL | SQL | ✓ |
| Upstash Vector | Serverless | Metadata | ✗ |

## References

- [RAG from scratch](https://github.com/langchain-ai/rag-from-scratch)
- [Vector DB benchmark](https://vector-db-benchmark.com/)
- [Chunking strategies](https://www.pinecone.io/learn/chunking-strategies/)
- [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)