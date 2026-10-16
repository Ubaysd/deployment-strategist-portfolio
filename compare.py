import os, time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # lit GROQ_API_KEY et GEMINI_API_KEY dans .env

QUESTION = "En 3 phrases : quelles pièces faut-il pour déclarer un dégât des eaux ?"

ollama = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
gemini = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=os.getenv("GEMINI_API_KEY"))

SOURCES = {
    "Ollama local": (ollama, "llama3.2"),
    "Ollama cloud": (ollama, "gpt-oss:120b-cloud"),
    "Groq":         (groq,   "openai/gpt-oss-120b"),
    "Gemini":       (gemini, "gemini-flash-lite-latest"),
    "Groq Qwen":    (groq,   "qwen/qwen3.8-27b"),
}

for nom, (client, modele) in SOURCES.items():
    debut = time.perf_counter()
    try:
        r = client.chat.completions.create(
            model=modele, messages=[{"role": "user", "content": QUESTION}])
        secondes = time.perf_counter() - debut
        tokens = r.usage.completion_tokens
        print(f"\n=== {nom} | {secondes:.1f} s | {tokens} tokens | {tokens/secondes:.0f} tokens/s")
        print(r.choices[0].message.content)
    except Exception as e:
        print(f"\n=== {nom} : ERREUR -> {e}")
