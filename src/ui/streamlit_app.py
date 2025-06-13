import streamlit as st
import os
import sys

# Adjusting project_root calculation to add the project's root directory to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import main functions from qa_bot.py
from src.qa_bot.qa_bot import initialize_qa_system, get_qa_response

# Streamlit page configuration must be the first Streamlit command
st.set_page_config(page_title="QA Bot Internal", page_icon="🤖")

try:
    # Initialize Model and Vector DB once for performance
    if 'qa_model_initialized' not in st.session_state:
        st.session_state['qa_model_initialized'] = False

    if not st.session_state['qa_model_initialized']:
        with st.spinner("Loading knowledge base and QA model (this may take time the first time)..."):
            try:
                initialize_qa_system() 
                st.session_state['qa_model_initialized'] = True
                st.success("Knowledge base and QA model loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load knowledge base and QA model: {e}")
                st.session_state['qa_model_initialized'] = False
                
except ImportError as ie:
    st.error(f"Import error: {ie}. Ensure folder structure is correct (e.g., 'src/qa_bot/qa_bot.py'). "
             f"Also ensure all LangChain dependencies are installed.")
    st.info("Try running `pip install -r requirements.txt` and ensure `__init__.py` exists in each sub-folder.")
except Exception as e:
    st.error(f"An unexpected error occurred during initialization: {e}")
    st.info("Check terminal logs for more details.")


st.title("🤖 QA Bot Internal")
st.caption("A smart assistant for your QA team.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages from chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask something about QA documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from QA bot
    with st.chat_message("assistant"):
        with st.spinner("Bot is thinking..."):
            if st.session_state['qa_model_initialized']:
                try:
                    response = get_qa_response(prompt) 
                    st.markdown(response)
                except Exception as e:
                    st.error(f"An error occurred while getting response: {e}")
                    response = "Sorry, an error occurred while processing your request. " \
                               "Please check the terminal logs for more details."
                    st.markdown(response)
            else:
                response = "Bot not successfully initialized. Please try again or check error logs."
                st.markdown(response)
        
        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
