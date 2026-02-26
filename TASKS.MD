# TASKS.MD - QUAAACK Notebook Tasks for Movie Recommendation App

## 1. Project Context (must be stated clearly in the first notebook and referenced in all others)

### Project Type
Movie recommendation software built with **Streamlit** and developed using the **QUAAACK process**.

### Primary Stakeholders (clearly define in Q-Phase)
1. **End Users (Movie Watchers)**
   Need fast, relevant, easy-to-understand recommendations.
2. **Product Owner / Project Team**
   Need measurable recommendation quality and a usable Streamlit app.
3. **Data/ML Developer (you / team)**
   Need reproducible experiments, clear metrics, and maintainable pipelines.
4. **Non-Technical Reviewers (teachers, stakeholders, demo audience)**
   Need plain-language explanations of charts, decisions, and outcomes.

### Data Used (from `ml-25m`)
Use and document these files explicitly:
- `ml-25m/ratings.csv` (core user-item interactions)
- `ml-25m/movies.csv` (movie metadata: title, genres)
- `ml-25m/tags.csv` (user-provided tags; optional but valuable for content signals)
- `ml-25m/links.csv` (external IDs; useful for posters/metadata extensions later)
- `ml-25m/genome-scores.csv` (fine-grained tag relevance, advanced content features)
- `ml-25m/genome-tags.csv` (lookup table for genome tags)
- `ml-25m/README.txt` (dataset documentation; summarize key limits)

### Project Goals (define in Q-Phase and track through C-Phase)
1. Build a **movie recommender** that supports:
   - personalized recommendations (for users with history)
   - cold-start recommendations (for new users)
   - similar-movie recommendations (item-to-item)
2. Deliver a **Streamlit app** with clear explanations:
   - "Because you liked X"
   - "Popular in genre Y"
   - "Similar to Z"
3. Evaluate models with **ranking metrics** (not only error metrics):
   - `Precision@K`, `Recall@K`, `NDCG@K`, `HitRate@K`
   - coverage and basic diversity checks
4. Keep the solution **explainable and reproducible**.

---

## 2. Notebook Writing Standards (follow style from `.tests` repo)

These standards apply to **every notebook task below**.

### Structure and Tone
- Start with a short narrative introduction:
  - what this phase is
  - why it matters for the project
  - what the reader will understand after reading it
- Use clear section headings and subheadings.
- Write for mixed audiences:
  - technical readers (methods, metrics, code)
  - non-technical readers (plain-language explanation)
- Prefer natural-language paragraphs over bullet-heavy writing.
- Use bullet points only when they are truly needed to improve clarity (e.g., short checklists, explicit comparisons, or required itemized lists); avoid "bullet dumps."
- End with a summary / interpretation section tied to the app.

### Required "Plain Language" Explanations
- Before or after each important technical step, add a short plain-language explanation.
- Explain key ML terms (e.g., collaborative filtering, sparse matrix, NDCG) in simple words.
- Every chart/table must include:
  - what it shows
  - why it matters for the recommender app

### Diagram Rule (important)
If you include a diagram (workflow, architecture, model comparison, user flow, etc.):
- Add a short explanation paragraph for non-technical readers directly below it.
- Explain the meaning of arrows/boxes/colors in plain language.
- State what decision the diagram supports.

### Documentation Quality
- Clearly name data sources and file paths (use `ml-25m/...` paths).
- State assumptions and limitations.
- State what is placeholder, what is final, and what still needs work.
- Use consistent notebook filenames and phase names.

---

## 3. QUAAACK Task List (Notebook Deliverables)

The tasks below follow your requirement:
- `Q` and `U` are separate tasks
- `AAA` is combined into a single task
- `C` and `K` are included to complete QUAAACK

### Task 1 - Q-Phase Notebook (`Q-Phase.ipynb`) DONE

### Goal
Define the recommendation problem clearly before building anything.

### Notebook Deliverable
Create `Q-Phase.ipynb` for the movie recommendation app.

### Must Include
1. **Project overview (plain language)**
   - What the app does
   - Why recommendations are useful
   - Why Streamlit is used
2. **Stakeholders**
   - End users
   - Product owner / reviewer
   - Developer / ML engineer
   - Non-technical readers
   - For each stakeholder: needs, pain points, success criteria
3. **Core recommendation questions**
   - How do we recommend for users with history?
   - How do we recommend for new users?
   - How do we explain recommendations clearly?
4. **Scope and non-scope**
   - In scope: offline recommendations, Streamlit demo, explainability
   - Out of scope (initial version): online learning, real-time retraining, production API scaling
