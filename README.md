# Myk Raws Legal RAG System

AI-powered Singapore Legal Assistant with Statutory Interpretation

## Features
- 🏛️ Hybrid retrieval (BM25 + Dense embeddings)
- 🔗 Interpretation link boosting (statute-case pairing)
- 🎯 LePaRD classification integration
- ✅ Response validation and quality metrics

## Architecture
- **Frontend**: Next.js 14 (Static) on Netlify
- **Backend**: FastAPI on your VPS
- **Database**: PostgreSQL + FAISS

## Live Demo
- Frontend: https://mykraws.netlify.app
- API Docs: Coming soon

## Local Development

### Backend
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment
See DEPLOYMENT_GUIDE.md for complete instructions.

## License
MIT
