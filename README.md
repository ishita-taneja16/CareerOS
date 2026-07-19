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

### Frontend

- React.js
- Vite
- JavaScript (ES6+)
- Tailwind CSS
- Axios

### Backend

- Python
- FastAPI
- Django
- REST APIs
- Pydantic

### AI/LLM

- Google Gemini API
- LangChain
- LangGraph
- Agentic AI
- RAG
- Prompt Engineering
- Semantic Search

### Databases

- PostgreSQL
- SQLite
- ChromaDB
- FAISS

### DevOps

- Docker
- Git
- GitHub Actions

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
