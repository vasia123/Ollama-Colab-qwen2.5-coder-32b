# =============================================
# IMPORTANT: How to get your ngrok authtoken
# =============================================
# 1. Go to https://ngrok.com and sign up for a free account
# 2. After signing in, go to https://dashboard.ngrok.com/get-started/your-authtoken
# 3. Copy your authtoken
# 4. In Google Colab:
#    - Click on the key icon in the left sidebar to open "Secrets"
#    - Click "Add new secret"
#    - Set "Name" as: authtoken
#    - Set "Value" as: your-ngrok-token-here
#    - Click "Add"
# 5. Run this notebook with a GPU runtime (Runtime -> Change runtime type -> GPU)
# =============================================

!curl https://ollama.ai/install.sh | sh

!echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections
!sudo apt-get update && sudo apt-get install -y cuda-drivers

!pip install pyngrok
from pyngrok import ngrok
from google.colab import userdata
import os
import subprocess
import threading

# Verify ngrok token exists
try:
    token = userdata.get('authtoken')
    if not token:
        raise ValueError("No authtoken found in Colab secrets")
    ngrok.set_auth_token(token)
except Exception as e:
    print("ERROR: Could not find ngrok authtoken in Colab secrets!")
    print("Please follow the instructions at the top of this notebook to set up your ngrok authtoken")
    print("Then restart the runtime and run again")
    raise e

# Set LD_LIBRARY_PATH for NVIDIA library
os.environ.update({'LD_LIBRARY_PATH': '/usr/lib64-nvidia'})

def run_and_print_output(process):
    """Helper function to continuously read and print process output"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

# Start ollama serve
print('>>> starting ollama serve')
ollama_serve = subprocess.Popen(
    ['ollama', 'serve'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

# Start thread to print ollama serve output
serve_thread = threading.Thread(target=run_and_print_output, args=(ollama_serve,))
serve_thread.daemon = True
serve_thread.start()

# Give ollama serve a moment to start up
import time
time.sleep(5)

# Pull the model
print('>>> starting ollama pull qwen2.5-coder:32b')
pull_process = subprocess.Popen(
    ['ollama', 'pull', 'qwen2.5-coder:32b'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

# Print pull process output
while True:
    output = pull_process.stdout.readline()
    if output == '' and pull_process.poll() is not None:
        break
    if output:
        print(output.strip())

# Start ngrok
print('>>> starting ngrok http server')
ngrok_process = subprocess.Popen(
    ['ngrok', 'http', '--log', 'stderr', '11434', '--host-header=localhost:11434'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

# Start thread to print ngrok output
ngrok_thread = threading.Thread(target=run_and_print_output, args=(ngrok_process,))
ngrok_thread.daemon = True
ngrok_thread.start()

# Get and display the public URL
time.sleep(5)  # Wait for ngrok to start
try:
    tunnels = ngrok.get_tunnels()
    if tunnels:
        print("\n=== Your Ollama server is available at ===")
        print(tunnels[0].public_url)
        print("=====================================")
    else:
        print("No active ngrok tunnels found")
except Exception as e:
    print("Error getting ngrok URL:", e)

# Keep the main process running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
    ollama_serve.terminate()
    ngrok_process.terminate()
