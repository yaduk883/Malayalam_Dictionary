import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime
from pathlib import Path
import io
import base64
import time

# Page configuration
st.set_page_config(
    page_title="മലയാളം നിഘണ്ടു | Malayalam Dictionary",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Google Sheets Data Configuration
try:
    ENML_SHEET_ID = st.secrets["ENML_SHEET_ID"]
except Exception:
    ENML_SHEET_ID = "1vujnZVEBTGzsRctZ5rhevnsqdEPMlfdS"

try:
    MLML_SHEET_ID = st.secrets["MLML_SHEET_ID"]
except Exception:
    MLML_SHEET_ID = "1UW8H2Kma8TNoREZ5ohnC1lV87laotTGW"

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

# Load data with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_dictionary_data():
    """Load dictionary data from Google Sheets with caching"""
    return load_data_uncached()

# --- JAVASCRIPT FOR CLIPBOARD COPY ---
def copy_to_clipboard_js(text):
    """Executes JavaScript to copy text to clipboard."""
    # Escape single quotes and backslashes in the text for JavaScript string
    safe_text = text.replace(r'\\', r'\\\\').replace(r"'", r"\'")
    
    js_code = f"""
    var textToCopy = '{safe_text}';
    
    if (navigator.clipboard) {{
      navigator.clipboard.writeText(textToCopy).then(function() {{
        console.log('Async: Copying to clipboard was successful!');
      }}, function(err) {{
        console.error('Async: Could not copy text: ', err);
      }});
    }} else {{
      // Fallback: This is less reliable but necessary for some Streamlit/browser combos
      const textArea = document.createElement("textarea");
      textArea.value = textToCopy;
      textArea.style.position = "fixed"; 
      textArea.style.left = "-9999px"; 
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {{
        document.execCommand('copy');
      }} catch (err) {{
        console.error('Fallback: Oops, unable to copy', err);
      }}
      document.body.removeChild(textArea);
    }}
    """
    # Use st.components.v1.html to execute the script
    st.components.v1.html(f"<script>{js_code}</script>", height=0, width=0)
    st.toast(f"✅ Copied: '{text}'")


# Custom CSS for enhanced styling with proper theme support
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Malayalam:wght@400;600;700&display=swap');
    
    :root {
        --primary-color: #009688;
        --secondary-color: #00796B;
        --accent-color: #4CAF50;
        --text-color: #333; /* Default light mode text color (Dark text) */
        --bg-color: #f0fff0;
        --card-bg: #ffffff;
        --border-color: #e0e0e0;
    }
    
    [data-theme="dark"] {
        --text-color: #ffffff; /* Dark mode text color (White text) */
        --bg-color: #1e1e1e;
        --card-bg: #2d2d2d;
        --border-color: #404040;
    }

    /* FIX: Global override for Streamlit components to ensure custom text color is used */
    .st-emotion-cache-1jmveo5, /* Main Streamlit block */
    .st-emotion-cache-1jmveo5 > div,
    .st-emotion-cache-1jmveo5 > div h3,
    .st-emotion-cache-1jmveo5 > div h4,
    .st-emotion-cache-1jmveo5 > div p {
        color: var(--text-color) !important;
    }
    
    .malayalam-font {
        font-family: 'Noto Sans Malayalam', sans-serif !important;
        font-size: 18px;
        line-height: 1.6;
    }
    
    .blinking-header {
        font-size: 3rem;
        font-weight: bold;
        color: var(--primary-color);
        text-align: center;
        font-family: 'Noto Sans Malayalam', sans-serif;
        margin: 20px 0;
        padding: 20px;
        background: linear-gradient(45deg, var(--bg-color), var(--card-bg));
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,150,136,0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 4px 12px rgba(0,150,136,0.3); }
        to { box-shadow: 0 8px 24px rgba(0,150,136,0.6); }
    }
    
    .search-result-card-container {
        background: linear-gradient(135deg, var(--card-bg) 0%, var(--bg-color) 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 5px solid var(--primary-color);
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .translation-header {
        color: var(--primary-color);
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 2px solid var(--border-color);
    }

    /* FIX: Use Flexbox for item and remove Streamlit columns to eliminate white gap */
    .translation-item-row {
        display: flex;
        align-items: center;
        gap: 5px; /* Small gap between text and buttons */
        background-color: rgba(0, 150, 136, 0.05); 
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 8px;
        border: 1px solid rgba(0, 150, 136, 0.1);
        transition: all 0.3s;
    }
    
    .translation-item-row:hover {
        background-color: rgba(0, 150, 136, 0.2);
        transform: none; /* No movement needed here, only inside */
    }

    .translation-text {
        flex-grow: 1;
        line-height: 1.4;
        font-family: 'Noto Sans Malayalam', sans-serif;
        font-size: 16px;
        /* FIX: Ensures white text in dark mode for the actual result text */
        color: var(--text-color) !important;
        padding-right: 10px; 
    }

    /* Target Streamlit buttons specifically within this context to make them small */
    .translation-item-row button {
        padding: 0px 8px !important; 
        font-size: 14px;
        margin: 0 !important;
        height: 30px; 
        line-height: 1;
        width: 30px; /* fixed width for icons */
    }


    .malayalam-keyboard {
        background: linear-gradient(135deg, var(--card-bg) 0%, var(--bg-color) 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
        border: 2px solid var(--border-color);
    }
    
    .stats-card {
        background: linear-gradient(135deg, var(--card-bg) 0%, var(--bg-color) 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px 0;
        transition: all 0.3s;
        border: 1px solid var(--border-color);
    }
    
    .stats-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        'search_history': [],
        'favorites': [],
        'current_header': "📖 മലയാളം നിഘണ്ടു",
        'show_keyboard': False,
        'search_term': "",
        'header_counter': 0,
        'dark_mode': False,
        'show_add_word': False,
        'show_history': False,
        'show_favorites': False,
        'show_export': False,
        'show_contact': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Auto header blinking with JavaScript-like behavior
def update_header():
    if st.session_state.header_counter % 4 == 0: 
        if "മലയാളം" in st.session_state.current_header:
            st.session_state.current_header = "📖 Malayalam Dictionary"
        else:
            st.session_state.current_header = "📖 മലയാളം നിഘണ്ടു"
    st.session_state.header_counter += 1

# Helper functions
def add_to_history(word, direction):
    """Add search to history"""
    if word.strip():
        st.session_state.search_history = [
            item for item in st.session_state.search_history 
            if not (item['word'].lower() == word.lower() and item['direction'] == direction)
        ]
        
        st.session_state.search_history.insert(0, {
            'word': word,
            'direction': direction,
            'timestamp': datetime.now().isoformat()
        })
        
        st.session_state.search_history = st.session_state.search_history[:100]

def add_to_favorites(word, translation, direction):
    """Add to favorites"""
    favorite_item = {
        'word': word,
        'translation': translation,
        'direction': direction,
        'timestamp': datetime.now().isoformat()
    }
    
    existing = next((item for item in st.session_state.favorites if 
                     item['word'].lower() == word.lower() and 
                     item['translation'] == translation and 
                     item['direction'] == direction), None)
    
    if not existing:
        st.session_state.favorites.append(favorite_item)
        st.toast(f"✨ Added '{word}' to favorites!")
    else:
        st.toast(f"'{word}' is already in favorites!")

def remove_from_favorites(word, translation, direction):
    """Remove from favorites"""
    st.session_state.favorites = [
        item for item in st.session_state.favorites
        if not (item['word'].lower() == word.lower() and 
                item['translation'] == translation and
                item['direction'] == direction)
    ]
    st.toast(f"🗑️ Removed '{word}' from favorites!")

def search_dictionary(query, direction, enml_data, mlml_data):
    """Search dictionary based on direction with enhanced matching"""
    if not query.strip():
        return [], []
    
    query_lower = query.strip().lower()
    
    if direction == "English → മലയാളം":
        startswith_matches = enml_data[enml_data['from_content'].astype(str).str.lower().str.startswith(query_lower)]
        contains_matches = enml_data[enml_data['from_content'].astype(str).str.lower().str.contains(query_lower)]
        exact_matches = enml_data[enml_data['from_content'].astype(str).str.lower() == query_lower]
        
        all_matches = pd.concat([startswith_matches, contains_matches]).drop_duplicates()
        suggestions = all_matches['from_content'].unique()[:20]
        results = [(row['from_content'], row['to_content']) for _, row in exact_matches.iterrows()]
        
    elif direction == "മലയാളം → English":
        startswith_matches = enml_data[enml_data['to_content'].astype(str).str.lower().str.startswith(query_lower)]
        contains_matches = enml_data[enml_data['to_content'].astype(str).str.lower().str.contains(query_lower)]
        exact_matches = enml_data[enml_data['to_content'].astype(str).str.lower() == query_lower]
        
        all_matches = pd.concat([startswith_matches, contains_matches]).drop_duplicates()
        suggestions = all_matches['to_content'].unique()[:20]
        results = [(row['to_content'], row['from_content']) for _, row in exact_matches.iterrows()] 
        
    else:  # മലയാളം → മലയാളം
        startswith_matches = mlml_data[mlml_data['from_content'].astype(str).str.lower().str.startswith(query_lower)]
        contains_matches = mlml_data[mlml_data['from_content'].astype(str).str.lower().str.contains(query_lower)]
        exact_matches = mlml_data[mlml_data['from_content'].astype(str).str.lower() == query_lower]
        
        all_matches = pd.concat([startswith_matches, contains_matches]).drop_duplicates()
        suggestions = all_matches['from_content'].unique()[:20]
        results = [(row['from_content'], row['to_content']) for _, row in exact_matches.iterrows()]
    
    return list(suggestions), results

# Malayalam Keyboard Layout (omitted for brevity, assume definition is above)
malayalam_layout = [
    ['അ', 'ആ', 'ഇ', 'ഈ', 'ഉ', 'ഊ', 'ഋ', 'എ', 'ഏ', 'ഐ', 'ഒ', 'ഓ', 'ഔ'],
    ['ക', 'ഖ', 'ഗ', 'ഘ', 'ങ', 'ച', 'ഛ', 'ജ', 'ഝ', 'ഞ', 'ട', 'ഠ', 'ഡ'],
    ['ഢ', 'ണ', 'ത', 'ഥ', 'ദ', 'ധ', 'ന', 'പ', 'ഫ', 'ബ', 'ഭ', 'മ', 'യ'],
    ['ര', 'ല', 'വ', 'ശ', 'ഷ', 'സ', 'ഹ', 'ള', 'ഴ', 'റ', 'ന്‍', 'ര്‍', 'ല്‍'],
    ['ാ', 'ി', 'ീ', 'ു', 'ൂ', 'ൃ', 'െ', 'േ', 'ൈ', 'ൊ', 'ോ', 'ൌ', '്'],
    ['ം', 'ഃ', 'അം', 'അഃ', 'ള്‍']
]


def render_add_word_dialog(enml_data, mlml_data):
    """Render add word dialog"""
    st.markdown("### ➕ Add New Word")
    
    with st.form("add_word_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            from_word = st.text_input("From Word:", placeholder="Enter source word", key="add_from")
        
        with col2:
            to_word = st.text_input("To Word:", placeholder="Enter translation", key="add_to")
        
        direction = st.selectbox("Dictionary Type:", 
                                 ["English → മലയാളം", "മലയാളം → മലയാളം"], 
                                 key="add_direction")
        
        submitted = st.form_submit_button("💾 Save Word", type="primary")
        
        if submitted:
            if from_word.strip() and to_word.strip():
                st.success(f"✅ Successfully added: {from_word} → {to_word}")
                st.info("Note: In production, this would be saved to your Google Sheet")
            else:
                st.error("❌ Both fields are required!")

def render_history_section():
    """Render search history section (omitted for brevity)"""
    st.markdown("### 📜 Search History")
    
    if st.session_state.search_history:
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state.search_history = []
            st.success("Search history cleared!")
            st.rerun()
        
        st.markdown(f"**{len(st.session_state.search_history)} recent searches:**")
        
        for i, item in enumerate(st.session_state.search_history[:20]):
            timestamp = datetime.fromisoformat(item['timestamp']).strftime("%Y-%m-%d %H:%M")
            direction_emoji = {"English → മലയാളം": "🇬🇧→🇮🇳", "മലയാളം → English": "🇮🇳→🇬🇧", "മലയാളം → മലയാളം": "🇮🇳→🇮🇳"}
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                if st.button(f"🔍 {item['word']}", key=f"hist_{i}", help="Search this word again"):
                    st.session_state.search_term = item['word']
                    st.rerun()
            
            with col2:
                st.caption(f"{direction_emoji.get(item['direction'], '')} {timestamp}")
            
            with col3:
                if st.button("❌", key=f"del_hist_{i}", help="Remove from history"):
                    st.session_state.search_history.pop(i)
                    st.rerun()
    else:
        st.info("No search history yet. Start searching to build your history!")

def render_favorites_section():
    """Render favorites section (omitted for brevity)"""
    st.markdown("### ⭐ Favorites")
    
    if st.session_state.favorites:
        if st.button("🗑️ Clear All Favorites", type="secondary"):
            st.session_state.favorites = []
            st.success("All favorites cleared!")
            st.rerun()
        
        st.markdown(f"**{len(st.session_state.favorites)} bookmarked words:**")
        
        for i, item in enumerate(st.session_state.favorites):
            timestamp = datetime.fromisoformat(item['timestamp']).strftime("%Y-%m-%d")
            direction_emoji = {"English → മലയാളം": "🇬🇧→🇮🇳", "മലയാളം → English": "🇮🇳→🇬🇧", "മലയാളം → മലയാളം": "🇮🇳→🇮🇳"}
            
            col1, col2, col3 = st.columns([4, 2, 1])
            
            with col1:
                if st.button(f"⭐ {item['word']} → {item['translation']}", key=f"fav_{i}", help="Search this word"):
                    st.session_state.search_term = item['word']
                    st.rerun()
            
            with col2:
                st.caption(f"{direction_emoji.get(item['direction'], '')} {timestamp}")
            
            with col3:
                if st.button("❌", key=f"del_fav_{i}", help="Remove from favorites"):
                    remove_from_favorites(item['word'], item['translation'], item['direction'])
                    st.rerun()
    else:
        st.info("No favorites yet. Click ☆ next to any word to bookmark it!")

def render_export_section():
    """Render export section (omitted for brevity)"""
    st.markdown("### 📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.search_history:
            history_df = pd.DataFrame(st.session_state.search_history)
            csv_history = history_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download Search History (.csv)",
                data=csv_history,
                file_name=f"search_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.info("No search history to export")
    
    with col2:
        if st.session_state.favorites:
            favorites_df = pd.DataFrame(st.session_state.favorites)
            csv_favorites = favorites_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⭐ Download Favorites (.csv)",
                data=csv_favorites,
                file_name=f"favorites_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.info("No favorites to export")

def render_contact_section():
    """Render contact section (omitted for brevity)"""
    st.markdown("### 📬 Contact Information")
    
    st.markdown("""
    **Developer**: Yadu Krishna
    
    📧 **Email**: [yaduk883@gmail.com](mailto:yaduk883@gmail.com)
    
    🐙 **GitHub**: [github.com/yaduk883](https://github.com/yaduk883)
    
    📱 **Instagram**: [@ig.yadu](https://instagram.com/ig.yadu/)
    
    ---
    
    **About this Dictionary**:
    - Version: 2.0 (Streamlit Web App)
    - Original: Tkinter Desktop Application
    - Data Source: Google Sheets
    - Last Updated: October 2025
    """)

def main():
    # Load data
    try:
        enml_data, mlml_data = load_dictionary_data()
    except Exception as e:
        st.error(f"Failed to load dictionary data: {e}")
        st.stop()
    
    update_header()
    
    st.markdown(f'<div class="blinking-header">{st.session_state.current_header}</div>', 
                unsafe_allow_html=True)
    
    col_theme1, col_theme2, col_theme3 = st.columns([4, 1, 4])
    with col_theme2:
        if st.button("🌙" if not st.session_state.dark_mode else "☀️", 
                     help="Toggle dark/light mode", 
                     key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    # Feature buttons row (omitted for brevity)
    st.markdown("### 🎛️ Features")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("➕ Add Word", type="secondary", use_container_width=True):
            st.session_state.show_add_word = not st.session_state.show_add_word
            st.session_state.show_history = False
            st.session_state.show_favorites = False
            st.session_state.show_export = False
            st.session_state.show_contact = False
    
    with col2:
        if st.button("📜 History", type="secondary", use_container_width=True):
            st.session_state.show_history = not st.session_state.show_history
            st.session_state.show_add_word = False
            st.session_state.show_favorites = False
            st.session_state.show_export = False
            st.session_state.show_contact = False
    
    with col3:
        if st.button("⭐ Favorites", type="secondary", use_container_width=True):
            st.session_state.show_favorites = not st.session_state.show_favorites
            st.session_state.show_add_word = False
            st.session_state.show_history = False
            st.session_state.show_export = False
            st.session_state.show_contact = False
    
    with col4:
        if st.button("📤 Export", type="secondary", use_container_width=True):
            st.session_state.show_export = not st.session_state.show_export
            st.session_state.show_add_word = False
            st.session_state.show_history = False
            st.session_state.show_favorites = False
            st.session_state.show_contact = False
    
    with col5:
        if st.button("📬 Contact", type="secondary", use_container_width=True):
            st.session_state.show_contact = not st.session_state.show_contact
            st.session_state.show_add_word = False
            st.session_state.show_history = False
            st.session_state.show_favorites = False
            st.session_state.show_export = False
    
    # Render selected feature
    if st.session_state.show_add_word:
        render_add_word_dialog(enml_data, mlml_data)
    elif st.session_state.show_history:
        render_history_section()
    elif st.session_state.show_favorites:
        render_favorites_section()
    elif st.session_state.show_export:
        render_export_section()
    elif st.session_state.show_contact:
        render_contact_section()
    
    st.markdown("---")
    
    # Main search interface
    col_main1, col_main2 = st.columns([4, 1]) 
    
    with col_main1:
        st.markdown('<div class="malayalam-font">', unsafe_allow_html=True)
        st.markdown("### 🔍 തിരയുക (Search)")
        
        direction = st.radio(
            "Choose Translation Direction:",
            ["English → മലയാളം", "മലയാളം → English", "മലയാളം → മലയാളം"],
            horizontal=True,
            key="direction_radio",
            help="Select the direction for translation"
        )
        
        search_query = st.text_input(
            "Enter word to search:",
            value=st.session_state.search_term,
            placeholder="Type a word here... / ഇവിടെ ഒരു വാക്ക് ടൈപ്പ് ചെയ്യുക...",
            key="search_input",
            help="Start typing to see suggestions"
        )
        
        # Keyboard controls (omitted for brevity)
        col_kb1, col_kb2, col_kb3 = st.columns(3)
        with col_kb1:
            if st.button("🔤 Malayalam Keyboard", type="secondary", use_container_width=True):
                st.session_state.show_keyboard = not st.session_state.show_keyboard
        
        with col_kb2:
            if st.button("🔄 Clear Search", use_container_width=True):
                st.session_state.search_term = ""
                st.rerun()
        
        with col_kb3:
            if st.button("🔍 Search", type="primary", use_container_width=True):
                if search_query:
                    st.session_state.search_term = search_query
                    st.rerun()
        
        # Malayalam Keyboard (omitted for brevity)
        if st.session_state.show_keyboard:
            st.markdown('<div class="malayalam-keyboard">', unsafe_allow_html=True)
            st.markdown("#### 🔤 മലയാളം അക്ഷരങ്ങൾ (Malayalam Characters)")
            st.markdown("*Click characters to add them to search box*")
            
            for row_idx, row in enumerate(malayalam_layout):
                cols = st.columns(len([c for c in row if c.strip()]))
                col_idx = 0
                for char in row:
                    if char.strip():
                        if cols[col_idx].button(char, key=f"kbd_{row_idx}_{char}", help=f"Add {char}"):
                            st.session_state.search_input += char
                            st.session_state.search_term = st.session_state.search_input
                            st.rerun()
                        col_idx += 1
            
            st.markdown("---")
            col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)
            
            with col_ctrl1:
                if st.button("⌫ Backspace", key="backspace", use_container_width=True):
                    if st.session_state.search_input:
                        st.session_state.search_input = st.session_state.search_input[:-1]
                        st.session_state.search_term = st.session_state.search_input
                        st.rerun()
                
            with col_ctrl2:
                if st.button("🔄 Clear All", key="clear_all", use_container_width=True):
                    st.session_state.search_input = ""
                    st.session_state.search_term = ""
                    st.rerun()
            
            with col_ctrl3:
                st.info("Use Ctrl+V to paste")
            
            with col_ctrl4:
                if st.button("❌ Hide Keyboard", key="hide_keyboard", use_container_width=True):
                    st.session_state.show_keyboard = False
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.search_term and st.session_state.search_term != search_query:
            search_query = st.session_state.search_term
        
        # Perform Search
        if search_query:
            suggestions, results = search_dictionary(search_query, direction, enml_data, mlml_data)
            
            if results:
                add_to_history(search_query, direction)
            
            if suggestions and not results:
                st.markdown("### 💡 Suggestions")
                
                num_cols = min(len(suggestions[:12]), 4)
                suggestion_cols = st.columns(num_cols)
                
                for i, suggestion in enumerate(suggestions[:12]):
                    with suggestion_cols[i % num_cols]:
                        if st.button(suggestion, key=f"sugg_{i}", help=f"Search for {suggestion}"):
                            st.session_state.search_term = suggestion
                            st.rerun()
                
                st.info(f"🔍 No exact matches found for **'{search_query}'**. Try clicking on suggestions above.")
            
            # --- FINAL CONSOLIDATED RESULTS DISPLAY ---
            if results:
                primary_word = results[0][0] 
                
                # FIX: No extra space/gap here
                st.markdown(f"### 📖 Translation Results for **{primary_word}**") 
                
                st.markdown('<div class="search-result-card-container malayalam-font">', unsafe_allow_html=True)
                st.markdown(f'<h4 class="translation-header">{primary_word} ({direction})</h4>', unsafe_allow_html=True)

                st.success(f"🎯 Found **{len(results)}** match(es) for **'{search_query}'**")

                
                def is_word_favorite(word, translation, direction):
                    return any(fav['word'].lower() == word.lower() and 
                               fav['translation'] == translation and 
                               fav['direction'] == direction 
                               for fav in st.session_state.favorites)

                for i, (word, translation) in enumerate(results):
                    is_favorite = is_word_favorite(word, translation, direction)
                    
                    # FIX: Use a custom markdown structure for the row to control spacing
                    st.markdown(f"""
                        <div class="translation-item-row">
                            <div class="translation-text">→ {translation}</div>
                            
                            <button id="copy_btn_{i}" 
                                class="stButton st-emotion-cache-1jmveo5 translation-item-button" 
                                style="background: var(--secondary-color); color: white;" 
                                onclick="window.parent.document.querySelector('button[kind=copy_{i}]').click();">
                                📋
                            </button>
                            
                            <button id="fav_btn_{i}" 
                                class="stButton st-emotion-cache-1jmveo5 translation-item-button" 
                                style="background: {'#FFC107' if is_favorite else 'grey'}; color: white;" 
                                onclick="window.parent.document.querySelector('button[kind={'unfav' if is_favorite else 'fav'}_{i}]').click();">
                                {'★' if is_favorite else '☆'}
                            </button>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # --- Hidden Streamlit Buttons (Triggers) ---
                    # We use a custom 'kind' attribute to target these buttons from the JS above
                    # These must exist to trigger the Python session state updates.

                    # Hidden Copy Trigger Button
                    if st.button("", key=f"copy_{i}", kind=f"copy_{i}", help="Trigger copy", disabled=True):
                        copy_to_clipboard_js(translation)
                        
                    # Hidden Favorite Trigger Buttons
                    if is_favorite:
                        if st.button("", key=f"unfav_{i}", kind=f"unfav_{i}", help="Trigger unfavorite", disabled=True):
                            remove_from_favorites(word, translation, direction)
                            st.rerun()
                    else:
                        if st.button("", key=f"fav_{i}", kind=f"fav_{i}", help="Trigger favorite", disabled=True):
                            add_to_favorites(word, translation, direction)
                            st.rerun()


                st.markdown('</div>', unsafe_allow_html=True)
                # --- END FINAL RESULTS DISPLAY ---

    # Statistics Tab (Right Column)
    with col_main2:
        st.markdown("### 📊 Statistics")
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("📚 English-Malayalam", f"{len(enml_data):,}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("📖 Malayalam-Malayalam", f"{len(mlml_data):,}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("📜 Search History", f"{len(st.session_state.search_history)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("⭐ Favorites", f"{len(st.session_state.favorites)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    
    # Auto-refresh for header blinking
    time.sleep(0.1) 
    st.rerun()

if __name__ == "__main__":
    main()
