# TODO

## Prompt-Anzeige im Frontend

- [ ] Collapsible Panel im Frontend, das den System-Prompt und den Page-Prompt anzeigt
- [ ] Hilft beim Debuggen und Nachvollziehen der generierten Inhalte
- [ ] Pro Seite den verwendeten Prompt in der Preview anzeigen

## Content-Styles

Verschiedene Schreibstile als Auswahl im Frontend anbieten, die den System-Prompt anpassen:

- [ ] **Professionell** — Sachlich, seriös, vertrauenserweckend (Kanzleien, Beratungen, B2B)
- [ ] **Warm & Persönlich** — Nahbar, einladend, du-Ansprache möglich (Cafés, Handwerk, lokale Shops)
- [ ] **Modern & Dynamisch** — Knackig, startup-like, aktivierend (Tech, Agenturen, Startups)
- [ ] **Elegant & Premium** — Gehoben, exklusiv, bildhafte Sprache (Hotels, Restaurants, Luxus)
- [ ] **Bodenständig** — Direkt, ehrlich, regional verwurzelt (Handwerk, Landwirtschaft, Vereine)

### Umsetzung

- [ ] Style-Definitionen als YAML in `config/styles/` (Name, Beschreibung, Prompt-Modifikation, Anrede Sie/Du)
- [ ] Style-Auswahl als Dropdown im Frontend neben Page-Set
- [ ] Backend: Style-Parameter an Generator durchreichen
- [ ] Generator: System-Prompt dynamisch anpassen basierend auf Style

## Firmen-Research vor Generierung

Vor der Content-Generierung einen Research-Schritt einbauen, der Details zum Unternehmen recherchiert und als Report zur Bestätigung vorlegt.

### Ablauf

1. User gibt Firmenbeschreibung ein
2. Claude recherchiert/generiert einen **Company Report** mit plausiblen Details:
   - Firmenname, Gründungsjahr, Standort(e)
   - Geschäftsführung / Ansprechpartner (fiktive Namen)
   - Kernleistungen / Produkte
   - Zielgruppe und Positionierung
   - USPs / Alleinstellungsmerkmale
   - Kontaktdaten (Adresse, Telefon, E-Mail)
   - Öffnungszeiten (falls relevant)
   - Teamgröße, Anzahl Mitarbeiter
3. Report wird im Frontend als **editierbares Formular/Preview** angezeigt
4. User kann Details anpassen, korrigieren, ergänzen
5. Nach Bestätigung fließen die Details als Kontext in die Content-Generierung ein

### Vorteile

- Konsistente Daten über alle Seiten (gleiche Namen, Adressen, Fakten)
- Realistischere Inhalte statt generischer Platzhalter
- User hat Kontrolle über die verwendeten Details
- Einmalige Research-Kosten statt Wiederholung in jedem Page-Prompt

### Umsetzung

- [ ] Neuer API-Endpoint `POST /api/research` — generiert Company Report
- [ ] Research-Prompt als Template in `config/`
- [ ] Frontend: Zwischenschritt mit editierbarem Report vor "Generieren"
- [ ] Company Report als JSON im Job speichern (DB + Datei)
- [ ] Generator: Report-Daten als zusätzlichen Kontext in System-Prompt injizieren
