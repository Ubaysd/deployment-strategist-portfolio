# Agent de déclaration de sinistres habitation : évaluation et fiabilisation

Prototype d'agent qui accompagne un assuré dans la déclaration d'un sinistre habitation en France, avec une démarche d'évaluation systématique de la qualité des réponses.

## Stack

- Modèle principal : gpt-oss-120b via Groq
- Juge des évaluations : Gemini Flash-Lite
- Alternatives testées : Llama 3.2 en local via Ollama, gpt-oss-120b via Ollama Cloud
- Évaluation : promptfoo
- 100 % offres gratuites, clés stockées hors du dépôt

## Comparaison des fournisseurs

Script `compare.py` : même question envoyée aux quatre sources, durée et débit mesurés.

| Source | Débit mesuré | Réponse métier correcte |
|---|---|---|
| Ollama local (Llama 3.2) | 14 tokens/s | Non |
| Ollama Cloud (gpt-oss-120b) | 191 tokens/s | Non |
| Groq (gpt-oss-120b) | 214 tokens/s | Oui |
| Gemini Flash-Lite | 11 tokens/s (relances incluses) | Oui |

Mesure ponctuelle, à confirmer sur plusieurs exécutions : d'un run à l'autre, le classement Groq / Ollama Cloud s'est inversé, et un même modèle n'a pas toujours donné la même réponse.

## Évaluation

| Itération | Changement | Score | Lecture |
|---|---|---|---|
| 1 | Prompt de base | 40 % | Faussé : raisonnement interne du modèle inclus dans la réponse notée |
| 2 | Raisonnement masqué (`showThinking: false`) | 20 % | 3 erreurs métier du modèle, 1 faux échec du juge |
| 3 | Règles de l'article L113-2 ajoutées au prompt, regex sur les délais | 40 % | 5 réponses justes, 3 faux échecs côté tests |
| 4 | Regex tolérante aux espaces, contrôle « récépissé » sans juge | 100 % | 5 cas sur 5 |

## Causes d'échec identifiées

- Connaissance métier absente : « constat d'incident » au lieu du constat amiable, 5 jours au lieu de 2 jours ouvrés pour un vol, procès-verbal au lieu du récépissé de dépôt de plainte
- Réponse polluée par le raisonnement interne du modèle
- Typographie française : espace fine insécable (U+202F) entre le chiffre et « jours », non reconnue par la regex
- Juge LLM instable : une même réponse notée tantôt réussie, tantôt échouée

## Enseignements

- Contrôles déterministes (`icontains`, `regex`) dès que possible, juge LLM réservé aux critères qualitatifs
- Une partie des échecs venait des tests et non du modèle : l'évaluation doit elle-même être évaluée
- L'ajout des règles métier au prompt a corrigé les 3 erreurs métier

## Limites et évolutions

- Jeu de test réduit (5 cas) : extension à 30-50 cas normaux, limites et hors périmètre
- Une réponse par cas : répétitions (`--repeat`) pour mesurer la stabilité
- Règles écrites dans le prompt : remplacement par un RAG sur les conditions générales
- Tests d'injection de prompt (red teaming)

## Reproduire

    pip install openai python-dotenv
    python compare.py
    npx promptfoo@latest eval -c evals/promptfooconfig.yaml -j 1

Clés attendues dans un fichier `.env` (non versionné) : `GROQ_API_KEY`, `GEMINI_API_KEY`.

## Structure

- `compare.py` : comparaison des fournisseurs
- `evals/promptfooconfig.yaml` : prompt, modèles et cas de test

Source des règles : Code des assurances, article L113-2 (délai de déclaration de 5 jours ouvrés minimum, ramené à 2 jours ouvrés en cas de vol).