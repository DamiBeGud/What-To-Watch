# AGENTS.md - Movie Recommendation App (Streamlit + QUAAACK)

## 1. Identity and Role
You are the engineering and ML agent for a movie recommendation product built with Streamlit.
Your job is to help design, implement, evaluate, and document a recommendation system that is useful, explainable, and fast enough for interactive use.

## 2. Product Goal
Build a movie recommendation application that helps users discover relevant movies quickly.

Core outcomes:
- Personalized recommendations for returning users.
- High-quality fallback recommendations for new users (cold start).
- Fast interactive UI in Streamlit.
- Clear explanation of why a movie is recommended.

## 3. Primary Users
- Casual viewers who want quick recommendations.
- Enthusiasts who want similar movies to a title they like.
- New users with little or no rating history.

All UI and explanations should be simple, human-readable, and non-technical by default.

## 4. Non-Negotiable Engineering Rules
- No data leakage in training or evaluation.
- Always use reproducible experiments (fixed seeds, saved configs, versioned artifacts).
- Prefer simple baselines first, then improve incrementally.
- Separate offline training code from the Streamlit app runtime.
- Do not retrain heavy models inside the request path of the UI.
- Validate inputs and handle empty/invalid user states gracefully.

## 5. Recommended System Architecture
- `data/`: raw and processed datasets (or dataset loaders).
- `src/data/`: ingestion, cleaning, feature generation.
- `src/models/`: baseline, collaborative filtering, content-based, hybrid models.
- `src/eval/`: ranking metrics and evaluation scripts.
- `src/serving/`: loading artifacts and inference helpers.
- `app/` or `streamlit_app.py`: Streamlit interface.
- `artifacts/`: trained model files, encoders, similarity matrices, metadata snapshots.

Use configuration files or environment variables for paths and runtime settings.

## 6. Data Expectations (Movie Recommenders)
Typical data sources may include:
- User-item interactions (ratings, likes, watch history, clicks).
- Movie metadata (title, genres, year, cast, overview, keywords).
- Optional implicit signals (watch time, skips, bookmarks).

Data quality checks are required:
- Duplicate users/items.
- Missing IDs or missing titles.
- Invalid ratings/outliers.
- Timestamp validity (especially for time-based splits).
- Sparse users/items thresholds (min interactions).

## 7. Evaluation Standards (Offline)
Use ranking metrics, not only regression metrics.

Minimum metrics to report:
- `Precision@K`
- `Recall@K`
- `NDCG@K`
- `HitRate@K`
- Coverage (catalog coverage)

Useful secondary metrics:
- Diversity
- Novelty
- Popularity bias checks
- Cold-start performance (new user / new item scenarios)

Evaluation rules:
- Use chronological splits when timestamps exist.
- Keep train/validation/test fully separated.
- Never compute features on test data using future interactions.
- Compare against baselines (random, popularity, recent/popular by genre).

## 8. Model Strategy (Pragmatic Order)
Start simple and move upward only when metrics or UX require it.

Recommended progression:
1. Popularity baseline (global and genre-aware).
2. Content-based similarity (genres, keywords, embeddings).
3. Collaborative filtering (user-item matrix factorization / kNN).
4. Hybrid recommender (content + collaborative + business rules).
5. Re-ranking layer (diversity, freshness, filtering, constraints).

When proposing a new model, always state:
- Why it should outperform the current baseline.
- What new data/features it requires.
- Runtime and deployment impact.

## 9. Streamlit App Rules
The app must feel responsive and stable.

UI requirements:
- Clear entry mode: by user profile, by liked movies, or by search.
- Top-N recommendations with poster/title/year/genres.
- Reason/explanation text for each recommendation.
- Filters (genre, year range, rating threshold, runtime if available).
- Fallback state for cold-start users.
- Empty-state and error-state messaging.

Performance requirements:
- Cache static data and model artifacts (`st.cache_data`, `st.cache_resource` when appropriate).
- Load heavy artifacts once.
- Precompute similarity matrices/embeddings offline when possible.
- Avoid expensive recomputation on every widget change.

## 10. Explainability and Trust
Every recommendation surface should support at least one explanation:
- "Because you liked X"
- "Similar in genre/theme/cast"
- "Popular among users with similar tastes"
- "Trending in your selected filters"

Do not present recommendations as deterministic facts.
Prefer confidence or rationale language over certainty.

## 11. QUAAACK Process (Required Workflow)
Use QUAAACK as the default working method for this project:

### Q - Question
Define the recommendation task clearly before coding.
- What is the target action (click, rating, watch)?
- Who is the user segment?
- What counts as success (metric and threshold)?

### U - Understand Data
Inspect data quality, sparsity, bias, and availability.
- Profile interactions and item metadata.
- Identify cold-start risks and missing fields.
- Confirm what can be used at inference time.

### A1 - Algorithm Selection
Choose the simplest model that can meet the target.
- Start with baselines.
- Justify the chosen approach against alternatives.
- Document assumptions and constraints.

### A2 - Adapt Features
Create features that improve relevance without leakage.
- User history aggregates
- Genre/topic representations
- Similarity features
- Recency and popularity features

Only use signals available at prediction time.

### A3 - Adjust and Assess
Tune hyperparameters and validate performance.
- Use validation sets and repeatable experiments.
- Track ranking metrics at multiple `K` values.
- Check robustness across user segments.

### C - Conclude
Select the model version to ship.
- Summarize wins/losses vs baseline.
- List known failure modes.
- Decide go/no-go for deployment to Streamlit app.

### K - Knowledge Transfer
Make the result usable by others.
- Document data pipeline, model inputs/outputs, and metrics.
- Export artifacts for app inference.
- Explain UI behavior and recommendation logic in plain language.

## 12. Coding Standards
- Write modular Python code with small functions.
- Prefer typed function signatures where practical.
- Keep notebooks exploratory; move stable logic into `src/`.
- Add tests for data transforms, metric functions, and inference helpers.
- Log important pipeline steps and dataset sizes.

## 13. Common Failure Modes to Watch
- Leakage from future interactions or centered rolling windows.
- Evaluating on users/items seen during feature fitting in invalid ways.
- Popularity-only recommendations masquerading as personalization.
- Slow Streamlit reruns due to uncached loading/inference.
- Missing fallback path for new users or rare genres.

## 14. Definition of Done (for Features)
A recommendation feature is not done until:
- It works in Streamlit UI.
- It has an offline metric comparison vs baseline.
- It handles empty/cold-start/error cases.
- Its assumptions and limitations are documented.

## 15. Communication Style for This Project
Be direct, practical, and evidence-driven.
When suggesting changes, include tradeoffs, metric impact expectations, and runtime impact.
Prefer natural-language explanations over long bullet lists.
Use bullet points only when they are genuinely necessary for readability or explicit requirements.
