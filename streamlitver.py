import pandas as pd
import streamlit as st
import requests
from pathlib import Path

ENML_SHEET_ID = "1vujnZVEBTGzsRctZ5rhevnsqdEPMlfdS"  # English ↔ Malayalam
MLML_SHEET_ID = "1UW8H2Kma8TNoREZ5ohnC1lV87laotTGW"  # Malayalam ↔ Malayalam


CACHE_DIR = Path(".cache_data")
CACHE_DIR.mkdir(exist_ok=True)
ENML_CACHE = CACHE_DIR / "en_ml.xlsx"
MLML_CACHE = CACHE_DIR / "datukexcel.xlsx"

def download_sheet_as_xlsx(sheet_id: str, target_path: Path):
    if target_path.exists():
        return
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    resp = requests.get(export_url, allow_redirects=True, timeout=30)
    if resp.status_code != 200:
        st.error(f"Failed to download sheet {sheet_id}: HTTP {resp.status_code}")
        raise RuntimeError(f"Download error for sheet {sheet_id}")
    target_path.write_bytes(resp.content)

@st.cache_data(ttl=300)
def load_data():
    download_sheet_as_xlsx(ENML_SHEET_ID, ENML_CACHE)
    download_sheet_as_xlsx(MLML_SHEET_ID, MLML_CACHE)

    enml = pd.read_excel(ENML_CACHE)
    mlml = pd.read_excel(MLML_CACHE)

    for df, name in [(enml, "English-Malayalam"), (mlml, "Malayalam-Malayalam")]:
        if "from_content" not in df.columns or "to_content" not in df.columns:
            st.error(f"Sheet '{name}' must have columns 'from_content' and 'to_content'.")
            raise ValueError(f"Missing required columns in {name} sheet")

    enml = enml.dropna(subset=["from_content", "to_content"])
    mlml = mlml.dropna(subset=["from_content", "to_content"])
    enml["from_content"] = enml["from_content"].astype(str).str.strip()
    enml["to_content"] = enml["to_content"].astype(str).str.strip()
    mlml["from_content"] = mlml["from_content"].astype(str).str.strip()
    mlml["to_content"] = mlml["to_content"].astype(str).str.strip()
    return enml, mlml

def save_enml(df: pd.DataFrame):
    try:
        df.to_excel(ENML_CACHE, index=False)
    except Exception as e:
        st.error(f"Could not save English-Malayalam dictionary locally: {e}")

def save_mlml(df: pd.DataFrame):
    try:
        df.to_excel(MLML_CACHE, index=False)
    except Exception as e:
        st.error(f"Could not save Malayalam-Malayalam dictionary locally: {e}")

def copy_js(text: str):
    st.components.v1.html(
        f"""
        <script>
        navigator.clipboard.writeText({text!r});
        </script>
        """,
        height=0,
        key=f"copy-{text}"
    )

