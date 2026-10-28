# 🚀 CareerOS – Agentic AI Career Copilot

CareerOS is a production-ready Full Stack Agentic AI platform that helps users optimize their careers using multiple specialized AI agents. The platform provides AI-powered resume analysis, ATS evaluation, career guidance, interview preparation, skill gap analysis, cover letter generation, intelligent job matching through a Supervisor-driven multi-agent workflow, **Microsoft Azure AI & Google Gemini provider integration**, **optional local Qwen LLM fine-tuning and inference**, and a **provider-agnostic Responsible AI evaluation framework**.

---

## ✨ Features

- 🤖 Multi-Agent AI Architecture (LangGraph Supervisor-Worker StateGraph)
- ☁️ **Microsoft Azure AI Integration** (Azure OpenAI Service & Azure AI Foundry Model Endpoints)
- ⚡ **Optional Azure Functions Worker** (Asynchronous Serverless Document Processing)
- 📊 Agent Monitoring & Tracing (Langfuse Spans, Token Tracking, Latency, Errors)
- 🔍 Hybrid Semantic Retrieval (ChromaDB Dense + BM25Okapi Sparse + Reciprocal Rank Fusion)
- 📈 Reproducible RAG Evaluation Baseline (RAGAS Context Recall & Faithfulness)
- 🌐 Provider-Agnostic LLM Engine (Google Gemini Free Tier, Azure OpenAI, Azure Foundry, OpenAI, and Local/Remote Qwen2.5)
- 👥 Multi-Agent Comparison Prototype (CrewAI Isolated Demonstration)
- 📄 AI Resume Parsing (PDF/DOCX with PyMuPDF, docling, and spacy)
- 📊 ATS Resume Analysis & Keyword Optimization
- 🎤 AI Interview Preparation & Skill Gap Analysis
- 🧠 Optional Local Qwen LLM Inference (`Qwen/Qwen2.5-1.5B-Instruct`)
- ⚙️ LoRA / QLoRA Custom Fine-Tuning Pipeline
- 🛡️ Provider-Agnostic Responsible AI Guardrails & Evaluation Framework
- ⚡ FastAPI REST APIs & Django Application
- 💻 Modern React Frontend (Vite)
- 🐳 Docker Support & GitHub Actions CI/CD

---

## 📚 Technical Documentation

- 🏛️ [**System Architecture Document**](docs/ARCHITECTURE.md): Multi-agent state machine, hybrid retrieval, provider routing, telemetry, and resilience.
- 📘 [**Agent Development Guide**](docs/AGENT_DEVELOPMENT_GUIDE.md): Prompts, state schemas, retries, Langfuse tracing, safety, and testing best practices.
- 🔬 [**LangGraph vs. CrewAI Comparison**](backend/fastapi_app/agents/crewai_demo/COMPARISON.md): Detailed architectural trade-offs in orchestration, state management, tool usage, and testing.
- ⚡ [**Azure Functions Guide**](azure_functions/README.md): Asynchronous serverless document processing, local Azurite emulator testing, and Consumption plan free allowances.

---

# 🏗 Architecture


```
                User
                  │
                  ▼
          React Frontend (Vite)
                  │
                  ▼
            FastAPI Backend  ◀══════ (Optional Async) ══════ Azure Functions
                  │                                         (1M free exec/mo)
                  ▼
        LangGraph Supervisor
                  │
      ┌───────────┴────────────┐
      │                        │
Pipeline Dispatcher      Memory Agent
      │
      ├──────── Resume Agent
      ├──────── ATS Agent
      ├──────── Advisor Agent
      ├──────── Interview Agent
      ├──────── Skill Gap Agent
      └──────── Cover Letter Agent
                  │
                  ▼
             LLMService (Centralized Multi-Provider Engine)
                  │
       ┌──────────┼──────────────────────┬──────────────────────┐
       │          │                      │                      │
  Gemini API   Azure OpenAI         Azure AI Foundry       Local Qwen
 (Free Default) (Optional Cloud)   (Serverless Model API)  (Offline OSS)
       │          │                      │                      │
       └──────────┴──────────────────────┴──────────────────────┘
                  │
                  ▼
     Responsible AI Evaluation
                  │
       ├──────── Safety & Toxicity (Detoxify)
       ├──────── Demographic Bias Detection
       ├──────── Factuality & Groundedness Audit
       └──────── Explainability & Audit Trail
                  │
                  ▼
               Response
```

