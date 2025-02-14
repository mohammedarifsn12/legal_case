import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import time

# Configure Gemini API Key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

st.title("⚖️ AI-Powered Legal Assistant")
st.subheader("🔍 Get legal insights based on Indian Laws")
query = st.text_input("Enter your legal question:")

# Function to scrape legal cases from multiple sources
def scrape_legal_cases(search_query):
    cases = []
    
    # Scrape Indian Kanoon
    url = f"https://www.indiankanoon.org/search/?formInput={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        case_links = soup.select("div.result_title a")
        for link in case_links[:3]:
            case_url = "https://www.indiankanoon.org" + link["href"]
            cases.append({"Title": link.text, "URL": case_url})
    
    # Scrape CommonLII
    commonlii_url = f"http://www.commonlii.org/cgi-bin/sinosrch.cgi?query={search_query}&results=3"
    response = requests.get(commonlii_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True)[:3]:
            cases.append({"Title": link.text, "URL": "http://www.commonlii.org" + link["href"]})
    
    return cases

# Function to get AI-generated legal response
def get_gemini_response(query, cases):
    case_texts = "\n".join([f"- {case['Title']} ({case['URL']})" for case in cases])
    prompt = f"""
    Legal Question: {query}
    Relevant Cases:
    {case_texts}
    
    Provide a legal response based on Indian laws, including relevant acts and possible legal actions.
    """
    
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

if query:
    st.write("🔎 Searching legal references... Please wait.")
    cases = scrape_legal_cases(query)
    
    if not cases:
        st.error("❌ No relevant legal cases found. Try a different query.")
    else:
        answer = get_gemini_response(query, cases)
        st.success("✅ AI Legal Response:")
        st.write(answer)
        
        st.subheader("📜 Relevant Legal Cases:")
        for case in cases:
            st.write(f"**{case['Title']}**")
            st.write(f"🔗 [Read Full Case]({case['URL']})")
            st.write("---")
