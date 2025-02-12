# -*- coding: utf-8 -*-
import time
import naoqi
from naoqi import ALProxy
import json
import io
import os
import random

# Constants
ip = "10.60.11.4"
port = 9559
CONTROL_FILE = "control.json"
RESPONSE_FILE = "response.txt"
prevResponce = ""

# Initialize proxies
tts = ALProxy("ALTextToSpeech", ip, port)
animated_speech = ALProxy("ALAnimatedSpeech", ip, port)
posture_proxy = ALProxy("ALRobotPosture", ip, port)
leds = ALProxy("ALLeds", ip, port)
motion = ALProxy("ALMotion", ip, port)
memory = ALProxy("ALMemory", ip, port)
speech_recognition = ALProxy("ALSpeechRecognition", ip, port)
behavior = ALProxy("ALBehaviorManager", ip, port)

current_posture = "Sit"  # Track the current posture

def set_posture(posture):
    global current_posture
    if current_posture != posture:
        posture_proxy.goToPosture(posture, 1.0)
        current_posture = posture

def look_away():
    # Generate random head angles for looking away
    yaw_angle = random.uniform(-1.0, 1.0)  # Left to right (-1.0 to 1.0 rad)
    pitch_angle = random.uniform(-0.3, 0.3)  # Up and down (-0.3 to 0.3 rad)
    
    # Move the head to the random position
    motion.angleInterpolation(["HeadYaw", "HeadPitch"], [yaw_angle, pitch_angle], [1.0, 1.0], True)

def look_at_person():
    motion.setStiffnesses("Head", 1.0)
    motion.angleInterpolation("Head", [0, 0], 1.0, True)  # Center head to face forward

# Loop to alternate between looking away and looking at the person
look_back_timer = time.time()  # Initialize timer for looking back
look_away_duration = 2  # Time in seconds to look away
look_back_interval = 4  # Time in seconds to look back at the person

def thinking_animation():
    leds.rotateEyes(0x0000FF, 0.25, 0.5)
    behavior.runBehavior("animations/Stand/Gestures/Thinking_1")

def set_turn(turn):
    with io.open(CONTROL_FILE, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps({"turn": turn}, ensure_ascii=False)))

def get_turn():
    try:
        with io.open(CONTROL_FILE, 'r', encoding='utf-8') as f:
            control = json.loads(f.read())
        return control["turn"]
    except IOError:
        return "listen"

def read_response():
    with io.open(RESPONSE_FILE, 'r') as f:
        return f.read().strip()

# Function to clear the response file
def clear_response_file():
    with open(RESPONSE_FILE, 'w') as f:
        f.write("")

# Track if response file has non-empty content
def is_response_ready():
    with open(RESPONSE_FILE, 'r') as f:
        content = f.read().strip()
    return bool(content)  # Return True if there's text, False otherwise

# Try pausing the ASR engine, if available
try:
    speech_recognition.pause(True)  # Pause ASR engine
except RuntimeError as e:
    print("Could not pause the ASR engine: ", e)

# Initialize wake word detection with new vocabulary
wake_word = "Hey Dave"
speech_recognition.setVocabulary([wake_word], False)

# Resume the ASR engine after setting the vocabulary
try:
    speech_recognition.pause(False)  # Resume ASR engine
    speech_recognition.subscribe("WakeWordDetection")  # Subscribe to restart ASR
except RuntimeError as e:
    print("Could not resume ASR engine or subscribe: ", e)

# Initially set the robot to Sit
set_posture("Sit")

clear_response_file()

while True:
    try:
        # Check for wake word
        if memory.getData("WordRecognized")[0] == wake_word:
            print("Wake word detected!")
            set_posture("Stand")
            look_at_person()
            
            # Signal the conversation script to listen
            set_turn("listen")
            
            # Wait for the response to be generated
            last_mod_time = os.path.getmtime(RESPONSE_FILE)

            while get_turn() != "respond":
                # LEDs rotate to indicate thinking
                leds.rotateEyes(0x0000FF, 0.25, 0.5)

            # Read and speak the response
            while get_turn() == "respond":
                # Wait for new content to appear in the response file
                while not is_response_ready():
                    leds.rotateEyes(0xFFFFFF, 0.25, 0.5)
                    print("Waiting for new response...")

                    # Look away and look back at intervals while waiting
                    current_time = time.time()

                    # Check if it's time to look away or look back
                    if current_time - look_back_timer >= look_back_interval:
                        look_away()  # Look away from the person
                        thinking_animation()  # Thinking animation
                        time.sleep(look_away_duration)  # Keep looking away for a few seconds
                        look_at_person()  # Look back at the person

                        # Reset the timer for the next interval
                        look_back_timer = time.time()

                    # Sleep for a short interval to avoid busy looping
                    time.sleep(0.1)

                # Now that the file has been updated, read the new response
                response = read_response()

                # After exiting the loop, look at the person before speaking
                look_at_person()
                # Now a new response is ready, look at the person before speaking
                print("Speaking")
                animated_speech.say(response.encode('utf-8'))
                print("Assistant: " + response)

                # Clear the response file after speaking
                clear_response_file()

                # Reset for the next interaction
                set_turn("listen")

                time.sleep(5)
                if is_response_ready():
                    clear_response_file()


            time.sleep(0.1)
    except Exception as e:
        print("An error occurred: " + str(e))
        time.sleep(1)