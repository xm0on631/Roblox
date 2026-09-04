import streamlit as st
import json
import random
import os
from datetime import datetime

st.set_page_config(page_title="Parser for Reddit Stories", layout="centered")

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

st.sidebar.header("Parser Settings")

uploaded_file = st.sidebar.file_uploader("Upload Dump (.jsonl)", type=['jsonl'])

if uploaded_file is not None:
    col_min, col_max = st.sidebar.columns(2)
    with col_min:
        min_words = st.number_input("Min Words:", min_value=1, value=1, step=10)
    with col_max:
        max_words = st.number_input("Max Words:", min_value=1, value=1000, step=100)
        
    min_score = st.sidebar.number_input("Min Upvotes:", min_value=0, value=1, step=10)
    
    search_keyword = st.sidebar.text_input("Contains Word (optional):", value="")

    if st.sidebar.button("Load and Shuffle", use_container_width=True):
        valid_stories = []
        viewed_ids = get_viewed_ids()
        
        with st.spinner('Reading database & skipping viewed posts...'):
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
        st.sidebar.success(f"Found NEW stories: {len(valid_stories)}")
else:
    st.sidebar.info("Please upload a .jsonl dump file to start.")

if st.session_state.approved_stories:
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Cart: {len(st.session_state.approved_stories)} items")
    
    export_text = ""
    for s in st.session_state.approved_stories:
        export_text += f"Title: {s['title']}\nWords: {s['words']} | Upvotes: {s['score']} | Date: {s['date']}\nURL: {s['url']}\n"
        export_text += "-" * 50 + "\n" + s['text'] + "\n" + "=" * 50 + "\n\n"
        
    st.sidebar.download_button(
        label="DOWNLOAD SCRIPT (.txt)",
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
            edit_mode = st.toggle("✏️ Edit Text")
            
        st.caption(f"**Words:** {current['words']} | **Upvotes:** {current['score']} | **Date:** {current['date']} | [Post Link]({current['url']})")
        
        if edit_mode:
            temp_draft = st.text_area("Edit mode active (save your changes below!):", value=current.get('draft', current['text']), height=400)
            
            col_save, col_revert = st.columns(2)
            with col_save:
                if st.button("💾 Save Edits to Draft", use_container_width=True):
                    current['draft'] = temp_draft
                    st.success("Draft saved!")
            with col_revert:
                if st.button("❌ Revert to Original", use_container_width=True):
                    current['draft'] = current['text']
                    st.rerun()
        else:
            with st.expander("Read Text", expanded=True):
                st.write(current.get('draft', current['text']))
            
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("APPROVE", use_container_width=True):
                save_viewed_id(current['id'])
                current['text'] = current.get('draft', current['text']) 
                st.session_state.approved_stories.append(current)
                st.session_state.current_index += 1
                st.rerun()
        with col2:
            if st.button("SKIP", use_container_width=True):
                save_viewed_id(current['id'])
                st.session_state.current_index += 1
                st.rerun()
                
        progress = st.session_state.current_index / len(st.session_state.stories)
        st.progress(progress, text=f"Reviewed {st.session_state.current_index} out of {len(st.session_state.stories)}")
        
    else:
        st.info("You've viewed all stories in this batch! Load and shuffle again or pick a new dump.")
else:
    st.write("Upload a .jsonl dump file from the left menu and click 'Load and Shuffle' to start.")
