import streamlit as st
from auth import show_login_page, show_registration_page
from chat import chat_interface
from utils import ensure_user_database_exists
from chat import ensure_user_database_exists

def main():
    ensure_user_database_exists()
    st.set_page_config(page_title="AgriBot", page_icon="🌾", layout="wide")

    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        # Apply background image for login and registration pages
        background_image_url = "https://ideogram.ai/api/images/direct/FnjrEUIXQUqCwRYC-BkEtg.png"
        background_style = f"""
        <style>
            .stApp {{
                background-image: url('{background_image_url}');
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
        </style>
        """
        st.markdown(background_style, unsafe_allow_html=True)

        # Login and registration interface
        page_container = st.empty()
        with page_container.container():
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                # Make sure to adjust the path to your logo image
                st.image("background/logo.png", width=100)

                st.markdown("""
                    <style>
                        .welcome-text, .option-text {
                            color: #000000; /* Black color */
                            background-color: rgba(255, 255, 255, 0.5); /* Translucent white background */
                            padding: 2px 5px; /* Reduced padding around the text */
                            border-radius: 5px; /* Rounded corners */
                            display: inline; /* Align highlight with text */
                            margin: 0; /* Remove default margins */
                        }
                        .welcome-text {
                            font-size:50px !important;
                            font-weight: bold !important;
                        }
                        .option-text {
                            font-size:28px !important;
                            font-weight: bold !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                st.markdown('<div class="welcome-text">Welcome to AgriBot 🌾</div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="option-text">Choose an option:</div>', unsafe_allow_html=True)
                
                form_selection = st.radio("", ["Register", "Login"], horizontal=True)

                if form_selection == "Register":
                    show_registration_page()
                elif form_selection == "Login":
                    show_login_page()
    else:
        # For the chat interface, no specific background
        # The CSS reset for background might not be effective once the app has loaded
        chat_interface()

if __name__ == "__main__":
    main()
