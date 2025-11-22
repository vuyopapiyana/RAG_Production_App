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
    return {"hello": "world"}

# ------ Serving app ---------
app = FastAPI()
inngest.fast_api.serve(app=app,client=inngest_client, functions=[inngest_pdf]) # type: ignore[arg-type]