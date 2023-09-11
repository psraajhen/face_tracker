#!/usr/bin/env python
import cv2
import os
import time
from PCA9685 import PCA9685
from flask import Flask, render_template_string, request
import threading  # Add this line to import threading module
import subprocess

# Initialize Flask app
app = Flask(__name__)


# Initialize PCA9685 for servo control
pwm = PCA9685(0x40)
pwm.setPWMFreq(50)

def start_mjpg_streamer():
    Road = 'mjpg-streamer/mjpg-streamer-experimental/'
    command = './' + Road + 'mjpg_streamer -i "./' + Road + '/input_uvc.so" -o "./' + Road + 'output_http.so -w ./' + Road + 'www"'
    subprocess.Popen(command, shell=True)

# Start MJPG-Streamer in a separate thread
mjpg_streamer_thread = threading.Thread(target=start_mjpg_streamer)
mjpg_streamer_thread.start()

# Set the initial Pulse and Step values for horizontal and vertical servos
HPulse = 1500
HStep = 0
VPulse = 1000
VStep = 0

pwm.setServoPulse(1, HPulse)
pwm.setServoPulse(0, VPulse)

# Define the HTML template as a string
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pan and Tilt Face Tracking</title>
</head>
<body>
    <h1>Pan and Tilt Face Tracking</h1>
    
    <div>
        <button onclick="sendCommand('up')">Up</button>
        <button onclick="sendCommand('down')">Down</button>
        <button onclick="sendCommand('left')">Left</button>
        <button onclick="sendCommand('right')">Right</button>
        <button onclick="sendCommand('stop')">Stop</button>
    </div>

    <script>
        function sendCommand(command) {
            fetch('/cmd', {
                method: 'POST',
                body: command
            });
        }
    </script>
</body>
</html>

"""

@app.route('/')
def index():
    # Render the HTML template defined as a string
    return render_template_string(html_template)

@app.route('/cmd', methods=['POST'])
def cmd():
    global HStep, VStep
    code = request.data.decode()
    
    if code == "stop":
        HStep = 0
        VStep = 0
    elif code == "up":
        VStep = -5
    elif code == "down":
        VStep = 5
    elif code == "left":
        HStep = 5
    elif code == "right":
        HStep = -5
    
    return "OK"

def timerfunc():
    global HPulse, VPulse, HStep, VStep, pwm

    if HStep != 0:
        HPulse += HStep
        if HPulse >= 2500:
            HPulse = 2500
        if HPulse <= 500:
            HPulse = 500
        pwm.start_PCA9685()
        pwm.setServoPulse(1, HPulse)

    if VStep != 0:
        VPulse += VStep
        if VPulse >= 2500:
            VPulse = 2500
        if VPulse <= 500:
            VPulse = 500
        pwm.start_PCA9685()
        pwm.setServoPulse(0, VPulse)

    global t
    t = threading.Timer(0.02, timerfunc)
    t.start()

if __name__ == '__main__':
    t = threading.Timer(0.02, timerfunc)
    t.setDaemon(True)
    t.start()

    app.run(host='0.0.0.0', port=8001)
