from fastapi import FastAPI, UploadFile, File
import shutil
import subprocess
import whisper
from googletrans import Translator
import os

app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

model = whisper.load_model("tiny")
translator = Translator()

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    audio_path = video_path.replace(".mp4", ".wav")

    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", audio_path
    ])

    result = model.transcribe(audio_path, language="ja")

    srt_path = os.path.join(OUTPUT_FOLDER, "output.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result['segments']):
            text = translator.translate(segment['text'], src='ja', dest='en').text
            f.write(f"{i+1}\n")
            f.write(f"{segment['start']:.2f} --> {segment['end']:.2f}\n")
            f.write(text + "\n\n")

    output_video = os.path.join(OUTPUT_FOLDER, "translated_" + file.filename)

    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles={srt_path}",
        output_video
    ])

    return {"output_video": output_video}
