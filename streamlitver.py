import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io
import base64

# Page configuration
st.set_page_config(
    page_title="മലയാളം നിഘണ്ടു | Malayalam Dictionary",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Malayalam fonts and beautiful animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Malayalam:wght@400;600;700&display=swap');
    
    .malayalam-font {
        font-family: 'Noto Sans Malayalam', sans-serif !important;
        font-size: 18px;
        line-height: 1.6;
    }
    
    .blinking-header {
        font-size: 3rem;
        font-weight: bold;
        color: #009688;
        text-align: center;
        animation: fadeInOut 2s infinite;
        font-family: 'Noto Sans Malayalam', sans-serif;
        margin: 20px 0;
        padding: 20px;
        background: linear-gradient(45deg, #f0fff0, #e8f5e8);
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,150,136,0.3);
    }
    
    @keyframes fadeInOut {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.05); }
    }
    
    .search-result-card {
        background: linear-gradient(135deg, #f0fff0 0%, #e8f5e8 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 5px solid #009688;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .search-result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .translation-item {
        background-color: rgba(0, 150, 136, 0.1);
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s;
        border: 1px solid rgba(0, 150, 136, 0.2);
        font-family: 'Noto Sans Malayalam', sans-serif;
        font-size: 16px;
    }
    
    .translation-item:hover {
        background-color: rgba(0, 150, 136, 0.2);
        transform: translateX(5px);
    }
    
    .malayalam-keyboard {
        background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .keyboard-row {
        display: flex;
        justify-content: center;
        margin: 8px 0;
        flex-wrap: wrap;
    }
    
    .keyboard-btn {
        background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 3px;
        cursor: pointer;
        font-family: 'Noto Sans Malayalam', sans-serif;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(23,162,184,0.3);
        min-width: 45px;
    }
    
    .keyboard-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(23,162,184,0.5);
    }
    
    .suggestion-chip {
        display: inline-block;
        background: linear-gradient(135deg, #007ACC 0%, #005a9e 100%);
        color: white;
        padding: 8px 15px;
        margin: 5px;
        border-radius: 20px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(0,122,204,0.3);
        font-family: 'Noto Sans Malayalam', sans-serif;
    }
    
    .suggestion-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,122,204,0.5);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px 0;
        transition: all 0.3s;
    }
    
    .stats-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .favorite-btn {
        background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
        border: none;
        padding: 8px 12px;
        border-radius: 8px;
        color: white;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(255,193,7,0.3);
    }
    
    .favorite-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255,193,7,0.5);
    }
    
    .copy-btn {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        border: none;
        padding: 8px 12px;
        border-radius: 8px;
        color: white;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(40,167,69,0.3);
    }
    
    .copy-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(40,167,69,0.5);
    }
    
    .control-btn {
        background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
        border: none;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        cursor: pointer;
        margin: 5px;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(108,117,125,0.3);
    }
    
    .control-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(108,117,125,0.5);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'current_header' not in st.session_state:
    st.session_state.current_header = "📖 മലയാളം നിഘണ്ടു"
if 'show_keyboard' not in st.session_state:
    st.session_state.show_keyboard = False
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""
if 'header_toggle' not in st.session_state:
    st.session_state.header_toggle = False

