import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import time

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain

# ✅ Secure API Key Handling
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🚨 API key missing! Please add `GEMINI_API_KEY` in Streamlit secrets.")
    st.stop()

# ✅ Configure Gemini Pro API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 🎨 Streamlit UI
st.title("⚖️ AI-Powered Legal Assistant")
st.subheader("🔍 Get legal insights based on Indian Laws")

query = st.text_input("Enter your legal question:")

# 🔍 Function to scrape Indian Kanoon for legal cases
def scrape_legal_cases(search_query, num_pages=1):
    base_url = "https://www.indiankanoon.org/search/?formInput="
    cases = []
    
    for page in range(num_pages):
        url = f"{base_url}{search_query}&pagenum={page+1}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            continue
        
        soup = BeautifulSoup(response.text, "html.parser")
        case_links = soup.select("div.result_title a")

        for link in case_links:
            case_url = "https://www.indiankanoon.org" + link["href"]
            case_details = scrape_case_details(case_url)
            if case_details:
                cases.append(case_details)
            
        time.sleep(2)  

    return cases

# 🔍 Extract case details
def scrape_case_details(case_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(case_url, headers=headers)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    case_title = soup.find("h1").text.strip() if soup.find("h1") else "Unknown Title"
    judgment_text = soup.find("div", {"id": "judgments"}).text.strip() if soup.find("div", {"id": "judgments"}) else "No Text Available"
    
    acts_sections = [act.text.strip() for act in soup.select(".docsource a")]

    return {
        "Title": case_title,
        "URL": case_url,
        "Acts_Sections": ", ".join(acts_sections),
        "Judgment": judgment_text[:1000]  # Limit text size
    }

# 🔍 Process cases with LangChain
def process_with_langchain(cases_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    
    all_documents = []
    for case in cases_data:
        chunks = text_splitter.split_text(case["Judgment"])
        all_documents.extend(chunks)

    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(all_documents, embeddings)

    return vector_store

# 🔍 Use Gemini Pro for answering
def get_gemini_response(query, case_texts):
    full_prompt = f"Legal Question: {query}\n\nRelevant Cases:\n" + "\n".join(case_texts)
    
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(full_prompt)
    
    return response.text

# 🔍 Fetch and Process Data
if query:
    st.write("🔎 Searching legal references... Please wait.")
    
    search_term = query  
    cases_data = scrape_legal_cases(search_term, num_pages=2)
    
    if not cases_data:
        st.error("❌ No relevant legal cases found. Try a different query.")
    else:
        vector_store = process_with_langchain(cases_data)
        
        retriever = vector_store.as_retriever()
        docs = retriever.get_relevant_documents(query)

        case_texts = [case["Judgment"] for case in cases_data[:3]]  # Limit to top 3 cases
        answer = get_gemini_response(query, case_texts)

        # 🎯 Display Result
        st.success("✅ AI Legal Response:")
        st.write(answer)

        # 📜 Show Relevant Cases
        st.subheader("📜 Relevant Legal Cases:")
        for case in cases_data[:3]:
            st.write(f"**{case['Title']}**")
            st.write(f"🔗 [Read Full Case]({case['URL']})")
            st.write(f"📖 **Acts & Sections:** {case['Acts_Sections']}")
            st.write("---")
