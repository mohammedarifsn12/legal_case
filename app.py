import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import time

# Configure Gemini Pro API Key
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Streamlit UI
st.title("⚖️ AI-Powered Legal Assistant")
st.subheader("🔍 Get legal insights based on Indian Laws")

query = st.text_input("Enter your legal question:")

# Function to scrape Indian Kanoon
def scrape_indiankanoon(search_query, num_pages=1):
    base_url = "https://www.indiankanoon.org/search/?formInput="
    cases = []
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    for page in range(num_pages):
        url = f"{base_url}{search_query}&pagenum={page+1}"
        
        try:
            response = session.get(url, headers=headers, timeout=10)
            if response.status_code == 403:
                print("Indian Kanoon blocked the request. Skipping...")
                return []

            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            case_links = soup.select("div.result_title a")

            for link in case_links[:3]:  
                case_url = "https://www.indiankanoon.org" + link["href"]
                case_details = scrape_case_details(case_url)
                if case_details:
                    cases.append(case_details)
            
            time.sleep(2)  
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Indian Kanoon: {e}")
    
    return cases

# Function to scrape CommonLII
def scrape_commonlii(search_query):
    base_url = "http://www.commonlii.org/cgi-bin/sinosrch.cgi"
    params = {"query": search_query, "results": 3}
    headers = {"User-Agent": "Mozilla/5.0"}

    cases = []
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            print("CommonLII is unavailable. Skipping...")
            return []

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        case_links = soup.select("a")

        for link in case_links[:3]:
            cases.append({"Title": link.text.strip(), "URL": base_url + link["href"]})
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from CommonLII: {e}")
    
    return cases

# Extract case details
def scrape_case_details(case_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(case_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        case_title = soup.find("h1").text.strip() if soup.find("h1") else "Unknown Title"
        judgment_text = soup.find("div", {"id": "judgments"})
        
        if judgment_text:
            judgment_text = judgment_text.text.strip()[:1000]
        else:
            judgment_text = "Judgment not available"
        
        acts_sections = [act.text.strip() for act in soup.select(".docsource a")]

        return {"Title": case_title, "URL": case_url, "Acts_Sections": ", ".join(acts_sections), "Judgment": judgment_text}
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching case details: {e}")
        return None

# Use Gemini Pro API for answering
def get_gemini_response(query, case_texts):
    full_prompt = f"Legal Question: {query}\n\nRelevant Cases:\n" + "\n".join(case_texts)
    
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(full_prompt)
    
    return response.text

# Fetch and Process Data
if query:
    st.write("🔎 Searching legal references... Please wait.")
    
    # Fetch cases from multiple sources
    cases_data = []
    cases_data.extend(scrape_indiankanoon(query, num_pages=2))
    cases_data.extend(scrape_commonlii(query))

    if not cases_data:
        st.warning("No legal cases found. Using Gemini AI for an answer.")
        answer = get_gemini_response(query, ["No relevant case data found."])
    else:
        # Limit to top 3 case texts
        case_texts = [case.get("Judgment", "No judgment available") for case in cases_data[:3]]

        # Get AI-powered legal response
        answer = get_gemini_response(query, case_texts)

    # Display AI Response
    st.success("✅ AI Legal Response:")
    st.write(answer)

    # Show Relevant Cases
    if cases_data:
        st.subheader("📜 Relevant Legal Cases:")
        for case in cases_data[:3]:
            st.write(f"**{case['Title']}**")
            st.write(f"🔗 [Read Full Case]({case['URL']})")
            st.write(f"📖 **Acts & Sections:** {case.get('Acts_Sections', 'N/A')}")
            st.write("---")