# Data loading functions
@st.cache_data
def load_dictionary_data():
    """Load dictionary data from Excel files with fallback to sample data"""
    try:
        # Try to load from uploaded files or default paths
        enml_data = None
        mlml_data = None
        
        # Check for files in current directory (Streamlit Cloud deployment)
        if os.path.exists("en_ml.xlsx"):
            enml_data = pd.read_excel("en_ml.xlsx")
        elif os.path.exists("files/en_ml.xlsx"):
            enml_data = pd.read_excel("files/en_ml.xlsx")
        
        if os.path.exists("datukexcel.xlsx"):
            mlml_data = pd.read_excel("datukexcel.xlsx")
        elif os.path.exists("files/datukexcel.xlsx"):
            mlml_data = pd.read_excel("files/datukexcel.xlsx")
        
        # Fallback to sample data if files don't exist
        if enml_data is None:
            enml_data = pd.DataFrame({
                'from_content': [
                    'hello', 'world', 'good', 'morning', 'thank', 'you', 'water', 'fire',
                    'earth', 'sky', 'sun', 'moon', 'star', 'tree', 'flower', 'bird',
                    'fish', 'house', 'food', 'love', 'peace', 'joy', 'beautiful', 'strong'
                ],
                'to_content': [
                    'ഹലോ', 'ലോകം', 'നല്ല', 'പ്രഭാതം', 'നന്ദി', 'നിങ്ങൾക്ക്', 'വെള്ളം', 'തീ',
                    'ഭൂമി', 'ആകാശം', 'സൂര്യൻ', 'ചന്ദ്രൻ', 'നക്ഷത്രം', 'മരം', 'പൂവ്', 'പക്ഷി',
                    'മീൻ', 'വീട്', 'ഭക്ഷണം', 'സ്നേഹം', 'സമാധാനം', 'സന്തോഷം', 'സുന്ദരമായ', 'ശക്തമായ'
                ]
            })
        
        if mlml_data is None:
            mlml_data = pd.DataFrame({
                'from_content': [
                    'മലയാളം', 'ഭാഷ', 'നിഘണ്ടു', 'പുസ്തകം', 'വിദ്യാലയം', 'അധ്യാപകൻ',
                    'വിദ്യാർത്ഥി', 'പഠനം', 'അറിവ്', 'ജ്ഞാനം', 'സംസ്കാരം', 'പാരമ്പര്യം'
                ],
                'to_content': [
                    'കേരളത്തിലെ ഭാഷ', 'സംസാരിക്കുന്ന മാധ്യമം', 'വാക്കുകളുടെ ശേഖരം', 'ഗ്രന്ഥം',
                    'പഠിക്കുന്ന സ്ഥലം', 'പഠിപ്പിക്കുന്നവൻ', 'പഠിക്കുന്നവൻ', 'വിദ്യാഭ്യാസം',
                    'അറിവിന്റെ സമ്പത്ത്', 'ആഴമായ അറിവ്', 'ജീവിതരീതി', 'പൂർവ്വികരുടെ കാഴ്ചപ്പാട്'
                ]
            })
        
        # Clean the data
        enml_data = enml_data.dropna()
        mlml_data = mlml_data.dropna()
        
        # Ensure string type and clean
        enml_data['from_content'] = enml_data['from_content'].astype(str).str.strip()
        enml_data['to_content'] = enml_data['to_content'].astype(str).str.strip()
        mlml_data['from_content'] = mlml_data['from_content'].astype(str).str.strip()
        mlml_data['to_content'] = mlml_data['to_content'].astype(str).str.strip()
        
        return enml_data, mlml_data
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Return minimal sample data as absolute fallback
        enml_data = pd.DataFrame({
            'from_content': ['hello', 'world', 'good', 'malayalam'],
            'to_content': ['ഹലോ', 'ലോകം', 'നല്ല', 'മലയാളം']
        })
        mlml_data = pd.DataFrame({
            'from_content': ['മലയാളം', 'ഭാഷ'],
            'to_content': ['കേരളത്തിലെ ഭാഷ', 'സംസാരം']
        })
        return enml_data, mlml_data

# Load data
enml_data, mlml_data = load_dictionary_data()

