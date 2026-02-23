🤖 Upwork Auto-Apply Bot
An intelligent Upwork job monitoring bot that automatically detects new job postings, evaluates fit using Google Gemini AI, and drafts personalized cover letters — all in real time.

🚀 Features

Live job monitoring — Watches your Upwork "Most Recent" feed at a configurable interval
AI-powered job analysis — Uses Gemini 2.5 Flash to extract full job details via multi-scroll screenshots
Smart fit detection — Evaluates each job against your profile and custom criteria before deciding to apply
Auto cover letter generation — Writes a tailored, human-sounding cover letter for matching jobs
Safe by default — Auto-submit is disabled; proposals are filled but require manual confirmation


🧱 Tech Stack
LayerToolBrowser automationSelenium + ChromeDriverAI vision & textGoogle Gemini 2.5 Flash LiteScreenshotsPyAutoGUI + PillowChrome connectionRemote debugging (port 9222)

⚙️ Setup
1. Prerequisites

Python 3.9+
Google Chrome installed
A Google Gemini API key — get one at aistudio.google.com

2. Install dependencies
bashpip install selenium webdriver-manager pyautogui pillow google-genai undetected-chromedriver
3. Launch Chrome with remote debugging
Before running the bot, start Chrome with the remote debugging port open:
macOS/Linux:
bashgoogle-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
Windows:
bash"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\tmp\chrome-debug
Then log in to your Upwork account manually in that Chrome window and navigate to your job feed sorted by Most Recent.
4. Configure the bot
Open the script and edit the config section at the top:
pythonAPI_KEY = "your-gemini-api-key"
interval = 10  # seconds between checks

YOUR_PROFILE = """
Name: Your Name
Skills: Python, Django, ...
Experience: X years
...
"""

APPLY_CRITERIA = """
- Must involve Python
- Budget not less than $10/hr
...
"""
5. Run the bot
bashpython upwork_bot.py

🔄 How It Works
Every N seconds:
│
├── 📸 Take screenshot of browser
├── 🔍 Gemini checks: Is this Upwork Most Recent? What's the top job?
│
├── 🆕 New job detected?
│   ├── NO → Wait and repeat
│   └── YES ↓
│
├── 🖱️ Selenium clicks the top job card
├── 📜 Scroll through job page (4 sections) + capture screenshots
├── 🤖 Gemini extracts full job details from all screenshots
├── ✅ Gemini evaluates fit against your profile & criteria
│
├── No match → Go back, continue monitoring
└── Match ↓
    ├── 🤖 Gemini writes a personalized cover letter
    ├── 📝 Selenium fills in the proposal form
    └── ⏸️ Waits for manual submit (auto-submit disabled by default)

🛡️ Safety Notes

Auto-submit is intentionally disabled. The bot fills the cover letter but does not click Submit. To enable it, uncomment this line in fill_and_submit_proposal():

python  # driver.find_element(By.CSS_SELECTOR, "[data-test='submit-proposal']").click()

The bot tracks applied jobs in memory (applied_titles) to avoid duplicate applications within a session.
Always review the generated cover letter before submitting manually.


🛠️ Customization
Change scroll depth — If job descriptions are very long, add more scroll positions in get_job_details():
pythonscroll_positions = [0, 400, 800, 1200, 1600]  # add more if needed
Change check interval — Modify the interval variable (in seconds):
pythoninterval = 30  # check every 30 seconds

📁 Project Structure
upwork-bot/
├── upwork_bot.py       # Main bot script
├── screenshots/        # Auto-created; stores monitoring screenshots
└── README.md

⚠️ Disclaimer
This bot is for educational and personal productivity purposes. Use responsibly and in accordance with Upwork's Terms of Service. Automated interactions with Upwork may violate their ToS — use at your own risk.

📄 License
MIT License — free to use, modify, and distribute.
