# Alauda GROS Copilot — Global Recruitment Operating System

AI-powered recruitment copilot built on Streamlit, designed for Alauda's global talent acquisition pipeline. Covers the full lifecycle from headcount approval to candidate onboarding.

## Modules

| # | Module | Description |
|---|--------|-------------|
| 0 | HC Approval | Business headcount request submission & HR approval |
| 1 | JD & Sourcing | AI-generated job descriptions + X-Ray Boolean search strings |
| 2 | Outreach | Personalized cold outreach (Email + LinkedIn InMail) |
| 3 | Resume Matcher | Quantitative resume scoring against JD (0-100 rubric) |
| 4 | Scorecard | BARS structured interview scorecard + STAR questions |
| 5 | Playbook Q&A | RAG-grounded knowledge base question answering |
| 6 | Knowledge Harvester | Web-scraped knowledge fragment accumulation |
| 7 | Candidate Pipeline | Kanban board for candidate stage tracking |

## Quick Start

```bash
# 1. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env   # Then fill in your API keys

# 3. Run the app
streamlit run web_app.py
```

Required environment variables (`.env`):
- `OPENAI_API_KEY` — LLM API key (OpenAI-compatible endpoint)
- `OPENAI_API_BASE` — API base URL (default: `https://api.openai.com/v1`)
- `LLM_MODEL` — Fast model for Q&A/scoring (default: `claude-haiku-4-5-20251001`)
- `STRONG_MODEL` — Strong model for JD generation (default: same as `LLM_MODEL`)
- `APP_PASSWORD` — Optional access password (leave empty for open access)

## Project Structure

```
├── web_app.py              # Streamlit entrypoint
├── app_shared.py           # Shared singletons, auth, CSS
├── recruitment_agent.py    # Core LLM agent (7 generation methods)
├── hc_manager.py           # Headcount request CRUD
├── candidate_manager.py    # Candidate pipeline management
├── knowledge_manager.py    # Knowledge fragment accumulation
├── document_parser.py      # RAG system (FAISS + keyword fallback)
├── db.py                   # SQLite database layer (WAL mode)
├── pages/                  # Streamlit page modules
├── assets/                 # Static assets (favicon, CSS)
├── data/                   # Runtime data (SQLite DB, FAISS index)
├── tests/                  # Pytest test suite
├── Dockerfile              # Container deployment
└── .github/workflows/      # CI/CD pipeline
```

## Running Tests

```bash
pip install pytest ruff
python -m pytest tests/ -v
ruff check .
```

## Docker

```bash
docker build -t recruitment-copilot .
docker run -p 8501:8501 --env-file .env recruitment-copilot
```
