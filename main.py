# --------- Imports -------------
from fastapi import FastAPI
import logging
import inngest
from inngest import Function
from inngest import TriggerEvent
import inngest.fast_api
from inngest.experimental import ai
import uuid
import datetime
import os
from dotenv import load_dotenv
from data_loader import load_and_chunk_pdf, embed_texts
from vector_db import QdrantStorage
from custom_types import RAGQueryResult, RAGSearchResult, RAGUpsertResult, RAGChunkAndSrc
# ------- Code logic --------------
load_dotenv()

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
    serializer=inngest.PydanticSerializer(),
)

@inngest_client.create_function(
    fn_id= "RAG: Inngest PDF",
    trigger=inngest.TriggerEvent(event='rag/inngest_pdf') # type: ignore[arg-type]
)
async def inngest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context)-> RAGChunkAndSrc:
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)

        return RAGChunkAndSrc(chunk=chunks, source_id=source_id)


    def _upsert(chunks_and_src: RAGChunkAndSrc)-> RAGUpsertResult:
        chunks = chunks_and_src.chunks
        source_id = chunks_and_src.source_id
        vectors=embed_texts(chunks_and_src.chunks)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}: {i}")) for i in range(len(chunks))]
        payloads = [{"source_id": source_id, "text": chunks[i]} for i in range(len(chunks))]
        QdrantStorage().upsert(ids=ids, vectors=vectors, payloads=payloads)

        return RAGUpsertResult(ingested=len(chunks))

    chunks_and_src = await ctx.step.run("load_and_chunk_pdf", lambda: _load(ctx), output_type=RAGChunkAndSrc)
    ingested = await ctx.step.run("embedding-and-upsert", lambda: _upsert(chunks_and_src), output_type=RAGUpsertResult)
    return ingested.model_dump()

# ------ Serving app ---------
app = FastAPI()
inngest.fast_api.serve(app=app,client=inngest_client, functions=[inngest_pdf]) # type: ignore[arg-type]