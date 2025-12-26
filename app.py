import pandas as pd
import streamlit as st
import feedparser
from dateutil import parser as dtparser
import urllib.parse

# =============================
# CONFIG DE LA PAGE
# =============================
st.set_page_config(
    page_title="Veille VSS – Art (France)",
    layout="wide"
)

# =============================
# FONCTION GOOGLE NEWS RSS
# =============================
def google_news_rss(query, hl="fr", gl="FR", ceid="FR:fr"):
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

# =============================
# 🔴 ICI TU AJOUTES / SUPPRIMES DES MOTS-CLÉS
# =============================
QUERIES = [
    '("violences sexuelles" OR "violences sexistes" OR "harcèlement sexuel" OR viol OR agression) (art OR cinéma OR theatre OR musique OR "arts plastiques" OR photographie OR festival) France',
    '("violences sexuelles" OR "harcèlement sexuel") cinéma France',
    '("violences sexuelles" OR "harcèlement sexuel") théâtre France',
    '("violences sexuelles" OR "harcèlement sexuel") musique France',
    '("violences sexuelles" OR "harcèlement sexuel") festival France',
]

# =============================
# COLLECTE DES ARTICLES
# =============================
@st.cache_data(ttl=900)  # cache 15 min
def fetch_articles(max_per_query=50):
    rows = []

    for q in QUERIES:
        url = google_news_rss(q)
        feed = feedparser.parse(url)

        for e in feed.entries[:max_per_query]:
            raw_date = getattr(e, "published", None) or getattr(e, "updated", None)

            try:
                date = dtparser.parse(raw_date) if raw_date else None
            except:
                date = None

            rows.append({
                "date": date,
                "titre": getattr(e, "title", "").strip(),
                "lien": getattr(e, "link", "").strip(),
                "source": getattr(getattr(e, "source", None), "title", "") if getattr(e, "source", None) else "",
                "requete": q
            })

    df = pd.DataFrame(rows)

    # suppression doublons
    df = df.drop_duplicates(subset=["lien"])

    # tri par date (récent → ancien)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date", ascending=False, na_position="last")

    # format date FR
    df["date_ddmmyyyy"] = df["date"].dt.strftime("%d/%m/%Y")

    return df.reset_index(drop=True)

# =============================
# INTERFACE
# =============================
st.title("Veille presse — Violences sexuelles et sexistes")
st.subheader("Secteur artistique – France")
st.caption("Sources : Google News RSS – tri du plus récent au plus ancien")

col1, col2, col3 = st.columns([1,1,2])

with col1:
    max_per_query = st.slider(
        "Articles max par requête",
        min_value=10,
        max_value=100,
        value=50,
        step=10
    )

with col2:
    if st.button("🔄 Rafraîchir"):
        st.cache_data.clear()

with col3:
    search = st.text_input("Recherche dans le titre", "")

df = fetch_articles(max_per_query=max_per_query)

# =============================
# FILTRES
# =============================
sources = ["(toutes)"] + sorted(df["source"].dropna().unique())
requetes = ["(toutes)"] + sorted(df["requete"].dropna().unique())

f1, f2 = st.columns(2)

with f1:
    source_pick = st.selectbox("Filtrer par source", sources)

with f2:
    requete_pick = st.selectbox("Filtrer par requête", requetes)

view = df.copy()

if source_pick != "(toutes)":
    view = view[view["source"] == source_pick]

if requete_pick != "(toutes)":
    view = view[view["requete"] == requete_pick]

if search.strip():
    view = view[view["titre"].str.contains(search, case=False, na=False)]

st.write(f"**{len(view)} articles affichés**")

# =============================
# AFFICHAGE DES ARTICLES
# =============================
for _, r in view.iterrows():
    date_txt = r["date_ddmmyyyy"] if isinstance(r["date_ddmmyyyy"], str) else "Date inconnue"

    st.markdown(f"### {date_txt} — {r['titre']}")
    st.write(f"**Source :** {r['source']}")
    st.markdown(f"➡️ {r['lien']}")
    st.divider()
