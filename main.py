from openai import AsyncOpenAI
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os
import requests
import webbrowser
import pyautogui
import time
from pygame import mixer
from io import BytesIO
import speech_recognition as sr
import subprocess
from datetime import datetime

# Initialize pygame mixer
mixer.init()

# Load environment variables
load_dotenv()

# API keys
elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Global counter for usage limit
MAX_CALLS = 10
call_count = 0

# Configure OpenRouter provider (for potential LLM use later)
provider = AsyncOpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

model = OpenAIChatCompletionsModel(
    model="qwen/Qwen2-7B-Chat",
    openai_client=provider,
)

config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

# Simulated data storage (in-memory for simplicity)
schedule = []


# Text-to-Speech function using ElevenLabs
def text_to_speech(text):
    global call_count

    if call_count >= MAX_CALLS:
        print("Error: ElevenLabs API call limit (10) reached for this session.")
        return False

    if not elevenlabs_api_key:
        print("Error: No ElevenLabs API key provided.")
        return False

    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
        headers = {"xi-api-key": elevenlabs_api_key, "Content-Type": "application/json"}
        data = {
            "text": text,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()

        audio_data = BytesIO(response.content)
        mixer.music.load(audio_data, "mp3")
        mixer.music.play()

        while mixer.music.get_busy():
            time.sleep(0.1)

        audio_data.close()
        call_count += 1
        print(
            f"Audio played using ElevenLabs. Calls remaining: {MAX_CALLS - call_count}"
        )
        return True

    except requests.exceptions.Timeout:
        print("Error: ElevenLabs API request timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: ElevenLabs API request failed - {str(e)}")
        return False
    except mixer.error as e:
        print(
            f"Error: Failed to play audio - {str(e)}. Ensure pygame is properly initialized."
        )
        return False
    except Exception as e:
        print(f"Error: Unexpected issue with ElevenLabs TTS - {str(e)}")
        return False


# Speech-to-Text function
def speech_to_text(max_attempts=3):
    recognizer = sr.Recognizer()
    attempt = 0
    while attempt < max_attempts:
        try:
            with sr.Microphone() as source:
                print(
                    f"Listening (Attempt {attempt + 1}/{max_attempts})... Say your command."
                )
                recognizer.adjust_for_ambient_noise(source, duration=2)
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=7)
            print("Processing speech...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            attempt += 1
            print(f"Timeout on attempt {attempt}. Please speak within {10} seconds.")
            if attempt == max_attempts:
                print("Max attempts reached. Please try again later.")
                return ""
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""
    return ""


# Function to detect wake word
def detect_wake_word():
    recognizer = sr.Recognizer()
    wake_word = "Vim"
    print("Waiting for wake word 'Vim'... (Press Ctrl+C to exit)")

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=2)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=2)
                text = recognizer.recognize_google(audio).lower()
                print(f"Detected: {text}")  # Debug output
                if wake_word.lower() in text:
                    print(f"Wake word 'Vim' detected! Ready for command.")
                    return True
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"Error with wake word detection: {e}")
            return False
        except KeyboardInterrupt:
            print("Exiting wake word detection.")
            return False


# Action functions
def open_website(website):
    try:
        url = f"https://www.{website.lower()}.com"
        webbrowser.open(url)
        time.sleep(2)
        return f"Successfully opened {url}."
    except Exception as e:
        return f"Failed to open {website}. Error: {str(e)}"


def perform_google_search(query):
    try:
        webbrowser.open("https://www.google.com")
        time.sleep(3)
        search_bar_x, search_bar_y = 540, 386
        pyautogui.moveTo(search_bar_x, search_bar_y)
        pyautogui.click()
        time.sleep(1)
        pyautogui.typewrite(query)
        pyautogui.press("enter")
        time.sleep(2)
        return f"Performed Google search for: {query}"
    except pyautogui.FailSafeException:
        return "Search operation interrupted (moved mouse to top-left corner)."
    except Exception as e:
        return f"Search operation failed. Error: {str(e)}"


def set_reminder(time_str, task):
    schedule.append({"time": time_str, "task": task})
    return f"Reminder set for {time_str} - {task}"


def check_schedule():
    return (
        "\n".join([f"{s['time']} - {s['task']}" for s in schedule])
        if schedule
        else "No reminders scheduled."
    )


