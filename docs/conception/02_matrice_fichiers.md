# Matrice d'impact des fichiers

## Légende

- **Conserver** : aucun changement métier prévu.
- **Adapter** : structure utile, comportement ou contrat à modifier.
- **Créer** : fichier absent indispensable à la v1.
- **Réduire** : conserver seulement la partie utile au scénario borné.
- **Référence** : ne participe pas à l'exécution.
- **Optionnel** : uniquement après définition de terminé.

## 1. Racine et infrastructure

| Chemin | Action | Raison |
|---|---|---|
| `LICENSE` | Conserver | Attribution AGPL du projet source. |
| `.gitignore` | Adapter | Ajouter sorties de tests/captures si nécessaire, sans ignorer la documentation finale. |
| `.dockerignore` | Adapter | Exclure caches de la gateway et tests. |
| `.pre-commit-config.yaml` | Adapter | Ajouter pytest et aligner les versions des outils. |
| `.env.example` | Adapter | Ajouter OT_PROFILE, clé de reset, URL interne fixe et budgets ; retirer les options de cible libre. |
| `README.md` | Adapter fortement | Présenter IASS-OT, sécurité, deux profils, démonstration, tests, limites et crédits. |
| `SECURITY.md` | Créer | Usage autorisé, cible locale, données sensibles et signalement. |
| `package.json` | Adapter | Ajouter raccourcis gateway, tests et changement de profil. |
| `justfile` | Adapter | Ajouter reset, tests et commandes de démonstration. |
| `dev.compose.yml` | Adapter | Ajouter gateway, healthcheck, profil et dépendances ; cinq conteneurs techniques en dev. |
| `compose.yml` | Adapter | Ajouter gateway interne ; quatre composants logiques en production. |
| `conf/docker/dev/fastapi.docker` | Conserver | Base backend déjà fonctionnelle. |
| `conf/docker/prod/fastapi.docker` | Conserver, puis vérifier | Gunicorn/non-root déjà présents. |
| `conf/docker/dev/vite.docker` | Conserver | pnpm/Vite stabilisés. |
| `conf/docker/prod/vite.docker` | Conserver | Build multi-stage stabilisé. |
| `conf/nginx/http.conf` | Adapter | Déclarer uniquement les upstream nécessaires ; gateway non routée publiquement. |
| `conf/nginx/dev.nginx` | Conserver, puis vérifier | `/api` et HMR suffisent ; ne pas exposer gateway. |
| `conf/nginx/prod.nginx` | Adapter | Ajouter route du rapport si nécessaire et CSP compatible impression. |

## 2. Backend - infrastructure, auth et données

