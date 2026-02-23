import os
import time
import json
import pyautogui
from datetime import datetime
from PIL import Image
import google.genai as genai
from google.genai import types

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =============================
# CONFIG  — edit these
# =============================

API_KEY = "AIzaSyCZ8ofs30HFDQsQIU9Tra2gIVBvEPmpCyY"
interval = 10
save_folder = "screenshots"
os.makedirs(save_folder, exist_ok=True)

# Your freelancer profile — Gemini uses this to judge fit & write cover letter
YOUR_PROFILE = """
Name: Inna Yadav
Skills: Python, Machine learning, web scraping, automation, Django, Flask
Experience: 4 years backend development
Past work: ntegrated WhatsApp Cloud API creating over 15 dynamic message templates and enabling two-way
communication. Applied deb ugging and system design principles to improve customer engagement by 30%.
Attempted EC2-based Redis deployment to address local machine connectivity issues, improving system
stability for development testing by 25%.Developed a chatbot using OpenAI's API leveraging NLP techniques and data preprocessing to improve user
interaction efficiency by 35%. Processed 10,000+ restaurant records into structured .csv files, enhancing data
Hourly rate: $30/hr
Availability: Full-time
"""

# Criteria Gemini uses to decide whether to apply
APPLY_CRITERIA = """
- Must involve Python or Django
- Budget should be reasonable (not less than $10/hr or $100 fixed)
- Should NOT require skills I don't have (e.g. mobile development, C++, Java)
- Prefer jobs posted by clients with payment verified
- I wokr in India so prefer jobs that are open to Indian freelancers or remote jobs without strict timezone requirements.
"""

# =============================
# GEMINI CLIENT
# =============================

client = genai.Client(api_key=API_KEY)


# =============================
# YOUR EXISTING ANALYZER (unchanged)
# =============================

def analyze_screenshot(image_path):
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = """
        Analyze this screenshot.

        1. Is this the Upwork website?
        2. If yes, is it sorted by "Most Recent"?
        3. If yes, extract the TOP visible project title.

        If not applicable, set latest_project_title to null.

        Return JSON only.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "is_upwork": {"type": "BOOLEAN"},
                        "is_most_recent_tab": {"type": "BOOLEAN"},
                        "latest_project_title": {
                            "type": "STRING",
                            "nullable": True
                        }
                    },
                    "required": ["is_upwork", "is_most_recent_tab", "latest_project_title"]
                }
            )
        )
        return json.loads(response.text)

    except Exception as e:
        print("❌ Analysis Error:", e)
        return None


# =============================
# SELENIUM SETUP
# =============================

def create_driver():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options 
    )
    print("✅ Connected to existing Chrome window")
    return driver


# =============================
# SELENIUM ACTIONS
# =============================

def click_top_job(driver):
    """Click the first job card on the current Upwork page."""
    wait = WebDriverWait(driver, 15)
    for selector in ["a.air3-link", "a[href*='/jobs/']", ".air3-link"]:
        try:
            card = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            card.click()
            time.sleep(3)
            print("✅ Clicked top job card")
            return True
        except Exception:
            continue
    print("❌ Could not find job card. Upwork DOM may have changed.")
    return False


def get_job_details(driver):
    """
    Scroll through the job page in sections, capturing screenshots at each position.
    Sends all screenshots to Gemini to extract complete job details.
    """
    # Scroll back to top first to start fresh
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1.5)

    screenshots = []
    scroll_positions = [0, 400, 800, 1200]  # px — adjust if job pages are longer

    for i, scroll_y in enumerate(scroll_positions):
        driver.execute_script(f"window.scrollTo(0, {scroll_y});")
        time.sleep(1)  # let content settle after scroll

        screenshot_bytes = driver.get_screenshot_as_png()
        screenshots.append(
            types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
        )
        print(f"   📸 Captured scroll position {scroll_y}px (section {i+1}/{len(scroll_positions)})")

    # Scroll back to top so Apply button is accessible later
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    print("   🤖 Sending all sections to Gemini for extraction...")

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[
            *screenshots,
            (
                "These are sequential scrolled screenshots of a single Upwork job posting. "
                "Using ALL the screenshots together, extract the complete: "
                "job title, full description, required skills, budget/rate, client info, "
                "and any other relevant details. Return plain text."
            )
        ]
    )

    return response.text.strip()


def check_fit_and_write_letter(job_details):
    """
    Single Gemini call that:
    1. Decides if the job is a match
    2. If yes, writes the cover letter
    Returns a dict: { match: bool, reason: str, cover_letter: str | None }
    """
    prompt = f"""
    FREELANCER PROFILE:
    {YOUR_PROFILE}

    APPLY CRITERIA:
    {APPLY_CRITERIA}

    JOB DETAILS:
    {job_details}

    Task:
    1. Decide if this job matches the profile and criteria.
    2. If it does, write a short cover letter (under 150 words). Start with a specific hook,
       mention 1-2 relevant skills, end with a call to action. Sound human and confident.
    3. If it doesn't match, leave cover_letter as null.

    Return JSON only.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt],
        config=types.GenerateContentConfig(
            temperature=0.4,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "match": {"type": "BOOLEAN"},
                    "reason": {"type": "STRING"},
                    "cover_letter": {"type": "STRING", "nullable": True}
                },
                "required": ["match", "reason", "cover_letter"]
            }
        )
    )
    return json.loads(response.text)


