# 🚀 CareerOS – Agentic AI Career Copilot

CareerOS is a production-ready Full Stack Agentic AI platform that helps users optimize their careers using multiple specialized AI agents. The platform provides AI-powered resume analysis, ATS evaluation, career guidance, interview preparation, skill gap analysis, cover letter generation, and intelligent job matching through a Supervisor-driven multi-agent workflow.

---

## ✨ Features

- 🤖 Multi-Agent AI Architecture (LangGraph)
- 📄 AI Resume Parsing (PDF/DOCX)
- 📊 ATS Resume Analysis
- 🎤 AI Interview Preparation
- 📈 Skill Gap Analysis
- 🔍 RAG-based Semantic Search
- 🧠 Memory-based Personalized Responses
- ⚡ FastAPI REST APIs
- 💻 Modern React Frontend
- 🐳 Docker Support
- 🔄 GitHub Actions CI/CD

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
        ChromaDB + Gemini API
```

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

### 🤖 AI / LLM

![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge)
![LangGraph](https://img.shields.io/badge/LangGraph-4CAF50?style=for-the-badge)
![Agentic AI](https://img.shields.io/badge/Agentic_AI-6A5ACD?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-8A2BE2?style=for-the-badge)
![Prompt Engineering](https://img.shields.io/badge/Prompt_Engineering-FF9800?style=for-the-badge)
![Semantic Search](https://img.shields.io/badge/Semantic_Search-00ACC1?style=for-the-badge)

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
│   ├── fastapi_app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── prompts/
│   │   ├── services/
│   │   ├── models/
│   │   ├── tests/
│   │   └── main.py
│
├── frontend/
│
├── docker/
│
├── .github/workflows/
│
└── README.md
```

---

# ⚙ Installation

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

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

---

## Environment Variables

Create a `.env` file inside `backend/fastapi_app`

```
GEMINI_API_KEY=YOUR_API_KEY
LLM_PROVIDER=gemini
LLM_MODEL=gemini/gemini-2.5-flash
DATABASE_URL=postgresql://...
```

---

## Run Backend

```bash
uvicorn main:app --reload
```

---

# 🧪 Running Tests

Backend Tests

```bash
pytest
```

Frontend Build

```bash
npm run build
```

Docker

```bash
docker compose up --build
```

---

# 🔄 CI/CD

GitHub Actions automatically performs:

- Backend Testing
- Frontend Build Validation
- Docker Build Validation

Every push to the `main` branch is automatically validated.

---

# 📌 Future Enhancements

- Authentication
- Resume Versioning
- Job Recommendation Engine
- Voice AI Interview
- Analytics Dashboard
- Email Notifications
- Deployment on AWS

---

# 👩‍💻 Author

**Ishita Taneja**

GitHub:
https://github.com/ishita-taneja16

LinkedIn:
https://linkedin.com/in/ishita-taneja16

Email:
ishitataneja1611@gmail.com

---

## ⭐ If you like this project, don't forget to star the repository!
