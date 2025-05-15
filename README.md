# NavigAid

NavigAid is an IoT-based navigation support system designed to assist users by processing visual and audio data to provide real-time navigation instructions. The system leverages decentralized sensing with centralized processing to ensure efficient operation.

## System Architecture

### ESP32 Node 1 (Audio Command Unit)

- **INMP441 Microphone**: Captures user voice commands.
- **Push Button**: Provides manual trigger input for initiating commands.
- **Wi-Fi Communication**: Sends trigger signals to the visual node.
- **User Interface**: Engages with the user to start navigation support.

### ESP32-CAM Node 2 (Visual Data Unit)

- **NodeMCU**: Controls the ESP32-CAM and manages Wi-Fi communication.
- **Image Capture**: Continuously captures images of the user's environment upon command.
- **Data Transmission**: Sends captured images to a remote central server for processing.

### Central Server

- **Image Analysis**: Performs object detection and spatial reasoning to analyze images.
- **Navigation Logic**: Determines obstacles, direction, and safe navigation paths.
- **Instruction Generation**: Creates text-based navigation instructions based on image analysis.

### Audio Feedback System

- **Text-to-Speech Conversion**: Converts navigation instructions into audio guidance.
- **User Feedback**: Delivers audio feedback to the user via a smartphone.

### Decentralized Sensing, Centralized Processing

- **Local Data Capture**: Handled by ESP32 devices to minimize power consumption.
- **Centralized Processing**: All intensive processing tasks (vision and decision logic) are performed on the server.
- **Efficiency**: Ensures low-power device operation with high-performance centralized analytics.

### IoT Level: Level 4

- **Connected Devices**: Devices transmit data to a centralized intelligent system.
- **Real-Time Interaction**: The system interacts with the user in real-time, providing immediate feedback and support.

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Flask
- gTTS
- Cloudinary
- Requests

### Installation

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**

   Use `pip` to install the required Python packages:

   ```bash
   pip install flask gTTS cloudinary requests
   ```

3. **Configure Environment Variables**

   Set up your environment variables for Cloudinary and Groq API keys:

   ```bash
   export CLOUDINARY_API_KEY='your_cloudinary_api_key'
   export CLOUDINARY_API_SECRET='your_cloudinary_api_secret'
   export CLOUDINARY_CLOUD_NAME='your_cloudinary_cloud_name'
   export GROQ_API_KEY='your_groq_api_key'
   ```

4. **Ensure Directory Structure**

   Make sure the following directories exist:

   - `recordings`: For storing audio recordings.
   - `received_images`: For storing uploaded images.
   - `beats`: For storing generated audio responses.

## Usage

### Running the Application

Start the Flask application:

```bash
python combined.py
```

The application will run on `http://0.0.0.0:5000`.

### Endpoints

- **`POST /`**: Upload an image for analysis.
- **`POST /stream`**: Stream audio data to the server.
- **`POST /analyze_image`**: Analyze an uploaded image and return context.
- **`POST /ask_question`**: Submit a question with audio, receive a text response, and convert it to audio.

### Example Usage

1. **Upload an Image**

   Use a tool like `curl` or Postman to upload an image to the `/` endpoint.

2. **Stream Audio**

   Stream audio data to the `/stream` endpoint.

3. **Ask a Question**

   Submit a question with audio to the `/ask_question` endpoint and receive a response.

## Troubleshooting

- **Debugging**: Ensure Flask is running in debug mode to capture detailed logs.
- **Permissions**: Verify that the application has write permissions for the directories used for storing files.

## License Agreement

Copyright © 2025  
All rights reserved. Maddi Rishi Dhaneswar

This software and its associated documentation are proprietary and confidential.  
Unauthorized use, reproduction, distribution, or modification of any part of this codebase is strictly prohibited without explicit written permission from the owner (Maddi Rishi Dhaneswar).

This repository is shared for academic evaluation and publication purposes only.

If you wish to collaborate, request access, or seek clarification, please contact:  
maddi.rishi2468@gmail.com

No license is granted by implication, estoppel, or otherwise.