| Chemin | Action | Raison |
|---|---|---|
| `backend/main.py` | Conserver | Point d'entrée minimal correct. |
| `backend/factory.py` | Adapter | Enregistrer nouvelles routes, retirer `create_all` seulement si migrations retenues, configurer templates. |
| `backend/config.py` | Adapter fortement | Target key, URL fixe, timeouts 3/5 s, 1 Mio, 60 requêtes, clé de reset et secrets gateway. |
| `backend/pyproject.toml` | Adapter | Ajouter pytest/coverage et supprimer dépendances inutiles si confirmé. |
| `backend/Justfile` | Adapter | Commandes tests, coverage et smoke OT. |
| `backend/core/database.py` | Conserver | Session SQLAlchemy synchrone adaptée au socle. |
| `backend/core/security.py` | Conserver | JWT plateforme et bcrypt restent valides. |
| `backend/core/dependencies.py` | Conserver | Protection des routes correcte. |
| `backend/core/enums.py` | Adapter | Ajouter trois TestType OT, ScanExecutionStatus et GatewayProfile. |
| `backend/core/target_policy.py` | Créer | Résoudre la seule target key et bloquer les destinations SSRF. |
| `backend/core/redaction.py` | Créer | Expurgation récursive et centralisée des preuves/logs. |
| `backend/core/request_budget.py` | Créer | Compteur global partagé entre les sept moteurs. |
| `backend/models/Base.py` | Conserver | Champs communs utiles. |
| `backend/models/User.py` | Conserver | Aucun rôle OT dans la plateforme elle-même. |
| `backend/models/Scan.py` | Adapter | status, profile, score, request_count, duration_ms, completed_at. |
| `backend/models/TestResult.py` | Adapter | title, endpoint, method, ot_impact ; JSON conservé. |
| `backend/models/__init__.py` | Adapter si nécessaire | Exporter les modèles modifiés. |
| `backend/schemas/user_schemas.py` | Adapter légèrement | LoginResponse cohérente avec l'UI si l'utilisateur public est inclus. |
| `backend/schemas/scan_schemas.py` | Remplacer le contrat d'entrée | Retirer URL/token/max_requests ; ajouter target enum et authorization_confirmed. |
| `backend/schemas/test_result_schemas.py` | Adapter | Ajouter les champs de restitution OT. |
| `backend/schemas/__init__.py` | Adapter | Réexporter les nouveaux schémas. |
| `backend/repositories/user_repository.py` | Conserver | Fonctions nécessaires déjà présentes. |
| `backend/repositories/scan_repository.py` | Adapter | Créer running, finaliser métriques et paginer à 20. |
| `backend/repositories/test_result_repository.py` | Adapter légèrement | Ordre déterministe et création transactionnelle à préciser. |
| `backend/services/auth_service.py` | Adapter légèrement | 409 doublon et réponse login cohérente. |
| `backend/services/scan_service.py` | Adapter fortement | Threadpool, reset, ordre, budget, persistance partielle et score. |
| `backend/services/report_service.py` | Créer | Préparer un contexte expurgé pour le template HTML. |
| `backend/routes/auth.py` | Adapter légèrement | Contrats/status harmonisés. |
| `backend/routes/scans.py` | Adapter fortement | Target fermée, confirmation, pagination 20 et route report. |
| `backend/routes/config.py` | Créer | Exposer cible, profil et tests disponibles à l'UI. |
| `backend/templates/report.html` | Créer | Rapport imprimable, sans secret. |

Tous les fichiers `__init__.py` non cités restent conservés et ne changent que pour réexporter de nouveaux modules.

## 3. Backend - scanners

| Chemin | Action | Raison |
|---|---|---|
| `backend/scanners/base_scanner.py` | Adapter fortement | Client sûr, redirects false, timeouts, taille, budget global, redaction et extraits. |
| `backend/scanners/payloads.py` | Réduire | Retirer stacked queries, XSS inutilisé, longs time-based et bypass IP hors périmètre. |
| `backend/scanners/auth_scanner.py` | Adapter | Cibler `/telemetry` avec la règle exacte du dossier. |
| `backend/scanners/idor_scanner.py` | Adapter | Scénario Operator A / pump-001 / pump-002. |
| `backend/scanners/sqli_scanner.py` | Adapter fortement | `/maintenance/orders`, quatre payloads max, non destructif, aucun délai long. |
| `backend/scanners/rate_limit_scanner.py` | Adapter fortement | Huit logins invalides max, aucun bypass d'IP. |
| `backend/scanners/ot_command_scanner.py` | Créer | Contrôles pump.start et emergency-stop sans confirmation. |
| `backend/scanners/ot_audit_scanner.py` | Créer | Correlation ID, recherche audit et restauration de pompe. |
| `backend/scanners/ot_rate_limit_scanner.py` | Créer | Huit commandes idempotentes et analyse Retry-After. |
| `backend/scanners/__init__.py` | Adapter | Exporter les sept scanners. |

## 4. Frontend

