import streamlit as st
import json
import random
import os
from datetime import datetime

st.set_page_config(page_title="Secret Reddit Parser", page_icon="📖", layout="centered")

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 Настройки визуала")
accent_color = st.sidebar.color_picker("Акцентный цвет", "#7952B3") 
font_size = st.sidebar.slider("Размер текста историй", min_value=14, max_value=24, value=16)

custom_css = f"""
<style>
    /* Прячем стандартный мусор Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Стилизуем все кнопки на сайте */
    .stButton>button {{
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    .stButton>button:hover {{
        border-color: {accent_color} !important;
        color: {accent_color} !important;
        box-shadow: 0 0 12px {accent_color}40 !important;
    }}
    
    /* Главная кнопка (Download Script) */
    .stDownloadButton>button {{
        background-color: {accent_color}20 !important;
        border: 1px solid {accent_color} !important;
        color: white !important;
    }}
    .stDownloadButton>button:hover {{
        background-color: {accent_color}40 !important;
    }}
    
    /* Текст самой истории (применяем ползунок размера) */
    .streamlit-expanderContent p, .stTextArea textarea {{
        font-size: {font_size}px !important;
        line-height: 1.6 !important;
    }}
    
    /* Скругляем края у текстовых полей */
    .stTextArea textarea {{
        border-radius: 10px !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
# -----------------------------------------------

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect Password")
        return False
    else:
        return True

if not check_password():
    st.stop()

VIEWED_FILE = "viewed_ids.txt"
if not os.path.exists(VIEWED_FILE):
    open(VIEWED_FILE, 'w').close()

def get_viewed_ids():
    with open(VIEWED_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_viewed_id(post_id):
    with open(VIEWED_FILE, 'a') as f:
        f.write(f"{post_id}\n")

def clear_cart():
    st.session_state.approved_stories = []

if 'stories' not in st.session_state:
    st.session_state.stories = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'approved_stories' not in st.session_state:
    st.session_state.approved_stories = []

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Настройки парсера")

uploaded_file = st.sidebar.file_uploader("Загрузить дамп (.jsonl)", type=['jsonl'])

if uploaded_file is not None:
    col_min, col_max = st.sidebar.columns(2)
    with col_min:
        min_words = st.number_input("Мин. слов:", min_value=1, value=1, step=10)
    with col_max:
        max_words = st.number_input("Макс. слов:", min_value=1, value=1000, step=100)
        
    min_score = st.sidebar.number_input("Мин. апвоутов:", min_value=0, value=1, step=10)
    
    search_keyword = st.sidebar.text_input("Содержит слово (необязательно):", value="")

    if st.sidebar.button("🎲 Загрузить и перемешать", use_container_width=True):
        valid_stories = []
        viewed_ids = get_viewed_ids()
        
        with st.spinner('Чтение базы и пропуск просмотренных...'):
            for line in uploaded_file:
                try:
                    post = json.loads(line)
                    post_id = str(post.get('id', ''))
                    text = post.get('selftext', '')
                    
                    if not post_id or post_id in viewed_ids:
                        continue
                        
                    if not text or text == "[removed]" or text == "[deleted]":
                        continue
                        
                    words_count = len(text.split())
                    score = post.get('score', 0)
                    
                    if min_words <= words_count <= max_words and score >= min_score:
                        if search_keyword and search_keyword.lower() not in text.lower() and search_keyword.lower() not in post.get('title', '').lower():
                            continue

                        date_str = "Unknown Date"
                        created_utc = post.get('created_utc')
                        if created_utc:
                            try:
                                date_str = datetime.fromtimestamp(int(created_utc)).strftime('%Y-%m-%d')
                            except:
                                pass
                                
                        valid_stories.append({
                            'id': post_id,
                            'title': post.get('title', 'No Title'),
                            'text': text,
                            'draft': text, 
                            'words': words_count,
                            'score': score,
                            'date': date_str,
                            'url': post.get('url', 'No URL')
                        })
                except:
                    continue
        
        random.shuffle(valid_stories)
        st.session_state.stories = valid_stories
        st.session_state.current_index = 0
        st.sidebar.success(f"Найдено НОВЫХ историй: {len(valid_stories)}")
else:
    st.sidebar.info("Загрузи .jsonl файл, чтобы начать.")

if st.session_state.approved_stories:
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"🛒 Корзина: {len(st.session_state.approved_stories)} шт.")
    
    export_text = ""
    for s in st.session_state.approved_stories:
        export_text += f"Title: {s['title']}\nWords: {s['words']} | Upvotes: {s['score']} | Date: {s['date']}\nURL: {s['url']}\n"
        export_text += "-" * 50 + "\n" + s['text'] + "\n" + "=" * 50 + "\n\n"
        
    st.sidebar.download_button(
        label="📥 СКАЧАТЬ СКРИПТ (.txt)",
        data=export_text,
        file_name="approved_stories.txt",
        mime="text/plain",
        type="primary",
        on_click=clear_cart
    )

st.title("Parser for Reddit Stories")

if st.session_state.stories:
    if st.session_state.current_index < len(st.session_state.stories):
        current = st.session_state.stories[st.session_state.current_index]
        
        col_title, col_edit = st.columns([4, 1])
        with col_title:
            st.markdown(f"### {current['title']}")
        with col_edit:
            edit_mode = st.toggle("✏️ Редактор")
            
        st.caption(f"**Слов:** {current['words']} | **Апвоутов:** {current['score']} | **Дата:** {current['date']} | [Ссылка на пост]({current['url']})")
        
        if edit_mode:
            temp_draft = st.text_area("Режим редактирования (не забудь сохранить!):", value=current.get('draft', current['text']), height=400)
            
            col_save, col_revert = st.columns(2)
            with col_save:
                if st.button("💾 Сохранить правки", use_container_width=True):
                    current['draft'] = temp_draft
                    st.success("Сохранено!")
            with col_revert:
                if st.button("❌ Сбросить", use_container_width=True):
                    current['draft'] = current['text']
                    st.rerun()
        else:
            with st.expander("Читать историю", expanded=True):
                st.write(current.get('draft', current['text']))
            
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ БЕРУ (APPROVE)", use_container_width=True):
                save_viewed_id(current['id'])
                current['text'] = current.get('draft', current['text']) 
                st.session_state.approved_stories.append(current)
                st.session_state.current_index += 1
                st.rerun()
        with col2:
            if st.button("🗑️ В МУСОРКУ (SKIP)", use_container_width=True):
                save_viewed_id(current['id'])
                st.session_state.current_index += 1
                st.rerun()
                
        progress = st.session_state.current_index / len(st.session_state.stories)
        st.progress(progress, text=f"Просмотрено {st.session_state.current_index} из {len(st.session_state.stories)}")
        
    else:
        st.info("Истории в этом дампе закончились! Загрузи заново и перемешай, или выбери другой дамп.")
else:
    st.write("Загрузи файл слева и нажми 'Загрузить и перемешать'.")
