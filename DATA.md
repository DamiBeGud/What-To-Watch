# DATA.md - Data Contract and Usage Rules (Movie Recommendation App)

## Purpose
This file defines how the project uses data from `ml-25m`, including:
- source-of-truth files
- schema expectations
- preprocessing rules
- evaluation split rules
- leakage guardrails

Agents and contributors should treat this as the default reference when building notebooks, pipelines, or the Streamlit app.

## Dataset Source of Truth
Primary dataset directory: `ml-25m/`

Dataset summary (from `ml-25m/README.txt`):
- 25,000,095 ratings
- 1,093,360 tag applications
- 62,423 movies
- 162,541 users
- activity period: January 9, 1995 to November 21, 2019

## Files and Schemas

### Required for v1
- `ml-25m/ratings.csv`
  - Columns: `userId`, `movieId`, `rating`, `timestamp`
  - Role: core user-item interactions for collaborative signals and evaluation

- `ml-25m/movies.csv`
  - Columns: `movieId`, `title`, `genres`
  - Role: item metadata for display, filtering, and content-based features

### Strongly recommended for v1.1 / v2
- `ml-25m/tags.csv`
  - Columns: `userId`, `movieId`, `tag`, `timestamp`
  - Role: lightweight content enrichment and explainability

- `ml-25m/links.csv`
  - Columns: `movieId`, `imdbId`, `tmdbId`
  - Role: external linking, poster lookup, metadata enrichment

### Optional / advanced (large)
- `ml-25m/genome-tags.csv`
  - Columns: `tagId`, `tag`
  - Role: tag dictionary for genome relevance features

- `ml-25m/genome-scores.csv`
  - Columns: `movieId`, `tagId`, `relevance`
  - Role: dense item-content signals (advanced content/hybrid models)
  - Note: large file; can be deferred for v1 performance and notebook runtime

## Data Usage Policy by QUAAACK Phase

### Q-Phase
- Document stakeholders, goals, and success metrics.
- No heavy data processing required.
- Use only high-level dataset summary counts and file descriptions.

### U-Phase
- Load and profile `ratings.csv` and `movies.csv` first.
- Add `tags.csv` and `links.csv` if needed for feature availability analysis.
- Inspect `genome-*` files but do not require full processing in early EDA if runtime is high.

### A-Phase (AAA combined)
- Minimum modeling inputs:
  - `ratings.csv`
  - `movies.csv`
- Optional feature enrichment:
  - `tags.csv`
  - `genome-scores.csv` + `genome-tags.csv`
- Any feature included in evaluation must be reproducible and documented.

### C-Phase / K-Phase
- Use saved artifacts and processed snapshots generated in A-Phase.
- Do not rerun expensive preprocessing inside the Streamlit app path.

## Canonical Data Rules

### Time Handling
- Parse `timestamp` as Unix epoch seconds.
- Convert to timezone-aware UTC (or document if naive UTC is used).
- Keep original timestamp column available until splits are finalized.

### Ratings
- Treat `rating` as explicit feedback (5-star scale).
- Do not round or rescale ratings unless the method explicitly requires it and the transformation is documented.
- For ranking evaluation, convert evaluation targets to relevant/non-relevant using a documented threshold (example: `rating >= 4.0`).

### Genres
- `genres` is pipe-delimited (e.g., `Adventure|Comedy`).
- Split into lists for modeling/filtering.
- Preserve original string for display and traceability.
- Handle special values like `(no genres listed)` explicitly.

### IDs
- `userId` and `movieId` are stable internal keys for this dataset.
- Never assume IDs are contiguous.
- Store encoder mappings if algorithms require index remapping.

## Data Quality Checks (Required)
Run and document these checks in `U-Phase.ipynb` and confirm assumptions in `A-Phase.ipynb`:
- row counts and unique counts (`userId`, `movieId`)
- duplicate rows (full-row and key-based duplicates)
- null values in required columns
- invalid ratings (outside expected scale)
- timestamp parsing failures
- missing `movieId` matches between `ratings.csv` and `movies.csv`
- malformed or empty genre values

Optional but recommended:
- tag text cleanup checks (`tags.csv`)
- coverage of `links.csv` and `tmdbId`/`imdbId` availability
- coverage of genome features by `movieId`

## Train/Validation/Test Split Policy (Leakage-Safe)

### Default Evaluation Strategy (recommended)
Use chronological splits, not random splits.

Recommended approach for top-N recommendation evaluation:
- Per-user chronological holdout (preferred)
  - Train: earlier interactions
  - Validation/Test: later interactions
- Keep only users with enough interactions for the chosen holdout strategy
- Document exact thresholds (example: min 5 interactions for leave-last-k)

Alternative (only if justified):
- Global time cutoff split

### Leakage Guardrails (non-negotiable)
- Do not use future user interactions to build train-time features.
- Do not fit encoders/scalers/similarity transforms on train+test combined data.
- Do not compute popularity or co-occurrence statistics using validation/test interactions.
- If using rolling or temporal features, avoid centered windows that peek into the future.
- If using item metadata (genres, static tags/genome), document whether the metadata is treated as static and available at prediction time.

## Modeling Data Decisions (v1 Recommendations)

### v1 fast path (recommended)
- Use `ratings.csv` + `movies.csv`
- Add:
  - popularity baseline
  - genre-filtered popularity
  - item-item similarity (ratings-based or simple content-based)
- Keep runtime reasonable for notebooks and Streamlit demo

### v1.1 / v2 path
- Add `tags.csv` for better content explanations
- Add genome features selectively (top tags or dimensionality reduction) instead of loading full dense matrices into UI runtime

## Processed Data and Artifacts (recommended paths)
Store derived outputs outside raw `ml-25m/`:
- `artifacts/` for model files, similarity matrices, encoders
- `data/processed/` for cleaned/intermediate tables (if created)

Example artifact types:
- movie metadata table for app display
- user/item index mappings
- item-item similarity matrix
- popularity tables by genre/global
- tuned model parameters

## Documentation Requirements for Notebooks
Every notebook that reads `ml-25m` data must state:
- which files it uses
- why those files are needed
- any row/user/item filtering applied
- split strategy used
- leakage controls used

For non-technical readers, each data chart should explain:
- what the chart shows
- why it matters for recommendation quality or app behavior

## Known Dataset Limitations (must be acknowledged)
- Ratings and tags are historical and end in 2019 (not real-time)
- Data reflects MovieLens users, not all movie audiences
- Metadata is limited compared to commercial streaming platforms
- Cold-start remains a real limitation for unseen users/items
- Popularity bias can dominate unless controlled in ranking/re-ranking

## Change Log (maintain over time)
- Add new preprocessing or split decisions here before they become implicit in code.
