# Lots de réalisation et critères de validation

## Principes d'exécution

- Un lot n'est terminé que lorsque ses contrôles passent.
- Aucun scanner OT n'est développé avant la politique de cible et la gateway.
- Les options `Could` ne commencent qu'après validation du parcours complet.
- Après chaque lot : liste des fichiers modifiés, tests exécutés et écarts documentés.

## Lot 0 - Baseline et point de reprise

**But :** figer le socle stabilisé avant l'OT.

**Travaux :**

- créer une branche `codex/iass-ot-mvp` après accord ;
- réaliser le premier commit du socle et des documents de conception ;
- vérifier l'absence de secret ;
- enregistrer les commandes de baseline.

**Acceptation :**

- frontend lint/typecheck/build verts ;
- backend Ruff/mypy verts ;
- dev et prod se construisent ;
- `/health`, `/api/health`, register et login fonctionnent ;
- arbre Git propre après commit.

**Estimation :** 0,5 jour.

## Lot 1 - Gateway OT déterministe

**But :** fournir la cible locale avant d'adapter le scanner.

**Travaux :** état, rôles, JWT gateway, endpoints, reset, deux profils, audit et rate limits.

**Acceptation :**

- healthcheck vert ;
- reset restaure exactement les valeurs initiales ;
- matrice RBAC/zone passe en hardened ;
- comportements volontairement faibles présents en vulnerable ;
- aucune route ne contacte un équipement externe ;
- tests gateway verts dans les deux profils.

**Estimation :** 2 jours.

## Lot 2 - Enveloppe de sécurité du scanner

**But :** garantir que l'outil ne devient pas un SSRF ou un générateur de charge.

**Travaux :** TargetPolicy, redaction, budget partagé, SafeScannerClient, timeouts, limite de réponse, redirects off, nouveau ScanRequest.

**Acceptation :**

- seule la target key fermée est acceptée ;
- tous les cas localhost/metadata/autre host sont rejetés sans réseau ;
- la 61e requête est impossible ;
- timeouts 3/5 s et redirects off prouvés ;
- secrets imbriqués masqués ;
- plus de champ URL/token/max_requests dans l'UI ou l'API.

**Estimation :** 1 jour.

## Lot 3 - Quatre contrôles API spécialisés

**But :** transformer les moteurs génériques en tests déterministes de la gateway.

**Travaux :** Auth, BOLA, SQLi et rate limit classique selon les règles exactes.

**Acceptation :**

- résultats attendus dans les deux profils ;
- quatre payloads SQL maximum, aucun destructif ou long time-based ;
- huit connexions invalides maximum ;
- BOLA utilise les deux zones ;
- chaque preuve respecte redaction/taille/budget.

**Estimation :** 1 jour.

## Lot 4 - Trois contrôles OT

**But :** produire la valeur différenciante du projet.

**Travaux :** autorisation OT, audit OT et rate limiting OT.

**Acceptation :**

- vulnerable : constats High/Critical attendus ;
- hardened : refus, audit complet et 429+Retry-After ;
- emergency stop jamais confirmé ;
- scanner audit restaure la pompe ;
- erreur réseau arrête immédiatement le moteur concerné.

**Estimation :** 1 jour.

## Lot 5 - Orchestration, données et score

**But :** rendre les sept résultats persistants et explicables.

**Travaux :** champs Scan/TestResult, threadpool, statuts, métriques, score et pagination 20.

**Acceptation :**

- orchestration hors boucle async ;
- erreur partielle conserve les résultats précédents ;
- request_count égale les appels réels ;
- score conforme aux poids et plancher ;
- scan complet < 60 s et <= 60 requêtes ;
- propriété inter-utilisateur toujours 403.

**Estimation :** 1 jour.

## Lot 6 - Interface et rapport

**But :** rendre le scénario présentable sans exposer la complexité technique.

**Travaux :** dashboard OT, cible fixe, profil, sept cases groupées, confirmation, historique enrichi, résultats, rapport HTML.

**Acceptation :**

- parcours register -> login -> scan -> résultats -> rapport ;
- UI utilisable à 1280x720 ;
- cible non éditable et profil issu du backend ;
- cartes triées et trois états visibles ;
- rapport imprimable sans secret ;
- build frontend vert.

**Estimation :** 1 jour.

## Lot 7 - Qualité, documentation et démonstration

**But :** rendre la v1 reproductible et défendable en entretien.

**Travaux :** tests essentiels, README, SECURITY, architecture réelle, captures, script de démonstration, nettoyage des dépendances.

**Acceptation :**

- Docker complet avec healthchecks ;
- deux profils reproductibles après reset ;
- tests backend obligatoires verts ;
- lint/typecheck/build frontend verts ;
- clone propre démarré en moins de 20 minutes ;
- démonstration répétée en 5-7 minutes ;
- captures sans secret ;
- crédits et limites présents.

**Estimation :** 1,5 jour.

## Marge J9-J10

Ordre strict :

1. corriger les défauts Must ;
2. améliorer lisibilité et démonstration ;
3. export JSON ;
4. filtres ou comparaison visuelle ;
5. événement Wazuh ;
6. quelques tests React.

Les options ne doivent jamais remplacer target policy, trois scanners OT, deux profils, tests backend, README ou rapport.

## Matrice de validation finale

| Domaine | Commande/scénario | Résultat requis |
|---|---|---|
| Backend statique | Ruff + mypy | Aucun échec. |
| Backend tests | pytest + coverage ciblée | Tous les Must verts. |
| Gateway | pytest dans les deux profils | Matrice opposée déterministe. |
| Frontend | pnpm lint/typecheck/build | Aucun échec. |
| Compose | build + up + ps | Services sains. |
| Parcours | register/login/scan/report | Terminé sans manipulation DB. |
| Sécurité | target/redaction/budget | Cas positifs et négatifs verts. |
| Performance | scan complet | < 60 s, <= 60 requêtes. |
| Confidentialité | logs/preuves/rapport/captures | Aucun secret. |
| Reproductibilité | clone propre + README | < 20 minutes. |

## Définition de terminé v1.0

- Les sept contrôles sont présents et explicites.
- Les deux profils produisent les écarts attendus.
- La cible hors allowlist est techniquement impossible.
- Les résultats, le score et le rapport sont cohérents.
- Le projet ne contacte que la gateway Docker locale.
- Les tests essentiels et builds sont verts.
- La documentation permet à une autre personne de reproduire la démonstration.
