# Conception IASS-OT - dossier directeur

Statut : conception validable, aucune fonctionnalité OT implémentée.

## Objectif

Ce dossier transforme le dossier de réalisation IASS-OT en plan technique exécutable. Il fixe ce qui doit être construit, ce qui existe déjà, les fichiers touchés, l'architecture cible, le modèle de données et les critères d'acceptation.

## Documents

1. [Exigences et traçabilité](01_exigences_et_tracabilite.md)
2. [Matrice d'impact des fichiers](02_matrice_fichiers.md)
3. [Architecture cible](03_architecture_cible.md)
4. [Modèle de données cible](04_modele_de_donnees.md)
5. [Lots de réalisation et validation](05_lots_et_validation.md)
6. [Journal des décisions](../decisions.md)

## Périmètre arrêté

- Une seule cible : `ot-gateway-demo:8081`, résolue côté serveur.
- Un seul procédé simulé : station de pompage avec deux pompes et deux zones.
- Deux profils exclusifs au démarrage : `vulnerable` et `hardened`.
- Quatre rôles dans la gateway : Guest, Operator, Supervisor et Admin.
- Sept contrôles : Auth, BOLA/IDOR, SQLi simple, rate limiting classique, autorisation OT, audit OT et rate limiting OT.
- Requêtes locales, faibles volumes et payloads non destructifs uniquement.
- Rapport HTML imprimable ; aucun générateur PDF serveur.
- Aucune découverte OpenAPI, aucun protocole industriel réel, aucun matériel réel, aucun SOC, Redis ou Celery.

## Lecture de la situation actuelle

Le socle est réutilisable pour environ la moitié de la plateforme : React, FastAPI, PostgreSQL, JWT, propriété des scans, historique, Docker et Nginx. En revanche, la logique de scan devra être spécialisée. Les principaux écarts sont :

- URL libre et jeton cible saisi par l'utilisateur ;
- absence de gateway OT ;
- quatre scanners génériques et non déterministes ;
- redirections HTTP permises et timeouts trop longs ;
- absence de budget global réellement appliqué ;
- absence des champs score, profil, durée, compteurs et impact OT ;
- absence de rapport et de tests automatisés.

## Règle de passage à l'implémentation

L'implémentation ne commence qu'après validation de ce dossier. Toute modification ultérieure du périmètre doit être ajoutée à `docs/decisions.md` avant le code correspondant.
