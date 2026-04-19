# Deliverable 1 — Choosy App

**Curs:** 2025/26  
**Assignatura:** Projecte Web  
**Grup:** choosy-friends-app

---

## 1. GitHub public address

**https://github.com/choosy-friends-app/choosy-app**

El repositori és públic i accessible sense autenticació.

---

## 2. Design decisions

### Escenari proposat
L'aplicació Choosy resol el problema de presa de decisions col·lectives en grups (plans d'oci, restaurants, activitats). El model reflecteix un flux complet: un grup de persones proposa opcions, vota entre elles i la decisió es registra com a historial.

### Model de dades
S'han implementat 6 entitats amb relacions complexes:

- **Group** — Entitat central amb estat (planning/voting/active/archived), imatge hero, interessos (camp JSON) i missió.
- **GroupMember** — Relació M2M entre User i Group enriquida amb rol (owner/admin/member) i estat d'invitació (invited/active/left). Permet membres sense compte registrat (display_name + avatar_url).
- **PlanProposal** — Ronda de votació temporal. Restricció de només una proposta oberta per grup (unique constraint condicional).
- **Plan** — Opció individual dins una proposta. Inclou preu, durada, etiqueta, ubicació i imatge. Ordre explícit (option_order).
- **Vote** — Vot upvote/downvote. Suporta tres modes d'identificació: membre autenticat, usuari de sessió, o sessió anònima. Restriccions úniques a nivell de base de dades per evitar doble vot.
- **Notification** — Sistema de notificacions intern per a invitacions, nous plans i decisions. Linked a grup i proposta per context.

Totes les entitats hereten de `TimestampedModel` (abstract) per tenir `created_at` i `updated_at` automàtics.

### Arquitectura de l'aplicació
- Les vistes estan organitzades per funcionalitat dins `core/web/` (auth, dashboard, groups, plans, notifications, shared) en lloc d'un únic fitxer `views.py`, per mantenibilitat.
- Les utilitats compartides (decoradors, helpers de query, enriquiment de templates) estan centralitzades a `shared.py`.
- El frontend usa Django Template Language amb components reutilitzables a `front/templates/includes/`, sense frameworks JS externs.
- El CSS és modular per pàgina/funcionalitat per evitar col·lisions i facilitar el manteniment.

### Autenticació
S'usa el sistema d'autenticació integrat de Django (`django.contrib.auth`) amb un formulari de registre personalitzat (`RegisterForm`) que inclou validació de correu electrònic.

### Docker i desplegament
- La configuració commuta automàticament entre SQLite (desenvolupament local) i PostgreSQL (Docker) en funció de si `DB_NAME` està definit a l'entorn.
- Es fa servir Gunicorn com a servidor WSGI de producció (en lloc del servidor de desenvolupament de Django).
- Les migracions s'executen automàticament a l'arrencada del contenidor.

### 12-Factor App
El projecte implementa les 12-factor guidelines: configuració via variables d'entorn, dependències declarades a `pyproject.toml` + `uv.lock`, logs a stdout, processos sense estat, i paritat dev/prod via Docker. Vegeu el README per al detall complet.

---

## 3. Distribució de notes

Tots els membres de l'equip han contribuït de manera equivalent al projecte. La nota hauria de ser la mateixa per a tots els membres.

| Membre | Contribució |
|--------|-------------|
| Aleix Rosinach | Model de dades, autenticació, backend general, Docker |
| Bru | Frontend, sistema de votació, notificacions |

> Si la distribució ha de ser diferent, cal actualitzar aquesta secció amb els percentatges acordats.

---

## Instruccions d'execució

Vegeu el fitxer `README.md` per a les instruccions detallades de desplegament.

```bash
cp .env.example .env
docker-compose up --build
```

Aplicació disponible a `http://localhost:8000`.