def fill_and_submit_proposal(driver, cover_letter):
    """Click Apply, fill cover letter. Submit is disabled by default — uncomment when ready."""
    wait = WebDriverWait(driver, 15)

    # Click Apply Now button
    for selector in ["[data-test='apply-button']", "button[aria-label='Buy Connects to apply']", ".apply-button"]:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            btn.click()
            print("✅ Clicked Apply button")
            time.sleep(3)
            break
        except Exception:
            continue

    # Fill cover letter
    for selector in ["textarea[name='coverLetter']", "[data-test='cover-letter'] textarea", "textarea"]:
        try:
            textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            textarea.clear()
            textarea.send_keys(cover_letter)
            print("✅ Cover letter filled")
            break
        except Exception:
            continue

    # ⚠️ SUBMIT IS INTENTIONALLY DISABLED — uncomment line below when confident
    # driver.find_element(By.CSS_SELECTOR, "[data-test='submit-proposal']").click()

    print("\n📋 Cover letter written (submit manually for now):")
    print("─" * 50)
    print(cover_letter)
    print("─" * 50)


# =============================
# MAIN LOOP
# =============================

def main():
    print("🚀 Starting Upwork Bot...")
    driver = create_driver()

    print("⏳ Log in to Upwork in the browser. You have 10 seconds...")
    time.sleep(10)

    previous_title = None
    applied_titles = set()  # Avoid applying to the same job twice

    print(f"🔁 Monitoring every {interval}s. Press Ctrl+C to stop.\n")

    while True:
        try:
            # ── Step 1: Screenshot (your existing logic) ──────────────────
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(save_folder, f"screenshot_{timestamp}.png")
            pyautogui.screenshot().save(filepath)
            print(f"📸 Screenshot saved: {filepath}")

            result = analyze_screenshot(filepath)

            if not result:
                time.sleep(interval)
                continue

            print("🔎 Result:", result)

            if not (result["is_upwork"] and result["is_most_recent_tab"]):
                print("⚠️  Not on Upwork Most Recent tab. Skipping.")
                time.sleep(interval)
                continue

            current_title = result["latest_project_title"]
            print(f"🔥 Latest Project: {current_title}")

            # ── Step 2: Check if it's a NEW job ──────────────────────────
            if current_title == previous_title or current_title in applied_titles:
                print("   No new job detected.")
                time.sleep(interval)
                continue

            print(f"\n🆕 NEW JOB DETECTED: {current_title}")
            previous_title = current_title

            # ── Step 3: Selenium clicks the top job ───────────────────────
            if not click_top_job(driver):
                time.sleep(interval)
                continue

            # ── Step 4: Extract job details (now with scrolling) ──────────
            print("📄 Extracting job details (scrolling through page)...")
            job_details = get_job_details(driver)

            # ── Step 5: Check fit + write cover letter ────────────────────
            print("🤖 Analyzing fit and writing cover letter...")
            decision = check_fit_and_write_letter(job_details)
            print(f"   Match: {decision['match']} | {decision['reason'][:80]}...")

            if not decision["match"]:
                print("⏭️  Job doesn't match. Going back.")
                driver.back()
                time.sleep(2)
                time.sleep(interval)
                continue

            # ── Step 6: Fill proposal ─────────────────────────────────────
            fill_and_submit_proposal(driver, decision["cover_letter"])
            applied_titles.add(current_title)

            # Go back to job list
            driver.back()
            time.sleep(3)

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\n👋 Stopped.")
            break
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            try:
                driver.back()
                time.sleep(5)
            except Exception:
                pass
            time.sleep(interval)

    driver.quit()
    print("✅ Bot exited.")


if __name__ == "__main__":
    main()