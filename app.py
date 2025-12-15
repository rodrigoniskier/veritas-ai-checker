import streamlit as st
import os
from groq import Groq
from tavily import TavilyClient

# --- Page Config (Browser Tab) ---
st.set_page_config(
    page_title="Veritas AI",
    page_icon="🛡️",
    layout="centered", # Layout centralizado estilo ChatGPT
    initial_sidebar_state="collapsed"
)

# --- CSS: Modern SaaS / Chat Interface Styling ---
st.markdown("""
<style>
    /* Remove default Streamlit padding to look like an App */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
    
    /* Header Styling */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6); /* Blue/Purple Gradient */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    
    /* Subtitle Styling */
    .subtitle {
        text-align: center;
        color: #6B7280;
        font-family: 'Inter', sans-serif;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    /* Developer Credit Styling */
    .dev-credit {
        text-align: center;
        color: #9CA3AF;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        margin-bottom: 2.5rem;
    }
    
    /* Chat Message Styling */
    .stChatMessage {
        background-color: transparent;
        border: none;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- API Setup (Secrets) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except:
    st.error("⚠️ API Keys missing. Please configure .streamlit/secrets.toml")
    st.stop()

# Initialize Clients
client_groq = Groq(api_key=GROQ_API_KEY)
client_tavily = TavilyClient(api_key=TAVILY_API_KEY)

# --- System Prompt (The Brain) ---
SYSTEM_PROMPT = """
You are Veritas AI, an elite informational integrity agent. 
Your purpose is to validate user claims against real-time web data and prevent hallucinations.

PROTOCOL:
1. SEARCH FIRST: Always rely on the provided search context. Do not use internal knowledge if it conflicts with fresh data.
2. VERIFY: Explicitly state if the user's claim is True, False, Misleading, or Unverified.
3. CITE SOURCES: Every fact must be backed by a link from the search results. Use markdown format: [Source Name](URL).
4. TONE: Professional, objective, and concise. Like a Bloomberg terminal analyst.
5. NO FLUFF: Go straight to the point.

STRUCTURE YOUR RESPONSE:
**Verdict:** [TRUE / FALSE / PARTIALLY TRUE]
**Analysis:** [Your synthesized findings]
**Verified Sources:** [List of valid links]
"""

# --- Session State (Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Header UI ---
st.markdown("<h1>Veritas AI</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time Truth Engine powered by Llama 3.3 & Tavily</p>', unsafe_allow_html=True)

# ASSINATURA DO DESENVOLVEDOR (BRANDING)
st.markdown('<div class="dev-credit">Engineered by <strong>Rodrigo Niskier</strong> | Integrity Protocol v2.0</div>', unsafe_allow_html=True)

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Logic (The Core) ---
if prompt := st.chat_input("Enter a claim to verify or a topic to investigate..."):
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI Processing
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Analyzing web data..."):
            try:
                # A. Search Step (The Eyes)
                # Faz a busca para pegar fatos reais
                search_result = client_tavily.search(query=prompt, search_depth="advanced")
                
                # Formata os resultados para a IA ler
                search_context = "\n".join([f"- {res['content']} (URL: {res['url']})" for res in search_result['results']])
                
                # B. Reasoning Step (The Brain)
                # Prepara o histórico da conversa + Prompt do Sistema
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ]
                
                # Adiciona as últimas 5 mensagens para manter o contexto sem estourar o limite
                for m in st.session_state.messages[-5:]:
                    messages.append({"role": m["role"], "content": m["content"]})
                
                # Injeta os dados da busca APENAS na última mensagem (a atual)
                messages[-1]["content"] = f"USER QUERY: {prompt}\n\nREAL-TIME SEARCH DATA: {search_context}"

                # Chama a Groq com o Modelo Atualizado (Llama 3.3)
                completion = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile", 
                    messages=messages,
                    temperature=0.3, # Baixa temperatura para ser mais factual
                    stream=True 
                )
                
                # C. Streaming Response (Efeito visual de digitação)
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                # Finaliza removendo o cursor
                message_placeholder.markdown(full_response)
                
                # Salva na memória
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"System Error: {str(e)}")