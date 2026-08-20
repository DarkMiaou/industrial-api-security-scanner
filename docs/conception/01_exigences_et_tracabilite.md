# Exigences vérifiables et traçabilité

## Légende

- **Couvert** : le socle satisfait déjà l'exigence.
- **Partiel** : un mécanisme existe mais doit être adapté.
- **Absent** : rien dans le socle ne satisfait l'exigence.
- **Conflit** : le comportement actuel va à l'encontre de l'exigence.

## 1. Périmètre et gouvernance

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| SCP-01 | Le produit représente une station de pompage simulée, pas une plateforme multi-sites. | Must | Une seule gateway et un seul jeu d'actifs sont présents. | Absent |
| SCP-02 | Aucun équipement ou protocole industriel réel n'est utilisé. | Must | Aucun client Modbus, OPC UA, DNP3 ou accès matériel dans les dépendances. | Couvert |
| SCP-03 | Aucun scan Internet ou cible arbitraire n'est possible. | Must | Toute cible autre que la clé fermée est rejetée avant I/O réseau. | Conflit |
| SCP-04 | Aucun payload destructif ni test de déni de service n'est exécuté. | Must | Revue des payloads et tests démontrant les volumes maximaux. | Conflit |
| SCP-05 | Les fonctions Redis, Celery, SOC, découverte OpenAPI, GraphQL et SOAP restent hors v1. | Must | Absence de ces services et fonctions dans le parcours v1. | Couvert |
| SCP-06 | IEC 62443 est un contexte, jamais une déclaration de conformité. | Must | README et rapport contiennent une limitation explicite. | Absent |
| SCP-07 | L'attribution du projet source et la licence AGPL sont conservées. | Must | LICENSE, crédits et commit source dans le README. | Partiel |

## 2. Plateforme existante

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| PLT-01 | Un utilisateur peut s'inscrire et se connecter. | Must | Register 201, login 200 et JWT valide. | Couvert |
| PLT-02 | Les mots de passe sont hashés avec bcrypt. | Must | Aucun mot de passe en clair en base. | Couvert |
| PLT-03 | Les routes de scans exigent un JWT valide. | Must | Appel sans Bearer token = 401/403. | Couvert |
| PLT-04 | Un utilisateur ne peut lire ou supprimer le scan d'un autre. | Must | Utilisateur B sur scan A = 403. | Couvert, test absent |
| PLT-05 | L'historique est paginé, trié du plus récent au plus ancien. | Must | GET scans avec skip/limit, ordre descendant. | Couvert |
| PLT-06 | La suppression d'un scan supprime ses résultats. | Must | DELETE = 204 et cascade en base. | Couvert |
| PLT-07 | Le doublon d'e-mail retourne 409. | Should | Test API précis. | Partiel : 400 actuel |
| PLT-08 | La connexion peut renvoyer token, type et utilisateur public. | Should | Contrat frontend/backend cohérent. | Partiel : utilisateur reconstruit côté UI |

## 3. Gateway OT simulée

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| GTW-01 | Un service Docker `ot-gateway-demo` écoute en interne sur 8081. | Must | Healthcheck vert et résolution DNS interne. | Absent |
| GTW-02 | `OT_PROFILE` sélectionne `vulnerable` ou `hardened` au démarrage. | Must | Deux exécutions produisent les comportements attendus. | Absent |
| GTW-03 | L'état initial contient pump-001 Zone A stopped et pump-002 Zone B running. | Must | GET pompes après reset. | Absent |
| GTW-04 | La télémétrie initiale vaut 2.5 bar, 120 L/min, niveau 65 %, arrêt d'urgence faux. | Must | GET telemetry après reset. | Absent |
| GTW-05 | Les rôles Guest, Operator, Supervisor et Admin existent. | Must | Jetons distincts et revendication de rôle vérifiable. | Absent |
| GTW-06 | Le mode hardened applique RBAC et appartenance de zone. | Must | Matrice de tests 401/403/200. | Absent |
| GTW-07 | Le mode vulnerable relâche volontairement RBAC, BOLA, audit, SQLi et rate limiting. | Must | Tests d'intégration opposés au mode hardened. | Absent |
| GTW-08 | Les endpoints définis dans le dossier existent exactement. | Must | OpenAPI et tests des 10 routes métier + health. | Absent |
| GTW-09 | `/demo/reset` restaure un état déterministe et exige une clé de démonstration. | Must | Mauvaise clé refusée ; bonne clé remet toutes les valeurs initiales. | Absent |
| GTW-10 | L'audit hardened contient actor, action, resource, result, timestamp et correlation_id. | Must | Recherche de l'événement après commande. | Absent |
| GTW-11 | Le rate limiting hardened applique 5 commandes/4 s puis 429 + Retry-After. | Must | Test déterministe en moins de 8 requêtes. | Absent |
| GTW-12 | Emergency stop n'est jamais réellement déclenché par le scanner. | Must | Aucun appel avec confirmation vraie dans les traces. | Absent |

