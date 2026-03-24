import azure.functions as func
import logging
import os
import uuid
import re
import json
from datetime import datetime, timezone
from collections import defaultdict

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.data.tables import TableClient
from azure.core.exceptions import ResourceExistsError
from openai import AzureOpenAI

app = func.FunctionApp()

# ============================================================
# UTILITIES
# ============================================================

def extract_numbers(text):
    return [float(x.replace(",", "")) for x in re.findall(r"\d+(?:,\d+)?", text)]

def calculate_page_confidence(results):
    scores = defaultdict(int)
    for r in results:
        scores[r["page_number"]] += 1
    return dict(scores)

def compute_confidence(results_count, extracted_docs_count):
    if results_count == 0:
        return 0.0
    base = min(results_count / 12, 1.0)
    coverage = extracted_docs_count / results_count
    return round(min((base * 0.6 + coverage * 0.4), 1.0), 2)

def aggregate_numeric_fields(extracted_data):
    total = 0
    for doc in extracted_data.get("documents", []):
        for fact in doc.get("facts", []):
            try:
                total += float(str(fact.get("value", "")).replace(",", ""))
            except:
                pass
    return total

# ============================================================
# BLOB INGESTION
# ============================================================

@app.blob_trigger(
    arg_name="myblob",
    path="documents/{name}",
    connection="AzureWebJobsStorage"
)
def ingest_document(myblob: func.InputStream):

    logging.info(f"Processing blob: {myblob.name}")
    document_name = myblob.name.split("/")[-1].strip()

    doc_client = DocumentAnalysisClient(
        endpoint=os.environ["DOC_INTEL_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["DOC_INTEL_KEY"])
    )

    poller = doc_client.begin_analyze_document("prebuilt-layout", myblob)
    result = poller.result()

    openai_client = AzureOpenAI(
        api_key=os.environ["OPENAI_KEY"],
        api_version="2024-02-15-preview",
        azure_endpoint=os.environ["OPENAI_ENDPOINT"]
    )

    search_client = SearchClient(
        endpoint=os.environ["SEARCH_ENDPOINT"],
        index_name=os.environ["SEARCH_INDEX"],
        credential=AzureKeyCredential(os.environ["SEARCH_KEY"])
    )

    docs_to_upload = []
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    for page in result.pages:
        text = " ".join([line.content for line in page.lines])

        if not text.strip():
            continue

        embedding = openai_client.embeddings.create(
            model=os.environ["OPENAI_EMBEDDING_DEPLOYMENT"],
            input=text
        ).data[0].embedding

        docs_to_upload.append({
            "chunk_id": str(uuid.uuid4()),
            "document_name": document_name,
            "page_number": page.page_number,
            "content": text,
            "numbers": extract_numbers(text),
            "upload_date": current_time,
            "embedding": embedding
        })

    if docs_to_upload:
        search_client.upload_documents(docs_to_upload)
        logging.info(f"Uploaded {len(docs_to_upload)} chunks.")

# ============================================================
# ENTERPRISE Q&A (OPTIMIZED)
# ============================================================

@app.route(route="ask", methods=["POST"])
def ask_question(req: func.HttpRequest):

    try:
        body = req.get_json()
        question = body.get("question")
        document_filter = body.get("document_name")
    except:
        return func.HttpResponse("Invalid request", status_code=400)

    if not question:
        return func.HttpResponse("Question cannot be empty.", status_code=400)

    openai_client = AzureOpenAI(
        api_key=os.environ["OPENAI_KEY"],
        api_version="2024-02-15-preview",
        azure_endpoint=os.environ["OPENAI_ENDPOINT"]
    )

    search_client = SearchClient(
        endpoint=os.environ["SEARCH_ENDPOINT"],
        index_name=os.environ["SEARCH_INDEX"],
        credential=AzureKeyCredential(os.environ["SEARCH_KEY"])
    )

    # ========================================================
    # 1️⃣ Retrieval
    # ========================================================

    query_embedding = openai_client.embeddings.create(
        model=os.environ["OPENAI_EMBEDDING_DEPLOYMENT"],
        input=question
    ).data[0].embedding

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=12,
        fields="embedding"
    )

    search_kwargs = {
        "search_text": question,
        "vector_queries": [vector_query],
        "top": 12
    }

    if document_filter:
        safe_filter = document_filter.strip().replace("'", "''")
        search_kwargs["filter"] = f"document_name eq '{safe_filter}'"

    results = list(search_client.search(**search_kwargs))

    if not results:
        return func.HttpResponse(
            json.dumps({"answer": "No relevant documents found."}),
            mimetype="application/json"
        )

    documents_used = list(set([r["document_name"] for r in results]))
    page_confidence = calculate_page_confidence(results)

    # ========================================================
    # 2️⃣ Single Structured Extraction (ALL DOCS)
    # ========================================================

    combined_context = [
        {
            "document_name": r["document_name"],
            "page_number": r["page_number"],
            "content": r["content"]
        }
        for r in results
    ]

    extraction_prompt = f"""
    You are an enterprise document extraction engine.

    Extract structured facts relevant to the question.
    Group them by document.

    Return STRICT JSON:

    {{
      "documents": [
        {{
          "document_name": "...",
          "facts": [
            {{
              "field": "...",
              "value": "...",
              "evidence_page": ...
            }}
          ]
        }}
      ]
    }}

    Question:
    {question}

    Context:
    {json.dumps(combined_context, indent=2)}
    """

    extraction_response = openai_client.chat.completions.create(
        model=os.environ["OPENAI_GPT_DEPLOYMENT"],
        messages=[{"role": "user", "content": extraction_prompt}],
        temperature=0
    )

    try:
        content = extraction_response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        extracted_data = json.loads(content)
    except:
        extracted_data = {"documents": []}

    # ========================================================
    # 3️⃣ Deterministic Aggregation (Python)
    # ========================================================

    aggregated_total = aggregate_numeric_fields(extracted_data)

    # ========================================================
    # 4️⃣ Final Reasoning (ONE CALL)
    # ========================================================

    reasoning_prompt = f"""
    You are an enterprise reasoning engine.

    Use ONLY the structured data below.
    Do NOT invent information.

    Structured Data:
    {json.dumps(extracted_data, indent=2)}

    Computed Aggregated Total (if applicable):
    {aggregated_total}

    Question:
    {question}

    Provide final answer clearly.
    """

    final_response = openai_client.chat.completions.create(
        model=os.environ["OPENAI_GPT_DEPLOYMENT"],
        messages=[{"role": "user", "content": reasoning_prompt}],
        temperature=0
    )

    answer = final_response.choices[0].message.content.strip()

    # ========================================================
    # 5️⃣ Real Confidence (Data Driven)
    # ========================================================

    confidence = compute_confidence(
        results_count=len(results),
        extracted_docs_count=len(extracted_data.get("documents", []))
    )

    # ========================================================
    # 6️⃣ Audit Logging
    # ========================================================

    try:
        table_client = TableClient.from_connection_string(
            conn_str=os.environ["AzureWebJobsStorage"],
            table_name="AuditLogs"
        )

        try:
            table_client.create_table()
        except ResourceExistsError:
            pass

        table_client.create_entity({
            "PartitionKey": "Queries",
            "RowKey": str(uuid.uuid4()),
            "question": question,
            "answer": answer,
            "documents": ",".join(documents_used),
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "confidence": confidence
        })

    except Exception as e:
        logging.warning(f"Audit log failed: {str(e)}")

    return func.HttpResponse(json.dumps({
        "answer": answer,
        "mode": "enterprise_cross_document_v5_optimized",
        "source_documents": documents_used,
        "page_confidence": page_confidence,
        "confidence": confidence
    }, indent=2), mimetype="application/json")
