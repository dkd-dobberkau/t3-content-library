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