> **Free-First Note**: Google Gemini remains the default zero-cost cloud LLM provider. Azure OpenAI, Microsoft Azure AI Foundry, and local Qwen are configuration-ready optional providers. No paid cloud resources are required to run or test CareerOS.

---

## ☁️ Microsoft Azure AI Integration (Free-First Architecture)

CareerOS includes enterprise-grade **Microsoft Azure AI** support seamlessly woven into the centralized `LLMService` engine without breaking existing Google Gemini workflows or requiring paid cloud resources.

### 💡 Free-First Philosophy
- **Zero-Cost Default**: Google Gemini remains the default production LLM provider, utilizing the free rate quotas available in Google AI Studio.
- **No Inadvertent Charges**: Azure OpenAI and Azure Foundry providers read configuration exclusively from environment variables and fail gracefully with helpful diagnostic messages if credentials or endpoints are omitted.
- **No Cloud Lock-in**: All LangGraph supervisor and specialist agents call `LLMService.call(...)` agnostic of whether Gemini, Azure OpenAI, Azure Foundry, or local Qwen is active.

### 💰 Pricing & Free-Tier Eligibility Guide
Before configuring or deploying cloud resources, verify your subscription terms and current pricing:

| Service / Provider | Free Allowance & Eligibility | Pricing Structure | Verification Link |
| :--- | :--- | :--- | :--- |
| **Google Gemini (Default)** | Free Tier available in Google AI Studio (rate-limited requests per minute) | Free tier available / Pay-as-you-go | [Google AI Studio Pricing](https://ai.google.dev/pricing) |
| **Azure Free Account** | **$200 credit** for the first 30 days + 12 months of select free services | Credit-based trial | [Azure Free Account Eligibility](https://azure.microsoft.com/free/) |
| **Azure OpenAI Service** | No perpetual free inference tier; consumes Azure free credits during trial | Pay-as-you-go per 1K tokens (e.g., GPT-4o-mini ~$0.15/1M input tokens) | [Azure OpenAI Pricing Calculator](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) |
| **Azure AI Foundry (MaaS)** | Varies by foundation model; serverless pay-per-token or hourly compute | Pay-as-you-go per token or hourly VM compute | [Azure AI Foundry Catalog](https://ai.azure.com/explore/models) |
| **Azure Functions** | **1,000,000 executions/month free** + **400,000 GB-seconds/month free** on Consumption Plan | $0 within free grant | [Azure Functions Pricing](https://azure.microsoft.com/pricing/details/functions/) |
| **Local Development** | **100% Free** via Azurite Emulator & Azure Functions Core Tools | Completely local, offline, no Azure account required | [Azurite Docs](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) |

---

### 🔧 LLM Provider Configuration & Setup

#### 1. Google Gemini (Default - Free First)
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY="your-gemini-api-key"
LLM_MODEL="gemini/gemini-2.5-flash"
```

#### 2. Microsoft Azure OpenAI Service (Optional)
To use Azure OpenAI, obtain a deployment in the Azure Portal or Azure OpenAI Studio:
```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-azure-api-key"
AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```
*Note: Both `LLM_PROVIDER=azure` and `LLM_PROVIDER=azure_openai` are supported.*

#### 3. Microsoft Azure AI Foundry (Optional Serverless Model API)
To route requests to Serverless Model-as-a-Service (MaaS) endpoints hosted in Microsoft Azure AI Foundry (e.g. Phi-4, Mistral, Llama-3.3):
```env
LLM_PROVIDER=foundry
AZURE_FOUNDRY_ENDPOINT="https://your-model-endpoint.models.ai.azure.com"
AZURE_FOUNDRY_API_KEY="your-foundry-api-key"
AZURE_FOUNDRY_MODEL="Phi-4"
```
*Note: Both `LLM_PROVIDER=foundry` and `LLM_PROVIDER=azure_foundry` are supported.*

---

### ⚡ Optional Azure Functions Workflow (Asynchronous Processing)

CareerOS includes an optional serverless worker in `azure_functions/` using the modern Azure Functions Python v2 model:
- **HTTP Trigger (`POST /api/process_resume`)**: Offloads document extraction (PDF/DOCX) and structuring without blocking FastAPI threads.
- **Queue Trigger (`resume-processing-queue`)**: Provides decoupled background worker processing for batch resume parsing.
- **100% Local Testing**: Run locally using Azure Functions Core Tools and the Azurite storage emulator without deploying cloud resources.
- See [azure_functions/README.md](azure_functions/README.md) for full setup instructions.

---

### 🏠 Local Development vs. Cloud Deployment Distinction
- **Local Application**: CareerOS runs 100% locally on your machine with FastAPI on port 8001, Django on port 8080, and Vite on port 5173.
- **Cloud Readiness**: Azure integrations are **configuration-ready**. CareerOS is **not** deployed to Azure cloud infrastructure by default. To deploy to Azure, deliberate provisioning (e.g. Azure App Service, Azure Container Apps, or Azure Functions) with proper billing setup is required.

---

CareerOS includes an implementation for career-domain fine-tuning of:

`Qwen/Qwen2.5-1.5B-Instruct`

using:
- PyTorch
- Hugging Face Transformers
- PEFT (Parameter-Efficient Fine-Tuning)
- LoRA / QLoRA
- Hugging Face Datasets

CareerOS provides a local LoRA/QLoRA fine-tuning pipeline for adapting Qwen models to career-domain instructions, such as:
- Resume improvement & bullet point formatting
- ATS keyword optimization
- Strategic career advice
- Technical & behavioral interview preparation
- Skill gap analysis & learning roadmaps
- Job-candidate matching
- Tailored cover letter guidance
- AI/ML career domain questions

### Fine-Tuning Pipeline Files
- `backend/fastapi_app/ml/fine_tuning/dataset_prep.py`: ChatML instruction formatting utility.
- `backend/fastapi_app/ml/fine_tuning/qwen_config.yaml`: LoRA rank, alpha, learning rate, and target projection configurations.
- `backend/fastapi_app/ml/fine_tuning/train_qwen.py`: PEFT/QLoRA training execution script (supports GPU execution and CPU dry-runs).
- `backend/fastapi_app/ml/datasets/train/career_instructions.jsonl`: Synthetic instruction training dataset.

> **Note**: The repository contains the complete fine-tuning training code and synthetic training dataset. Fine-tuning is run as a separate offline process, and trained model checkpoints are not committed to Git.

---

## 🧠 Local Qwen Inference

- Qwen is integrated as an optional LLM provider via the provider registry abstraction.
- Existing Gemini functionality remains fully available and active by default.
- Qwen inference supports local Hugging Face Transformers pipelines as well as integration paths for Ollama or vLLM endpoints where locally configured.

### Key Service Components
- `backend/fastapi_app/services/qwen_inference_service.py`: Local Qwen model initialization and inference wrapper.
- `QwenProvider` in `backend/fastapi_app/services/llm_service.py`: Provider abstraction class for Qwen routing.

### Provider Selection
In your `backend/fastapi_app/.env` file:

```env
# Google Gemini API provider (Default)
LLM_PROVIDER=gemini
GEMINI_API_KEY="your-gemini-key"

# OpenAI API provider
LLM_PROVIDER=openai
OPENAI_API_KEY="your-openai-key"
OPENAI_MODEL=gpt-4o-mini

# Optional local/remote Qwen provider
LLM_PROVIDER=qwen
QWEN_MODEL_PATH="Qwen/Qwen2.5-7B-Instruct"
```

---

## 📊 Agent Monitoring & Tracing (Langfuse)

CareerOS integrates **Langfuse** for enterprise-grade LLM and agentic observability:
- **Node Spans**: Every agent execution (`supervisor`, `resume_agent`, `ats_agent`, `advisor_agent`, etc.) is traced with duration, user ID, state metadata, and routing decisions.
- **Generation Tracking**: LLM prompts, completions, latencies, and exact token usage (`prompt_tokens`, `completion_tokens`, `total_tokens`) are recorded without fabricating missing values.
- **Cost & Latency Audits**: Captures actual provider-exposed cost figures when available.
- **Graceful Degradation**: Tracing is optional. If `LANGFUSE_ENABLED=false` or credentials are absent, the system runs with `NoOpSpan` without network overhead or runtime exceptions.

### Configuration
```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"
```

---

## 🔍 Hybrid Semantic Retrieval & RAGAS Evaluation

CareerOS implements an optimized two-stage RAG retrieval pipeline:
1. **Dense Semantic Retrieval**: ChromaDB vector collection powered by `all-MiniLM-L6-v2` embeddings for conceptual matching.
2. **Sparse Lexical Retrieval**: Custom `BM25OkapiRetriever` ($k_1=1.5, b=0.75$) matching exact technical acronyms, tools, and certifications (e.g. `FastAPI`, `Alembic`, `PostgreSQL`, `QLoRA`).
3. **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse rankings ($k=60$) to prioritize candidate chunks with both semantic relevance and technical precision.
4. **Backward Compatibility**: `query_resume_chunks(..., use_hybrid=True)` enables hybrid search while preserving existing vector queries.

### RAGAS Evaluation Baseline
Reproducible evaluation baseline comparing standard Dense retrieval vs. Optimized Hybrid + RRF Reranking on real-world career domain queries:
- **Context Recall**: Measures proportion of ground-truth technical competencies retrieved.
- **Faithfulness**: Measures whether answer claims are strictly grounded in retrieved passages (via `GroundednessEvaluator`).
- **Mean Reciprocal Rank (MRR)**: Measures ranking quality of the top relevant chunk.
- Results saved to: `backend/fastapi_app/ml/evaluation/ragas_evaluation_results.json`.

---

## 👥 CrewAI Demonstration Prototype

To benchmark multi-agent frameworks, CareerOS includes an isolated **CrewAI comparison demonstration**:
- Location: `backend/fastapi_app/agents/crewai_demo/`
- Architecture: 2-agent sequential crew (`Senior Technical Resume Reviewer` and `ATS Specialist`).
- Custom Tools: `ats_keyword_match_tool` and `resume_bullet_auditor_tool`.
- Complete isolation: Existing LangGraph supervisor workflow remains the primary production orchestrator.
- Detailed Trade-Off Analysis: See [COMPARISON.md](backend/fastapi_app/agents/crewai_demo/COMPARISON.md).

---


## 🛡 Responsible AI

CareerOS contains a provider-agnostic Responsible AI evaluation framework for auditing LLM-generated outputs across multiple categories:
- Toxicity & Output Safety
- Demographic & Cultural Bias
- Factual Accuracy & Unsupported Claims
- RAG Groundedness
- Prompt Injection Prevention
- Explainability & Auditability

The evaluation framework evaluates **Gemini**, **Base Qwen**, **Fine-Tuned Qwen**, and other supported providers using identical, standardized evaluation criteria.

---

### 🚨 Toxicity Evaluation
- Location: `backend/fastapi_app/ml/responsible_ai/toxicity_evaluator.py`
- Uses local Detoxify models alongside heuristic classifiers to evaluate output categories:
  - `toxicity`
  - `severe_toxicity`
  - `insult`
  - `threat`
  - `identity_attack`
  - `sexual_explicit`
- Classifies outputs into `SAFE`, `REVIEW`, or `UNSAFE` using configurable score thresholds.

> **Notice**: The toxicity evaluator is an automated safety signal and does not provide complete safety guarantees.

---

### ⚖ Demographic Bias Evaluation
- Location: `backend/fastapi_app/ml/responsible_ai/bias_detector.py`
- Evaluates responses for potential demographic, gender, age, and protected-class stereotyping patterns in career recommendations and candidate assessments.
- Evaluated against synthetic benchmark cases.

> **Notice**: This evaluation framework does not prove that a model is unbiased; it provides automated signals for potential bias.

---

## 🎯 Factuality & Groundedness Evaluation

- Location: `backend/fastapi_app/ml/responsible_ai/groundedness_evaluator.py`
- Compares generated LLM claims against context sources:
  - **Structured Resume Data**: Verifies whether claimed skills, roles, or companies exist in `structured_resume_data`.
  - **Job Descriptions**: Checks whether claimed job requirements exist in `job_description`.
  - **RAG Context**: Compares RAG response metrics against `user_query` and `retrieved_context`.
- Reports structured metrics:
  - `grounded` (boolean)
  - `unsupported_claims` (list of flagged claims)
  - `hallucination_risk` (`low`, `medium`, or `high`)
  - `evaluation_notes`

> **Notice**: Groundedness evaluation uses automated heuristic analysis and is not perfect fact verification.

---

## 📊 Model Evaluation & Benchmarking

- Locations:
  - `backend/fastapi_app/ml/responsible_ai/evaluator_engine.py`
  - `backend/fastapi_app/ml/evaluation/eval_framework.py`
  - `backend/fastapi_app/ml/evaluation/eval_qwen.py`

The framework allows comparing **Gemini**, **Qwen Base**, and **Qwen Fine-Tuned** side-by-side against the same evaluation dataset using identical test criteria (`evaluate_output(prompt, response, context, provider)`).

### Synthetic Benchmark Dataset
- `backend/fastapi_app/ml/datasets/eval/benchmark_dataset.jsonl`
- `backend/fastapi_app/ml/datasets/eval/test_eval_cases.jsonl`

Covers synthetic test cases across 11 categories:
1. Normal career advice
2. Resume optimization
3. ATS recommendations
4. Interview advice
5. Skill recommendations
6. Job matching
7. Toxicity & safety cases
8. Prompt injection cases
9. Demographic bias cases
10. Hallucination cases
11. RAG groundedness cases

---

## 🔍 Explainability & Auditability

- Location: `backend/fastapi_app/ml/responsible_ai/explainability.py`
- Provides transparent audit breakdowns for platform decisions, including:
  - ATS score keyword match percentage and section weight breakdown
  - Supervisor routing rationale and agent decision logs
  - Keyword coverage and feature attribution audit trails

---

## 🧪 ML & Responsible AI Testing

The ML and Responsible AI modules are verified by dedicated test suites:
- `backend/fastapi_app/tests/test_responsible_ai.py`
- `backend/fastapi_app/tests/test_qwen_inference.py`

### Verified Test Suite Results
- **Responsible AI & Qwen Tests**: 13/13 passed (100% pass rate)
- **Full FastAPI Backend Tests**: Passed
- **Django Backend Tests**: Passed (`python manage.py test`)
- **Frontend Production Build**: Passed (`npm run build` in 3.54s)

---

## 💰 Free & Open-Source ML Stack

The Qwen fine-tuning, inference, and Responsible AI evaluation functionality are built entirely on free and open-source local components:
- Qwen2.5-1.5B-Instruct
- PyTorch
- Hugging Face Transformers & Datasets
- PEFT (LoRA / QLoRA)
- Detoxify (Local PyTorch model)
- ChromaDB & FAISS
- Ollama / vLLM (Optional local servers)
- Docker & GitHub Actions

> **Notice**: No paid API is required for the local Qwen fine-tuning, inference, or Responsible AI evaluation pipeline. Google Gemini remains documented separately as the existing default cloud LLM provider.

---

# 🛠 Tech Stack

### 🎨 Frontend

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge)

---

### ⚙ Backend

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![REST API](https://img.shields.io/badge/REST_API-FF6F00?style=for-the-badge)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

---

### 🤖 AI / LLM / ML

![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Qwen](https://img.shields.io/badge/Qwen2.5-673AB7?style=for-the-badge)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![PEFT / LoRA](https://img.shields.io/badge/PEFT_/_LoRA-009688?style=for-the-badge)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge)
![LangGraph](https://img.shields.io/badge/LangGraph-4CAF50?style=for-the-badge)
![Agentic AI](https://img.shields.io/badge/Agentic_AI-6A5ACD?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-8A2BE2?style=for-the-badge)

---

### 🛡 Responsible AI & Evaluation

![Detoxify](https://img.shields.io/badge/Detoxify-FF5722?style=for-the-badge)
![Bias Evaluation](https://img.shields.io/badge/Bias_Evaluation-3F51B5?style=for-the-badge)
![Groundedness](https://img.shields.io/badge/Groundedness_Audit-009688?style=for-the-badge)
![Explainability](https://img.shields.io/badge/Explainability-795548?style=for-the-badge)

---

### 🗄 Databases

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FFB000?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-00599C?style=for-the-badge)

---

### 🚀 DevOps

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

---

# 📂 Project Structure

```
CareerOS/
│
├── backend/
│   ├── django_app/
│   │
│   └── fastapi_app/
│       ├── agents/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── prompts/
│       ├── services/
│       │   ├── llm_service.py
│       │   ├── qwen_inference_service.py
│       │   └── vector_service.py
│       │
│       ├── ml/
│       │   ├── datasets/
│       │   │   ├── train/
│       │   │   │   └── career_instructions.jsonl
│       │   │   └── eval/
│       │   │       ├── benchmark_dataset.jsonl
│       │   │       └── test_eval_cases.jsonl
│       │   │
│       │   ├── evaluation/
│       │   │   ├── eval_framework.py
│       │   │   └── eval_qwen.py
│       │   │
│       │   ├── fine_tuning/
│       │   │   ├── dataset_prep.py
│       │   │   ├── qwen_config.yaml
│       │   │   └── train_qwen.py
│       │   │
│       │   └── responsible_ai/
│       │       ├── bias_detector.py
│       │       ├── evaluator_engine.py
│       │       ├── explainability.py
│       │       ├── groundedness_evaluator.py
│       │       ├── guardrails.py
│       │       └── toxicity_evaluator.py
│       │
│       ├── tests/
│       │   ├── test_endpoints.py
│       │   ├── test_qwen_inference.py
│       │   └── test_responsible_ai.py
│       │
│       └── main.py
│
├── frontend/
├── Dockerfile.django
├── Dockerfile.fastapi
├── docker-compose.yml
├── .github/workflows/
└── README.md
```

---

# ⚙ Installation & Usage

## Clone Repository

```bash
git clone https://github.com/ishita-taneja16/CareerOS.git
cd CareerOS
```

---

## Backend Setup

```bash
cd backend/fastapi_app
python -m venv venv
```

### Windows
```bash
venv\Scripts\activate
```

### Linux / Mac
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside `backend/fastapi_app`:

```env
# Production Default Provider
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
LLM_PROVIDER=gemini
LLM_MODEL=gemini/gemini-2.5-flash

# Optional Responsible AI Guardrail Settings
ENABLE_RESPONSIBLE_AI_GUARDRAILS=True
BIAS_THRESHOLD=0.15
MAX_HALLUCINATION_SCORE=0.20

# Optional Local Qwen Provider Override
# LLM_PROVIDER=qwen
# QWEN_MODEL_PATH=Qwen/Qwen2.5-1.5B-Instruct
```

---

## Run Backend Application

```bash
uvicorn main:app --reload
```

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

# 🧪 Running Tests & ML Evaluation

### 1. Run Backend Unit, Azure AI & Responsible AI Tests

```bash
cd backend/fastapi_app

# Run Azure OpenAI and Foundry provider test suite
pytest tests/test_azure_provider.py

# Run Responsible AI & Qwen inference test suite
pytest tests/test_responsible_ai.py tests/test_qwen_inference.py

# Run all FastAPI backend tests
pytest tests/
```

### 2. Run Django Tests

```bash
cd backend/django_app
python manage.py test --noinput
```

### 3. Run Provider-Agnostic Comparative Benchmark Evaluation

```bash
cd backend/fastapi_app

# Execute comparative evaluation benchmark across providers
python -m ml.evaluation.eval_framework
```

### 4. Fine-Tuning Pipeline Dry-Run Validation

> **Note**: Normal CareerOS startup does not automatically fine-tune Qwen models. Fine-tuning is an optional, separate process. Model weights/adapters should not be committed to Git.

```bash
cd backend/fastapi_app

# Validate fine-tuning pipeline configuration
python ml/fine_tuning/train_qwen.py --dry-run
```

---

# 🔄 CI/CD

GitHub Actions automatically performs:
- Backend Testing (`pytest`)
- Frontend Build Validation (`npm run build`)
- Docker Build Validation

Every push to the `main` branch is automatically validated.

---

# 📌 Future Enhancements

- Authentication & Role Management
- Resume Versioning & Export Templates
- Advanced Voice AI Mock Interviewer
- Fine-Tuned Model Weights Registry & Model Quantization (GGUF / AWQ)
- Real-Time Analytics & Responsible AI Audit Dashboard
- AWS / Cloud Deployment Architecture

---

# 👩‍💻 Author

**Ishita Taneja**

GitHub: https://github.com/ishita-taneja16  
LinkedIn: https://linkedin.com/in/ishita-taneja16  
Email: ishitataneja1611@gmail.com

---

## ⭐ If you like this project, don't forget to star the repository!
