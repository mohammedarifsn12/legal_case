import streamlit as st
import pandas as pd
import google.generativeai as genai



def load_dataset():
    try:
        df = pd.read_csv(datafile.csv)  # Change to read_excel if it's an Excel file
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return None

# Gemini AI Setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_gemini_response(query):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(query)
    return response.text

# Streamlit UI
st.title("⚖️ AI-Powered Legal Assistant")
st.subheader("🔍 Get legal insights based on Indian Laws")

query = st.text_input("Enter your legal question:")

df = load_dataset()

if query:
    if df is not None:
        # Search dataset for relevant cases
        results = df[df.apply(lambda row: query.lower() in str(row).lower(), axis=1)]
        if not results.empty:
            st.success("✅ Relevant cases found in the dataset:")
            st.write(results)
        else:
            st.warning("No relevant cases found in the dataset. Fetching response from AI...")
            answer = get_gemini_response(query)
            st.success("✅ AI Legal Response:")
            st.write(answer)
    else:
        st.warning("Dataset not found. Using AI for legal response...")
        answer = get_gemini_response(query)
        st.success("✅ AI Legal Response:")
        st.write(answer)



