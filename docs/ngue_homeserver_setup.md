# NGÜ Bibelvers-Sponsoring-App - Homeserver Setup Dokumentation

**Erstellt:** August 2025  
**Domain:** `ngue.familieprobst.org`  
**Server:** homeserver (192.168.178.201)

## 🏗️ Infrastruktur-Setup

### Server-Details

- **IP:** 192.168.178.201 (statisch)
- **Betriebssystem:** Ubuntu Server LTS
- **Container-Plattform:** Docker + Docker Compose

### Port-Konfiguration Fritz!Box

```
8090 → 192.168.178.201:8090 (HTTP für Let's Encrypt Challenge)
8091 → 192.168.178.201:8091 (HTTPS für ngue-app)
443  → 192.168.178.201:443  (HTTPS für nc.familieprobst.org - Nextcloud)
80  → 192.168.178.201:80  (HTTP für nc.familieprobst.org - Nextcloud)
```

### DNS & Domain-Setup
- **Registrar:** Strato
- **DNS-Provider:** Cloudflare (kostenloser Plan)
- **Domain:** `familieprobst.org`
- **Subdomain:** `ngue.familieprobst.org`

#### Cloudflare-Konfiguration
- **A-Record:** `ngue.familieprobst.org` → öffentliche IP (mit Proxy/orangener Wolke)
- **SSL/TLS-Modus:** "Full" (akzeptiert Let's Encrypt Zertifikate)
- **Origin Rule:** `ngue.familieprobst.org` → Port 8091 Weiterleitung

## 🔧 SSL/HTTPS-Setup

### Let's Encrypt via DNS Challenge
- **Provider:** Cloudflare DNS Challenge (statt HTTP Challenge)
- **Vorteil:** Funktioniert auch mit Cloudflare Proxy aktiv
- **Zertifikat-Renewal:** Automatisch alle 90 Tage
- **Storage:** `./traefik/letsencrypt/acme.json`

### Cloudflare API-Token Setup
**Benötigte Berechtigungen:**
- `Zone:Read` für alle Zonen
- `DNS:Edit` für `familieprobst.org`

## 🌐 URLs & Zugriff

- **Produktions-URL:** https://ngue.familieprobst.org
- **Stripe Webhook URL:** https://ngue.familieprobst.org/webhook

