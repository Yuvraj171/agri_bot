background_image_url = "https://ideogram.ai/api/images/direct/FnjrEUIXQUqCwRYC-BkEtg.png"

chat_message_styles = f"""
<style>
    .stApp {{
        background-image: url({background_image_url});
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Custom styles for radio buttons to make them bolder and bigger */
    .stRadio > div > label {{
        font-size: 25px; /* Increase font size */
        font-weight: bold; /* Make font bolder */
    }}

    /* Enhanced visibility for headings */
    .stHeader, .stSubheader {{
        color: #ffffff; /* White text for better contrast */
        background-color: #007BFF; /* Example background color */
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
    }}

    /* Ensure text fields are easily readable */
    .stTextInput > div > div > input, .stPassword > div > div > input {{
        background-color: rgba(255, 255, 255, 1) !important; /* Ensure white background */
        color: #000; /* Text color */
        border-radius: 4px;
        border: 1px solid #ced4da;
        padding: 10px;
    }}

    .login-highlight, .registration-highlight {{
        font-size: 24px !important;
        font-weight: bold !important;
        color: #000000; /* Black color */
        background-color: rgba(255, 255, 255, 0.5); /* Translucent white background */
        padding: 5px 10px;
        border-radius: 5px;
        margin: 10px 0;
        display: inline-block;
    }}

    /* Custom style to ensure prompt box is white */
    /* If your app still shows a green box, it might be necessary to inspect the element
       and identify the specific CSS class or ID that requires overriding */
</style>
"""

welcome_styles = """
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
"""