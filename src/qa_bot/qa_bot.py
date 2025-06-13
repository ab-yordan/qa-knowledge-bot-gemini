import os
from dotenv import load_dotenv
import google.genai as genai 
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from langchain_community.document_loaders import PyPDFLoader, TextLoader 
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.qa_bot.drive_loader import load_documents_from_google_drive 
import sys # Added for sys.exit

# Global variables for the loaded QA bot object.
qa_chain_instance = None
global_qa_system_initialized = False

# Function to initialize the QA System (Load Documents, Models, etc.)
def initialize_qa_system():
    global qa_chain_instance, global_qa_system_initialized

    if global_qa_system_initialized:
        print("QA system already initialized. Skipping re-initialization.")
        return qa_chain_instance

    print("Starting QA system initialization...")

    # Load API Key from .env
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
    dotenv_path = os.path.join(project_root, 'config', '.env')

    load_dotenv(dotenv_path=dotenv_path) 
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file. Please ensure it is set.")
    print("API Key loaded successfully.")

    # Load Knowledge Documents
    GOOGLE_DRIVE_QA_FOLDER_ID = os.getenv("GOOGLE_DRIVE_QA_FOLDER_ID") 
    
    if not GOOGLE_DRIVE_QA_FOLDER_ID:
        raise ValueError("GOOGLE_DRIVE_QA_FOLDER_ID not found in .env file. "
                         "Please ensure it is set in your .env file.")

    documents = load_documents_from_google_drive(GOOGLE_DRIVE_QA_FOLDER_ID)

    if not documents:
        print("WARNING: No documents successfully loaded from Google Drive.")
        print("The bot may not be able to answer specific questions from your knowledge base.")
        qa_chain_instance = None
        global_qa_system_initialized = False
        raise RuntimeError("No documents successfully loaded from Google Drive.")
    else:
        print(f"Successfully loaded {len(documents)} documents from Google Drive.")

    # Split Documents into Chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200) 
    chunks = text_splitter.split_documents(documents)
    print(f"Documents split into {len(chunks)} chunks.")

    if not chunks:
        qa_chain_instance = None
        global_qa_system_initialized = False
        raise RuntimeError("Documents split into 0 chunks. Cannot create Vector DB.")

    # Create Embeddings & Store in Vector Database (FAISS)
    print("Creating embeddings and building Vector DB (this may take time depending on the number of documents)...")
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_documents(chunks, embeddings_model)
    print("Vector DB successfully created.")

    # Prepare Gemini Model and Prompt for the Bot
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2) 

    prompt = ChatPromptTemplate.from_template("""
You are a smart and helpful internal QA assistant, specifically for the QA team in the company.
Use only the provided context to answer the user's question.
If you don't know the answer based on the given context, simply say 'Sorry, I don't have specific information about that in my knowledge base.'
Provide concise, accurate, and to-the-point answers. Avoid information outside the context.

Context:
{context}

Question: {input}
""")

    # Build the Chain for the Bot (RAG concept at work here!)
    retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    document_chain = create_stuff_documents_chain(llm, prompt)
    qa_chain = create_retrieval_chain(retriever, document_chain)
    
    qa_chain_instance = qa_chain
    global_qa_system_initialized = True
    print("QA system successfully initialized.")
    return qa_chain_instance

# Function to get Response from the Bot (Called by Streamlit)
def get_qa_response(user_query: str):
    global qa_chain_instance

    if qa_chain_instance is None:
        print("QA system not initialized or failed to initialize. Attempting to re-initialize.")
        try:
            qa_chain_instance = initialize_qa_system()
            if qa_chain_instance is None: 
                return "Sorry, the QA system failed to initialize. Please check the server logs."
        except Exception as e:
            print(f"Error during re-initialization of QA system: {e}")
            return "Sorry, the QA system failed to initialize. Please check the server logs."

    try:
        response = qa_chain_instance.invoke({"input": user_query})
        return response['answer']
    except Exception as e:
        print(f"An error occurred while processing the question: {e}")
        if "API key" in str(e) or "network" in str(e).lower():
            return "Connection issue or invalid API key. Please try again later or check your configuration."
        return "An error occurred while processing the question. Please try again."

# Section for Direct Execution (If run as the main script)
# This section will NOT be executed when qa_bot.py is imported by streamlit_app.py
if __name__ == "__main__":
    print("\nRunning QA Bot in terminal mode. For UI, use 'streamlit run src/ui/streamlit_app.py'.")
    try:
        qa_chain_instance = initialize_qa_system()
        if qa_chain_instance is None:
            print("Failed to initialize QA bot. Exiting.")
            sys.exit(1)

        print("\nBot is ready. Type 'exit' to quit.")
        while True:
            user_input = input("\nYou (ask bot): ")
            if user_input.lower() == 'exit':
                print("Thank you for using QA Knowledge Bot!")
                break
            
            bot_response = get_qa_response(user_input)
            print(f"QA Bot: {bot_response}")

    except Exception as e:
        print(f"Fatal error during startup: {e}")
        print("Please ensure all dependencies are installed, API key is valid, and 'config' folder is correct.")