5. **Success metrics (business + ML)**
   - `Precision@10`, `Recall@10`, `NDCG@10`, `HitRate@10`
   - catalog coverage
   - app response target (e.g., recommendation generation under a few seconds after selection)
6. **Risks and constraints**
   - cold-start
   - popularity bias
   - sparse ratings
   - limited metadata (compared to commercial systems)
7. **QUAAACK roadmap preview**
   - one short section explaining what happens in U, AAA, C, K

### Recommended Visuals / Diagrams
- User journey diagram (input -> recommender -> top-N list -> explanation)
- QUAAACK phase roadmap

### Non-Technical Explanation Requirement
Add a short explanation below each diagram describing:
- what the boxes mean
- what happens first/next
- how this helps a movie watcher

---

### Task 2 - U-Phase Notebook (`U-Phase.ipynb`) DONE

### Goal
Understand the `ml-25m` dataset structure, quality, sparsity, and modeling constraints.

### Notebook Deliverable
Create `U-Phase.ipynb` focused on EDA and data understanding for movie recommendations.

### Must Include
1. **Dataset inventory (`ml-25m`)**
   - Describe each file and whether it is required or optional in v1
   - Summarize `ml-25m/README.txt` key points
2. **Data loading and schema inspection**
   - column names
   - dtypes
   - row counts
   - memory considerations (especially `ratings.csv`, `genome-scores.csv`)
3. **Data quality checks**
   - duplicates
   - missing values
   - invalid ratings
   - timestamp parsing
   - malformed genres or tags
4. **Exploratory analysis (core recommender insights)**
   - ratings distribution
   - users per number of ratings (activity distribution)
   - movies per number of ratings (long-tail popularity)
   - average rating per movie / user
   - time trends (rating activity over years)
   - genre frequency and co-occurrence (from `movies.csv`)
5. **Sparsity and cold-start analysis**
   - user-item matrix sparsity estimate
   - proportion of low-activity users
   - proportion of low-interaction movies
   - implications for collaborative filtering
6. **Feature availability assessment**
   - what can support content-based methods (genres, tags, genome features)
   - what can support collaborative filtering (ratings + timestamps)
7. **Train/validation/test split strategy**
   - chronological split rationale
   - why random split can mislead in recommender systems
   - leakage risks to avoid
8. **U-Phase summary**
   - which files/features move to modeling (AAA)
   - what is postponed for performance reasons (e.g., full genome usage in v1)

### Recommended Visuals / Diagrams
- Ratings histogram
- User activity histogram
- Movie popularity long-tail plot
- Timeline plot of rating counts by year
- Simple data pipeline diagram (`ml-25m` files -> processed tables)

### Non-Technical Explanation Requirement
For each chart:
- one paragraph explaining what the chart means in everyday language
- one sentence explaining how it affects recommendation quality or app UX

---

### Task 3 - AAA-Phase Notebook (`A-Phase.ipynb` or `AAA-Phase.ipynb`)

### Goal
Combine **A1 (Algorithm Selection)**, **A2 (Adapt Features)**, and **A3 (Adjust/Assess)** in one notebook and build the first working recommendation models.

### Notebook Deliverable
Create one combined notebook for model development and evaluation.

### Must Include

#### A1 - Algorithm Selection
1. **Baseline methods (required)**
   - random baseline (for sanity check)
   - popularity baseline (global top-rated/top-rated-with-min-count)
   - genre-filtered popularity baseline
2. **Candidate recommender approaches**
   - content-based (genres/tags/genome)
   - collaborative filtering (user-user, item-item, or matrix factorization)
   - hybrid recommendation (recommended final direction for app)
3. **Model selection rationale**
   - explain tradeoffs: quality, speed, explainability, implementation complexity
   - explicitly state which approach is best for the Streamlit v1 app

#### A2 - Adapt Features
4. **Feature engineering / preprocessing**
   - encode genres
   - tag preprocessing (optional in v1, required if used)
   - rating normalization strategy (if applicable)
   - minimum interaction thresholds (users/items)
   - candidate generation rules
5. **Cold-start strategy**
   - new user: genre preferences + popularity fallback
   - new item: metadata-based similarity or exclude until enough interactions
6. **Data split implementation**
   - chronological split for evaluation
   - holdout logic for top-N recommendation testing
   - leakage checks (must be documented)

#### A3 - Adjust and Assess
7. **Hyperparameter tuning**
   - choose a small, justified search space
   - tune for ranking metrics (not RMSE-only)
