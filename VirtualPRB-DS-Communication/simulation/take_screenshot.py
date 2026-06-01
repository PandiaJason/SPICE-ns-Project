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
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a large 1080p resolution to capture the whole UI beautifully
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        print("Navigating to dashboard...")
        page.goto('http://localhost:5000')
        
        # 1. Nominal State
        print("Waiting for nominal state (sim t ~30s)...")
        time.sleep(10)
        page.screenshot(path=os.path.join(paper_dir, 'fig_web_ui_nominal.png'))
        print(f"Saved {os.path.join(paper_dir, 'fig_web_ui_nominal.png')}")
        
        # 2. Anomaly State
        print("Waiting for anomaly state (sim t ~105s)...")
        time.sleep(25)
        page.screenshot(path=os.path.join(paper_dir, 'fig_web_ui_anomaly.png'))
        print(f"Saved {os.path.join(paper_dir, 'fig_web_ui_anomaly.png')}")
        
        # Execute Correction
        print("Executing Interception Correction...")
        page.click('#btn-execute', timeout=5000)
        
        # 3. Reconciled State
        print("Waiting for reconciliation to take effect (sim t ~140s)...")
        time.sleep(15)
        page.screenshot(path=os.path.join(paper_dir, 'fig_web_ui_reconciled.png'))
        print(f"Saved {os.path.join(paper_dir, 'fig_web_ui_reconciled.png')}")
        
        browser.close()
        
    print("Shutting down server...")
    server_process.terminate()
    server_process.wait()
    print("Screenshots captured successfully.")

if __name__ == '__main__':
    capture_screenshots()
