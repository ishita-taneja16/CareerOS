# 🚀 CareerOS – Agentic AI Career Copilot

CareerOS is a production-ready Full Stack Agentic AI platform that helps users optimize their careers using multiple specialized AI agents. The platform provides AI-powered resume analysis, ATS evaluation, career guidance, interview preparation, skill gap analysis, cover letter generation, intelligent job matching through a Supervisor-driven multi-agent workflow, **optional local Qwen LLM fine-tuning and inference**, and a **provider-agnostic Responsible AI evaluation framework**.

---

## ✨ Features

- 🤖 Multi-Agent AI Architecture (LangGraph)
- 📄 AI Resume Parsing (PDF/DOCX)
- 📊 ATS Resume Analysis & Keyword Optimization
- 🎤 AI Interview Preparation & Skill Gap Analysis
- 🔍 RAG-based Semantic Search & Memory Retention
- 🧠 Optional Local Qwen LLM Inference (`Qwen/Qwen2.5-1.5B-Instruct`)
- ⚙️ LoRA / QLoRA Custom Fine-Tuning Pipeline
- 🛡️ Provider-Agnostic Responsible AI Guardrails & Evaluation Framework
- ⚡ FastAPI REST APIs & Django Application
- 💻 Modern React Frontend (Vite)
- 🐳 Docker Support & GitHub Actions CI/CD

---

# 🏗 Architecture

```
                User
                  │
                  ▼
          React Frontend (Vite)
                  │
                  ▼
            FastAPI Backend
                  │
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
             LLMService
                  │
       ┌──────────┴──────────┐
       │                     │
  Gemini (Default)     Local Qwen (Optional)
       └──────────┬──────────┘
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

> **Note**: Google Gemini remains the default production LLM provider. Qwen is integrated as an optional, locally hosted LLM provider.

---

## 🤖 Custom Qwen Fine-Tuning

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
# Default Gemini API provider
LLM_PROVIDER=gemini

# Optional local Qwen provider
LLM_PROVIDER=qwen
```

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

### 1. Run Backend Unit & Responsible AI Tests

```bash
cd backend/fastapi_app

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
