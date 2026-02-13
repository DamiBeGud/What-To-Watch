# Erklärung zur Nutzung von KI-Werkzeugen im QUAAACK Movie-Recommender-Projekt

Dieses Dokument beschreibt den tatsächlichen Einsatz von KI-Werkzeugen im bisherigen Projektverlauf.  
Der aktuelle Stand umfasst die Phasen **Q (Question)** und **U (Understanding)** des QUAAACK-Prozesses.

## Projektkontext (bis jetzt)

- **Thema:** Scoping und Datenverständnis für ein skalierbares Movie-Recommender-System.
- **Bereits umgesetzt:** `Phase1.ipynb` (Q) und `Phase2_U.ipynb` (U).
- **Noch nicht umgesetzt:** nachgelagerte QUAAACK-Phasen (A/A/A/C/K) sind vorbereitet, aber inhaltlich noch nicht abgeschlossen.

## Eingesetzte KI-Modelle und Zweck

| Phase | KI-Tool (Version) | Einsatz im Projekt |
| :--- | :--- | :--- |
| **Q - Question** | **GPT-5.3 Codex** (primär), **GPT-5.2 Codex** (Fallback) | Strukturierung der Problemstellung, Formulierung von Hypothesen, Auswahl von Offline-Metriken und SLO-Zielen. |
| **U - Understanding** | **GPT-5.3 Codex** (primär), **GPT-5.2 Codex** (Fallback) | Unterstützung bei Datenprüfung und EDA-Logik (Sparsity, Long Tail, Cold Start, zeitliche Drift), sowie bei der Struktur der Notebook-Analyse. |
| **Dokumentation** | **GPT-5.3 Codex** (primär), **GPT-5.2 Codex** (Fallback) | Überarbeitung technischer Dokumentation (z.B. README/Disclosure) passend zum aktuellen Projektstand. |

## Hinweis zur Modellverfügbarkeit

Wenn **GPT-5.3 Codex** temporär nicht verfügbar war (z.B. wegen hoher Auslastung), wurde **GPT-5.2 Codex** als Ersatz verwendet.

## Verwendete Daten im bisherigen Stand

| Datensatz | Quelle | Verwendung |
| :--- | :--- | :--- |
| **MovieLens 25M** (`ratings.csv`, `movies.csv`) | GroupLens Research | Hauptgrundlage für Q/U-Analyse im Recommender-Kontext. |
| **Synthetische Daten (Fallback)** | Im Notebook generiert | Ausführbarkeit der U-Phase ohne lokale Originaldaten. |

## Verantwortung

Alle durch KI erzeugten Inhalte (Code, Texte, Analyseschritte) wurden von mir überprüft und bei Bedarf angepasst.  
Die fachliche und technische Verantwortung für den finalen Projektinhalt liegt vollständig bei mir.
