# Misconfig Mayhem – SharePy  
*OWASP A02:2025 – Security Misconfiguration*

Misconfig Mayhem est un laboratoire pédagogique dédié à la catégorie **OWASP A02:2025 – Security Misconfiguration**.  
L’application cible, **SharePy** (un clone Dropbox), repose sur une architecture micro-services délibérément vulnérable afin de reproduire les erreurs de configuration les plus courantes rencontrées en 2025.

> Projet réalisé dans le cadre du module *Développement d’applications sécurisées*  
> Encadré par M. Mohammed Airaj.

---

## Architecture

Stack complète orchestrée via `docker-compose` (6 services) :

| Service         | Technologie       | Port exposé |
|-----------------|-------------------|-------------|
| Backend         | FastAPI (Python)  | 8000        |
| Base de données | PostgreSQL 15     | 5432        |
| Object Storage  | MinIO (S3-compat) | 9000        |
| Reverse Proxy   | Nginx             | 80          |
| DB Admin        | Adminer           | 8080        |

---

## Vulnérabilitées implémentées (15 – M1→M15)

| ID  | Titre | Description |
|-----|-------|-------------|
| M1  | Secrets en clair | `.env` et code source accessibles |
| M2  | JWT faible | Secret = `changeme` |
| M3  | Directory Listing | `/uploads` indexé |
| M4  | Debug enabled | Endpoint `/debug/info` |
| M5  | Ports sensibles | PostgreSQL & MinIO publics |
| M6  | Permissions laxistes | `chmod 777` sur `uploads/` |
| M7  | CORS wildcard | `Access-Control-Allow-Origin: *` |
| …   | … | … |

---

## Audit automatisé

`checkSec9.py` – scanner Python 3 autonome  
Fonctionnalités clés :

1. **Network scan** – détection des ports exposés  
2. **Env dump** – extraction automatique des secrets via `/debug/info`  
3. **Exploit M13** – upload de fichier malveillant + exécution

```bash
python3 checkSec9.py <host>
```

---

## Quick start

```bash
git clone https://github.com/ZaikOSS/Misconfig-Mayhem.git
cd Misconfig-Mayhem
docker compose up -d
python3 checkSec9.py localhost
```

---

## Auteur

**Zaikos**

---

*Ce projet est strictement éducatif. Ne jamais reproduire ces configurations en production.*
