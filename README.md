# Agent de déclaration de sinistres habitation : évaluation et fiabilisation

[![Contrôle rapide](https://github.com/Ubaysd/deployment-strategist-portfolio/actions/workflows/evals.yml/badge.svg)](https://github.com/Ubaysd/deployment-strategist-portfolio/actions/workflows/evals.yml) [![Éval complète](https://github.com/Ubaysd/deployment-strategist-portfolio/actions/workflows/evals-complet.yml/badge.svg)](https://github.com/Ubaysd/deployment-strategist-portfolio/actions/workflows/evals-complet.yml)

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

Jeu de 30 cas : 20 à contrôle automatique (délais, vol et dépôt de plainte, constat amiable, montants, injection de prompt) et 10 notés par le juge (point de départ du délai, déclaration tardive, hors périmètre, demande ambiguë, changement de rôle).

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
| 11 | Juge avec raisonnement complet, mesure du temps de CI | 100&nbsp;% | 30 cas sur 30 en 14 min, dont 8 min 39 d'attente après une seule erreur 429 |

## Stabilité

Chaque cas rejoué 3 fois (90 réponses, cache désactivé, appels espacés pour respecter le quota de Groq) : 86 réussis.
- 3 échecs dus au juge (Gemini indisponible, erreur 503) : réponses non notées
- 1 faux échec : réponse correcte (« garanties souscrites », « franchise », « expertise ») rejetée par un contrôle limité au mot « contrat », élargi depuis
- Aucune erreur du modèle sur les 87 réponses notées

## Intégration continue

Deux niveaux, sur le modèle des suites de tests longues :
- Contrôle rapide à chaque modification du prompt, des tests ou des workflows : les 20 cas à contrôle automatique, sans juge
- Éval complète chaque nuit et à la demande : les 30 cas, juge au raisonnement complet, timeout de 60 minutes

Pourquoi deux niveaux : les quotas gratuits de Groq (8 000 tokens par minute pour l'agent, 1 000 tokens générés par minute pour le juge) provoquent ponctuellement une erreur 429. promptfoo attend alors plusieurs minutes avant de réessayer, très probablement parce qu'il lit le délai dans l'en-tête de remise à zéro du quota journalier (« 6h8m38.4s » lu comme 8 min 38) au lieu du délai réel de quelques secondes. Sans juge, le contrôle rapide ne frôle plus les quotas.

- Clés d'API stockées en secrets chiffrés du dépôt
- Appels de l'agent espacés de 10 s
- Publication locale conditionnée à un contrôle rapide sans échec (barrière de qualité)

## Causes d'échec identifiées

- Connaissance métier absente : constat amiable, délai de 2 jours ouvrés pour un vol, récépissé de dépôt de plainte, conditions de la déchéance pour retard
- Réponse polluée par le raisonnement interne du modèle
- Typographie française : espace fine insécable (U+202F) entre le chiffre et « jours », non reconnue par la regex
- Juge LLM instable ou indisponible : une même réponse notée tantôt réussie, tantôt échouée, et des erreurs 503 aux heures de forte demande
- Critère de notation ambigu : deux juges en désaccord sur la même réponse
- Gestion des quotas par l'outil d'évaluation : attente de plusieurs minutes après une erreur 429 au lieu de quelques secondes

## Enseignements

- Un PASS ne garantit pas une bonne réponse : la relecture métier a révélé une réponse validée par le juge mais contradictoire dans sa conclusion
- Les erreurs se pondèrent par leur gravité : une erreur sur le droit à indemnisation pèse plus qu'une formulation imprécise
- Contrôles déterministes (`icontains`, `regex`, `not-regex`) dès que possible, juge LLM réservé aux critères qualitatifs
- Une partie des échecs venait des tests et non du modèle : l'évaluation doit elle-même être évaluée
- Un juge doit recevoir la vérité de référence : sans elle, il note avec ses propres connaissances, parfois inexactes
- Deux juges en désaccord signalent un critère mal formulé
- Mesurer avant de corriger : la décomposition du temps de CI (300 s de délai, 519 s d'attente, 32 s d'appels) a isolé la cause réelle là où plusieurs réglages successifs avaient échoué

## Limites et évolutions

- Score obtenu sur les cas ayant servi à ajuster le prompt : constitution d'un jeu hold-out de cas jamais vus
- Règles écrites dans le prompt : remplacement par un RAG sur les conditions générales
- Red teaming automatisé
- Juge de secours en cas d'indisponibilité du juge principal
- Signalement à promptfoo de la lecture de l'en-tête de quota de Groq

## Reproduire

En local :

    pip install openai python-dotenv
    python compare.py
    npx promptfoo@latest eval -c evals/promptfooconfig-rapide.yaml -j 1 --delay 10000
    npx promptfoo@latest eval -c evals/promptfooconfig.yaml -j 1 --delay 10000

Clé attendue dans un fichier `.env` (non versionné) : `GROQ_API_KEY`.

En CI, relance manuelle :

    gh workflow run evals.yml
    gh workflow run evals-complet.yml

## Structure

- `compare.py` : comparaison des fournisseurs
- `evals/prompt.txt` : prompt de l'agent, partagé par les deux configurations
- `evals/promptfooconfig-rapide.yaml` : contrôle rapide, sans juge
- `evals/promptfooconfig.yaml` : éval complète, avec le juge
- `evals/tests.yaml` : les 20 cas à contrôle automatique
- `evals/tests-juge.yaml` : les 10 cas notés par le juge
- `.github/workflows/evals.yml` : contrôle rapide à chaque modification
- `.github/workflows/evals-complet.yml` : éval complète nocturne et à la demande

Source des règles : Code des assurances, article L113-2 (délai de déclaration de 5 jours ouvrés minimum, ramené à 2 jours ouvrés en cas de vol ; déchéance pour retard opposable seulement si le contrat la prévoit et si l'assureur prouve un préjudice).