# ---------------- LOAD API KEY ----------------
# load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# # ---------------- FFMPEG PATH ----------------
# ffmpeg_path = r"C:\Users\Ratnesh Singh\Downloads\ffmpeg-2026-03-22-git-9c63742425-essentials_build\ffmpeg-2026-03-22-git-9c63742425-essentials_build\bin\ffmpeg.exe"
# AudioSegment.converter = ffmpeg_path if os.path.isfile(ffmpeg_path) else "ffmpeg"

# # ---------------- STREAMLIT PAGE ----------------
# st.set_page_config(page_title="YouTube AI Assistant", page_icon="🔥")
# st.title("🔥 YouTube AI Assistant")
# st.write("Summarize, analyze, and chat with any YouTube video")

# youtube_link = st.text_input("Enter YouTube Video URL")

# # Thumbnail preview
# if youtube_link:
#     try:
#         video_id = youtube_link.split("/")[-1] if "youtu.be" in youtube_link else youtube_link.split("v=")[1].split("&")[0]
#         st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg")
#     except:
#         st.warning("Invalid link")

# # ---------------- WHISPER MODEL ----------------
# @st.cache_resource
# def load_whisper_model(name="base"):
#     return whisper.load_model(name)

# model = load_whisper_model()

# # ---------------- AUDIO DOWNLOAD & CHUNK ----------------
# def download_audio(url):
#     audio_file = "audio_full.m4a"
#     if os.path.exists(audio_file):
#         os.remove(audio_file)
#     ydl_opts = {
#         "format": "bestaudio/best",
#         "outtmpl": audio_file,
#         "quiet": True,
#         "noplaylist": True,
#         "ffmpeg_location": ffmpeg_path,
#         "http_chunk_size": 10485760,
#         "ratelimit": None,
#         "socket_timeout": 60 
#     }
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.extract_info(url, download=True)
#         return audio_file
#     except Exception as e:
#         st.error(f"❌ Failed to download audio: {e}")
#         return None

# def chunk_audio(file_path, chunk_length_ms=5*60*1000):
#     audio = AudioSegment.from_file(file_path)
#     chunk_files = []

#     for i in range(0, len(audio), chunk_length_ms):
#         tmp_chunk = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
#         tmp_chunk.close()  # important for Windows

#         chunk = audio[i:i+chunk_length_ms]
#         chunk.export(tmp_chunk.name, format="wav")
#         chunk_files.append(tmp_chunk.name)

#     return chunk_files

# def transcribe_whole_video(url):
#     audio_file = download_audio(url)
#     if not audio_file:
#         return None

#     chunk_files = chunk_audio(audio_file)
#     transcript = ""
#     progress = st.progress(0)

#     for idx, chunk_path in enumerate(chunk_files):
#         st.text(f"Transcribing chunk {idx+1}/{len(chunk_files)}...")
#         try:
#             result = model.transcribe(chunk_path)
#             transcript += result["text"] + " "
#         except Exception as e:
#             st.warning(f"⚠️ Error transcribing chunk {idx+1}: {e}")
#         finally:
#             os.unlink(chunk_path)
#         progress.progress((idx + 1) / len(chunk_files))

#     return transcript.strip()

# # ---------------- SESSION CACHE ----------------
# if "transcript_cache" not in st.session_state:
#     st.session_state.transcript_cache = {}

# def get_transcript(url):
#     if url in st.session_state.transcript_cache:
#         return st.session_state.transcript_cache[url]
#     transcript = transcribe_whole_video(url)
#     st.session_state.transcript_cache[url] = transcript
#     return transcript

# # ---------------- CHATGPT ----------------
# def ask_chatgpt(prompt, max_tokens=1200):
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a technical assistant that summarizes video transcripts into professional study notes with one bullet per line."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=max_tokens,
#             temperature=0.3
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         st.warning(f"⚠️ ChatGPT API error: {str(e)}")
#         return None

# def clean_summary(text):
#     text = text.replace("I ", "The presenter ")
#     text = text.replace("my ", "the ")
#     text = text.replace("we ", "The team ")
#     text = text.replace("you ", "the user ")
#     return text

# # ---------------- STREAMLIT TABS ----------------
# tab1, tab2 = st.tabs(["📘 Summary", "💬 Ask Questions"])

# # -------- SUMMARY TAB --------
# with tab1:
#     if st.button("Generate Summary"):
#         if youtube_link:
#             with st.spinner("Processing video and generating summary..."):
#                 transcript = get_transcript(youtube_link)
#                 if transcript:
#                     summary_prompt = f"""
# Summarize this video transcript into professional study notes:
# - 🧠 Overview: 1 concise sentence
# - 📌 Key Points: each main idea as a separate bullet (1 per line)
# - 🎯 Takeaway: 1 sentence conclusion
# - Remove filler words and irrelevant speech
# - Replace first-person references (I, we, you, my) with neutral, technical phrasing

# Transcript:
# {transcript}
# """
#                     summary = ask_chatgpt(summary_prompt)
#                     summary = clean_summary(summary) if summary else "Could not generate summary."
#                     st.subheader("📌 Summary")
#                     st.write(summary)
#                     st.download_button("📄 Download Notes", summary, file_name="summary.txt")
#                 else:
#                     st.warning("Failed to extract transcript. Check the video or cookies.")
#         else:
#             st.warning("Enter a YouTube link first.")

# # -------- Q&A TAB --------
# with tab2:
#     question = st.text_input("Ask something about the video")
#     if st.button("Get Answer"):
#         if youtube_link and question:
#             with st.spinner("Thinking..."):
#                 transcript = get_transcript(youtube_link)
#                 if transcript:
#                     qa_prompt = f"""
# Answer this question based on the video transcript.
# - Provide a concise, clear answer in bullet points if necessary.
# - Remove filler words.
# - Replace first-person references with neutral phrasing.

# Question: {question}

# Transcript:
# {transcript}
# """
#                     answer = ask_chatgpt(qa_prompt)
#                     answer = clean_summary(answer) if answer else "Could not generate answer."
#                     st.subheader("💡 Answer")
#                     st.write(answer)
#                 else:
#                     st.warning("Failed to extract transcript. Check the video or cookies.")