## 4. Sécurité propre au scanner

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| SEC-01 | Le client transmet une clé de cible fermée, jamais une URL. | Must | Schéma refuse `target_url` et n'accepte que `ot-gateway-demo`. | Conflit |
| SEC-02 | Le backend résout la clé vers `http://ot-gateway-demo:8081`. | Must | Test unitaire de politique de cible. | Absent |
| SEC-03 | Localhost, metadata IP, autres hosts, ports et schémas sont refusés. | Must | Table de cas négatifs sans appel réseau. | Absent |
| SEC-04 | Les redirections HTTP sont désactivées. | Must | Réponse 30x non suivie dans un test. | Conflit : requests les suit |
| SEC-05 | Timeout connexion 3 s et lecture 5 s. | Must | Client configuré et tests timeout. | Conflit : 180 s actuel |
| SEC-06 | Une réponse lue est plafonnée à 1 Mio. | Must | Test d'une réponse supérieure au plafond. | Absent |
| SEC-07 | Le budget global est de 60 requêtes maximum par scan. | Must | Compteur partagé bloque la 61e requête. | Conflit : max_requests n'est pas un plafond |
| SEC-08 | Le nombre de requêtes réellement émises est persisté. | Must | `Scan.request_count` correspond au compteur partagé. | Absent |
| SEC-09 | Les preuves masquent Authorization, Cookie, Set-Cookie, token, password, secret et key. | Must | Tests d'expurgation imbriquée et insensible à la casse. | Partiel |
| SEC-10 | Les extraits de réponse sont limités à 500 caractères. | Must | Assertion sur la preuve persistée. | Partiel |
| SEC-11 | Les jetons gateway sont distincts du JWT de la plateforme. | Must | Secrets, émetteurs et usages séparés. | Absent |
| SEC-12 | L'utilisateur ne saisit plus de jeton cible. | Must | Aucun champ token dans l'UI ou ScanRequest. | Conflit |
| SEC-13 | L'utilisateur confirme son autorisation avant lancement. | Must | Case obligatoire côté UI et booléen validé côté API. | Absent |
| SEC-14 | Toute latence anormale ou erreur réseau arrête le moteur concerné. | Must | Résultat `error` explicite, sans poursuite de sa boucle. | Partiel |

