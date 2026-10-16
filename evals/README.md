# Évals — Agent de déclaration de sinistres habitation (semaine 1)

Agent qui aide un assuré à déclarer un sinistre habitation en France.
- Modèle testé : gpt-oss-120b via Groq
- Juge : Gemini Flash-Lite (offre gratuite)
- Outil : promptfoo, 5 cas de test

## Résultats par itération

| Run | Changement | Score | Lecture |
|---|---|---|---|
| 1 | Prompt de base | 40 % | Faussé : raisonnement interne du modèle inclus dans la réponse notée |
| 2 | `showThinking: false` | 20 % | 3 erreurs métier du modèle + 1 faux échec du juge |
| 3 | Règles de l'article L113-2 ajoutées au prompt, regex sur les délais | 40 % | Les 5 réponses sont justes ; 3 faux échecs côté tests |
| 4 | Regex tolérante aux espaces, vérification « récépissé » sans juge | **100 %** | 5/5 |

## Causes d'échec identifiées

- Connaissance métier absente : « constat d'incident » au lieu du constat amiable, 5 jours au lieu de 2 jours ouvrés pour un vol, procès-verbal au lieu du récépissé de dépôt de plainte
- Sortie polluée par le raisonnement interne du modèle
- Typographie française : espace fine insécable (U+202F) entre le chiffre et « jours », non reconnue par la regex
- Juge LLM instable : la même réponse notée PASS puis FAIL d'un run à l'autre

## Enseignements

- Vérification déterministe (`icontains`, `regex`) dès que c'est possible ; juge LLM réservé aux critères qualitatifs
- Sur les échecs analysés, une partie venait des tests et non du modèle : il faut évaluer l'évaluation elle-même
- Injecter les règles métier dans le prompt a corrigé les 3 erreurs métier

## Limites et prochaines étapes

- 5 cas, c'est trop peu : passer à 30-50 cas (normaux, limites, hors périmètre)
- 1 réponse par cas : répéter chaque cas (`--repeat`) pour mesurer la stabilité
- Règles écrites en dur dans le prompt : les remplacer par un RAG sur les conditions générales
- Ajouter du red teaming (injection de prompt)

## Reproduire

    npx promptfoo@latest eval -c evals/promptfooconfig.yaml -j 1

Source des règles : Code des assurances, article L113-2 (délai de déclaration de 5 jours ouvrés minimum, ramené à 2 jours ouvrés en cas de vol).