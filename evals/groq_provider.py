"""Fournisseur promptfoo pour Groq avec relance controlee.

Sur un quota atteint (429) ou une erreur serveur, attend 10 s puis renvoie
la meme requete, jusqu'a 5 fois. promptfoo ne relance pas lui-meme
(maxRetries: 0) : les cas deja traites ne sont jamais rejoues.
"""
import json
import os
import re
import sys
import time

from openai import OpenAI, APIStatusError, APIConnectionError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ATTENTE_S = 10
TENTATIVES = 5


def _messages(prompt):
    """promptfoo envoie soit du texte, soit une liste de messages en JSON (juge)."""
    try:
        data = json.loads(prompt)
        if isinstance(data, list) and all(isinstance(m, dict) and "role" in m for m in data):
            return data
    except (ValueError, TypeError):
        pass
    return [{"role": "user", "content": prompt}]


def call_api(prompt, options, context):
    cfg = (options or {}).get("config", {})
    modele = cfg["model"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1",
                    api_key=os.environ["GROQ_API_KEY"], max_retries=0, timeout=120)
    cause = ""
    for essai in range(1, TENTATIVES + 1):
        try:
            r = client.chat.completions.create(model=modele, messages=_messages(prompt),
                                               temperature=cfg.get("temperature", 0))
            texte = r.choices[0].message.content or ""
            texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.S).strip()
            u = r.usage
            return {"output": texte,
                    "tokenUsage": {"total": u.total_tokens, "prompt": u.prompt_tokens,
                                   "completion": u.completion_tokens}}
        except APIStatusError as e:
            if e.status_code != 429 and e.status_code < 500:
                return {"error": f"Erreur Groq {e.status_code} : {str(e)[:200]}"}
            cause = "quota atteint" if e.status_code == 429 else f"erreur serveur {e.status_code}"
        except APIConnectionError:
            cause = "connexion perdue"
        print(f"RELANCE {modele} essai {essai}/{TENTATIVES} : {cause}, attente {ATTENTE_S} s",
              file=sys.stderr, flush=True)
        if essai < TENTATIVES:
            time.sleep(ATTENTE_S)
    return {"error": f"Groq indisponible apres {TENTATIVES} tentatives ({cause})"}