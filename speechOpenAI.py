import time
import multiprocessing
import speech_recognition as sr
from openai import OpenAI
import json
import os
import pyaudio
from enum import Enum

# Constants
CONTROL_FILE = "control.json"
RESPONSE_FILE = "response.txt"
HISTORY_FILE = "history.txt"
MODEL = "gpt-4"

class Turn(Enum):
    LISTEN = "listen"
    RESPOND = "respond"

# Initialize the recognizer
r = sr.Recognizer()

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def list_microphones():
    microphones = sr.Microphone.list_microphone_names()
    for index, name in enumerate(microphones):
        print(f"Microphone with index {index} and name \"{name}\" found")

def clear_chat_history():
    with open(HISTORY_FILE, "w") as f:
        default_history = [{
            "role": "system",
            "content": """You are a robot named Dave that provides appropriate gestures while answering my questions. 
            Provide the response in this example format: First part of response ^start(animations/Stand/Gestures/Hey_1) 
            second part of response. Make sure your response is considerate. You are talking to a patient that wouldn't be medically educated. 
            Start with asking for their name. Only respond to your name or directed prompts.
            Explain everything as if you are talking to someone who wouldn't understand overly complex information and invite further questioning.
            Make your mood professional and concise. Please limit your responce to 200 words to avoid overly extended processing time"""
        }]
        json.dump(default_history, f)


def load_chat_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return [{"role": "system", "content": 
            """You are a robot named Dave that provides appropriate gestures while answering my questions. 
            Provide the response in this example format: First part of response ^start(animations/Stand/Gestures/Hey_1) 
            second part of response. Make sure your response is considerate. You are talking to a patient that wouldn't be medically educated. 
            Start with asking for their name. Only respond to your name or directed prompts.
            Explain everything as if you are talking to someone who wouldn't understand overly complex information and invite further questioning.
            Make your mood professional and concise.  Please limit your responce to 200 words to avoid overly extended processing time
            """}]

def save_chat_history(chat_history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(chat_history, f)

def get_turn():
    try:
        with open(CONTROL_FILE, "r") as f:
            control = json.load(f)
        return Turn(control["turn"])
    except FileNotFoundError:
        return Turn.LISTEN

def set_turn(turn):
    with open(CONTROL_FILE, "w") as f:
        json.dump({"turn": turn.value}, f)

def listen_and_transcribe(mic_index):
    with sr.Microphone(device_index=mic_index) as source:
        r.adjust_for_ambient_noise(source)  # Adjust for background noise
        print("Listening...")

        # Set longer durations to avoid cutting people off
        audio = r.listen(source, timeout=None, phrase_time_limit=5)  # Adjust phrase_time_limit as needed

        print("Processing...")
        try:
            return r.recognize_google(audio)  # You can handle specific exceptions here if needed
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand the audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None


def get_ai_response(chat_history):
    completion = client.chat.completions.create(
        model=MODEL,
        messages=chat_history
    )
    return completion.choices[0].message.content

def save_response(response):
    with open(RESPONSE_FILE, "w") as f:
        f.write(response)

def conversation_loop(mic_index):
    clear_chat_history()
    chat_history = load_chat_history()

    while True:
        current_turn = get_turn()

        if current_turn == Turn.LISTEN:
            try:
                user_input = listen_and_transcribe(mic_index)
                print(f"User said: {user_input}")
                chat_history.append({'role': 'user', 'content': user_input})
                print("Changing to respond")
                set_turn(Turn.RESPOND)
                print(get_turn())
            except Exception as e:
                print(f"An error occurred while listening: {e}")
                time.sleep(1)
                continue

        elif current_turn == Turn.RESPOND:
            try:
                response = get_ai_response(chat_history)
                print(f"Assistant: {response}")
                chat_history.append({"role": "assistant", "content": response})
                save_chat_history(chat_history)
                save_response(response)
                time.sleep(3)
            except Exception as e:
                print(f"An error occurred while getting AI response: {e}")
                time.sleep(1)
                continue

        time.sleep(0.1)  # Small delay to prevent busy-waiting

if __name__ == "__main__":
    list_microphones()
    mic_index = int(input("Enter the index of the microphone you want to use: "))
    conversation_loop(mic_index)