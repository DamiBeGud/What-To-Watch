from __future__ import annotations

from typing import Any, Sequence

import streamlit as st


def render_recommendation_cards(cards: Sequence[dict[str, Any]]) -> None:
    if not cards:
        st.info("No recommendation cards to display for the current request.")
        return

    st.markdown("### Recommendations")
    columns = st.columns(2)
    for idx, card in enumerate(cards):
        column = columns[idx % 2]
        with column:
            with st.container(border=True):
                title = card.get("title") or "Unknown title"
                year = card.get("year")
                title_line = "{}. {}".format(card.get("rank", idx + 1), title)
                if year:
                    title_line = "{} ({})".format(title_line, year)
                st.markdown("**{}**".format(title_line))

                poster_url = str(card.get("poster_url") or "").strip()
                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.caption(card.get("poster_placeholder") or "Poster unavailable in this artifact bundle.")

                st.caption("movieId: {}".format(card.get("movieId")))
                st.write("Genres: {}".format(card.get("genres") or "(no genres listed)"))
                st.write("Why this appears: {}".format(card.get("reason") or "No explanation available."))

                score = card.get("score")
                if score is not None:
                    st.caption("Score: {:.4f}".format(float(score)))
                source_label = card.get("source_label")
                if source_label:
                    st.caption("Source: {}".format(source_label))
                if card.get("metadata_notes"):
                    st.caption(str(card.get("metadata_notes")))
