import streamlit as st
import boto3
import uuid
import io
import tempfile
import os
import time
import json
import urllib.request
import base64
from PIL import Image, ImageDraw, ImageFont

from bedrock_utils import invoke_bedrock
from prompts       import INTERVIEW_SYSTEM_PROMPT, SCORING_SYSTEM_PROMPT
from resume_utils  import upload_resume_to_s3, extract_text_from_resume
from db_utils      import save_message, get_session_messages, get_all_sessions, save_score

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ── AWS Clients ───────────────────────────────────────────────
polly      = boto3.client("polly", region_name="us-east-1")
transcribe = boto3.client("transcribe", region_name="us-east-1")
s3_client  = boto3.client("s3", region_name="us-east-1")

MAX_QUESTIONS = 5
S3_BUCKET = "ali-interview-coach"


# ── Helpers ───────────────────────────────────────────────────
def text_to_speech(text: str):
    """Convert text to speech using Amazon Polly and auto-play it."""
    try:
        clean_text = text[:2999].replace('\n', ' ').replace('*', '')
        response = polly.synthesize_speech(
            Text=clean_text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            Engine="neural"
        )
        audio_bytes = response["AudioStream"].read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception as e:
        st.warning(f"🔇 Voice output unavailable: {str(e)}")


def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert speech to text using Amazon Transcribe."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        audio_key = f"audio/{uuid.uuid4()}.wav"
        s3_client.upload_file(tmp_path, S3_BUCKET, audio_key)

        job_name = f"interview-{uuid.uuid4()}"
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": f"s3://{S3_BUCKET}/{audio_key}"},
            MediaFormat="wav",
            LanguageCode="en-US"
        )

        max_tries, tries = 60, 0
        job_status = ""
        while tries < max_tries:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
            if job_status in ["COMPLETED", "FAILED"]:
                break
            time.sleep(2)
            tries += 1

        transcript_text = ""
        if job_status == "COMPLETED":
            transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            with urllib.request.urlopen(transcript_uri) as response:
                result = json.loads(response.read())
                transcript_text = result["results"]["transcripts"][0]["transcript"]

        try:
            os.unlink(tmp_path)
            s3_client.delete_object(Bucket=S3_BUCKET, Key=audio_key)
            transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        except Exception:
            pass

        return transcript_text

    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return ""


def extract_name(resume_text: str) -> str:
    """Extract candidate name from resume (simple heuristic)."""
    for line in resume_text.split("\n")[:5]:
        clean_line = line.strip()
        if len(clean_line.split()) <= 4 and "@" not in clean_line:
            return clean_line
    return "Candidate"


def generate_first_question(resume: str, jd: str) -> str:
    name = extract_name(resume)
    prompt = (
        f"Candidate Name: {name}\n\n"
        f"Candidate Resume:\n{resume[:3000]}\n\n"
        f"Job Description:\n{jd[:2000]}\n\n"
        "Start the interview.\n"
        "- Greet the candidate using their name (e.g., 'Hi Ali 👋')\n"
        "- Be friendly and professional\n"
        "- Ask ONLY the first question\n"
    )
    return invoke_bedrock(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=INTERVIEW_SYSTEM_PROMPT
    )


def generate_next_question(history: list, resume: str, jd: str, q_num: int) -> str:
    system = (
        INTERVIEW_SYSTEM_PROMPT
        + f"\n\n### CURRENT PROGRESS:\n"
        + f"You have asked {q_num - 1} question(s) so far. Now ask question {q_num} of {MAX_QUESTIONS}.\n"
        + f"Resume:\n{resume[:1500]}\n\nJob Description:\n{jd[:1000]}"
    )

    # Pass the real conversation history — DO NOT append a fake user message
    messages = [m for m in history if m["role"] in ("user", "assistant")]

    return invoke_bedrock(messages=messages, system_prompt=system)


def generate_score(history: list, resume: str, jd: str) -> str:
    qa = []
    msgs = [m for m in history if m["role"] in ("user", "assistant")]
    for i in range(0, len(msgs) - 1, 2):
        if msgs[i]["role"] == "assistant":
            qa.append(f"Q: {msgs[i]['content']}\nA: {msgs[i+1]['content']}")
    prompt = (
        f"Resume:\n{resume[:2000]}\n\n"
        f"Job Description:\n{jd[:1500]}\n\n"
        f"Interview Q&A:\n" + "\n\n".join(qa) +
        "\n\nGenerate the full evaluation report now."
    )
    return invoke_bedrock(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=SCORING_SYSTEM_PROMPT,
        max_tokens=1500
    )


