# IASS-OT Design Record

This directory preserves the requirements and implementation plan used to transform the original generic API scanner into IASS-OT. The seven implementation lots are now complete.

The authoritative description of the running system is [../ARCHITECTURE.md](../ARCHITECTURE.md). The files in this directory explain why the system was built this way and how the delivered result maps back to the original requirements.

## Contents

- [01 — Requirements and traceability](01_exigences_et_tracabilite.md): final requirement status and verification evidence.
- [02 — File responsibility matrix](02_matrice_fichiers.md): what is retained, adapted, or newly introduced.
- [03 — Delivered architecture](03_architecture_cible.md): concise implementation view and safety invariants.
- [04 — Data model](04_modele_de_donnees.md): persisted entities, enums, evidence, and scoring.
- [05 — Delivery lots and validation](05_lots_et_validation.md): the completed implementation sequence and acceptance criteria.
- [Decision log](../decisions.md): the main design decisions and later adjustments.

## Delivered scope

IASS-OT assesses one simulated pumping-station gateway through seven deterministic controls. The user selects a closed target key, confirms authorization, and can review a stored scan or generate a printable browser report. The gateway runs in either a deliberately vulnerable or hardened profile selected at container startup.

The project is an educational laboratory. It is not an IEC 62443 certification tool and must not be aimed at real industrial assets.