| Chemin | Action | Raison |
|---|---|---|
| `frontend/src/main.tsx` | Conserver | Entrée React correcte. |
| `frontend/src/App.tsx` | Conserver | Providers corrects ; devtools à désactiver en production si nécessaire. |
| `frontend/src/router.tsx` | Adapter | Ajouter route rapport imprimable si rendu côté React, sinon conserver route backend. |
| `frontend/src/pages/LoginPage.tsx` | Conserver | Coquille adéquate. |
| `frontend/src/pages/RegisterPage.tsx` | Conserver | Coquille adéquate. |
| `frontend/src/pages/DashboardPage.tsx` | Adapter fortement | Identité OT, badge laboratoire, configuration cible et métriques d'historique. |
| `frontend/src/pages/ScanResultsPage.tsx` | Adapter fortement | Score, profil, durée, requêtes, compteurs, tri et rapport. |
| `frontend/src/components/auth/LoginForm.tsx` | Conserver | Parcours compatible. |
| `frontend/src/components/auth/RegisterForm.tsx` | Conserver | Parcours compatible. |
| `frontend/src/components/common/Button.tsx` | Conserver | Réutilisable. |
| `frontend/src/components/common/Input.tsx` | Conserver | Réutilisable, mais plus utilisé pour une URL cible. |
| `frontend/src/components/common/LoadingOverlay.tsx` | Adapter | Afficher progression non temps réel et avertissement durée < 60 s. |
| `frontend/src/components/common/ProtectedRoute.tsx` | Conserver | Protection locale existante. |
| `frontend/src/components/scan/NewScanForm.tsx` | Adapter fortement | Cible fixe, groupes API/OT, sept cases et confirmation obligatoire. |
| `frontend/src/components/scan/ScansList.tsx` | Adapter | Statut, score, Critical/High et éventuellement suppression. |
| `frontend/src/components/scan/TestResultCard.tsx` | Adapter | Endpoint, méthode, impact OT, preuve expurgée et ordre de sévérité. |
| Tous les CSS des pages/composants ci-dessus | Adapter | Nouvelle identité visuelle et mise en page 1280x720. |
| `frontend/src/config/constants.ts` | Adapter fortement | Trois tests OT, groupes, labels, cible et nouvelles routes. |
| `frontend/src/hooks/useAuth.ts` | Adapter légèrement | Utiliser l'utilisateur renvoyé par le backend au lieu de l'id fictif 0. |
| `frontend/src/hooks/useScan.ts` | Adapter | Config cible, rapport et nouveaux contrats. |
| `frontend/src/services/authService.ts` | Conserver/adapter contrat | Endpoints inchangés. |
| `frontend/src/services/scanService.ts` | Adapter | Route config, nouveau payload et URL report. |
| `frontend/src/store/authStore.ts` | Conserver | Session plateforme inchangée. |
| `frontend/src/store/uiStore.ts` | Adapter | Retirer URL/token/max_requests, ajouter tests et confirmation. |
| `frontend/src/lib/api.ts` | Conserver | Intercepteur JWT correct. |
| `frontend/src/lib/errors.ts` | Conserver | Gestion générique utile. |
| `frontend/src/lib/queryClient.ts` | Conserver | Cache suffisant. |
| `frontend/src/lib/utils.ts` | Adapter | Format score/durée et tri des sévérités. |
| `frontend/src/lib/validation.ts` | Adapter fortement | Target enum et confirmation ; plus d'URL/token/max_requests. |
| `frontend/src/types/auth.types.ts` | Adapter légèrement | LoginResponse avec user si décision retenue. |
| `frontend/src/types/scan.types.ts` | Adapter fortement | Profil, status, score, compteurs et champs OT. |
| `frontend/src/types/guards.ts` | Adapter fortement | Valider tous les nouveaux champs runtime. |
| `frontend/src/vite-env.d.ts` | Conserver | Types Vite. |
| `frontend/src/styles/index.css` | Adapter légèrement | Identité globale. |
| `frontend/src/styles/variables.css` | Adapter | Palette laboratoire OT et tokens de statut. |
| `frontend/index.html` | Adapter | Titre et description IASS-OT. |
| `frontend/package.json` | Réduire/adapter | Retirer socket.io-client inutilisé ; ajouter test runner seulement si lot optionnel. |
| `frontend/pnpm-lock.yaml` | Régénérer | Conséquence des dépendances modifiées. |
| `frontend/pnpm-workspace.yaml` | Conserver | Overrides utiles. |
| `frontend/.npmrc` | Conserver | Installation stable. |
| `frontend/vite.config.ts` | Conserver/adapter | Proxy existant ; test runner seulement si retenu. |
| `frontend/tsconfig*.json` | Conserver | Strict mode déjà correct. |
| `frontend/biome.json` | Conserver | Qualité/accessibilité. |
| `frontend/eslint.config.js` | Décider au nettoyage | Conserver si utilisé, sinon retirer pour une seule chaîne de lint. |
| `frontend/public/*` | Adapter ultérieurement | Icônes génériques à remplacer seulement après parcours fonctionnel. |

