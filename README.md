# Agent de déclaration de sinistres habitation : évaluation et fiabilisation

[![Evals](https://github.com/Ubaysd/deployment-strategist-portfolio/actions/workflows/evals.yml/badge.svg)](https://github.com/Ubaysd/deployment-strategist-portfolio/actions/workflows/evals.yml)

Prototype d'agent qui accompagne un assuré dans la déclaration d'un sinistre habitation en France, avec une démarche d'évaluation systématique de la qualité des réponses.

## Stack

- Modèle principal : gpt-oss-120b via Groq
- Juge des évaluations : Qwen 3.8 27B via Groq (famille distincte du modèle testé)
- Alternatives testées : Llama 3.2 en local via Ollama, gpt-oss-120b via Ollama Cloud, Gemini Flash-Lite
- Évaluation : promptfoo, rejouée en intégration continue par GitHub Actions
- 100&nbsp;% offres gratuites, clés stockées hors du dépôt

## Comparaison des fournisseurs

Script `compare.py` : même question envoyée aux cinq sources, durée et débit mesurés sur 2 exécutions (1 pour Qwen).

| Source | Débit mesuré | Réponse métier correcte |
|---|---|---|
| Ollama local (Llama 3.2) | 4 à 14 tokens/s | Non |
| Ollama Cloud (gpt-oss-120b) | 150 à 191 tokens/s | Non |
| Groq (gpt-oss-120b) | 72 à 214 tokens/s | Oui |
| Gemini Flash-Lite | 11 à 17 tokens/s (relances incluses) | Oui |
| Groq (Qwen 3.8 27B) | 270 tokens/s | Non |

- Débits très variables d'une exécution à l'autre : une mesure isolée ne suffit pas à classer des fournisseurs
- Un même modèle (gpt-oss-120b) ne donne pas la même réponse selon l'hébergeur ni d'un run à l'autre
- Qwen, le plus rapide, ignore la règle métier mais juge correctement dès qu'on lui fournit la référence : la qualité d'un juge dépend du contexte qu'on lui donne

## Évaluation

Jeu de 30 cas répartis par catégorie : délais de déclaration, vol et dépôt de plainte, constat amiable, point de départ du délai, déclaration tardive, hors périmètre, demandes ambiguës, injection de prompt.

| Itération | Changement | Score | Lecture |
|---|---|---|---|
| 1 | Prompt de base, 5 cas | 40&nbsp;% | Faussé : raisonnement interne du modèle inclus dans la réponse notée |
| 2 | Raisonnement masqué | 20&nbsp;% | 3 erreurs métier du modèle, 1 faux échec du juge |
| 3 | Règles de l'article L113-2 ajoutées au prompt | 40&nbsp;% | 5 réponses justes, 3 faux échecs côté tests |
| 4 | Contrôles déterministes corrigés | 100&nbsp;% | 5 cas sur 5 |
| 5 | Jeu étendu à 30 cas | 93&nbsp;% | 2 erreurs graves : l'agent affirmait qu'un simple retard suffit à refuser l'indemnisation |
| 6 | Règle sur la déclaration tardive ajoutée, critère « absence prolongée » durci après relecture métier | 97&nbsp;% | 1 cas non noté : juge indisponible (erreur 503) |
| 7 | Contrôle des montants rendu déterministe | 100&nbsp;% | 30 cas sur 30 |
| 8 | Stabilité : chaque cas rejoué 3 fois (90 réponses) | 96&nbsp;% | Aucune erreur du modèle : 3 cas non notés (juge en 503), 1 contrôle trop strict élargi |
| 9 | Évals lancées en CI (GitHub Actions), juge Gemini | 80&nbsp;% | 6 cas non notés : juge indisponible (erreur 503) |
| 10 | Juge remplacé par Qwen sur Groq, règles de référence fournies dans les critères | 100&nbsp;% | 30 cas sur 30, en local et en CI |

## Stabilité

Chaque cas rejoué 3 fois (90 réponses, cache désactivé, appels espacés de 2,5 s pour respecter le quota de Groq) : 86 réussis.
- 3 échecs dus au juge (Gemini indisponible, erreur 503) : réponses non notées
- 1 faux échec : réponse correcte (« garanties souscrites », « franchise », « expertise ») rejetée par un contrôle limité au mot « contrat », élargi depuis
- Aucune erreur du modèle sur les 87 réponses notées

## Intégration continue

Les 30 cas sont rejoués automatiquement par GitHub Actions à chaque modification du prompt, des tests ou du workflow : une régression fait échouer le build.
- Clés d'API stockées en secrets chiffrés du dépôt
- Appels espacés de 10 s : quota Groq de 8 000 tokens par minute et par modèle, prompt et réponse compris
- Juge déplacé de Gemini (erreurs 503 répétées, jusqu'à 6 cas non notés sur un run) vers Qwen sur Groq, avec les règles de référence fournies dans les critères
- Publication locale conditionnée à un score de 30/30 (barrière de qualité)

## Causes d'échec identifiées

- Connaissance métier absente : constat amiable, délai de 2 jours ouvrés pour un vol, récépissé de dépôt de plainte, conditions de la déchéance pour retard
- Réponse polluée par le raisonnement interne du modèle
- Typographie française : espace fine insécable (U+202F) entre le chiffre et « jours », non reconnue par la regex
- Juge LLM instable ou indisponible : une même réponse notée tantôt réussie, tantôt échouée, et des erreurs 503 aux heures de forte demande
- Critère de notation ambigu : deux juges en désaccord sur la même réponse

## Enseignements

- Un PASS ne garantit pas une bonne réponse : la relecture métier a révélé une réponse validée par le juge mais contradictoire dans sa conclusion
- Les erreurs se pondèrent par leur gravité : une erreur sur le droit à indemnisation pèse plus qu'une formulation imprécise
- Contrôles déterministes (`icontains`, `regex`, `not-regex`) dès que possible, juge LLM réservé aux critères qualitatifs
- Une partie des échecs venait des tests et non du modèle : l'évaluation doit elle-même être évaluée
- Un juge doit recevoir la vérité de référence : sans elle, il note avec ses propres connaissances, parfois inexactes
- Deux juges en désaccord signalent un critère mal formulé

## Limites et évolutions

- Score obtenu sur les cas ayant servi à ajuster le prompt : constitution d'un jeu hold-out de cas jamais vus
- Règles écrites dans le prompt : remplacement par un RAG sur les conditions générales
- Red teaming automatisé
- Juge de secours en cas d'indisponibilité du juge principal

## Reproduire

En local :

    pip install openai python-dotenv
    python compare.py
    npx promptfoo@latest eval -c evals/promptfooconfig.yaml -j 1 --delay 10000

Clés attendues dans un fichier `.env` (non versionné) : `GROQ_API_KEY`, `GEMINI_API_KEY`.

En CI, relance manuelle :

    gh workflow run evals.yml

## Structure

- `compare.py` : comparaison des fournisseurs
- `evals/promptfooconfig.yaml` : prompt de l'agent, modèle testé et juge
- `evals/tests.yaml` : les 30 cas de test
- `.github/workflows/evals.yml` : intégration continue (GitHub Actions)

Source des règles : Code des assurances, article L113-2 (délai de déclaration de 5 jours ouvrés minimum, ramené à 2 jours ouvrés en cas de vol ; déchéance pour retard opposable seulement si le contrat la prévoit et si l'assureur prouve un préjudice).