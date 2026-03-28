import streamlit as st
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# ---------------- OPENAI SETUP ----------------
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="YouTube AI Assistant", page_icon="🔥")
st.title("🔥 YouTube AI Assistant")
st.write("Summarize, analyze, and chat with any YouTube video")

youtube_link = st.text_input("Enter YouTube Video URL")

# ---------------- GET VIDEO ID ----------------
def get_video_id(url):
    try:
        if "youtu.be" in url:
            return url.split("/")[-1]
        return url.split("v=")[1].split("&")[0]
    except:
        return None

# ---------------- THUMBNAIL ----------------
if youtube_link:
    video_id = get_video_id(youtube_link)
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg")
    else:
        st.warning("Invalid YouTube link")

# ---------------- TRANSCRIPT FUNCTION ----------------
@st.cache_data
def extract_transcript(url):
    video_id = get_video_id(url)

    # -------- METHOD 1: YOUTUBE TRANSCRIPT (FAST) --------
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except:
        pass

    # -------- METHOD 2: WHISPER FALLBACK --------
    try:
        import yt_dlp
        import whisper
        import ssl

        ssl._create_default_https_context = ssl._create_unverified_context

        audio_file = "audio.m4a"
        if os.path.exists(audio_file):
            os.remove(audio_file)

        ydl_opts = {
            'format': 'bestaudio/best/bestaudio*',
            'outtmpl': audio_file,
            'quiet': True,
            'noplaylist': True,
            'cookiesfile': "cookies.txt",
            'retries': 10,
            'ignoreerrors': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        model = whisper.load_model("base")
        result = model.transcribe(file_path)

        return result["text"]

    except Exception as e:
        st.error(f"❌ Failed to extract transcript: {str(e)}")
        return None

# ---------------- OPENAI FUNCTION ----------------
def ask_openai(prompt):
    if not OPENAI_AVAILABLE:
        return None
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.warning(f"⚠️ OpenAI error: {str(e)}")
        return None

# ---------------- LOCAL SUMMARY ----------------
def local_summary(text, max_sentences=5):
    if not text:
        return "Transcript unavailable."
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences.sort(key=len, reverse=True)
    return " ".join(sentences[:max_sentences])

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["📘 Summary", "💬 Ask Questions"])

# -------- SUMMARY --------
with tab1:
    if st.button("Generate Summary"):
        if not youtube_link:
            st.warning("Enter a YouTube link first.")
        else:
            with st.spinner("Processing..."):
                transcript = extract_transcript(youtube_link)

                if transcript:
                    prompt = f"""
Summarize this video into:
- Key bullet points
- Important insights
- Final takeaway

Transcript:
{transcript}
"""
                    summary = ask_openai(prompt)

                    if not summary:
                        summary = local_summary(transcript)

                    st.subheader("📌 Summary")
                    st.write(summary)

                    st.download_button(
                        "📄 Download Notes",
                        summary,
                        file_name="summary.txt"
                    )
                else:
                    st.error("Could not extract transcript.")

# -------- Q&A --------
with tab2:
    question = st.text_input("Ask something about the video")

    if st.button("Get Answer"):
        if not youtube_link or not question:
            st.warning("Enter both link and question.")
        else:
            with st.spinner("Thinking..."):
                transcript = extract_transcript(youtube_link)

                if transcript:
                    prompt = f"""
Answer this question based on the video:

Question: {question}

Transcript:
{transcript}
"""
                    answer = ask_openai(prompt)

                    if not answer:
                        answer = local_summary(transcript, 3)

                    st.subheader("💡 Answer")
                    st.write(answer)
                else:
                    st.error("Could not extract transcript.")