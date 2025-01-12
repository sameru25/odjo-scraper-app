import streamlit as st
from playwright.sync_api import sync_playwright
import re
import openai
import streamlit as st
from playwright.sync_api import sync_playwright
import re
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to scrape emails from a URL
def scrape_emails_from_url(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")

            # Extract emails from page content
            page_content = page.inner_text('body')
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_content)

            browser.close()
            return list(set(emails))  # Remove duplicates
    except Exception as e:
        return {"error": str(e)}

# Function to analyze text tone using GPT
def analyze_tone_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in tone analysis."},
                {"role": "user", "content": f"Analyze the tone of this text: {text}"}
            ],
            max_tokens=100
        )
        tone = response.choices[0].message["content"].strip()
        return tone
    except Exception as e:
        return f"Error analyzing tone: {str(e)}"

# Function to generate personalized emails using GPT
def generate_emails_with_gpt(username, service, audience, unique_value, tone="professional"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert email writer."},
                {"role": "user", "content": (
                    f"Write three {tone} emails for a {service}. "
                    f"The target audience is {audience}. Highlight their unique value: {unique_value}. "
                    f"The emails should be signed off from {username}. "
                    f"The emails should include: 1) An introductory email, 2) A follow-up email, "
                    f"and 3) A final outreach email."
                )}
            ],
            max_tokens=600
        )
        emails = response.choices[0].message["content"].strip()
        return emails
    except Exception as e:
        return f"Error generating emails: {str(e)}"

# Streamlit App
st.title("ODJO AI - Personalized Steps")

# Initialize session state for step tracking and username
if "step" not in st.session_state:
    st.session_state["step"] = 1  # Start at Step 1
if "username" not in st.session_state:
    st.session_state["username"] = ""

# Total number of steps
total_steps = 4

# Progress bar
progress = st.progress(st.session_state["step"] / total_steps)
# Step 1: Collect Name and Optional Analysis
if st.session_state["step"] == 1:
    st.header("Step 1: Tell Us About You")
    st.session_state["username"] = st.text_input("What is your name?", st.session_state["username"])

    if st.session_state["username"]:
        st.write(f"Welcome, {st.session_state['username']}! Let's get started.")
    else:
        st.warning("Please enter your name to proceed.")

    analysis_choice = st.radio("Choose an option:", ["Analyze Website", "Enter Text for Tone Analysis", "Skip"])
    if analysis_choice == "Analyze Website":
        url = st.text_input("Enter a website URL to analyze:", "")
        if st.button("Analyze Website"):
            if url:
                st.write(f"Scraping data from {url}...")
                emails = scrape_emails_from_url(url)

                if "error" in emails:
                    st.error(f"Error: {emails['error']}")
                elif emails:
                    st.write("### Emails Found:")
                    st.write(emails)
                    if len(emails) > 0:
                        sample_text = emails[0]  # Using first email for tone analysis
                        tone = analyze_tone_with_gpt(sample_text)
                        st.write("### Detected Tone of Text:")
                        st.write(tone)
                else:
                    st.write("No emails found on this website.")
    elif analysis_choice == "Enter Text for Tone Analysis":
        manual_text = st.text_area("Enter text to analyze its tone:", "")
        if st.button("Analyze Text Tone"):
            if manual_text:
                tone = analyze_tone_with_gpt(manual_text)
                st.write("### Detected Tone of Text:")
                st.write(tone)
            else:
                st.warning("Please enter some text to analyze.")
    else:
        st.write("Skipping this step.")

    if st.button("Proceed to Step 2"):
        if st.session_state["username"]:
            st.session_state["step"] = 2
            # No need for rerun; Streamlit will refresh automatically
        else:
            st.warning("Please enter your name to proceed.")

# Step 2: Define Service and Audience
if st.session_state["step"] == 2:
    st.header(f"Step 2: Define Your Service and Audience, {st.session_state['username']}")
    service = st.text_input("Describe your service (e.g., 'I am a photographer specializing in weddings')", "")
    audience = st.text_input("Who is your target audience? (e.g., 'event planners, couples')", "")
    unique_value = st.text_input("What makes your service unique? (e.g., 'My style is candid and creative')", "")
    tone = st.text_input("What tone would you like for your emails? (e.g., 'professional', 'friendly')", "professional")

    if st.button("Proceed to Step 3"):
        if service and audience and unique_value:
            st.session_state["service"] = service
            st.session_state["audience"] = audience
            st.session_state["unique_value"] = unique_value
            st.session_state["tone"] = tone
            st.session_state["step"] = 3
        else:
            st.warning(f"Please fill in all fields to proceed, {st.session_state['username']}.")


# Step 3: Generate Personalized Emails
if st.session_state["step"] == 3:
    st.header(f"Step 3: Generate Personalised Emails for {st.session_state['username']}")
    if st.button("Generate Emails"):
        emails = generate_emails_with_gpt(
            st.session_state["username"],
            st.session_state["service"],
            st.session_state["audience"],
            st.session_state["unique_value"],
            st.session_state["tone"]
        )
        st.subheader("Generated Emails:")
        st.write(emails)

    if st.button("Proceed to Step 4"):
        st.session_state["step"] = 4
        st.experimental_rerun()

# Step 4: Find ICPs with Emails
if st.session_state["step"] == 4:
    st.header(f"Step 4: Find Ideal Customer Profiles (ICPs) with Emails for {st.session_state['username']}")
    service_keywords = st.session_state["service"].replace(" ", "+")
    audience_keywords = st.session_state["audience"].replace(" ", "+")
    if st.button("Find ICP Emails"):
        st.write("Searching for ICPs... (This may take a moment)")
        # Here you would use your ICP scraping logic
        # Placeholder ICP result
        icps = [
            {"name": "Example Business", "url": "https://example.com", "emails": ["contact@example.com"]}
        ]
        st.subheader("Top ICPs:")
        for idx, icp in enumerate(icps, 1):
            st.write(f"### #{idx}: {icp['name']}")
            st.write(f"URL: [{icp['url']}]({icp['url']})")
            st.write(f"Emails: {', '.join(icp['emails']) if icp['emails'] else 'No emails found'}")

# Update progress bar
progress.progress(st.session_state["step"] / total_steps)
