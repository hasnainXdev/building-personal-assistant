from agents import (
    Agent,
    RunConfig,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
)
from openai import AsyncOpenAI
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
from gtts import gTTS
import playsound

# Initialize pygame mixer (kept for compatibility, though not used with gTTS)
mixer.init()

# Load environment variables
load_dotenv()

# API keys
gemini_api_key = os.getenv("GEMINI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")  # Still needed if you revert to ElevenLabs

# Configure Gemini provider
provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Configure model
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider,
)

# Configure run settings
config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

# Simulated data storage (in-memory for simplicity)
schedule = []

# Utility function to format website URL
def format_website_url(website_name: str) -> str:
    """Converts a website name to a full URL (e.g., 'google' -> 'https://www.google.com')."""
    if not website_name:
        return ""
    return f"https://www.{website_name.lower()}.com"

# Tools
@function_tool
def set_reminder(time_str: str, task: str) -> str:
    """Sets a reminder for a given time and task."""
    schedule.append({"time": time_str, "task": task})
    return f"Reminder set for {time_str} - {task}"

@function_tool
def check_schedule() -> str:
    """Lists all scheduled reminders."""
    return "\n".join([f"{s['time']} - {s['task']}" for s in schedule]) if schedule else "No reminders scheduled."

@function_tool
def open_website(url: str) -> str:
    """Opens a website in the default browser."""
    try:
        webbrowser.open(url)
        time.sleep(2)  # Wait for the browser to open
        return f"Successfully opened {url}."
    except Exception as e:
        return f"Failed to open {url}. Error: {str(e)}"

@function_tool
def perform_google_search(query: str) -> str:
    """Performs a Google search by opening the site, clicking the search bar, and typing the query."""
    try:
        # Open Google
        webbrowser.open("https://www.google.com")
        time.sleep(3)  # Increased delay to ensure page loads

        # Use fixed coordinates as requested
        search_bar_x, search_bar_y = 540, 386
        pyautogui.moveTo(search_bar_x, search_bar_y)
        pyautogui.click()
        time.sleep(1)  # Wait for focus

        # Type the query and submit
        pyautogui.typewrite(query)
        pyautogui.press("enter")
        time.sleep(2)  # Wait for search results to load
        return f"Performed Google search for: {query}"
    except pyautogui.FailSafeException:
        return "Search operation interrupted (moved mouse to top-left corner)."
    except Exception as e:
        return f"Search operation failed. Error: {str(e)}"

@function_tool
def simulate_click(x: int = None, y: int = None, element: str = None) -> str:
    """Simulates a mouse click at specified coordinates or on a webpage element."""
    time.sleep(1)  # Additional delay to ensure page loads
    try:
        if x and y:
            pyautogui.click(x=x, y=y)
            return f"Clicked at coordinates ({x}, {y})."
        elif element and "search" in element.lower() and "google" in element.lower():
            pyautogui.moveTo(x=800, y=500)  # Example for Google search button
            pyautogui.click()
            return f"Clicked on Google search button (approximated at 800, 500)."
        return "No valid click target specified or coordinates/element name required."
    except pyautogui.FailSafeException:
        return "Click operation interrupted (moved mouse to top-left corner)."
    except Exception as e:
        return f"Click operation failed. Error: {str(e)}"

@function_tool
def perform_system_task(task: str) -> str:
    """Performs system-level tasks like opening apps, volume control, or showing date/time."""
    try:
        task = task.lower().strip()

        if task == "open whatsapp":
            try:
                subprocess.run(["start", "whatsapp:"], shell=True, check=True, timeout=5)
                time.sleep(3)  # Wait for app to open
                print("Move your mouse to the WhatsApp window/icon and press 'q' to capture coordinates and continue.")
                while True:
                    if pyautogui.hotkey('q'):  # Check for 'q' key press
                        whatsapp_x, whatsapp_y = pyautogui.position()
                        print(f"\nCaptured WhatsApp coordinates: x={whatsapp_x}, y={whatsapp_y}")
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
            pyautogui.hotkey("volumemute")  # Toggle to unmute
            return "Unmuted volume."
        elif task in ["date and time", "current time", "current date"]:
            if task == "current time":
                current = datetime.now().strftime("%H:%M:%S")
                return f"Current time: {current}"
            elif task == "current date":
                current = datetime.now().strftime("%Y-%m-%d")
                return f"Current date: {current}"
            else:  # date and time
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
                subprocess.run(["start", "ms-settings:"], shell=True, check=True, timeout=5)
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