## 5. Sept contrôles déterministes

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| CTL-01 | Auth : GET `/telemetry` sans token puis Bearer invalide ; 401/403 safe, 2xx High. | Must | Tests vulnerable/hardened. | Partiel : scanner générique |
| CTL-02 | BOLA : Operator A lit pump-001 puis pump-002 ; 200 hors zone High, 403/404 safe. | Must | Baseline 200 obligatoire puis cas croisé. | Partiel : scanner générique |
| CTL-03 | SQLi : baseline order 100 et au plus 4 payloads non destructifs, sans long time-based. | Must | Signature SQL ou différence stable = Critical. | Conflit : payloads trop larges/time-based |
| CTL-04 | Rate limit classique : au plus 8 connexions invalides ; 429 safe sinon Medium. | Must | Aucun contournement par en-têtes IP. | Conflit : beaucoup plus de requêtes/bypass |
| CTL-05 | Autorisation OT : pump.start Guest/Operator et emergency-stop sans confirmation. | Must | 2xx = High/Critical selon l'action. | Absent |
| CTL-06 | Audit OT : commande corrélée, recherche Admin, validation des champs, puis restauration. | Must | Absent High, incomplet Medium, complet safe. | Absent |
| CTL-07 | Rate limit OT : au plus 8 commandes idempotentes espacées de 0,5 s. | Must | 429+Retry-After safe, sans header Low, aucun 429 High. | Absent |
| CTL-08 | Les contrôles sont exécutables individuellement ou ensemble. | Must | 7 choix API/UI et résultat par choix. | Partiel : 4 choix |
| CTL-09 | Une erreur d'un contrôle ne supprime pas les résultats précédents. | Must | Test d'orchestration avec moteur défaillant. | Couvert conceptuellement, test absent |
| CTL-10 | L'ordre complet est auth, IDOR, SQLi, rate limit, authz OT, audit OT, rate limit OT. | Should | Résultats ordonnés ou ordre d'appel testé. | Partiel |

## 6. Orchestration, données et score

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| DAT-01 | Scan porte status, profile, score, request_count, duration_ms et completed_at. | Must | Colonnes, schémas et réponses cohérents. | Absent |
| DAT-02 | TestResult porte title, endpoint, method et ot_impact. | Must | Colonnes et cartes UI cohérentes. | Absent |
| DAT-03 | Evidence et recommandations restent en JSON. | Must | Persistance de structures variables. | Couvert |
| DAT-04 | Aucun jeton ou mot de passe gateway n'est persisté. | Must | Inspection base et fixtures. | Partiel |
| ORC-01 | Un Scan est créé avant l'exécution. | Must | Scan `running` visible en base pendant l'orchestration. | Partiel |
| ORC-02 | L'orchestration synchrone s'exécute dans un threadpool. | Must | La route async n'exécute pas directement requests. | Absent |
| ORC-03 | Le statut final vaut completed, partial ou failed selon les résultats. | Must | Tests sur combinaisons safe/vulnerable/error. | Absent |
| ORC-04 | Score = max(0, 100 - 30C - 15H - 7M - 2L). | Must | Tests des poids et plancher zéro. | Absent |
| ORC-05 | Les erreurs n'abaissent pas le score mais sont comptées séparément. | Must | Test de score avec résultat error. | Absent |
| ORC-06 | Le scan complet local termine en moins de 60 s. | Must | Mesure automatisée ou smoke test horodaté. | Non démontré |

## 7. Contrats API et interface

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| API-01 | POST `/scans/` accepte target fermé, tests et confirmation d'autorisation. | Must | 201 après scan ; 422 sur cible/confirmation invalide. | Conflit |
| API-02 | GET `/scans/` applique skip/limit avec limite par défaut 20. | Must | Tests de pagination. | Partiel : défaut 100 |
| API-03 | GET et DELETE d'un scan vérifient le propriétaire. | Must | 403 inter-utilisateur. | Couvert |
| API-04 | GET `/scans/{id}/report` retourne un HTML imprimable au propriétaire. | Must | 200 HTML, 403 autre utilisateur. | Absent |
| API-05 | Une route authentifiée expose cible, profil courant et tests disponibles. | Must | L'UI n'invente pas le profil. | Absent |
| API-06 | Les réponses utilisent un format de résultat standard OT. | Must | Types backend/frontend et guards alignés. | Absent |
| UI-01 | Le titre devient Industrial API Security Scanner avec badge laboratoire OT. | Must | Revue visuelle 1280x720. | Absent |
| UI-02 | La cible Water Pump Gateway est affichée mais non éditable. | Must | Aucun champ URL. | Conflit |
| UI-03 | Le profil vulnerable/hardened est affiché. | Must | Valeur provenant du backend. | Absent |
| UI-04 | Sept cases, cochées par défaut et regroupées API/OT, sont présentes. | Must | Test composant ou revue manuelle. | Partiel |
| UI-05 | Une confirmation d'autorisation est obligatoire. | Must | Bouton désactivé ou validation explicite. | Absent |
| UI-06 | Historique affiche statut, score, Critical et High. | Must | Valeurs présentes pour chaque scan. | Absent |
| UI-07 | Résultats affichent profil, durée, requêtes, score, compteurs, endpoint, rôle/impact et preuve. | Must | Revue du scénario complet. | Absent |
| UI-08 | Les cartes sont triées par sévérité et distinguent safe/vulnerable/error. | Must | Ordre Critical à Info et styles visibles. | Partiel |