8. **Evaluation**
   - report `Precision@K`, `Recall@K`, `NDCG@K`, `HitRate@K`
   - compare all candidates in a summary table
   - evaluate by user segments (low activity vs high activity)
9. **Explainability examples**
   - show sample recommendations with "why" text
   - at least 2-3 user examples and 2 similar-movie examples
10. **Export plan for Streamlit**
   - what artifacts are saved (model, encoders, similarity matrix, metadata)
   - artifact paths and formats

### Recommended Visuals / Diagrams
- Model comparison table/plot (ranking metrics)
- Hybrid recommender architecture diagram
- Offline evaluation flow diagram (train -> validate -> test -> metrics)
- Example recommendation explanation cards/screenshots (if available)

### Non-Technical Explanation Requirement
Below each model comparison chart/table:
- explain which model is "better" in plain terms
- explain why a slightly lower score may still be preferred (e.g., faster and clearer)

---

### Task 4 - C-Phase Notebook (`C-Phase.ipynb`)

### Goal
Conclude, compare, and formally choose the model setup for the Streamlit app.

### Notebook Deliverable
Create `C-Phase.ipynb` as the final decision notebook.

### Must Include
1. **Final comparison summary**
   - baselines vs chosen model
   - key ranking metrics at chosen `K`
   - runtime / inference tradeoff
2. **Stakeholder-oriented interpretation**
   - what the results mean for end users
   - what they mean for project reviewers
   - what they mean for implementation complexity
3. **Failure modes and limitations**
   - sparse users
   - niche content
   - popularity dominance
   - metadata limitations in `ml-25m`
4. **Go / No-Go decision for Streamlit integration**
   - selected v1 model setup
   - deferred improvements for v2
5. **Final recommended app behavior**
   - personalized mode
   - cold-start mode
   - similar-movie mode
   - fallback behavior

### Recommended Visuals / Diagrams
- Decision matrix (quality vs speed vs explainability)
- Final system behavior flow (user input -> recommendation mode -> output)

### Non-Technical Explanation Requirement
Add a plain-language "What this means in practice" section after the decision matrix.

---

### Task 5 - K-Phase Notebook (`K-Phase.ipynb`)

### Goal
Transfer knowledge into implementation-ready guidance for the Streamlit app.

### Notebook Deliverable
Create `K-Phase.ipynb` that documents how the selected recommender is integrated into Streamlit.

### Must Include
1. **Streamlit app concept**
   - user flows (new user vs returning user vs similar-movie search)
   - screens/components (search, filters, recommendation list, explanation panel)
2. **Inference pipeline for the app**
   - load artifacts
   - preprocess user input
   - generate candidates
   - rank and explain
   - display top-N results
3. **Caching and performance strategy**
   - what to cache in Streamlit
   - what is precomputed offline
   - expected bottlenecks
4. **Error handling / edge cases**
   - no matching movie search
   - insufficient user preferences
   - missing metadata
   - empty recommendation set
5. **Plain-language demo script**
   - a short step-by-step walkthrough for non-technical stakeholders
6. **Handover checklist**
   - files needed
   - run command(s)
   - assumptions
   - known limitations

### Recommended Visuals / Diagrams
- Streamlit UI wireframe
- Request-to-result inference flow
- Artifact map (`artifacts/` + metadata + app inputs)

### Non-Technical Explanation Requirement
For each UI/inference diagram, add a short paragraph that explains:
- what the user clicks/selects
- what the app does behind the scenes
- what appears on screen and why

---

## 4. Cross-Task Standards (applies to all notebooks)

### Naming and Consistency
- Use consistent phase names:
  - `Q-Phase.ipynb`
  - `U-Phase.ipynb`
  - `A-Phase.ipynb` (combined AAA)
  - `C-Phase.ipynb`
  - `K-Phase.ipynb`
- Refer to the app consistently as the **Movie Recommendation App** (or your final product name).

### Reproducibility
- Fix random seeds where randomness exists.
- State package versions (or link to `requirements.txt` when available).
- Use explicit file paths from `ml-25m/`.
- Do not hide critical preprocessing in untracked ad-hoc scripts without documentation.

### Accessibility for Non-Technical Readers
- Avoid unexplained jargon.
- Add "Simple explanation" callouts for complex concepts.
- Connect every technical result back to a user-facing app impact.

---

## 5. Suggested Execution Order
1. `Q-Phase.ipynb`
2. `U-Phase.ipynb`
3. `A-Phase.ipynb` (AAA combined)
4. `C-Phase.ipynb`
5. `K-Phase.ipynb`

This order preserves the QUAAACK logic and matches the writing style pattern used in the `.tests` reference repo.