## 5. Gateway, tests et documentation à créer

| Chemin cible | Action | Contenu |
|---|---|---|
| `ot-gateway-demo/pyproject.toml` | Créer | Dépendances minimales FastAPI/Uvicorn/JWT/rate limiting. |
| `ot-gateway-demo/Dockerfile` | Créer | Image Python non-root avec healthcheck. |
| `ot-gateway-demo/app/main.py` | Créer | Application, état, routes, profil et reset. |
| `ot-gateway-demo/app/config.py` | Créer | OT_PROFILE, secrets de démonstration, limites. |
| `ot-gateway-demo/app/models.py` | Créer | Etat pompe, télémétrie, commandes et événements. |
| `ot-gateway-demo/app/security.py` | Créer | Comptes/jetons/rôles/zones distincts de la plateforme. |
| `ot-gateway-demo/app/audit.py` | Créer | Journal mémoire corrélé. |
| `ot-gateway-demo/app/rate_limit.py` | Créer | Compteurs déterministes par endpoint/acteur. |
| `ot-gateway-demo/tests/*` | Créer | Endpoints, profils, RBAC, BOLA, audit, SQLi et rate limit. |
| `backend/tests/conftest.py` | Créer | DB de test, clients et fixtures gateway. |
| `backend/tests/test_target_policy.py` | Créer | Allowlist/SSRF. |
| `backend/tests/test_redaction.py` | Créer | Secrets et structures imbriquées. |
| `backend/tests/test_score.py` | Créer | Formule, erreurs et plancher. |
| `backend/tests/test_scan_ownership.py` | Créer | 403 inter-utilisateur. |
| `backend/tests/scanners/*` | Créer | Sept moteurs et deux profils. |
| `backend/tests/integration/*` | Créer | Parcours scan complet avec gateway locale. |
| `docs/architecture.md` | Créer à l'implémentation | Architecture réellement construite, pas seulement prévue. |
| `docs/demo-script.md` | Créer | Démonstration 5-7 minutes. |
| `docs/assets/*` | Créer en finition | Captures expurgées vulnerable/hardened. |

## 6. Fichiers de référence ou générés

| Chemin | Action |
|---|---|
| `learn/*` | Référence : conserver sans présenter comme documentation OT finale. |
| `output/pdf/manuel_complet_api_security_scanner.pdf` | Conserver comme manuel du socle initial. |
| `frontend/node_modules`, `frontend/dist`, caches Python | Ne jamais modifier manuellement ni versionner. |

## Conclusion

Aucun fichier applicatif n'est supprimé au début. On sécurise d'abord le chemin réseau et on ajoute la gateway. Les dépendances et fichiers réellement inutilisés ne sont retirés qu'au lot de finition, lorsque les tests prouvent qu'ils ne sont plus référencés.