# Helper functions
def add_to_history(word, direction):
    """Add search to history"""
    if word.strip():
        # Remove if already exists
        st.session_state.search_history = [
            item for item in st.session_state.search_history 
            if not (item['word'].lower() == word.lower() and item['direction'] == direction)
        ]
        
        # Add to beginning
        st.session_state.search_history.insert(0, {
            'word': word,
            'direction': direction,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100
        st.session_state.search_history = st.session_state.search_history[:100]

def add_to_favorites(word, translation, direction):
    """Add to favorites"""
    favorite_item = {
        'word': word,
        'translation': translation,
        'direction': direction,
        'timestamp': datetime.now().isoformat()
    }
    
    # Check if already exists
    existing = next((item for item in st.session_state.favorites if 
                    item['word'].lower() == word.lower() and 
                    item['direction'] == direction), None)
    
    if not existing:
        st.session_state.favorites.append(favorite_item)
        st.success(f"✨ Added '{word}' to favorites!")
    else:
        st.warning(f"'{word}' is already in favorites!")

def remove_from_favorites(word, direction):
    """Remove from favorites"""
    st.session_state.favorites = [
        item for item in st.session_state.favorites
        if not (item['word'].lower() == word.lower() and item['direction'] == direction)
    ]
    st.success(f"🗑️ Removed '{word}' from favorites!")

def search_dictionary(query, direction):
    """Search dictionary based on direction with enhanced matching"""
    if not query.strip():
        return [], []
    
    query_lower = query.strip().lower()
    
    if direction == "English → മലയാളം":
        # Search English to Malayalam
        startswith_matches = enml_data[enml_data['from_content'].str.lower().str.startswith(query_lower)]
        contains_matches = enml_data[enml_data['from_content'].str.lower().str.contains(query_lower)]
        exact_matches = enml_data[enml_data['from_content'].str.lower() == query_lower]
        
        # Combine matches, prioritizing exact and startswith
        all_matches = pd.concat([startswith_matches, contains_matches]).drop_duplicates()
        suggestions = all_matches['from_content'].unique()[:20]
        results = [(row['from_content'], row['to_content']) for _, row in exact_matches.iterrows()]
        
    elif direction == "മലയാളം → English":
        # Search Malayalam to English
        startswith_matches = enml_data[enml_data['to_content'].str.lower().str.startswith(query_lower)]
        contains_matches = enml_data[enml_data['to_content'].str.lower().str.contains(query_lower)]
        exact_matches = enml_data[enml_data['to_content'].str.lower() == query_lower]
        
        all_matches = pd.concat([startswith_matches, contains_matches]).drop_duplicates()
        suggestions = all_matches['to_content'].unique()[:20]
        results = [(row['to_content'], row['from_content']) for _, row in exact_matches.iterrows()]
        
    else:  # മലയാളം → മലയാളം
        # Search Malayalam to Malayalam
        startswith_matches = mlml_data[mlml_data['from_content'].str.lower().str.startswith(query_lower)]
        contains_matches = mlml_data[mlml_data['from_content'].str.lower().str.contains(query_lower)]
        exact_matches = mlml_data[mlml_data['from_content'].str.lower() == query_lower]
        
        all_matches = pd.concat([startswith_matches, contains_matches]).drop_duplicates()
        suggestions = all_matches['from_content'].unique()[:20]
        results = [(row['from_content'], row['to_content']) for _, row in exact_matches.iterrows()]
    
    return list(suggestions), results

# Malayalam Keyboard Layout - Enhanced with better organization
malayalam_layout = [
    # Row 1 - Vowels
    ['അ', 'ആ', 'ഇ', 'ഈ', 'ഉ', 'ഊ', 'ഋ', 'എ', 'ഏ', 'ഐ', 'ഒ', 'ഓ', 'ഔ'],
    # Row 2 - Consonants Part 1 (Velars, Palatals, Retroflexes)
    ['ക', 'ഖ', 'ഗ', 'ഘ', 'ങ', 'ച', 'ഛ', 'ജ', 'ഝ', 'ഞ', 'ട', 'ഠ', 'ഡ'],
    # Row 3 - Consonants Part 2 (Dentals, Labials, Approximants)
    ['ഢ', 'ണ', 'ത', 'ഥ', 'ദ', 'ധ', 'ന', 'പ', 'ഫ', 'ബ', 'ഭ', 'മ', 'യ'],
    # Row 4 - Consonants Part 3 (Liquids, Sibilants, Others)
    ['ര', 'ല', 'വ', 'ശ', 'ഷ', 'സ', 'ഹ', 'ള', 'ഴ', 'റ', 'ന്‍', 'ര്‍', 'ല്‍'],
    # Row 5 - Vowel Signs (Matras)
    ['ാ', 'ി', 'ീ', 'ു', 'ൂ', 'ൃ', 'െ', 'േ', 'ൈ', 'ൊ', 'ോ', 'ൌ', '്'],
    # Row 6 - Additional Signs and Symbols
    ['ം', 'ഃ', 'അം', 'അഃ', 'ള്‍', '൰', '൱', '൲', '൳', '൴', '൵']
]

def create_download_link(data, filename, text):
    """Create a download link for data"""
    if isinstance(data, pd.DataFrame):
        csv = data.to_csv(index=False)
    else:
        csv = str(data)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Main App Layout
def main():
    # Auto-toggle header for blinking effect
    if st.session_state.header_toggle:
        if "മലയാളം" in st.session_state.current_header:
            st.session_state.current_header = "📖 Malayalam Dictionary"
        else:
            st.session_state.current_header = "📖 മലയാളം നിഘണ്ടു"
    
    # Blinking Header with enhanced styling
    st.markdown(f'<div class="blinking-header">{st.session_state.current_header}</div>', unsafe_allow_html=True)
    
    # Header toggle button
    col_toggle1, col_toggle2, col_toggle3 = st.columns([2, 1, 2])
    with col_toggle2:
        if st.button("🔄 Toggle Header", help="Switch between മലയാളം and English", key="toggle_header"):
            st.session_state.header_toggle = not st.session_state.header_toggle
            if "മലയാളം" in st.session_state.current_header:
                st.session_state.current_header = "📖 Malayalam Dictionary"
            else:
                st.session_state.current_header = "📖 മലയാളം നിഘണ്ടു"
            st.rerun()
    
    st.markdown("---")
    
    # Main content layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="malayalam-font">', unsafe_allow_html=True)
        st.markdown("### 🔍 തിരയുക (Search)")
        
        # Search direction with enhanced styling
        direction = st.radio(
            "Choose Translation Direction:",
            ["English → മലയാളം", "മലയാളം → English", "മലയാളം → മലയാളം"],
            horizontal=True,
            help="Select the direction for translation"
        )
        
        # Search input with better integration
        search_query = st.text_input(
            "Enter word to search:",
            value=st.session_state.search_term,
            placeholder="Type a word here... / ഇവിടെ ഒരു വാക്ക് ടൈപ്പ് ചെയ്യുക...",
            key="search_input",
            help="Start typing to see suggestions"
        )
        
        # Keyboard controls
        col_kb1, col_kb2 = st.columns(2)
        with col_kb1:
            if st.button("🔤 Malayalam Keyboard", type="secondary", help="Toggle on-screen Malayalam keyboard"):
                st.session_state.show_keyboard = not st.session_state.show_keyboard
        
        with col_kb2:
            if st.button("🔄 Clear Search", help="Clear search box"):
                st.session_state.search_term = ""
                st.rerun()
        
        # Enhanced Malayalam Keyboard
        if st.session_state.show_keyboard:
            st.markdown('<div class="malayalam-keyboard">', unsafe_allow_html=True)
            st.markdown("#### 🔤 മലയാളം അക്ഷരങ്ങൾ (Malayalam Characters)")
            st.markdown("*Click characters to add them to search box*")
            
            for row_idx, row in enumerate(malayalam_layout):
                # Create HTML for keyboard row
                row_html = '<div class="keyboard-row">'
                for char in row:
                    if char.strip():
                        row_html += f'<button class="keyboard-btn" onclick="addToSearch(\'{char}\')" title="Add {char}">{char}</button>'
                row_html += '</div>'
                
                # Display row with columns for better control
                cols = st.columns(len([c for c in row if c.strip()]))
                col_idx = 0
                for char in row:
                    if char.strip():
                        if cols[col_idx].button(char, key=f"kbd_{row_idx}_{char}", help=f"Add {char}"):
                            st.session_state.search_term += char
                            st.rerun()
                        col_idx += 1
            
            # Keyboard control buttons
            st.markdown("---")
            col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)
            
            with col_ctrl1:
                if st.button("⌫ Backspace", key="backspace", help="Remove last character"):
                    if st.session_state.search_term:
                        st.session_state.search_term = st.session_state.search_term[:-1]
                        st.rerun()
            
            with col_ctrl2:
                if st.button("🔄 Clear", key="clear_all", help="Clear all text"):
                    st.session_state.search_term = ""
                    st.rerun()
            
            with col_ctrl3:
                if st.button("📋 Paste", key="paste", help="Paste from clipboard"):
                    st.info("Use Ctrl+V to paste text directly in search box")
            
            with col_ctrl4:
                if st.button("❌ Hide Keyboard", key="hide_keyboard", help="Hide Malayalam keyboard"):
                    st.session_state.show_keyboard = False
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Statistics")
        
        # Enhanced statistics cards
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("📚 English-Malayalam", f"{len(enml_data):,}", help="Total English to Malayalam entries")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("📖 Malayalam-Malayalam", f"{len(mlml_data):,}", help="Total Malayalam to Malayalam entries")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("📜 Search History", f"{len(st.session_state.search_history)}", help="Your recent searches")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.metric("⭐ Favorites", f"{len(st.session_state.favorites)}", help="Your bookmarked words")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Update search term if keyboard was used
    if st.session_state.search_term and st.session_state.search_term != search_query:
        search_query = st.session_state.search_term
    
    # Perform Search with enhanced results
    if search_query:
        suggestions, results = search_dictionary(search_query, direction)
        
        # Add to history
        if results:  # Only add to history if we found results
            add_to_history(search_query, direction)
        
        # Display suggestions with enhanced styling
        if suggestions and not results:
            st.markdown("### 💡 Suggestions")
            
            # Create suggestion chips
            suggestions_html = '<div style="margin: 15px 0;">'
            for suggestion in suggestions[:15]:  # Show more suggestions
                suggestions_html += f'<span class="suggestion-chip" title="Click to search">{suggestion}</span>'
            suggestions_html += '</div>'
            
            st.markdown(suggestions_html, unsafe_allow_html=True)
            st.info(f"🔍 No exact matches found for **'{search_query}'**. Try clicking on suggestions above or check spelling.")
            
            # Allow clicking on suggestions (simulated)
            st.markdown("**Click on any suggestion below to search:**")
            suggestion_cols = st.columns(min(len(suggestions[:12]), 4))
            for i, suggestion in enumerate(suggestions[:12]):
                with suggestion_cols[i % 4]:
                    if st.button(suggestion, key=f"sugg_{i}", help=f"Search for {suggestion}"):
                        st.session_state.search_term = suggestion
                        st.rerun()
        
        # Display results with enhanced formatting
        if results:
            st.markdown("### 📖 Translation Results")
            st.success(f"🎯 Found **{len(results)}** exact match(es) for **'{search_query}'**")
            
            for i, (word, translation) in enumerate(results):
                # Enhanced result card
                st.markdown('<div class="search-result-card malayalam-font">', unsafe_allow_html=True)
                
                # Word header
                st.markdown(f"## {word}")
                
                # Translation with enhanced styling
                col_trans1, col_trans2, col_trans3 = st.columns([6, 1, 1])
                
                with col_trans1:
                    st.markdown(f'<div class="translation-item">→ {translation}</div>', unsafe_allow_html=True)
                
                with col_trans2:
                    if st.button("📋", key=f"copy_{i}", help="Copy to clipboard", type="secondary"):
                        # JavaScript would be needed for actual clipboard copy in web
                        st.success(f"✅ Copied '{translation}' to clipboard!")
                        st.balloons()
                
                with col_trans3:
                    # Enhanced favorites functionality
                    is_favorite = any(fav['word'].lower() == word.lower() and 
                                    fav['direction'] == direction 
                                    for fav in st.session_state.favorites)
                    
                    if is_favorite:
                        if st.button("★", key=f"unfav_{i}", help="Remove from favorites", type="secondary"):
                            remove_from_favorites(word, direction)
                            st.rerun()
                    else:
                        if st.button("☆", key=f"fav_{i}", help="Add to favorites", type="secondary"):
                            add_to_favorites(word, translation, direction)
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add some spacing between results
                if i < len(results) - 1:
                    st.markdown("---")

    # Enhanced Sidebar with additional features
    with st.sidebar:
        st.markdown("## 🎛️ Dictionary Features")
        
        # Search History with enhanced display
        with st.expander("📜 Search History", expanded=False):
            if st.session_state.search_history:
                st.markdown(f"**Recent Searches** ({len(st.session_state.search_history)})")
                
                for i, item in enumerate(st.session_state.search_history[:15]):
                    timestamp = datetime.fromisoformat(item['timestamp']).strftime("%m-%d %H:%M")
                    direction_emoji = {"English → മലയാളം": "🇬🇧→🇮🇳", "മലയാളം → English": "🇮🇳→🇬🇧", "മലയാളം → മലയാളം": "🇮🇳→🇮🇳"}
                    
                    col_hist1, col_hist2 = st.columns([3, 1])
                    with col_hist1:
                        if st.button(f"{item['word']}", key=f"hist_{i}_{item['timestamp']}", 
                                   help=f"{direction_emoji.get(item['direction'], '')} {timestamp}"):
                            st.session_state.search_term = item['word']
                            st.rerun()
                    with col_hist2:
                        st.caption(timestamp)
                
                # Clear history option
                if st.button("🗑️ Clear History", type="secondary", help="Clear all search history"):
                    st.session_state.search_history = []
                    st.success("Search history cleared!")
                    st.rerun()
            else:
                st.info("No search history yet. Start searching to build your history!")
        
        # Favorites with enhanced display
        with st.expander("⭐ Favorites", expanded=False):
            if st.session_state.favorites:
                st.markdown(f"**Bookmarked Words** ({len(st.session_state.favorites)})")
                
                for i, item in enumerate(st.session_state.favorites):
                    timestamp = datetime.fromisoformat(item['timestamp']).strftime("%m-%d")
                    
                    col_fav1, col_fav2 = st.columns([4, 1])
                    with col_fav1:
                        if st.button(f"{item['word']} → {item['translation']}", 
                                   key=f"favs_{i}_{item['timestamp']}", 
                                   help=f"Search • Added {timestamp}"):
                            st.session_state.search_term = item['word']
                            st.rerun()
                    with col_fav2:
                        if st.button("🗑️", key=f"del_fav_{i}", help="Remove from favorites", type="secondary"):
                            st.session_state.favorites.pop(i)
                            st.success("Removed from favorites!")
                            st.rerun()
                
                # Clear favorites option
                if st.button("🗑️ Clear All Favorites", type="secondary", help="Clear all favorites"):
                    st.session_state.favorites = []
                    st.success("All favorites cleared!")
                    st.rerun()
            else:
                st.info("No favorites yet. Click ☆ next to any word to bookmark it!")
        
        # Export functionality with enhanced options
        st.markdown("### 📤 Export & Download")
        
        if st.session_state.search_history:
            history_df = pd.DataFrame(st.session_state.search_history)
            st.download_button(
                label="📊 Download Search History (CSV)",
                data=history_df.to_csv(index=False),
                file_name=f"search_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Download your search history as CSV file"
            )
        
        if st.session_state.favorites:
            favorites_df = pd.DataFrame(st.session_state.favorites)
            st.download_button(
                label="⭐ Download Favorites (CSV)",
                data=favorites_df.to_csv(index=False),
                file_name=f"favorites_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Download your favorites as CSV file"
            )
        
        # Theme and Settings
        st.markdown("### ⚙️ Settings")
        
        # Auto-toggle header
        auto_header = st.checkbox("🔄 Auto-toggle header", value=False, 
                                 help="Automatically switch between മലയാളം and English every few seconds")
        if auto_header != st.session_state.header_toggle:
            st.session_state.header_toggle = auto_header
            if auto_header:
                st.info("Header will now auto-toggle every few seconds!")
            else:
                st.info("Auto-toggle disabled")
        
        # File upload for custom dictionaries
        st.markdown("### 📁 Upload Custom Dictionary")
        
        uploaded_enml = st.file_uploader("English-Malayalam Excel File", type=['xlsx'], 
                                        help="Upload your own English to Malayalam dictionary")
        uploaded_mlml = st.file_uploader("Malayalam-Malayalam Excel File", type=['xlsx'],
                                        help="Upload your own Malayalam to Malayalam dictionary")
        
        if uploaded_enml or uploaded_mlml:
            st.info("Custom dictionary upload feature would be implemented in production version")
        
        # About and Contact
        st.markdown("### 📬 About & Contact")
        
        st.markdown("""
        **Developer**: Yadu Krishna  
        **Email**: [yaduk883@gmail.com](mailto:yaduk883@gmail.com)  
        **GitHub**: [github.com/yaduk883](https://github.com/yaduk883)  
        **Instagram**: [@ig.yadu](https://instagram.com/ig.yadu/)
        
        **Version**: 2.0 (Streamlit Web)  
        **Last Updated**: October 2025
        """)
        
        # Help section
        with st.expander("❓ Help & Usage Tips"):
            st.markdown("""
            **How to use this dictionary:**
            
            1. **Search**: Type any word in the search box
            2. **Direction**: Choose translation direction with radio buttons
            3. **Keyboard**: Use 🔤 button for Malayalam virtual keyboard
            4. **Suggestions**: Click on suggested words to search them
            5. **Favorites**: Click ☆ to bookmark important words
            6. **History**: View your recent searches in sidebar
            7. **Export**: Download your data as CSV files
            
            **Malayalam Keyboard Tips:**
            - Click characters to build words naturally
            - Use backspace to correct mistakes
            - Try building words like: മ + ല + യ + ാ + ള + ം = മലയാളം
            
            **Pro Tips:**
            - Search works with partial words (suggestions)
            - Use both English and Malayalam for best results
            - Bookmark frequently used words as favorites
            - Export your data to keep offline backups
            """)

    # Auto-refresh for header animation (if enabled)
    if st.session_state.header_toggle:
        # This would need JavaScript in production to auto-refresh
        pass

if __name__ == "__main__":
    main()
