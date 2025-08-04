import pandas as pd
import streamlit as st
import requests
from pathlib import Path


try:
    import openpyxl  
except ImportError:
    st.error("Missing dependency openpyxl. Please add it to requirements.txt and install (`pip install openpyxl`).")
    st.stop()


try:
    ENML_SHEET_ID = st.secrets["ENML_SHEET_ID"]
except Exception:
    ENML_SHEET_ID = "1vujnZVEBTGzsRctZ5rhevnsqdEPMlfdS"

try:
    MLML_SHEET_ID = st.secrets["MLML_SHEET_ID"]
except Exception:
    MLML_SHEET_ID = "1UW8H2Kma8TNoREZ5ohnC1lV87laotTGW"
# -------------------------------------------------------

# Local cache
CACHE_DIR = Path(".cache_data")
CACHE_DIR.mkdir(exist_ok=True)
ENML_CACHE = CACHE_DIR / "en_ml.xlsx"
MLML_CACHE = CACHE_DIR / "datukexcel.xlsx"

def download_sheet_as_xlsx(sheet_id: str, target_path: Path):
    if target_path.exists():
        return
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        resp = requests.get(export_url, allow_redirects=True, timeout=30)
    except Exception as e:
        st.error(f"Network error downloading sheet {sheet_id}: {e}")
        raise
    if resp.status_code != 200:
        st.error(f"Failed to download sheet {sheet_id}: HTTP {resp.status_code}")
        raise RuntimeError(f"Download error for sheet {sheet_id}")
    target_path.write_bytes(resp.content)

def load_data_uncached():
    download_sheet_as_xlsx(ENML_SHEET_ID, ENML_CACHE)
    download_sheet_as_xlsx(MLML_SHEET_ID, MLML_CACHE)

    enml = pd.read_excel(ENML_CACHE)
    mlml = pd.read_excel(MLML_CACHE)

    for df, name in [(enml, "English-Malayalam"), (mlml, "Malayalam-Malayalam")]:
        if "from_content" not in df.columns or "to_content" not in df.columns:
            st.error(f"Sheet '{name}' must have columns 'from_content' and 'to_content'.")
            raise ValueError(f"Missing required columns in {name} sheet")

    enml = enml.loc[:, ["from_content", "to_content"]].dropna().copy()
    mlml = mlml.loc[:, ["from_content", "to_content"]].dropna().copy()

    enml.loc[:, "from_content"] = enml["from_content"].astype(str).str.strip()
    enml.loc[:, "to_content"] = enml["to_content"].astype(str).str.strip()
    mlml.loc[:, "from_content"] = mlml["from_content"].astype(str).str.strip()
    mlml.loc[:, "to_content"] = mlml["to_content"].astype(str).str.strip()

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

def build_prefix_maps():
    if "prefix_map_enml" not in st.session_state:
        pm = {}
        for src, tgt in st.session_state.enml_pairs:
            for i in range(1, len(src) + 1):
                key = src[:i]
                pm.setdefault(key, []).append((src, tgt))
        st.session_state.prefix_map_enml = pm
    if "prefix_map_ml_en" not in st.session_state:
        pm = {}
        for src, tgt in st.session_state.enml_pairs:
            t_low = tgt.lower()
            for i in range(1, len(t_low) + 1):
                key = t_low[:i]
                pm.setdefault(key, []).append((t_low, src))
        st.session_state.prefix_map_ml_en = pm
    if "prefix_map_mlml" not in st.session_state:
        pm = {}
        for src, tgt in st.session_state.mlml_pairs:
            for i in range(1, len(src) + 1):
                key = src[:i]
                pm.setdefault(key, []).append((src, tgt))
        st.session_state.prefix_map_mlml = pm

def get_suggestions(word_lower: str, direction: str, limit=20):
    if not word_lower:
        return []
    suggestions = []
    if direction == "English → മലയാളം":
        matches = st.session_state.prefix_map_enml.get(word_lower, [])
        suggestions = [src for src, _ in matches]
    elif direction == "മലയാളം → English":
        matches = st.session_state.prefix_map_ml_en.get(word_lower, [])
        suggestions = [src for src, _ in matches]
    else:
        matches = st.session_state.prefix_map_mlml.get(word_lower, [])
        suggestions = [src for src, _ in matches]
    seen = set()
    out = []
    for s in suggestions:
        if s not in seen:
            out.append(s)
            seen.add(s)
        if len(out) >= limit:
            break
    return out

def render_contact():
    st.markdown("### 📬 Let's Connect")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<a href="mailto:yaduk883@gmail.com" target="_blank" style="text-decoration:none;">'
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'background:#0d6efd;color:white;padding:8px 14px;border-radius:8px;">'
            '📧 Email</div></a>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<a href="https://github.com/yaduk883" target="_blank" style="text-decoration:none;">'
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'background:#24292f;color:white;padding:8px 14px;border-radius:8px;">'
            '🐙 GitHub</div></a>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<a href="https://instagram.com/ig.yadu/" target="_blank" style="text-decoration:none;">'
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'background:#E1306C;color:white;padding:8px 14px;border-radius:8px;">'
            '📸 Instagram</div></a>',
            unsafe_allow_html=True,
        )

def main():
    st.set_page_config(page_title="📖 മലയാളം നിഘണ്ടു", layout="wide")
    st.title("📖 മലയാളം നിഘണ്ടു – Malayalam Bilingual Dictionary")

    with st.spinner("“Words are, in my not-so-humble opinion, our most inexhaustible source of magic.” – Albus Dumbledore"):
        if "cached_data" not in st.session_state:
            st.session_state.cached_data = load_data_uncached()
        enml_df, mlml_df = st.session_state.cached_data

    if "enml_pairs" not in st.session_state:
        st.session_state.enml_pairs = list(zip(enml_df["from_content"].str.lower(), enml_df["to_content"]))
    if "mlml_pairs" not in st.session_state:
        st.session_state.mlml_pairs = list(zip(mlml_df["from_content"].str.lower(), mlml_df["to_content"]))
    if "search_input" not in st.session_state:
        st.session_state.search_input = ""

    build_prefix_maps()

    direction = st.radio(
        "Select Direction",
        ("English → മലയാളം", "മലയാളം → English", "മലയാളം → മലയാളം"),
        index=0,
        horizontal=True
    )

    search_term = st.text_input(
        "തിരയുക 🔍",
        value=st.session_state.get("search_input", ""),
        placeholder="Type a word...",
        key="search_input"
    )
    word_lower = search_term.strip().lower()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Suggestions")
        suggestions = get_suggestions(word_lower, direction)
        if suggestions:
            st.write("Click a suggestion to fill and search:")
            for sug in suggestions:
                if st.button(sug, key=f"sugg-{direction}-{sug}"):
                    st.session_state.search_input = sug
                    st.experimental_rerun()

        st.markdown("---")
        with st.expander("Add / Extend Dictionary"):
            if direction == "English → മലയാളം":
                from_label = "English word"
                to_label = "Malayalam word"
            elif direction == "മലയാളം → English":
                from_label = "Malayalam word"
                to_label = "English word"
            else:
                from_label = "Malayalam word"
                to_label = "Malayalam synonym/translation"

            with st.form("add_word_form", clear_on_submit=True):
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
                        st.write(f"→ {tgt}")
                        shown.add(tgt)
            else:
                st.info("No exact match found.")
        else:
            st.write("Type to search or click a suggestion.")

    with st.expander("Contact Me"):
        render_contact()

if __name__ == "__main__":
    main()