def perform_system_task(task):
    try:
        task = task.lower().strip()
        if task == "open whatsapp":
            try:
                subprocess.run(
                    ["start", "whatsapp:"], shell=True, check=True, timeout=5
                )
                time.sleep(3)
                print(
                    "Move your mouse to the WhatsApp window/icon and press 'q' to capture coordinates and continue."
                )
                while True:
                    if pyautogui.hotkey("q"):
                        whatsapp_x, whatsapp_y = pyautogui.position()
                        print(
                            f"\nCaptured WhatsApp coordinates: x={whatsapp_x}, y={whatsapp_y}"
                        )
                        pyautogui.moveTo(whatsapp_x, whatsapp_y)
                        pyautogui.click()
                        break
                    time.sleep(0.1)
                return f"Opened and clicked WhatsApp at coordinates ({whatsapp_x}, {whatsapp_y})."
            except subprocess.CalledProcessError:
                return "Failed to open WhatsApp. Ensure it is installed."
            except subprocess.TimeoutExpired:
                return "Timed out opening WhatsApp."
        elif task == "volume up":
            pyautogui.hotkey("volumeup")
            return "Increased volume."
        elif task == "volume down":
            pyautogui.hotkey("volumedown")
            return "Decreased volume."
        elif task == "mute":
            pyautogui.hotkey("volumemute")
            return "Muted volume."
        elif task == "unmute":
            pyautogui.hotkey("volumemute")
            return "Unmuted volume."
        elif task in ["date and time", "current time", "current date"]:
            if task == "current time":
                current = datetime.now().strftime("%H:%M:%S")
                return f"Current time: {current}"
            elif task == "current date":
                current = datetime.now().strftime("%Y-%m-%d")
                return f"Current date: {current}"
            else:
                current = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return f"Current date and time: {current}"
        elif task == "open vscode":
            try:
                subprocess.run(["code"], shell=True, check=True, timeout=5)
                time.sleep(3)
                return "Opened VS Code."
            except subprocess.CalledProcessError:
                return "Failed to open VS Code. Ensure it is installed."
            except subprocess.TimeoutExpired:
                return "Timed out opening VS Code."
        elif task == "open spotify":
            try:
                subprocess.run(["start", "spotify:"], shell=True, check=True, timeout=5)
                time.sleep(3)
                return "Opened Spotify."
            except subprocess.CalledProcessError:
                return "Failed to open Spotify. Ensure it is installed."
            except subprocess.TimeoutExpired:
                return "Timed out opening Spotify."
        elif task == "open settings":
            try:
                subprocess.run(
                    ["start", "ms-settings:"], shell=True, check=True, timeout=5
                )
                time.sleep(2)
                return "Opened system settings."
            except subprocess.CalledProcessError:
                return "Failed to open settings. Ensure command is supported."
            except subprocess.TimeoutExpired:
                return "Timed out opening settings."
        else:
            return "Task not recognized. Supported tasks: open whatsapp, volume up, volume down, mute, unmute, date and time, current time, current date, open vscode, open spotify, open settings."
    except subprocess.SubprocessError as e:
        return f"Failed to execute system task. Error: {str(e)}"
    except pyautogui.FailSafeException:
        return "System task interrupted (moved mouse to top-left corner)."
    except Exception as e:
        return f"System task failed. Error: {str(e)}"


# Function to process and execute multiple tasks
def process_multiple_tasks(command):
    tasks = command.lower().split(" and ")
    results = []
    for task in tasks:
        task = task.strip()
        result = handle_task(task)
        results.append(result if result else f"Task '{task}' failed or not recognized.")
        time.sleep(2)  # Delay between tasks
    return "\n".join(results)


# Function to handle individual tasks with Jarvis triage
def handle_task(command):
    command = command.lower().strip()
    # Direct actions based on command patterns
    if command.startswith("open "):
        if any(site in command for site in ["google", "youtube", "facebook"]):
            website = next(
                site for site in ["google", "youtube", "facebook"] if site in command
            )
            return open_website(website)
        elif command in [
            "open whatsapp",
            "open vscode",
            "open spotify",
            "open settings",
        ]:
            return perform_system_task(command)
    elif command.startswith("search for "):
        query = command.replace("search for ", "").strip()
        return (
            perform_google_search(query) if query else "Please specify a search query."
        )
    elif command.startswith("set reminder "):
        parts = command.replace("set reminder ", "").strip().split(" ", 1)
        if len(parts) == 2:
            time_str, task_desc = parts
            return set_reminder(time_str, task_desc)
    elif command == "check schedule":
        return check_schedule()
    elif command in [
        "volume up",
        "volume down",
        "mute",
        "unmute",
        "date and time",
        "current time",
        "current date",
    ]:
        return perform_system_task(command)

    # Fallback to Jarvis for queries or unclear commands
    result = Runner.run_sync(jarvis, run_config=config, input=command)
    return (
        result.final_output
        if result.final_output
        else "Command unclear. Please provide more details or use a supported action."
    )


# Define Main Agent (Jarvis)
jarvis = Agent(
    name="Jarvis Assistant",
    instructions="""
    You are Jarvis, a personal assistant for a full-stack developer. Your role is to assist with daily tasks like coding, debugging, managing schedules, browsing, and system control based on voice commands converted to text. 
    - Understand and guide actions for clear commands (e.g., 'open VS Code', 'search for React docs', 'set reminder 3 PM meeting', 'volume up').
    - For queries or ambiguous commands (e.g., 'how to fix a CORS error', 'what is a REST API'), provide assistance using your knowledge and request clarification if needed.

    Keep responses concise, relevant, and tailored to a developer's workflow.

    Never guess or assume intent; rely on your understanding to assist or seek clarification.
    """,
)

# Main loop for voice interaction with wake word
if __name__ == "__main__":
    while True:
        if detect_wake_word():
            command = speech_to_text()
            if not command:
                continue

            if " and " in command.lower():
                task = process_multiple_tasks(command)
            else:
                task = handle_task(command)

            print(task)
            if task:
                text_to_speech(task)
