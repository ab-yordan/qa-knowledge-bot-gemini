QA Knowledge Bot with Google Gemini & Streamlit
===============================================
This project is an internal Question Answering (QA) bot built using Google Gemini's large language model (LLM), the LangChain framework, and Streamlit for the graphical user interface (GUI). The bot is designed to answer specific questions based on knowledge documents loaded from a specified Google Drive folder, making it an intelligent assistant for your QA team.

Prerequisites
-------------
Before getting started, make sure you have the following:
*   **Python 3.9+** installed.
*   **Docker Desktop** installed and running.
*   **Active Google Cloud Project** account.
*   **Git** installed.

Project Structure
-----------------
```
your_qa_bot_project/
├── config/
│   ├── .env                    # Environment variables (API Key, Folder ID)
│   ├── credentials.json        # Google Drive OAuth 2.0 credentials
│   └── token.json              # Google Drive authentication token (auto-generated)
├── src/
│   ├── qa_bot/
│   │   ├── __init__.py
│   │   ├── qa_bot.py           # Main QA bot logic
│   │   └── drive_loader.py     # Google Drive document loading logic
│   └── ui/
│       ├── __init__.py
│       └── streamlit_app.py    # Streamlit user interface
├── Dockerfile                  # Instructions for building the Docker image
├── .dockerignore               # Files/folders ignored by Docker
├── requirements.txt            # Python dependencies list
└── README.md                   # This document
```
Setup Guide
-----------

### 1\. Google Cloud Project & Credentials Setup

