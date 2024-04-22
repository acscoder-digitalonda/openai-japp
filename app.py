 
from openai import OpenAI
import streamlit as st
import pandas as pd 
import serpapi

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]  
SERP_API_KEY = st.secrets["SERP_API_KEY"]  

model_name = "gpt-4-turbo-preview"
def send_llm(prompt,data):
    last_prompt = st.session_state.the_last_prompt
    last_reply = st.session_state.the_last_reply
    
    system_prompting = "You are a helpful assistant."
    system_prompting += "Based on the documents provided below, please complete the task requested by the user:" 
    system_prompting += "\n\n"
    system_prompting += data
        
    client = OpenAI(
        api_key=OPENAI_API_KEY,
    )
    our_sms = []
    our_sms.append({"role": "system", "content": system_prompting })
    if last_prompt != "":
        our_sms.append( {"role": "user", "content": last_prompt})
    if last_reply != "":
        our_sms.append( {"role": "assistant", "content": last_reply})
    our_sms.append( {"role": "user", "content": prompt})
    chat_completion = client.chat.completions.create(
        messages=our_sms,
        model=model_name,
    )
    return chat_completion.choices[0].message

 
def fetch_serpapi_results(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY  
    }
    search = serpapi.search(params)
    results = search.get_dict()
    
    # Extracting the organic results
    organic_results = results.get("organic_results", [])
    organic_text = ""
    for result in organic_results:
        title = result['title']
        snippet = result.get('snippet', '')
        
        # Extract rating and price information from rich_snippet
        rich_snippet = result.get('rich_snippet', {})
        top_info = rich_snippet.get('top', {})
        detected_extensions = top_info.get('detected_extensions', {})
        rating = detected_extensions.get('rating')
        price_range_from = detected_extensions.get('price_range_from')
        
        # Add rating and price information to the organic text if available
        if rating:
            organic_text += f"Rating: {rating}\n"
        if price_range_from:
            organic_text += f"Price range: from ${price_range_from}\n"
            
        organic_text += f"{title}: {snippet}\n\n"
        
    # Extracting the answer box or the desired snippet from organic results
    answer_text = ""
    answer_box = results.get("answer_box", {})
    if answer_box:
        answer_text = answer_box.get("answer", "")
    if not answer_text:
        # If the answer box doesn't have an "answer" key, 
        # look for the desired snippet in organic results.
        for result in organic_results:
            if 'organic_result' in result.get('type', ''):
                answer_text = result.get('snippet', '')
                break
            
    # If still no answer text, extract the snippet from the answer_box
    if not answer_text and answer_box:
        answer_text = answer_box.get('snippet', '')
        
    # Combining the organic text and answer box text
    text = f"{answer_text}\n{organic_text}"
    return text 
 
with st.sidebar:
  st.subheader("Upload Your CSV file")
  uploaded_file = st.file_uploader("Upload Your Document", type=["csv"])
  submit_button = st.button("Upload Document")
  

  if not "uploaded_document" in st.session_state:
        st.session_state.uploaded_document = ""

  uploaded_document = st.session_state.uploaded_document
 
  if not "the_last_reply" in st.session_state:
    st.session_state.the_last_reply = ""
  if not "the_last_prompt" in st.session_state:
    st.session_state.the_last_prompt = ""

  if uploaded_file is not None:
   df = pd.read_csv(uploaded_file)
   st.session_state.uploaded_document = df.to_csv(index=False)  
  
#your_prompt = st.text_area("Enter your Prompt:" ) 
your_prompt = st.chat_input ("Enter your Prompt:" ) 
#submit_llm = st.button("Send")
if your_prompt:
    st.session_state.the_last_prompt = your_prompt
    response = send_llm(your_prompt,uploaded_document)
    st.session_state.the_last_reply = response.content
    st.write(response.content)
     