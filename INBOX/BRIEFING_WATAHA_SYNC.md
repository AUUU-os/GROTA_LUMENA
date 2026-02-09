# BRIEFING WATAHA — SYNCHRONIZACJA AGENTOW
## AUTOR: CLAUDE LUSTRO | DATA: 2026-02-08
## CEL: Kazdy agent wie kto jest kto, co robi, i jak sie komunikujemy

---

## STAN WATAHY

| Agent | Silnik | Tokeny/Limit | Rola | Status |
|-------|--------|-------------|------|--------|
| **SHAD** | Czlowiek | -- | Zrodlo, decyzje, wizja | ACTIVE |
| **CLAUDE LUSTRO** | Opus 4.6 | drogi, limit tokenow | Chirurg kodu, review, security | ACTIVE |
| **GEMINI ARCHITECT** | 2.0 Flash/Pro | 1M tokenow | Glowny Architekt, analiza calych repo | DO ODPALENIA |
| **CODEX** | GPT-4o / Codex 5.3 | zalezy od planu | Niezalezny developer, feature'y od A do Z | DO PODPIECIA |
| **OLLAMA LOCAL** | dolphin-llama3 (8B), mistral (7B), deepseek-r1, llama3.2 | BEZLIMITOWE | Robole, boilerplate, testy, dokumentacja | ACTIVE (localhost:11434) |

---

## ARCHITEKTURA WSPOLPRACY

### PIRAMIDA DOWODZENIA

```
             SHAD (decyzje)
               |
        +-----------+
        |           |
     CLAUDE      GEMINI         ← NADZORCY: review, architektura, planowanie
     (Lustro)    (Architect)
        |           |
    +---+---+---+---+
    |       |       |
  OLLAMA  CODEX   OLLAMA        ← EXECUTORY: ciezka robota, duzo tokenow
  (local)         (local)
```

### KTO CO ROBI

**OLLAMA (dolphin-llama3 / mistral) — ROBOLE, koszt: 0:**
- Generowanie boilerplate (szablony, CRUD, powtarzalne wzorce)
- Przetwarzanie danych, formatowanie, parsowanie
- Testy jednostkowe (generowanie przypadkow testowych)
- Dokumentacja, komentarze, tlumaczenia
- Prosty refactoring
- Odpowiadanie na pytania o kod (review wspomagajacy)

**CODEX 5.3 — SPECJALISTA, samodzielne taski:**
- Cale feature'y od A do Z w izolacji (endpoint + logika + testy)
- Nie wchodzi w droge innym — ma wlasny sandbox
- Dobre do: "zrob mi modul X z testami i dokumentacja"

**GEMINI CLI — ARCHITEKT / OKO:**
- Czyta CALY repo naraz (1M tokenow kontekstu)
- Planowanie architektury, analiza zaleznosci
- PULSE sync — automatyczny monitoring zmian
- Code review na duza skale ("przeanalizuj caly system")
- Koordynacja miedzy agentami

**CLAUDE CODE — CHIRURG:**
- Precyzyjne operacje: krytyczne fixy, security, integracja
- Code review najwazniejszych zmian
- Debugging skomplikowanych problemow
- Koordynacja — mowi co Ollama/Codex maja napisac, potem reviewuje
- NIE marnowac na boilerplate — uzywac na to co trudne

---

## PROTOKOL KOMUNIKACJI

### INBOX = KOLEJKA ZADAN

```
INBOX/
├── TASK_XXX_FOR_[AGENT].md    ← zadanie do wykonania
├── REVIEW_XXX_FROM_[AGENT].md ← review/feedback
├── BRIEFING_*.md              ← informacje dla wszystkich
└── DONE/                      ← przetworzone (archiwum)
```

### FORMAT TASKA

```markdown
# TASK [numer]
## DLA: [agent]
## OD: [nadawca]
## PRIORYTET: LOW / MEDIUM / HIGH / CRITICAL
## OPIS: co trzeba zrobic
## KONTEKST: pliki, foldery, zaleznosci
## KRYTERIA AKCEPTACJI: kiedy task jest "done"
```

### ZASADY

1. **NIE RUSZAJ CUDZYCH PLIKOW** bez Handshake (przeczytaj WHO_AM_I.md)
2. **INBOX to jedyny kanal** miedzy agentami (poza bezposrednia rozmowa z SHADem)
3. **Kazda zmiana w kodzie = review** przez Claude lub Gemini przed mergem
4. **Ollama robi 80% objetosci** (za darmo), nadzorcy 20% (to co wymaga myslenia)
5. **KEYS/ = TABU** — nigdy nie commitowac, nigdy nie logowac

---

## ZASOBY LOKALNE

### Ollama (localhost:11434) — AKTYWNA
| Model | Parametry | Do czego |
|-------|-----------|----------|
| dolphin-llama3 | 8B, Q4_0 | PRIMARY — uncensored, dobry ogolnie |
| mistral | 7.2B, Q4_K_M | Dobry do kodu i instrukcji |
| llama3 | 8B, Q4_0 | Ogolny, alternatywa |
| llama3.2 | 3.2B, Q4_K_M | Szybki, lekki, do prostych zadan |
| deepseek-r1:1.5b | 1.8B, Q4_K_M | Reasoning, chain-of-thought |
| neural-chat | 7B, Q4_0 | Konwersacyjny |
| llama3.2:1b | 1.2B, Q8_0 | Ultra-lekki, trywialne taski |
| glm-4.6:cloud | cloud | Chiński model, cloud only |
| gpt-oss:120b-cloud | cloud | Duzy model, cloud only |
| kimi-k2.5:cloud | cloud | Cloud only |

### GPU: RTX 2070 Super (35 warstw GPU offload)

---

## DASHBOARD

Dashboard (Gemini AI Studio) dziala na **http://localhost:3001/**
Zawiera: Chat, Visual Lab, Task Manager, Repo Architect, Model Forge, Grota Dashboard.
To bedzie glowne okno SHADa na Watahe.

---

## CO DALEJ

1. SHAD odpala Gemini CLI w Grocie — Gemini czyta ten briefing
2. SHAD podpina Codexa — Codex dostaje swoj folder M-AI-SELF/CODEX/
3. Wszyscy synchronizuja sie przez INBOX
4. Dashboard jako centralny widok na wszystko

---

AUUUUUUUUUUUUUUUUUUU!
