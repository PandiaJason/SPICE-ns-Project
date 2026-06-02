import subprocess
import time
import os
from playwright.sync_api import sync_playwright

def capture_screenshots():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, 'paper')
    server_script = os.path.join(base_dir, 'simulation', 'server.py')
    
    print("Starting Flask server...")
    server_process = subprocess.Popen(['python3', server_script])
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Use a large 1080p resolution to capture the whole UI beautifully
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            print("Navigating to dashboard...")
            page.goto('http://localhost:5000')
            
            # Wait for nominal state (sim t ~15s) with some initial telemetry lines drawn
            print("Waiting for nominal state (sim t ~15s)...")
            time.sleep(12)
            
            # 1. Dark Theme Screenshot in root
            dark_path = os.path.join(base_dir, 'ui_screenshot.png')
            page.screenshot(path=dark_path)
            print(f"Saved dark theme screenshot to {dark_path}")
            
            # 2. Toggle to Light Theme
            print("Toggling to light theme...")
            page.click('#btn-theme-toggle', timeout=5000)
            time.sleep(1) # Wait for theme transition
            
            # 3. Light Theme Screenshot in root
            light_path = os.path.join(base_dir, 'ui_screenshot_light.png')
            page.screenshot(path=light_path)
            print(f"Saved light theme screenshot to {light_path}")
            
            browser.close()
    finally:
        print("Shutting down server...")
        server_process.terminate()
        server_process.wait()
        print("Server shutdown completed.")

if __name__ == '__main__':
    capture_screenshots()
