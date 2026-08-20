# Architecture IASS-OT cible

## 1. Vue logique

```text
Navigateur
   |
   v
Nginx / React
   | /api
   v
FastAPI Scanner ---------------------- PostgreSQL
   |
   | HTTP interne seulement
   | cible résolue par TargetPolicy
   v
OT Gateway Demo :8081
   |- état station de pompage
   |- JWT et rôles de démonstration
   |- RBAC / zones
   |- audit mémoire
   `- rate limiting déterministe
```

Les quatre composants logiques sont frontend/nginx, scanner, base et gateway. En développement, Vite et Nginx restent deux conteneurs distincts : il y aura donc cinq conteneurs techniques, sans changer l'architecture logique.

## 2. Frontières de confiance

### Navigateur vers scanner

- JWT de la plateforme uniquement.
- L'utilisateur choisit des tests, pas une URL ni un jeton gateway.
- La confirmation d'autorisation est obligatoire et auditée dans le Scan.

### Scanner vers gateway

- Réseau Docker interne.
- Adresse produite par `TargetPolicy`, jamais concaténée depuis une saisie.
- Jetons de démonstration conservés dans l'environnement backend et expurgés.
- Redirections interdites, timeouts 3/5 s, réponse 1 Mio maximum.
- Budget partagé de 60 appels pour tout le scan.

### Gateway

- Aucun protocole ou équipement industriel réel.
- Etat en mémoire, réinitialisable et déterministe.
- Mode fixé au démarrage ; aucun endpoint ne change le profil à chaud.
- Port non publié sur l'hôte par défaut.

## 3. Composants backend

### TargetPolicy

Entrée : enum `ot-gateway-demo`.

Sortie interne : cible canonique `http://ot-gateway-demo:8081` et nom d'affichage `Water Pump Gateway`.

La politique refuse avant réseau toute URL, IP, autre host, port ou schéma. Les scanners ne reçoivent jamais de valeur arbitraire.

### SafeScannerClient

Le comportement commun de `BaseScanner` devient une enveloppe sûre :

- budget atomique partagé ;
- session sans redirects ;
- timeouts séparés ;
- lecture streaming plafonnée ;
- compteur exact ;
- redaction récursive ;
- extrait de réponse limité ;
- arrêt du moteur sur latence ou réseau anormal.

### Orchestrateur

La route reste async mais appelle le workflow synchrone dans `run_in_threadpool`.

Ordre :

1. validation utilisateur, cible, confirmation et sélection ;
2. création du Scan `running` ;
3. reset de la gateway ;
4. auth ;
5. BOLA ;
6. SQLi ;
7. rate limit classique ;
8. autorisation OT ;
9. audit OT ;
10. rate limit OT ;
11. calcul score/compteurs ;
12. finalisation `completed`, `partial` ou `failed`.

Chaque résultat est persisté dès qu'il est produit. Une exception d'un moteur devient un résultat `error` et ne supprime pas les résultats précédents.

## 4. Gateway OT

### Etat initial

```text
pump-001  zone A  stopped
pump-002  zone B  running
pressure  2.5 bar
flow      120 L/min
level     65 %
emergency_stop false
```

### Rôles hardened

| Rôle | Droits |
|---|---|
| Guest | Aucun endpoint métier. |
| Operator A/B | Télémétrie et lecture de la pompe de sa zone. |
| Supervisor | Lecture, start/stop et consigne. |
| Admin | Tous droits, audit et emergency stop confirmé. |

Le scanner possède des identités de démonstration connues et distinctes pour chaque rôle. Elles ne sont jamais montrées dans les résultats.

### Routes gateway

| Méthode | Route | Usage |
|---|---|---|
| POST | `/auth/token` | Obtenir un jeton de démonstration. |
| GET | `/telemetry` | Contrôle d'authentification. |
| GET | `/pumps/{id}` | BOLA inter-zones. |
| POST | `/pumps/{id}/start` | Commande OT réversible. |
| POST | `/pumps/{id}/stop` | Restauration. |
| PUT | `/process/setpoint` | Commande Supervisor. |
| POST | `/process/emergency-stop` | Test sans confirmation réelle. |
| GET | `/audit/events` | Recherche par correlation_id. |
| GET | `/maintenance/orders?id=` | SQLi simulée. |
| POST | `/demo/reset` | Etat initial protégé par demo key. |
| GET | `/health` | Santé et profil courant. |

## 5. Profils reproductibles

| Contrôle | vulnerable | hardened |
|---|---|---|
| Auth | Télémétrie accessible avec identité invalide ou absente selon scénario. | 401/403. |
| BOLA | Operator A lit pump-002. | 403 hors zone. |
| SQLi | Payload connu renvoie une erreur SQL simulée/différence stable. | Identifiant strictement validé. |
| Rate limit auth | Aucun 429 sur 8 essais. | 429 avant ou au 8e essai. |
| Autorisation OT | Rôles insuffisants exécutent les commandes. | 401/403. |
| Audit OT | Commande absente ou incomplète dans le journal. | Evénement complet et corrélé. |
| Rate limit OT | Aucun 429. | 5 commandes/4 s puis 429 + Retry-After. |

## 6. Contrats API plateforme

### Configuration de la cible

`GET /api/config/scan`

```json
{
  "target": "ot-gateway-demo",
  "display_name": "Water Pump Gateway",
  "profile": "vulnerable",
  "tests": ["auth", "idor", "sqli", "rate_limit", "ot_command_authz", "ot_audit", "ot_rate_limit"]
}
```

### Création

`POST /api/scans/`

```json
{
  "target": "ot-gateway-demo",
  "tests_to_run": ["auth", "idor", "sqli", "rate_limit", "ot_command_authz", "ot_audit", "ot_rate_limit"],
  "authorization_confirmed": true
}
```

Le serveur ignore toute notion d'URL ou de token fournie par un client et renvoie 422 si la cible ou la confirmation est invalide.

### Résultat unitaire

```json
{
  "test_name": "ot_command_authz",
  "status": "vulnerable",
  "severity": "high",
  "title": "Commande pompe accessible au rôle Operator",
  "method": "POST",
  "endpoint": "/pumps/pump-001/start",
  "details": "Le rôle Operator a obtenu une réponse 2xx.",
  "ot_impact": "Modification non autorisée du procédé simulé.",
  "evidence_json": {"status_code": 200, "correlation_id": "redacted-safe-value"},
  "recommendations_json": ["Appliquer le RBAC côté serveur."]
}
```

## 7. Rapport

Le rapport est rendu par le backend depuis un template HTML, avec un bouton d'impression navigateur. Il ne contient que des objets déjà expurgés. Sections :

1. synthèse et avertissement ;
2. cible, profil, date, durée et budget ;
3. score et compteurs ;
4. constats triés ;
5. erreurs ;
6. limites ;
7. mention que le score n'est ni certification ni mesure exhaustive.

## 8. Gestion des erreurs

- Gateway indisponible avant scan : Scan `failed`, résultat de diagnostic explicite, zéro faux `safe`.
- Erreur après certains moteurs : Scan `partial`, résultats précédents conservés.
- Budget épuisé : moteur courant `error`, aucun appel supplémentaire.
- Reset impossible : scan non lancé ou `failed` avant les sept contrôles.
- Profil inattendu : rejet de configuration, jamais de supposition côté UI.
