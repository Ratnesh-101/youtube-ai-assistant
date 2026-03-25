import streamlit as st
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# ---------------- GEMINI SETUP ----------------
try:
    from google import genai
    GEMINI_AVAILABLE = True
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception:
    GEMINI_AVAILABLE = False

# ---------------- FFMPEG PATH ----------------
ffmpeg_path = r"C:\Users\Ratnesh Singh\Downloads\ffmpeg-2026-03-22-git-9c63742425-essentials_build\ffmpeg-2026-03-22-git-9c63742425-essentials_build\bin\ffmpeg.exe"
ffmpeg_exe = ffmpeg_path if os.path.isfile(ffmpeg_path) else "ffmpeg"

# ---------------- STREAMLIT PAGE ----------------
st.set_page_config(page_title="YouTube AI Assistant", page_icon="🔥")
st.title("🔥 YouTube AI Assistant")
st.write("Summarize, analyze, and chat with any YouTube video")

youtube_link = st.text_input("Enter YouTube Video URL")

# Thumbnail preview
if youtube_link:
    try:
        if "youtu.be" in youtube_link:
            video_id = youtube_link.split("/")[-1]
        else:
            video_id = youtube_link.split("v=")[1].split("&")[0]

        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg")
    except:
        st.warning("Invalid link")

# ---------------- WHISPER TRANSCRIPT ----------------
def extract_transcript_whisper(url):
    try:
        import yt_dlp
        import whisper
        import ssl

        ssl._create_default_https_context = ssl._create_unverified_context

        # Delete old audio if exists
        audio_file = "audio.m4a"
        if os.path.exists(audio_file):
            os.remove(audio_file)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_file,
            'quiet': False,
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_exe,
            'cookiefile': r"C:\Users\Ratnesh Singh\cookies.txt",
            'nooverwrites': True,
            'continuedl': False,
            'retries': 10
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        model = whisper.load_model("base")
        result = model.transcribe(file_path)

        return result["text"]

    except Exception as e:
        st.error(f"❌ Error extracting transcript: {str(e)}")
        return None

# ---------------- GEMINI ASK ----------------
def ask_gemini(prompt):
    if not GEMINI_AVAILABLE:
        return None
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        st.warning(f"⚠️ Gemini unavailable or quota exceeded: {str(e)}")
        return None

# ---------------- LOCAL SMART SUMMARY ----------------
def local_summary(transcript, max_sentences=5):
    if not transcript:
        return "Transcript unavailable. Cannot summarize."
    sentences = re.split(r'(?<=[.!?]) +', transcript)
    sentences.sort(key=lambda s: len(s), reverse=True)
    summary = " ".join(sentences[:max_sentences])
    return summary if summary else "Transcript too short to summarize."

# ---------------- STREAMLIT TABS ----------------
tab1, tab2 = st.tabs(["📘 Summary", "💬 Ask Questions"])

# -------- SUMMARY TAB --------
with tab1:
    if st.button("Generate Summary"):
        if youtube_link:
            with st.spinner("Processing video..."):
                transcript = extract_transcript_whisper(youtube_link)

                if transcript:
                    summary_prompt = f"""
Summarize this video into:
- Key bullet points
- Important insights
- Final takeaway

Transcript:
{transcript}
"""
                    summary = ask_gemini(summary_prompt)

                    if not summary:
                        summary = local_summary(transcript)

                    st.subheader("📌 Summary")
                    st.write(summary)

                    if summary:
                        st.download_button(
                            "📄 Download Notes",
                            summary,
                            file_name="summary.txt"
                        )
                else:
                    st.warning("Failed to extract transcript. Check the video or cookies.")
        else:
            st.warning("Enter a YouTube link first.")

# -------- Q&A TAB --------
with tab2:
    question = st.text_input("Ask something about the video")

    if st.button("Get Answer"):
        if youtube_link and question:
            with st.spinner("Thinking..."):
                transcript = extract_transcript_whisper(youtube_link)

                if transcript:
                    qa_prompt = f"""
Answer this question based on the video:

Question: {question}

Transcript:
{transcript}
"""
                    answer = ask_gemini(qa_prompt)

                    if not answer:
                        answer = local_summary(transcript, max_sentences=3)

                    st.subheader("💡 Answer")
                    st.write(answer)
                else:
                    st.warning("Failed to extract transcript. Check the video or cookies.")
                