# Journal des décisions IASS-OT

Ce fichier enregistre les choix qui précisent le dossier de réalisation. Toute déviation future doit être ajoutée ici avant l'implémentation correspondante.

## DEC-001 - Quatre composants logiques, cinq conteneurs en développement

**Décision :** l'architecture reste présentée comme frontend/nginx, backend, PostgreSQL et gateway. En développement, Vite et Nginx sont séparés, donc cinq conteneurs techniques.

**Raison :** conserver le HMR existant sans fausser le schéma logique du dossier.

## DEC-002 - La cible utilisateur devient une clé fermée

**Décision :** `ScanRequest` accepte `target: "ot-gateway-demo"`, jamais une URL. `target_url` reste en base comme valeur canonique résolue côté serveur.

**Raison :** supprimer le risque SSRF tout en limitant la migration du modèle existant.

## DEC-003 - Suppression du token cible et de max_requests côté utilisateur

**Décision :** le frontend ne demande plus de token gateway ni de nombre de requêtes. Les identités et budgets sont imposés par le backend.

**Raison :** un scénario déterministe et sûr ne doit pas dépendre d'une saisie libre.

## DEC-004 - Profil fixé au démarrage

**Décision :** `OT_PROFILE` est lu au démarrage du conteneur gateway. Aucun endpoint ne bascule le profil à chaud.

**Raison :** rendre la démonstration reproductible et empêcher un changement accidentel pendant un scan.

## DEC-005 - Gateway uniquement sur le réseau Docker

**Décision :** le port 8081 n'est pas publié sur l'hôte par défaut. Les tests manuels utilisent le réseau Compose ou une surcharge locale explicitement documentée.

**Raison :** respecter la cible interne du dossier et réduire l'exposition.

## DEC-006 - Etat et audit gateway en mémoire

**Décision :** état du procédé, compteurs de limite et audit sont en mémoire et restaurés par `/demo/reset`.

**Raison :** aucune persistance industrielle n'est nécessaire ; le reset déterministe est plus important.

## DEC-007 - Identités gateway séparées

**Décision :** les JWT de la plateforme et de la gateway ont des secrets, émetteurs et usages distincts. Les rôles OT ne sont pas ajoutés au modèle User.

**Raison :** séparer la sécurité du produit de celle du système simulé.

## DEC-008 - Workflow synchrone dans un threadpool

**Décision :** pas de Celery/Redis. Le workflow synchrone est exécuté avec `run_in_threadpool` depuis la route async.

**Raison :** éviter de bloquer la boucle FastAPI sans élargir l'architecture.

## DEC-009 - Rapport HTML côté backend

**Décision :** route propriétaire `/scans/{id}/report`, template HTML et impression navigateur. Aucun PDF serveur.

**Raison :** rapport stable, partage du contrôle d'accès et périmètre borné.

## DEC-010 - Modèle de données enrichi mais non universel

**Décision :** ajouter profil, statut, score, compteurs, durée et champs de constat OT aux trois entités existantes. Pas de tables Site, Asset ou Protocol.

**Raison :** le produit représente un scénario unique et ne prétend pas être une plateforme industrielle générique.

## DEC-011 - Base locale neuve pour le passage OT

**Décision :** la v1 documente la recréation du volume PostgreSQL. Un environnement Alembic complet est reporté après le MVP.

**Raison :** le dépôt n'a pas de structure Alembic opérationnelle et aucune conservation des données historiques n'est exigée.

## DEC-012 - Route de configuration authentifiée

**Décision :** ajouter `GET /config/scan` pour donner à l'UI la cible, le profil et les tests disponibles.

**Raison :** le frontend ne doit pas inventer une information de sécurité ou diverger du backend.

## DEC-013 - Confirmation d'autorisation persistée

**Décision :** la case UI produit `authorization_confirmed: true` et la valeur est conservée dans Scan.

**Raison :** rendre l'autorisation explicite et démontrable, même dans un laboratoire local.

## DEC-014 - Pas de suppression prématurée du code source

**Décision :** les dépendances et modules inutilisés sont retirés seulement au lot de finition après vérification des références et tests.

**Raison :** réduire le risque de casser le socle avant que le parcours OT remplaçant soit fonctionnel.