# Define specialized agents
search_agent = Agent(
    name="SearchAgent",
    instructions="Perform a Google search based on user queries. Use `perform_google_search` tool to open Google, click the search bar, and type the query.",
    tools=[perform_google_search],
)

scheduler_agent = Agent(
    name="SchedulerAgent",
    instructions="Manage user schedules and reminders. Use `set_reminder` tool to set reminders and `check_schedule` tool to list scheduled tasks.",
    tools=[set_reminder, check_schedule],
)

browser_agent = Agent(
    name="BrowserAgent",
    instructions="Automate browser actions like opening websites and clicking. Use `open_website` and `simulate_click` tools as needed.",
    tools=[open_website, simulate_click],
)

system_agent = Agent(
    name="SystemAgent",
    instructions="Handle system-level tasks such as opening apps, volume control, and displaying date/time. Use `perform_system_task` tool for all system operations.",
    tools=[perform_system_task],
)

# Define Main Agent (Jarvis)
jarvis = Agent(
    name="Jarvis",
    instructions="""Understand user requests, plan daily tasks, and directly execute browser or system actions when applicable. For other tasks, delegate to specialized agents using handoffs. Process voice commands if provided.
    
    important!
    - use search_agent for google searches
    - use scheduler_agent for reminders and schedule management
    - use browser_agent for opening websites and clicking elements
    - use system_agent for system-level tasks like opening apps, volume control, and showing date/time
    """,
    tools=[open_website, simulate_click],  # Add tools directly to Jarvis for automation
    handoffs=[search_agent, scheduler_agent, browser_agent, system_agent],
)

# Function to convert text to speech using Google TTS
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        playsound.playsound("temp.mp3")
        os.remove("temp.mp3")  # Clean up temporary file
        print("Audio played using Google TTS.")
    except Exception as e:
        print(f"Error in Google TTS: {str(e)}")

# Function to convert speech to text using Google Speech Recognition with improved timeout
def speech_to_text(max_attempts=3):
    recognizer = sr.Recognizer()
    attempt = 0
    while attempt < max_attempts:
        try:
            with sr.Microphone() as source:
                print(f"Listening (Attempt {attempt + 1}/{max_attempts})... Say your command.")
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

# Function to process and execute multiple tasks
def process_multiple_tasks(command):
    tasks = command.lower().split(" and ")
    results = []
    for task in tasks:
        task = task.strip()
        if "search" in task:
            query = task.replace("search for ", "").strip()
            if query:
                result = Runner.run_sync(jarvis, run_config=config, input=f"perform google search with query: {query}")
                results.append(result.final_output if result.final_output else "Search task failed.")
        elif any(t in task for t in ["open whatsapp", "volume up", "volume down", "mute", "unmute", "date and time", "open vscode", "open spotify", "open settings"]):
            result = Runner.run_sync(jarvis, run_config=config, input=task)
            results.append(result.final_output if result.final_output else f"{task} failed.")
        elif "open" in task and any(site in task for site in ["google", "youtube", "facebook"]):
            website_name = next((site for site in ["google", "youtube", "facebook"] if site in task), None)
            if website_name:
                url = format_website_url(website_name)
                result = Runner.run_sync(jarvis, run_config=config, input=url)
                results.append(result.final_output if result.final_output else f"Failed to open {url}.")
        else:
            results.append(f"Task '{task}' not recognized.")
        time.sleep(2)  # Delay between tasks to prevent overlap
    return "\n".join(results)

# Main loop for voice interaction
if __name__ == "__main__":
    while True:
        # Get voice input
        command = speech_to_text()
        if not command:
            continue

        # Process single or multiple commands
        if " and " in command.lower():
            task = process_multiple_tasks(command)
        else:
            # Process single commands
            if "search" in command.lower():
                query = command.lower().replace("search for ", "").strip()
                if query:
                    task = f"perform google search with query: {query}"
                else:
                    task = command
            elif any(task in command.lower() for task in ["open whatsapp", "volume up", "volume down", "mute", "unmute", "date and time", "open vscode", "open spotify", "open settings"]):
                task = command
            elif "open" in command.lower() and any(site in command.lower() for site in ["google", "youtube", "facebook"]):
                website_name = next((site for site in ["google", "youtube", "facebook"] if site in command.lower()), None)
                if website_name:
                    url = format_website_url(website_name)
                    task = f"{url}"
                else:
                    task = command
            else:
                task = command

            # Run the agent for single task
            result = Runner.run_sync(jarvis, run_config=config, input=task)
            task = result.final_output if result.final_output else "Task failed."

        print(task)
        if task:
            text_to_speech(task)  # Use Google TTS instead of fallback