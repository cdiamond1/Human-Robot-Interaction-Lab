from pydub import AudioSegment
import speech_recognition as sr
import os

# Ensure that pydub can find ffmpeg
from pydub.utils import which
ffmpeg_path = r"C:\Users\tdiam\Downloads\ffmpeg-2024-09-02-git-3f9ca51015-essentials_build\ffmpeg-2024-09-02-git-3f9ca51015-essentials_build\bin\ffmpeg.exe"  # Use the absolute path to ffmpeg
AudioSegment.converter = which("ffmpeg")
if not os.path.isfile(ffmpeg_path):
        raise RuntimeError(f"FFmpeg executable not found at {ffmpeg_path}")
AudioSegment.converter = ffmpeg_path

# Define and print the audio file path
audio_path = r"C:\Users\tdiam\Documents\GitHub\Nao-ChatGPT\audio1012082750.m4a"
print(f"Audio file path: {audio_path}")

# Check if the audio file exists
if not os.path.isfile(audio_path):
    raise FileNotFoundError(f"Audio file not found: {audio_path}")

# Load the audio file
audio = AudioSegment.from_file(audio_path, format="m4a")

# Export the audio to a WAV file
wav_path = "output.wav"
audio.export(wav_path, format="wav")

# Initialize the recognizer and load the WAV file
recognizer = sr.Recognizer()
with sr.AudioFile(wav_path) as source:
    audio_data = recognizer.record(source)
    try:
        # Recognize speech using Google Web Speech API
        text = recognizer.recognize_sphinx(audio_data)
    except sr.UnknownValueError:
        text = "Could not understand the audio."
    except sr.RequestError as e:
        text = f"Could not request results; {e}"

# Write the recognized text to a file
with open("transcript.txt", "w", encoding="utf-8") as file:
    file.write(text)