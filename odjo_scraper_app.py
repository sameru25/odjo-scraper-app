import streamlit as st
from playwright.sync_api import sync_playwright
import re
import phonenumbers
import openai

# OpenAI API Key
openai.api_key = "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"  # Replace with your OpenAI API key

# Function to clean and validate phone numbers
def clean_phone_numbers(phone_numbers):
    valid_numbers = []
    for number in phone_numbers:
        try:
            parsed_number = phonenumbers.parse(number, "GB")  # Default to UK region
            if phonenumbers.is_valid_number(parsed_number):
                valid_numbers.append(phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        except phonenumbers.NumberParseException:
            continue
    return valid_numbers

# Function to analyze tone of voice using GPT
def analyze_tone(text):
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

# Function to scrape website for contact details and tone
def scrape_dynamic_site(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")

            # Extract visible content
            page_content = page.inner_text('body')

            # Extract phone numbers and emails
            phone_numbers = re.findall(
                r'\+?\d{1,3}?[-.\s()]*(\d{2,4})[-.\s()]*(\d{2,4})[-.\s()]*(\d{2,4})',
                page_content
            )
            email_addresses = re.findall(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                page_content
            )

            # Flatten and join phone number parts
            phone_numbers = ["".join(parts) for parts in phone_numbers]
            valid_numbers = clean_phone_numbers(phone_numbers)

            # Extract tone of voice from text (use first 500 characters)
            sample_text = page_content[:500]
            tone = analyze_tone(sample_text)

            browser.close()
            return {
                "emails": list(set(email_addresses)),
                "phone_numbers": valid_numbers,
                "tone_of_voice": tone
            }
    except Exception as e:
        return {"error": str(e)}

# Streamlit App
st.title("ODJO Freelancer Assistant")

# Step 1: Scrape or Enter Text
st.header("Step 1: Analyze Freelancer Content")

# Option to provide URL or enter text
input_option = st.radio("Choose an input method:", ["Enter a URL", "Manually enter text"])

scraped_data = {}
if input_option == "Enter a URL":
    url = st.text_input("Enter the portfolio website URL to scrape:", "")
    if url:
        st.write(f"Scraping data from {url}...")
        scraped_data = scrape_dynamic_site(url)

        if scraped_data and "error" in scraped_data:
            st.error(f"Error: {scraped_data['error']}")
        elif scraped_data:
            st.write("### Emails Found:")
            st.write(scraped_data["emails"])

            st.write("### Phone Numbers Found:")
            st.write(scraped_data["phone_numbers"])

            st.write("### Detected Tone of Voice:")
            st.write(scraped_data["tone_of_voice"])

else:
    manual_text = st.text_area("Enter text to analyze tone of voice:", "")
    if manual_text:
        detected_tone = analyze_tone(manual_text)
        st.write("### Detected Tone of Voice:")
        st.write(detected_tone)
        scraped_data["tone_of_voice"] = detected_tone

# Step 2: Generate Personalized Emails
st.header("Step 2: Generate Personalized Emails")

if "tone_of_voice" in scraped_data:
    detected_tone = scraped_data["tone_of_voice"]
else:
    detected_tone = "professional"  # Default fallback tone

service = st.text_input("Describe your service (e.g., 'I am a photographer specializing in weddings')", "")
audience = st.text_input("Who is your target audience? (e.g., 'event planners, couples')", "")
unique_value = st.text_input("What makes your service unique? (e.g., 'My style is candid and creative')", "")

if st.button("Generate Emails"):
    if service and audience and unique_value:
        try:
            # Generate three emails using GPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert email writer."},
                    {"role": "user", "content": (
                        f"Write three {detected_tone} emails for a {service}. "
                        f"The target audience is {audience}. Highlight their unique value: {unique_value}. "
                        f"The emails should include: 1) An introductory email, 2) A follow-up email, "
                        f"and 3) A final outreach email."
                    )}
                ],
                max_tokens=600
            )
            emails = response.choices[0].message["content"].strip()
            st.subheader("Generated Emails:")
            st.write(emails)
        except Exception as e:
            st.error(f"Error generating emails: {str(e)}")
    else:
        st.warning("Please fill in all fields to generate emails.")