def main():
    st.set_page_config(page_title="📖 മലയാളം നിഘണ്ടു", layout="wide")
    st.title("📖 മലയാളം നിഘണ്ടു – Malayalam Bilingual Dictionary")

    # Custom loading message / quote
    with st.spinner("Loading dictionary... “Words are, in my not-so-humble opinion, our most inexhaustible source of magic.” – Albus Dumbledore"):
        enml_df, mlml_df = load_data()

    if "enml_pairs" not in st.session_state:
        st.session_state.enml_pairs = list(
            zip(enml_df["from_content"].str.lower(), enml_df["to_content"])
        )
    if "mlml_pairs" not in st.session_state:
        st.session_state.mlml_pairs = list(
            zip(mlml_df["from_content"].str.lower(), mlml_df["to_content"])
        )
    if "search_input_override" not in st.session_state:
        st.session_state.search_input_override = ""

    direction = st.radio(
        "Select Direction",
        ("English → മലയാളം", "മലയാളം → English", "മലയാളം → മലയാളം"),
        index=0,
        horizontal=True
    )

    search_term = st.text_input(
        "തിരയുക 🔍",
        value=st.session_state.search_input_override,
        placeholder="Type a word...",
        key="search_input"
    )
    word_lower = search_term.strip().lower()

    col1, col2 = st.columns([1, 2])

    selected = "-- none --"
    with col1:
        st.subheader("Suggestions")
        suggestions = []
        if word_lower:
            if direction == "English → മലയാളം":
                matches = [(src, tgt) for src, tgt in st.session_state.enml_pairs if src.startswith(word_lower)]
                exacts = [(src, tgt) for src, tgt in st.session_state.enml_pairs if src == word_lower]
            elif direction == "മലയാളം → English":
                matches = [(tgt.lower(), src) for src, tgt in st.session_state.enml_pairs if tgt.lower().startswith(word_lower)]
                exacts = [(tgt.lower(), src) for src, tgt in st.session_state.enml_pairs if tgt.lower() == word_lower]
            else:
                matches = [(src, tgt) for src, tgt in st.session_state.mlml_pairs if src.startswith(word_lower)]
                exacts = [(src, tgt) for src, tgt in st.session_state.mlml_pairs if src == word_lower]

            seen = set()
            for src, tgt in matches:
                if src not in seen:
                    suggestions.append(src)
                    seen.add(src)
                if len(suggestions) >= 20:
                    break

        if suggestions:
            st.write("Click a suggestion to search:")
            for sug in suggestions:
                if st.button(sug, key=f"sugg-{sug}"):
                    selected = sug
                    word_lower = sug.lower()
                    st.session_state.search_input_override = sug

        st.markdown("---")
        st.subheader("Add / Extend Dictionary")
        with st.form("add_word_form", clear_on_submit=True):
            if direction == "English → മലയാളം":
                from_label = "English word"
                to_label = "Malayalam word"
            elif direction == "മലയാളം → English":
                from_label = "Malayalam word"
                to_label = "English word"
            else:
                from_label = "Malayalam word"
                to_label = "Malayalam synonym/translation"

            new_from = st.text_input(from_label, key="new_from")
            new_to = st.text_input(to_label, key="new_to")
            submitted = st.form_submit_button("Add Word")
            if submitted:
                if not new_from.strip() or not new_to.strip():
                    st.warning("Both fields are required.")
                else:
                    if direction in ("English → മലയാളം", "മലയാളം → English"):
                        st.session_state.enml_pairs.append((new_from.strip().lower(), new_to.strip()))
                        enml_df.loc[len(enml_df)] = [new_from.strip(), new_to.strip()]
                        save_enml(enml_df)
                        st.success(f"Added: {new_from} → {new_to}")
                    else:
                        st.session_state.mlml_pairs.append((new_from.strip().lower(), new_to.strip()))
                        mlml_df.loc[len(mlml_df)] = [new_from.strip(), new_to.strip()]
                        save_mlml(mlml_df)
                        st.success(f"Added: {new_from} → {new_to}")

    with col2:
        st.subheader("Result")
        if word_lower:
            results = []
            if direction == "English → മലയാളം":
                results = [(src, tgt) for src, tgt in st.session_state.enml_pairs if src == word_lower]
            elif direction == "മലയാളം → English":
                results = [(tgt.lower(), src) for src, tgt in st.session_state.enml_pairs if tgt.lower() == word_lower]
            else:
                results = [(src, tgt) for src, tgt in st.session_state.mlml_pairs if src == word_lower]

            if results:
                display_src = results[0][0]
                st.markdown(f"### **{display_src}**")
                shown = set()
                for _, tgt in results:
                    if tgt not in shown:
                        col_a, col_b = st.columns([8, 1])
                        with col_a:
                            st.write(f"→ {tgt}")
                        with col_b:
                            if st.button("Copy", key=f"copy-{tgt}"):
                                copy_js(tgt)
                                st.success("Copied to clipboard")
                        shown.add(tgt)
            else:
                st.info("No exact match found.")
        else:
            st.write("Type to search or click a suggestion.")

    st.markdown("---")
    st.caption(
        "Dictionary data is loaded from the provided Google Sheets (exported as Excel) and cached locally. "
        "New additions are saved to the local cache only."
    )

if __name__ == "__main__":
    main()
