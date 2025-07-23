import os
from dotenv import load_dotenv
import httpx
import json
from typing import Optional

# Load .env variables
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

if not OLLAMA_MODEL:
    raise RuntimeError("Environment variable OLLAMA_MODEL must be set to a valid Ollama model name (e.g., 'mistral:latest')")

async def generate_feedback(prompt: str) -> str:
    """
    Send a chat-based prompt to Ollama and return the assistant's response text.
    Uses both OpenAI-compatible endpoint and fallback to native Ollama API.
    """
    
    # First try OpenAI-compatible endpoint
    try:
        return await _generate_openai_compatible(prompt)
    except Exception as e:
        print(f"OpenAI-compatible endpoint failed: {e}")
        # Fallback to native Ollama API
        try:
            return await _generate_native_ollama(prompt)
        except Exception as e2:
            print(f"Native Ollama API also failed: {e2}")
            return "Sorry, I'm unable to generate feedback at this time. Please check your nutrition data manually."

async def _generate_openai_compatible(prompt: str) -> str:
    """Try OpenAI-compatible endpoint first"""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful nutrition coach. Provide concise, actionable advice."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

async def _generate_native_ollama(prompt: str) -> str:
    """Fallback to native Ollama API"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"You are a helpful nutrition coach. {prompt}",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 100
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()

# Test function to verify Ollama connectivity
async def test_ollama_connection() -> dict:
    """Test Ollama connection and return status"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test if Ollama is running
            health_resp = await client.get(f"{OLLAMA_URL}/api/tags")
            health_resp.raise_for_status()
            
            # Test if our model is available
            models = health_resp.json().get("models", [])
            model_available = any(model.get("name") == OLLAMA_MODEL for model in models)
            
            return {
                "status": "healthy",
                "ollama_running": True,
                "model_available": model_available,
                "available_models": [m.get("name") for m in models]
            }
    except Exception as e:
        return {
            "status": "error",
            "ollama_running": False,
            "error": str(e)
        }