## 8. Rapport, qualité et documentation

| ID | Exigence vérifiable | Priorité | Vérification attendue | Socle |
|---|---|---:|---|---|
| RPT-01 | Le rapport HTML contient synthèse, périmètre, constats, erreurs, limites et avertissement légal. | Must | Revue du HTML vulnerable et hardened. | Absent |
| RPT-02 | Le rapport est imprimable avec `window.print()`. | Must | Aperçu impression navigateur lisible. | Absent |
| RPT-03 | Le rapport et les captures ne contiennent aucun secret. | Must | Recherche automatisée de marqueurs sensibles. | Absent |
| NFR-01 | Docker Compose démarre tous les services avec healthchecks. | Must | Tous les conteneurs healthy/running. | Partiel |
| NFR-02 | Les différences vulnerable/hardened sont déterministes après reset. | Must | Deux exécutions répétées identiques. | Absent |
| NFR-03 | L'interface est utilisable en 1280x720. | Must | Revue navigateur. | Non démontré |
| NFR-04 | Un clone propre est reproductible en moins de 20 minutes. | Must | Test chronométré du README. | Partiel |
| NFR-05 | Aucun secret réel n'est dans Git, logs, preuves ou captures. | Must | scan de secrets + tests de redaction. | Partiel |
| TST-01 | Tests unitaires de target policy. | Must | Allowlist positive et cas SSRF négatifs. | Absent |
| TST-02 | Tests unitaires de redaction. | Must | En-têtes et JSON imbriqué. | Absent |
| TST-03 | Tests des trois scanners OT dans les deux profils. | Must | Six cas principaux verts. | Absent |
| TST-04 | Test BOLA des deux zones. | Must | 200 vulnerable / 403 hardened. | Absent |
| TST-05 | Tests du score et du plancher. | Must | Jeux de sévérités connus. | Absent |
| TST-06 | Test de propriété des scans. | Must | 403 inter-utilisateur. | Absent |
| TST-07 | Build, lint et typecheck frontend passent. | Must | Commandes CI vertes. | Couvert localement |
| DOC-01 | README décrit architecture, démarrage, démonstration, tests, sécurité, limites, roadmap et crédits. | Must | Relecture depuis clone propre. | Partiel |
| DOC-02 | SECURITY.md précise usage autorisé et cible locale. | Must | Fichier présent et cohérent. | Absent |
| DOC-03 | Un script de démonstration 5-7 minutes est fourni. | Must | Répétition chronométrée. | Absent |
| DOC-04 | Captures vulnerable et hardened sont fournies sans secret. | Must | Deux parcours documentés. | Absent |
| DOC-05 | Export JSON, comparaison graphique, Wazuh et tests React sont seulement optionnels. | Could | Aucun ne bloque la définition de terminé. | Absent, conforme |

## Synthèse des écarts

Le socle couvre la plateforme utilisateur et la persistance de base. Il ne couvre pas le scénario OT, la sécurité de ciblage, les contrats déterministes, le score, le rapport ni les tests. Les conflits les plus urgents avant tout nouveau scanner sont `SCP-03`, `SCP-04`, `SEC-01`, `SEC-04`, `SEC-05`, `SEC-07`, `SEC-12`, `CTL-03` et `CTL-04`.
