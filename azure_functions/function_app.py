"""
Azure Functions v2 Python Programming Model
Asynchronous Resume & Document Processing Workflow

This is an OPTIONAL serverless component designed to offload long-running document
processing, text extraction, and resume structuring without impacting core FastAPI services.
It runs locally via Azure Functions Core Tools (100% free) or in Azure Functions Consumption Plan
(1 Million executions + 400,000 GB-seconds per month free).
"""

import os
import json
import base64
import logging
import tempfile
import azure.functions as func

# Setup logger
logger = logging.getLogger("azure_functions_resume_processor")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Reusable Extraction Prompts (aligned with backend/fastapi_app/services/parser_service.py)
STAGE1_PROMPT = """
You are a highly precise resume parser. Extract information from the raw resume text provided below.
Return ONLY valid JSON matching this schema:
{
  "contact_info": {
    "name": "Full name",
    "email": "Email address",
    "phone": "Phone number",
    "location": "City, State or Country",
    "website": "Personal portfolio/website URL or null",
    "linkedin": "LinkedIn profile link or null",
    "github": "GitHub link or null"
  },
  "skills": ["Skill 1", "Skill 2"],
  "experiences": [
    {
      "company": "Company Name",
      "role": "Job Title",
      "location": "City, State",
      "start_date": "Start Date",
      "end_date": "End Date",
      "description_bullets": ["Bullet 1", "Bullet 2"],
      "technologies": ["Tech 1", "Tech 2"]
    }
  ]
}

Raw Resume Text:
---
{raw_text}
---
"""

def call_llm(prompt: str) -> str:
    """
    Lightweight, provider-agnostic LLM caller using LiteLLM.
    Supports Gemini (default), Azure OpenAI, and Azure Foundry.
    """
    from litellm import completion

    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()

    if provider in ["azure", "azure_openai"]:
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        model = f"azure/{deployment}"
        api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        api_base = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            api_base=api_base,
            api_version=api_version,
            timeout=45
        )
    elif provider in ["foundry", "azure_foundry"]:
        model_name = os.environ.get("AZURE_FOUNDRY_MODEL", "Phi-4")
        model = f"openai/{model_name}"
        api_key = os.environ.get("AZURE_FOUNDRY_API_KEY", "")
        api_base = os.environ.get("AZURE_FOUNDRY_ENDPOINT", "")
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            api_base=api_base,
            timeout=45
        )
    else:
        # Default: Gemini
        model = os.environ.get("LLM_MODEL", "gemini/gemini-2.5-flash")
        api_key = os.environ.get("GEMINI_API_KEY", "")
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            timeout=45
        )

    return response.choices[0].message.content


@app.route(route="process_resume", methods=["POST"])
def process_resume_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger: Asynchronously processes resume text or base64 file payloads.
    URL: POST http://localhost:7071/api/process_resume
    """
    logger.info("Processing HTTP resume parsing request.")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body. Please provide a JSON request."}),
            status_code=400,
            mimetype="application/json"
        )

    raw_text = req_body.get("raw_text")
    base64_data = req_body.get("file_base64")
    file_type = req_body.get("file_type", "pdf").lower()

    if not raw_text and not base64_data:
        return func.HttpResponse(
            json.dumps({"error": "Must provide either 'raw_text' or 'file_base64' in payload."}),
            status_code=400,
            mimetype="application/json"
        )

    # If base64 file provided, extract raw text
    if base64_data:
        try:
            file_bytes = base64.b64decode(base64_data)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            if file_type == "pdf":
                import fitz
                doc = fitz.open(tmp_path)
                pages = [page.get_text() for page in doc]
                raw_text = "\n".join(pages)
            elif file_type in ["docx", "doc"]:
                from docx import Document
                doc = Document(tmp_path)
                raw_text = "\n".join([p.text for p in doc.paragraphs])
            else:
                raw_text = file_bytes.decode("utf-8", errors="ignore")

            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as fe:
            logger.error(f"Failed to extract text from base64 document: {fe}")
            return func.HttpResponse(
                json.dumps({"error": f"Document extraction failed: {str(fe)}"}),
                status_code=500,
                mimetype="application/json"
            )

    # Run extraction via LLM
    try:
        prompt = STAGE1_PROMPT.format(raw_text=raw_text[:12000])
        llm_output = call_llm(prompt)

        # Clean JSON markdown fences if returned
        cleaned = llm_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        parsed_data = json.loads(cleaned.strip())

        return func.HttpResponse(
            json.dumps({"status": "success", "data": parsed_data}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as le:
        logger.error(f"LLM extraction failure: {le}")
        return func.HttpResponse(
            json.dumps({"error": f"LLM parsing failed: {str(le)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.queue_trigger(arg_name="msg", queue_name="resume-processing-queue", connection="AzureWebJobsStorage")
def process_resume_queue(msg: func.QueueMessage) -> None:
    """
    Queue Trigger: Processes queued resume tasks from Azure Storage Queue / Azurite emulator.
    Provides decoupled asynchronous background worker processing for high-volume scenarios.
    """
    body = msg.get_body().decode("utf-8")
    logger.info(f"Received queue item from resume-processing-queue: {msg.id}")

    try:
        payload = json.loads(body)
        user_id = payload.get("user_id", "unknown")
        raw_text = payload.get("raw_text", "")

        if raw_text:
            prompt = STAGE1_PROMPT.format(raw_text=raw_text[:12000])
            structured_result = call_llm(prompt)
            logger.info(f"Asynchronous queue processing complete for user '{user_id}'. Output length: {len(structured_result)}")
    except Exception as qe:
        logger.error(f"Failed processing queue message {msg.id}: {qe}")
        raise qe
