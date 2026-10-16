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

Mesure ponctuelle : d'un run à l'autre, le classement Groq / Ollama Cloud s'est inversé, et un même modèle n'a pas toujours donné la même réponse.

## Évaluation

Jeu de 30 cas répartis par catégorie : délais de déclaration, vol et dépôt de plainte, constat amiable, point de départ du délai, déclaration tardive, hors périmètre, demandes ambiguës, injection de prompt.

| Itération | Changement | Score | Lecture |
|---|---|---|---|
| 1 | Prompt de base, 5 cas | 40 % | Faussé : raisonnement interne du modèle inclus dans la réponse notée |
| 2 | Raisonnement masqué | 20 % | 3 erreurs métier du modèle, 1 faux échec du juge |
| 3 | Règles de l'article L113-2 ajoutées au prompt | 40 % | 5 réponses justes, 3 faux échecs côté tests |
| 4 | Contrôles déterministes corrigés | 100 % | 5 cas sur 5 |
| 5 | Jeu étendu à 30 cas | 93 % | 2 erreurs graves : l'agent affirmait qu'un simple retard suffit à refuser l'indemnisation |
| 6 | Règle sur la déclaration tardive ajoutée, critère « absence prolongée » durci après relecture métier | 97 % | 1 cas non noté : juge indisponible (erreur 503) |
| 7 | Contrôle des montants rendu déterministe | 100 % | 30 cas sur 30 |

## Stabilité

Chaque cas rejoué 3 fois (90 réponses, cache désactivé, appels espacés de 2,5 s pour respecter le quota de Groq) : 86 réussis.
- 3 échecs dus au juge (Gemini indisponible, erreur 503) : réponses non notées
- 1 faux échec : réponse correcte (« garanties souscrites », « franchise », « expertise ») rejetée par un contrôle limité au mot « contrat », élargi depuis
- Aucune erreur du modèle sur les 87 réponses notées
## Causes d'échec identifiées

- Connaissance métier absente : constat amiable, délai de 2 jours ouvrés pour un vol, récépissé de dépôt de plainte, conditions de la déchéance pour retard
- Réponse polluée par le raisonnement interne du modèle
- Typographie française : espace fine insécable (U+202F) entre le chiffre et « jours », non reconnue par la regex
- Juge LLM instable ou indisponible : une même réponse notée tantôt réussie, tantôt échouée, et des erreurs 503 aux heures de forte demande

## Enseignements

- Un PASS ne garantit pas une bonne réponse : la relecture métier a révélé une réponse validée par le juge mais contradictoire dans sa conclusion
- Les erreurs se pondèrent par leur gravité : une erreur sur le droit à indemnisation pèse plus qu'une formulation imprécise
- Contrôles déterministes (`icontains`, `regex`, `not-regex`) dès que possible, juge LLM réservé aux critères qualitatifs
- Une partie des échecs venait des tests et non du modèle : l'évaluation doit elle-même être évaluée

## Limites et évolutions

- Score obtenu sur les cas ayant servi à ajuster le prompt : constitution d'un jeu hold-out de cas jamais vus
- Une réponse par cas : répétitions pour mesurer la stabilité
- Règles écrites dans le prompt : remplacement par un RAG sur les conditions générales
- Red teaming automatisé
- Évaluations lancées automatiquement à chaque modification (GitHub Actions), avec un juge de secours

## Reproduire

    pip install openai python-dotenv
    python compare.py
    npx promptfoo@latest eval -c evals/promptfooconfig.yaml -j 1

Clés attendues dans un fichier `.env` (non versionné) : `GROQ_API_KEY`, `GEMINI_API_KEY`.

## Structure

- `compare.py` : comparaison des fournisseurs
- `evals/promptfooconfig.yaml` : prompt, modèle testé et juge
- `evals/tests.yaml` : les 30 cas de test

Source des règles : Code des assurances, article L113-2 (délai de déclaration de 5 jours ouvrés minimum, ramené à 2 jours ouvrés en cas de vol ; déchéance pour retard opposable seulement si le contrat la prévoit et si l'assureur prouve un préjudice).