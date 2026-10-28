# ⚡ Optional Azure Functions Asynchronous Document Processor

This directory contains an **optional, decoupled serverless worker** built using the Azure Functions Python v2 model. It provides asynchronous and HTTP-triggered document processing pipelines for CareerOS.

---

## 🎯 Architecture Overview

```
               [FastAPI Backend / Client]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    (Direct HTTP Trigger)      (Asynchronous Queue)
  POST /api/process_resume      Azure Storage Queue:
             │                 "resume-processing-queue"
             │                           │
             ▼                           ▼
   [Azure Function HTTP]       [Azure Function Queue]
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    LLM Parser Call
           (Gemini / Azure OpenAI / Foundry)
                           │
                           ▼
               Structured Resume JSON
```

- **Non-Breaking**: The main FastAPI application (`backend/fastapi_app`) remains 100% self-contained and fully functional without Azure Functions.
- **Enterprise Decoupling**: For high-volume resume parsing workloads, document parsing can be queued into Azure Storage Queues or executed via serverless HTTP invocations to prevent blocking FastAPI worker threads.
- **Provider Agnostic**: Reuses LiteLLM for routing prompts to **Google Gemini** (free tier default), **Azure OpenAI**, or **Microsoft Azure AI Foundry**.

---

## 💰 Free-Tier & Pricing Verification

Before deploying any cloud resources, review the official Microsoft Azure pricing details:

1. **Azure Functions Consumption Plan Free Allowance**:
   - **Executions**: First **1,000,000 executions** are free every month per Azure subscription.
   - **Resource Consumption**: First **400,000 GB-seconds** of execution time are free every month.
   - Official Documentation: [Azure Functions Pricing](https://azure.microsoft.com/en-us/pricing/details/functions/)
2. **Local Development is 100% Free**:
   - Local testing uses the open-source **Azure Functions Core Tools** and **Azurite Storage Emulator**.
   - No Azure account, credit card, or active subscription is needed for local development.

---

## 🛠 Local Development & Testing Instructions

### Prerequisites

1. **Azure Functions Core Tools v4**:
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```
2. **Azurite Storage Emulator (Optional, for Queue Trigger)**:
   ```bash
   npm install -g azurite
   # Run local storage emulator
   azurite
   ```

### Setup Steps

1. **Configure Environment Variables**:
   Copy the example settings:
   ```bash
   cd azure_functions
   # Linux / macOS / Git Bash:
   cp local.settings.json.example local.settings.json

   # Windows PowerShell:
   Copy-Item local.settings.json.example local.settings.json
   ```
   Add your API keys to `local.settings.json` (e.g. `GEMINI_API_KEY` for free testing, or `AZURE_OPENAI_API_KEY`).

2. **Install Local Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Function App Locally**:
   ```bash
   func start
   ```

   Functions will be exposed at:
   - **HTTP Trigger**: `http://localhost:7071/api/process_resume`

### Testing the HTTP Endpoint

```bash
curl -X POST http://localhost:7071/api/process_resume \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Jane Doe | Software Engineer | Python, FastAPI, Docker | Built asynchronous microservices at CloudCorp."
  }'
```

Expected Response:
```json
{
  "status": "success",
  "data": {
    "contact_info": {
      "name": "Jane Doe",
      "email": null,
      "phone": null,
      "location": null
    },
    "skills": ["Python", "FastAPI", "Docker"],
    "experiences": [
      {
        "company": "CloudCorp",
        "role": "Software Engineer",
        "description_bullets": ["Built asynchronous microservices at CloudCorp."],
        "technologies": ["Python", "FastAPI", "Docker"]
      }
    ]
  }
}
```

---

## 🔒 Security & Secrets Hygiene

- **Never commit `local.settings.json`**: It is ignored by git.
- **Never commit credentials**: Use Azure Key Vault or Managed Identity (`DefaultAzureCredential`) when deploying to production.
