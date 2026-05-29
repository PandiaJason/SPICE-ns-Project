import subprocess
import time

def run_script(script_name):
    print(f"\n=======================================================")
    print(f"🚀 RUNNING STAGE: {script_name}")
    print(f"=======================================================")
    start_time = time.time()
    
    # Run the script via subprocess
    result = subprocess.run(["python3", script_name], capture_output=False)
    
    end_time = time.time()
    duration = end_time - start_time
    
    if result.returncode != 0:
        print(f"❌ STAGE FAILED: {script_name} (Exit code: {result.returncode})")
        raise RuntimeError(f"Pipeline failed at stage: {script_name}")
        
    print(f"✅ STAGE COMPLETE: {script_name} (Duration: {duration:.2f} seconds)")

if __name__ == "__main__":
    start_pipeline = time.time()
    print("=======================================================")
    print("🌍 STARTING EDGE-AI TELEMETRY SIMULATION PIPELINE")
    print("=======================================================")
    
    try:
        run_script("data_generator.py")
        run_script("train_model.py")
        run_script("test_model.py")
        run_script("analyze_performance.py")
        
        duration_total = time.time() - start_pipeline
        print(f"\n🎉 PIPELINE SUCCESSFUL! All stages completed.")
        print(f"⏱️ Total Pipeline Execution Time: {duration_total:.2f} seconds")
        print("=======================================================")
    except Exception as e:
        print(f"\n🛑 PIPELINE TERMINATED DU TO ERROR: {e}")
