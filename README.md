# 🥗 Food Tracker AI  

A **FastAPI service** for logging meals, attaching **USDA FoodData Central nutrition facts**, storing them in **SQLModel**, and generating **AI coaching feedback** via Ollama.  

---

## 🚀 Features  
- Log meals with nutrition profiles from USDA API  
- Daily/weekly summaries (timezone-aware)  
- AI feedback with Ollama  
- Health checks for DB & Ollama  

---

## ⚡ Quick Start  
```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# .env example
FDC_API_KEY=your-usda-key
OLLAMA_MODEL=mistral:latest

uvicorn backend.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for Swagger UI.  

---

## 📡 Key Endpoints  
- `POST /foodlogs/` → log a meal  
- `GET /summaries/daily` → daily nutrition summary  
- `GET /summaries/weekly` → weekly summary  
- `GET /feedback/daily` → AI coaching tip  
