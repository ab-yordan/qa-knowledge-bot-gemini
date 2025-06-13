import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from io import BytesIO
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain.docstore.document import Document
from googleapiclient.http import MediaIoBaseDownload 

# .env PATH CONFIGURATION
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
dotenv_path = os.path.join(project_root, 'config', '.env')

load_dotenv(dotenv_path=dotenv_path) 

# INITIAL CONFIGURATION
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file when loading Drive.")

SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] 

def authenticate_google_drive():
    creds = None
    token_path = os.path.join('config', 'token.json') 

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES) 
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = os.path.join('config', 'credentials.json') 
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}. Ensure it is in the 'config/' folder.")

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob" 
            
            print("\n----- GOOGLE DRIVE AUTHENTICATION -----")
            print("Please open the following URL in your web browser:")
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(auth_url)
            
            print("After authorizing the application, copy the 'authorization code' that appears in your browser.")
            
            auth_code = input("Enter the 'authorization code' here: ").strip()
            
            flow.fetch_token(code=auth_code) 

            creds = flow.credentials
        
        # Save credentials for the next session
        with open(token_path, 'w') as token: 
            token.write(creds.to_json())
    return creds

def load_documents_from_google_drive(folder_id):
    creds = authenticate_google_drive()
    if not creds:
        print("Failed to authenticate Google Drive.")
        return []

    try:
        service = build('drive', 'v3', credentials=creds, developerKey=GOOGLE_API_KEY)
        
        results = service.files().list(
            q=f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name, mimeType)",
            spaces='drive'
        ).execute()
        items = results.get('files', [])

        if not items:
            print('No files found in the Google Drive folder.')
            return []

        drive_documents = []
        for item in items:
            temp_filepath = None 
            try:
                if not isinstance(item, dict):
                    print(f"Skipping non-dictionary item received from Drive: {item}")
                    continue

                required_keys = ['id', 'name', 'mimeType']
                if not all(key in item for key in required_keys):
                    print(f"Skipping item with incomplete metadata (missing ID, Name, or MimeType): {item}")
                    continue

                file_id = item['id']
                file_name = item['name']
                mime_type = item['mimeType']
                
                print(f"Downloading file from Drive: {file_name} (MIME Type: {mime_type})")

                if 'application/vnd.google-apps' in mime_type:
                    if 'document' in mime_type:
                        request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
                    elif 'spreadsheet' in mime_type:
                        request = service.files().export_media(fileId=file_id, mimeType='text/csv')
                    elif 'presentation' in mime_type:
                        request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
                    else:
                        print(f"Google Apps type not supported for export: {file_name} (MIME Type: {mime_type})")
                        continue
                else:
                    request = service.files().get_media(fileId=file_id)

                file_content = BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"Downloading {file_name}: {int(status.progress() * 100)}%.")
                
                file_content.seek(0)

                base_name, _ = os.path.splitext(file_name)
                exported_extension = ""

                if 'application/vnd.google-apps.spreadsheet' in mime_type:
                    exported_extension = ".csv"
                elif 'application/vnd.google-apps.document' in mime_type or 'application/vnd.google-apps.presentation' in mime_type:
                    exported_extension = ".pdf"
                elif 'application/pdf' in mime_type:
                    exported_extension = ".pdf"
                elif 'text/plain' in mime_type:
                    exported_extension = ".txt"
                elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in mime_type:
                    exported_extension = ".docx"
                elif 'text/csv' in mime_type:
                    exported_extension = ".csv"
                else:
                    print(f"File type not supported for processing: {file_name} (MIME Type: {mime_type}). Skipping.")
                    continue

                temp_filepath = os.path.join('/tmp', base_name + exported_extension)

                try:
                    with open(temp_filepath, "wb") as f:
                        f.write(file_content.read())

                    doc_loader = None
                    
                    if temp_filepath.lower().endswith(".pdf"):
                        doc_loader = PyPDFLoader(temp_filepath)
                    elif temp_filepath.lower().endswith(".txt") or temp_filepath.lower().endswith(".csv"):
                        doc_loader = TextLoader(temp_filepath)
                    elif temp_filepath.lower().endswith(".docx"):
                        doc_loader = Docx2txtLoader(temp_filepath)
                    else:
                        print(f"No LangChain Loader found for temporary file: {temp_filepath}. Skipping.")
                        continue
                    
                    if doc_loader:
                        docs = doc_loader.load()
                        drive_documents.extend(docs)
                        print(f"Successfully loaded {len(docs)} pages/parts from {file_name}.")

                except Exception as inner_e:
                    print(f"Failed to process document {file_name} after download: {inner_e}")
                finally:
                    if temp_filepath and os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                
            except HttpError as http_err:
                print(f"Google Drive API HTTP error for file {file_name if 'name' in locals() else 'Unknown'}: {http_err}")
                print(f"Problematic item details: {item}")
                continue
            except Exception as e:
                print(f"General error processing file {file_name if 'name' in locals() else 'Unknown'} from Drive: {e}")
                print(f"Problematic item details: {item}")
                continue
            finally:
                if temp_filepath and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)

        return drive_documents

    except HttpError as error:
        print(f'Google Drive API error during file listing: {error}')
        print(f"Ensure your GOOGLE_DRIVE_QA_FOLDER_ID is correct and you have access permissions.")
        return []
    except Exception as e:
        print(f"General error during file listing from Drive: {e}")
        return []