1.  **Create or Select a Google Cloud Project:**

    *   Open [Google Cloud Console](https://console.cloud.google.com/).
      
    *   Select an existing project or create a new one.
      
3.  **Enable APIs:**
   
    *   In the left navigation menu, go to "APIs & Services" > "Enabled APIs & services".
      
    *   Click "+ ENABLE APIS AND SERVICES".
      
    *   Search for and enable:
      
        *   `Google Drive API`
          
        *   `Gemini API` (or `Generative Language API` if Gemini API is not directly available).
          
5.  **Create an OAuth 2.0 Client ID (For Google Drive):**
   
    *   Go to "APIs & Services" > "Credentials".
      
    *   Click "+ CREATE CREDENTIALS" > "OAuth client ID".
      
    *   Select **"Desktop app"** as the "Application type". Give it a name (e.g., "QA Bot Drive Access").
      
    *   Click "CREATE".
      
    *   Once created, click **"DOWNLOAD JSON"**. Save this file as `credentials.json` inside the `config/` folder at the root of your project.
      
    *   **Important:** Open `config/credentials.json` with a text editor and ensure the `redirect\_uris` section contains `"urn:ietf:wg:oauth:2.0:oob"` or a long list of `http://localhost:`. If not present, manually add `"urn:ietf:wg:oauth:2.0:oob"`.
      
7.  **Configure OAuth Consent Screen:**
   
    *   Go to "APIs & Services" > "OAuth consent screen".
      
    *   Select "User Type":
      
        *   **"Internal"**: If all your users have Google Workspace accounts within the same organization (does not require Google verification).
          
        *   **"External"**: If you are using it personally or for users outside your organization.
          
            *   If "External", you will be in "In testing" mode. Scroll down to "Test users" and **add your Google account** (which you will use for bot authentication).
              
9.  **Create a Google API Key (For Gemini API):**
    
    *   Go to "APIs & Services" > "Credentials".
      
    *   Click "+ CREATE CREDENTIALS" > "API Key".
      
    *   Copy the generated API Key.
      

### 2\. Configure Environment Variables (`.env`)
Create a file named `.env` inside the `config/` folder (i.e., `your_qa_bot_project/config/.env`). Populate it with the following variables:

```
 GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"  
 GOOGLE_DRIVE_QA_FOLDER_ID="YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE"
```

*   Replace `"YOUR_GEMINI_API_KEY_HERE"` with the API Key you created in step 1.5.
    
*   Replace `"YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE"` with the ID of the Google Drive folder where your QA documents are stored. You can get the folder ID from the Google Drive URL (e.g., `https://drive.google.com/drive/folders/THIS_FOLDER_ID`).
    

### 3\. Install Python Dependencies (Optional, for Local Run Without Docker)

If you wish to run the project locally without Docker (e.g., for development), follow these steps:

1.  **Clone the Repository:**
   
```
git clone https://github.com/your-username/your_qa_bot_project.git
cd your_qa_bot_project
```
 
3. **Create a Virtual Environment:**

```
python -m venv .venv
```

5.  **Activate the Virtual Environment:**
    
    *   **Windows:** `.\\.venv\\Scripts\\activate`
        
    *   **macOS/Linux:** `source ./.venv/bin/activate`
        
6. **Install Dependencies:**

```
pip install -r requirements.txt
``` 

### 4\. Run the Application Locally (Optional)

Once dependencies are installed and the virtual environment is active:

```
streamlit run src/ui/streamlit_app.py 
```

The Streamlit application will open in your browser. When running for the first time, the application will prompt you to authenticate Google Drive via the terminal.

Docker Guide
------------

Running your application in a Docker container ensures a consistent and portable environment.

### 1\. Build the Docker Image

Navigate to the root directory of your project (`your_qa_bot_project/`) in your terminal, then build the Docker _image_:

```
docker build -t qa-bot-app:latest .
```

*   Use docker `build -t qa-bot-app:latest --no-cache .` if you encounter issues with Docker _caching_ or want to ensure a completely clean _build_.
    

### 2\. Run the Docker Container

Ensure `config/.env`, `config/credentials.json`, and `config/token.json` (if present) are at the root of your project. Then, run the _container_ by mounting the `config/` folder:

Important: Before running, ensure there's no corrupted `config/token.json` (file or folder) on your host. You can delete it with: `rm -rf config/token.json`

```
docker run --rm -it \
    -p 8501:8501 \
    -v "$(pwd)/config:/app/config" \  # Mount the entire config directory
    qa-bot-app:latest 
```

*   `-p 8501:8501`: Maps _port_ 8501 from the _container_ to your _host_, allowing you to access the Streamlit UI via `http://localhost:8501`.
    
*   `-v "$(pwd)/config:/app/config"`: Mounts the `config` folder from your _host_ into the _container_. This enables the bot to read `.env` and `credentials.json`, and to save token.json on your _host_ after authentication.
    

### 3\. Google Drive Authentication in Docker (Manual)

The first time you run the _container_ (or if `config/token.json` is missing/deleted), the application will attempt to authenticate with Google Drive. Since Docker runs _headless_, you must perform these steps manually:

1.  **Observe the Docker Terminal:** The bot will print an authentication URL to your terminal:

```
\----- GOOGLE DRIVE AUTHENTICATION -----
Please open the following URL in your web browser:
https://accounts.google.com/o/oauth2/auth?...
After authorizing the application, copy the 'authorization code' that appears in your browser.

```
    
3.  **Copy the URL:** Copy the **entire URL** provided from the terminal.
    
4.  **Open an Incognito/Private Window:** Paste the copied URL into a **new Incognito (Chrome) or Private (Firefox/Edge) window** in your _browser_. This ensures you start a clean _login_ session and can select the correct Google account.
    
5.  **Choose Account & Grant Permissions:** Follow the steps on Google to select your correct Google account (the one linked to your Google Cloud Project) and grant permissions to the application.
    
6.  **Copy the Authorization Code:** After successful authorization, Google will display an "authorization code" in your _browser_. **Copy this code.**
    
7.  **Paste into Docker Terminal:** Return to your Docker terminal and paste the copied "authorization code", then press Enter.
    

Once you paste the code, the bot will complete authentication and save `token.json` in your `config/` folder. Afterward, the Streamlit application will start functioning, and you can access it at `http://localhost:8501`.

Usage
-----

Once the Streamlit application is running (either locally or in Docker), open `http://localhost:8501` in your _web browser_. You will see a chat interface where you can ask questions related to the documents in your Google Drive folder.

