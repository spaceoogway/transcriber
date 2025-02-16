import re
import os
import streamlit as st
import openai
from youtube_transcript_api import YouTubeTranscriptApi

# ----- Utility Functions -----

def extract_video_id(url):
    """
    Extract the 11-character video ID from a YouTube URL.
    Supports standard and shortened URLs.
    """
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    """
    Retrieves the transcript for a given video ID and combines it into a single text block.
    """
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry["text"] for entry in transcript])

def correct_text_gpt(text):
    """
    Uses OpenAI's GPT-3.5-turbo API to correct punctuation, grammar, and clarity.
    Ensure that your OPENAI_API_KEY is set.
    """
    if not os.getenv("OPENAI_API_KEY") and "OPENAI_API_KEY" not in st.secrets:
        st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or in Streamlit secrets.")
        return text

    try:
        prompt = (
            "Please correct the following text for grammar, punctuation, clarity, and style:\n\n"
            f"{text}\n\nCorrected text:"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1024,
        )
        corrected = response.choices[0].message['content'].strip()
        return corrected
    except Exception as e:
        st.error(f"Error during text correction: {e}")
        return text

def translate_text(text, target_lang_code):
    """
    Uses Google Cloud Translation API to translate the text.
    Make sure you have set up your Google Cloud credentials.
    """
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        result = client.translate(text, target_language=target_lang_code)
        return result["translatedText"]
    except Exception as e:
        st.error(f"Error during translation: {e}")
        return text

def apply_custom_css(font_family, theme):
    """
    Inject custom CSS to set the app's font and theme.
    """
    # Set background and text colors based on the selected theme.
    if theme == "Light Mode":
        bg_color = "#ffffff"
        text_color = "#000000"
    elif theme == "Dark Mode":
        bg_color = "#121212"
        text_color = "#ffffff"
    elif theme == "Book Mode":
        bg_color = "#fdf6e3"  # light paper-like color
        text_color = "#333333"
    else:
        bg_color = "#ffffff"
        text_color = "#000000"

    css = f"""
    <style>
    /* Page background and text styling */
    .reportview-container, .main .block-container {{
        background-color: {bg_color};
        color: {text_color};
        font-family: '{font_family}', sans-serif;
    }}
    .sidebar .sidebar-content {{
        background-color: {bg_color};
        color: {text_color};
        font-family: '{font_family}', sans-serif;
    }}
    /* Styling for input widgets */
    input, textarea, .stTextInput>div>div>input {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ----- Main App -----

def main():
    st.title("YouTube Subtitle Enhancer & Translator")
    st.write(
        """
        Enter a YouTube URL to fetch its subtitles. The app will use OpenAI's GPT-3.5-turbo to correct the text for grammar and punctuation,
        then translate it into your chosen language using Google Cloud Translation.
        """
    )

    # Sidebar: Customization Options
    st.sidebar.header("Customization Options")

    # Font selection (feel free to add more fonts)
    font_option = st.sidebar.selectbox(
        "Choose a font",
        ["Roboto", "Open Sans", "Lato", "Merriweather", "Georgia"]
    )

    # Theme selection
    theme_option = st.sidebar.selectbox(
        "Choose a Theme",
        ["Light Mode", "Dark Mode", "Book Mode"]
    )

    # Target language selection, including Turkish
    target_language = st.sidebar.selectbox(
        "Select target language",
        ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Turkish"]
    )
    lang_map = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Turkish": "tr"
    }

    # Apply custom styling.
    apply_custom_css(font_option, theme_option)

    # Main input: YouTube URL
    url = st.text_input("Enter YouTube Video URL")

    if st.button("Process"):
        if not url:
            st.error("Please enter a YouTube URL.")
            return

        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL. Please check and try again.")
            return

        # Fetch transcript
        try:
            original_text = get_transcript(video_id)
        except Exception as e:
            st.error(f"Error fetching subtitles: {e}")
            return

        st.subheader("Original Transcript")
        st.write(original_text)

        # Correct the text using GPT
        with st.spinner("Correcting text..."):
            corrected_text = correct_text_gpt(original_text)
        st.subheader("Corrected Transcript")
        st.write(corrected_text)

        # Translate the corrected text
        target_lang_code = lang_map.get(target_language, "en")
        with st.spinner("Translating text..."):
            translated_text = translate_text(corrected_text, target_lang_code)
        st.subheader(f"Translated Text ({target_language})")
        st.write(translated_text)

if __name__ == "__main__":
    main()