def export_chat_png(history: list, score: str = "") -> bytes:
    W, LH, PAD = 900, 22, 30
    lines = ["=" * 65, "   AI INTERVIEW COACH — SESSION TRANSCRIPT", "=" * 65, ""]

    for msg in history:
        label = "🧑 You:" if msg["role"] == "user" else "🤖 Coach:"
        raw = f"{label} {msg['content']}"
        cur = ""
        for word in raw.split():
            if len(cur) + len(word) + 1 > 100:
                lines.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}" if cur else word
        if cur:
            lines.append(cur)
        lines.append("")

    if score:
        lines += ["", "=" * 65, "   SCORE REPORT", "=" * 65]
        lines += score.split("\n")

    H = PAD * 2 + LH * len(lines) + 40
    img = Image.new("RGB", (W, max(H, 400)), (255, 255, 255))
    drw = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        fnt = ImageFont.load_default()

    y = PAD
    for line in lines:
        color = (30, 30, 30)
        if "🤖" in line:         color = (0, 80, 160)
        elif "🧑" in line:       color = (20, 120, 20)
        elif line.startswith("="): color = (160, 0, 0)
        drw.text((PAD, y), line, fill=color, font=fnt)
        y += LH

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Session state init ────────────────────────────────────────
def _init():
    for k, v in {
        "session_id":  str(uuid.uuid4()),
        "messages":    [],
        "resume_text": "",
        "jd_text":     "",
        "q_count":     0,
        "done":        False,
        "score":       "",
        "tts":         False,
        "voice_input": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.session_state.tts = st.toggle("🔊 Voice Responses (Polly)", value=st.session_state.tts)
    st.session_state.voice_input = st.toggle("🎤 Voice Input (Transcribe)", value=st.session_state.voice_input)

    if st.session_state.tts:
        st.info("🔊 Voice is enabled. Questions will be read aloud.")

    st.divider()
    st.subheader("📄 Upload Resume")
    resume_file = st.file_uploader("PDF / Image", type=["pdf", "png", "jpg", "jpeg"])

    if resume_file and not st.session_state.resume_text:
        with st.spinner("Extracting resume text via Textract…"):
            key = upload_resume_to_s3(resume_file.read(), resume_file.name)
            st.session_state.resume_text = extract_text_from_resume(key)
        st.success("✅ Resume ready!")

    st.subheader("💼 Job Description")
    jd = st.text_area("Paste JD here", height=150)
    if jd:
        st.session_state.jd_text = jd

    if st.button("🗑️ New Session"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.divider()
    st.subheader("📜 Past Sessions")
    for s in get_all_sessions()[:6]:
        with st.expander(f"🕐 {s['timestamp']}"):
            st.caption(s["preview"])

# ── Main ──────────────────────────────────────────────────────
st.title("💼 AI Interview Coach")
st.caption("Upload your resume + paste the JD, then click Start Interview.")

# Render existing chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Interview finished — show score + download
if st.session_state.done:
    st.success("🎉 Interview Complete!")
    st.markdown(st.session_state.score)

    if st.session_state.tts:
        st.subheader("🔊 Listen to Your Score Report")
        text_to_speech(st.session_state.score)

    png = export_chat_png(st.session_state.messages, st.session_state.score)
    st.download_button(
        "📥 Download Chat as PNG",
        data=png,
        file_name=f"interview_{st.session_state.session_id[:8]}.png",
        mime="image/png"
    )
    st.stop()

# Start button (only shown before first message)
if not st.session_state.messages:
    if st.session_state.resume_text and st.session_state.jd_text:
        if st.button("🚀 Start Interview", type="primary"):
            with st.spinner("Generating first question…"):
                q = generate_first_question(
                    st.session_state.resume_text,
                    st.session_state.jd_text
                )
            st.session_state.messages.append({"role": "assistant", "content": q})
            st.session_state.q_count = 1
            save_message(st.session_state.session_id, "assistant", q)
            st.rerun()
    else:
        st.info("👈 Upload your resume and paste the job description in the sidebar to begin.")
    st.stop()

# Show last assistant message with audio if TTS enabled
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]["content"]
    if st.session_state.tts:
        with st.chat_message("assistant"):
            st.write(last_msg)
            st.caption("🔊 Playing audio...")
            text_to_speech(last_msg)

# ── Voice Input Section ───────────────────────────────────────
answer = None

if st.session_state.voice_input:
    st.markdown("### 🎤 Record Your Answer")
    st.caption("Click the microphone below to record your answer")

    audio_file = st.audio_input("Record audio")

    if audio_file is not None:
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/wav")

        if st.button("🔄 Transcribe & Submit", type="primary"):
            with st.spinner("🎧 Converting speech to text... Please wait 10-15 seconds..."):
                transcribed_text = transcribe_audio(audio_bytes)

                if transcribed_text:
                    st.success(f"✅ **Transcribed:** {transcribed_text}")
                    answer = transcribed_text
                else:
                    st.error("❌ Could not transcribe. Please try again or use text input below.")

# ── Text Input (always available as fallback) ─────────────────
if not answer:
    prompt_text = "Type your answer…" if not st.session_state.voice_input else "Or type your answer here…"
    text_answer = st.chat_input(prompt_text)
    if text_answer:
        answer = text_answer

# ── Process Answer ────────────────────────────────────────────
if answer:
    st.session_state.messages.append({"role": "user", "content": answer})
    save_message(st.session_state.session_id, "user", answer)

    with st.chat_message("user"):
        st.write(answer)

    if st.session_state.q_count >= MAX_QUESTIONS:
        with st.spinner("Evaluating your performance…"):
            report = generate_score(
                st.session_state.messages,
                st.session_state.resume_text,
                st.session_state.jd_text
            )
        st.session_state.score = report
        st.session_state.done  = True
        save_score(st.session_state.session_id, report)
        st.rerun()
    else:
        with st.spinner("Coach is thinking…"):
            next_q = generate_next_question(
                st.session_state.messages,
                st.session_state.resume_text,
                st.session_state.jd_text,
                st.session_state.q_count + 1
            )
        st.session_state.messages.append({"role": "assistant", "content": next_q})
        st.session_state.q_count += 1
        save_message(st.session_state.session_id, "assistant", next_q)
        st.rerun()