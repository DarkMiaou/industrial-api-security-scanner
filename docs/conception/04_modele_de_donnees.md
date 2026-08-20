# Modèle de données cible

## 1. Principes

- Conserver `User`, `Scan` et `TestResult`.
- Ajouter uniquement les champs nécessaires à la démonstration, au score et au rapport.
- Ne pas créer de table d'actifs OT : la gateway possède un scénario fixe.
- Ne jamais persister les secrets ou jetons de la gateway.
- Garder les preuves et recommandations en JSON pour leur variabilité.

## 2. User

Aucun changement métier.

| Champ | Type | Rôle |
|---|---|---|
| id | integer | Clé primaire. |
| email | varchar unique | Identité plateforme. |
| hashed_password | varchar | Hash bcrypt. |
| is_active | boolean | Autorisation de connexion. |
| created_at / updated_at | timestamptz | Traçabilité. |

Les rôles Guest/Operator/Supervisor/Admin appartiennent uniquement à la gateway simulée. Ils ne doivent pas être ajoutés à `User`.

## 3. Scan

| Champ | Type cible | Null | Description |
|---|---|---:|---|
| id | integer | non | Clé primaire. |
| user_id | FK users | non | Propriétaire plateforme. |
| target_url | varchar | non | URL canonique interne résolue par le serveur, jamais une saisie. |
| target_key | varchar/enum | non | `ot-gateway-demo`. |
| target_name | varchar | non | `Water Pump Gateway`. |
| profile | enum | non | `vulnerable` ou `hardened`. |
| status | enum | non | `running`, `completed`, `partial`, `failed`. |
| authorization_confirmed | boolean | non | Consentement explicite reçu au lancement. |
| score | integer | oui pendant running | 0 à 100. |
| request_count | integer | non | Appels gateway réellement émis. |
| duration_ms | integer | oui pendant running | Durée totale. |
| scan_date | timestamptz | non | Début du scan. |
| completed_at | timestamptz | oui | Fin du scan. |
| created_at / updated_at | timestamptz | non | Traçabilité technique. |

`target_url` est conservé pour limiter la rupture avec le modèle existant, mais il devient une donnée serveur. Le client ne peut ni l'envoyer ni la modifier.

## 4. TestResult

| Champ | Type cible | Description |
|---|---|---|
| id | integer | Clé primaire. |
| scan_id | FK scans | Scan parent. |
| test_name | enum | Un des sept contrôles. |
| status | enum | vulnerable, safe ou error. |
| severity | enum | critical, high, medium, low ou info. |
| title | varchar | Titre court du constat. |
| method | varchar | GET, POST ou PUT. |
| endpoint | varchar | Chemin relatif sans host ni secret. |
| details | text | Explication du comportement observé. |
| ot_impact | text | Impact potentiel sur le procédé simulé. |
| evidence_json | json | Preuve bornée et expurgée. |
| recommendations_json | json | Liste d'actions correctives. |
| created_at / updated_at | timestamptz | Traçabilité. |

## 5. Enums

### TestType

```text
auth
idor
sqli
rate_limit
ot_command_authz
ot_audit
ot_rate_limit
```

### ScanExecutionStatus

```text
running
completed
partial
failed
```

### GatewayProfile

```text
vulnerable
hardened
```

Les enums `ScanStatus` et `Severity` des résultats restent inchangés.

## 6. Etat du scan

```text
création -> running
running -> completed  si tous les moteurs ont produit safe/vulnerable
running -> partial    si au moins un résultat utile et au moins une error
running -> failed     si reset/cible échoue avant résultat utile
```

Un constat `vulnerable` ne signifie pas que le scan a échoué : un scan peut être `completed` avec plusieurs vulnérabilités.

## 7. Score

```text
score = max(
  0,
  100
  - 30 * critical_count
  - 15 * high_count
  - 7  * medium_count
  - 2  * low_count
)
```

- `info` ne réduit pas le score.
- `error` ne réduit pas le score, mais apparaît dans un compteur séparé.
- Le score est pédagogique et porte obligatoirement un avertissement.

## 8. Forme des preuves

Chaque moteur peut ajouter des champs différents, mais la preuve doit respecter ces règles :

```json
{
  "status_code": 403,
  "response_time_ms": 18.4,
  "response_excerpt": "...500 caractères maximum...",
  "correlation_id": "valeur non secrète",
  "attempts": 6,
  "retry_after": "4"
}
```

Interdits dans les preuves : Authorization, Cookie, Set-Cookie, mots de passe, jetons complets, demo key, secret et corps non borné.

## 9. Stratégie de changement de schéma

Le dépôt n'a pas d'environnement Alembic opérationnel malgré la dépendance déclarée. Pour la v1 locale :

1. les modèles sont modifiés ;
2. le README exige une base neuve avec `docker compose down -v` lors du passage au modèle OT ;
3. aucune donnée de l'ancien prototype n'est promise comme conservée ;
4. l'ajout d'un environnement Alembic complet reste une amélioration post-MVP.

Cette décision évite une fausse migration de production dans un projet volontairement local et borné.
