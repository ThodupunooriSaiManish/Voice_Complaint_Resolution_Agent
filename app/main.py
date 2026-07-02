import time
import os
import streamlit as st
import numpy as np
import pandas as pd

from app.config import settings
from app.database import db
from app.services.stt import stt_service
from app.services.tts import tts_service
from app.subagents import check_ollama_status
from app.subagents.manager import agent_manager

# Set up page configurations
st.set_page_config(
    page_title="Voice Complaint Agent Console",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Dark glassmorphic theme styling */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #1e1b4b 0%, #090514 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Title and logo styling */
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        background: linear-gradient(to right, #a5b4fc, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(25, 20, 48, 0.45);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 1.5rem;
    }
    
    .glass-card-header {
        font-family: 'Outfit', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding-bottom: 0.5rem;
    }

    /* Badges */
    .badge {
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    
    .badge-p0 { background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #fca5a5; }
    .badge-p1 { background: rgba(249, 115, 22, 0.2); border: 1px solid #f97316; color: #ffedd5; }
    .badge-p2 { background: rgba(234, 179, 8, 0.2); border: 1px solid #eab308; color: #fef9c3; }
    .badge-p3 { background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #d1fae5; }
    
    /* Grid cells for active ticket */
    .ticket-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    
    .ticket-cell {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 0.75rem 1rem;
    }
    
    .ticket-lbl {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.25rem;
        font-weight: 600;
    }
    
    .ticket-val {
        color: #e2e8f0;
        font-size: 0.95rem;
    }
    
    /* Plan list styling */
    .plan-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        font-size: 0.9rem;
        margin-bottom: 0.4rem;
        color: #e2e8f0;
    }
    
    .plan-item-icon {
        color: #6366f1;
        margin-top: 0.2rem;
    }
    
    /* Sidebar adjustments */
    [data-testid="stSidebar"] {
        background: rgba(13, 9, 29, 0.9) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: ENGINE STATUS & STATS -----------------
with st.sidebar:
    st.markdown('<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;"><div style="background: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%); width: 35px; height: 35px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; color: white;"><i class="fa-solid fa-microphone-lines">🎙️</i></div><h3 style="font-family:\'Outfit\'; font-weight:800; color:white; margin:0; font-size:1.25rem;">Voice AI Console</h3></div>', unsafe_allow_html=True)
    
    st.markdown("### 📊 Live Analytics")
    
    # Fetch current tickets for metrics
    tickets = db.get_all_tickets()
    total_tickets = len(tickets)
    p0_tickets = len([t for t in tickets if t.get("priority") == "P0"])
    p1_tickets = len([t for t in tickets if t.get("priority") == "P1"])
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric(label="Total Tickets", value=total_tickets)
    with col_stat2:
        st.metric(label="P0/P1 Urgencies", value=f"{p0_tickets + p1_tickets}")
        
    critical_ratio = round((p0_tickets / total_tickets * 100)) if total_tickets > 0 else 0
    st.progress(critical_ratio / 100, text=f"Critical Ratio: {critical_ratio}%")
    
    st.markdown("---")
    
    st.markdown("### 🔌 Core Engines")
    # Check Ollama
    ollama_reachable = check_ollama_status()
    ollama_icon = "🟢 Connected" if ollama_reachable else "🟡 Fallback Mode"
    db_icon = "🟢 MongoDB" if not db.use_fallback else "🟡 JSON File Fallback"
    
    st.markdown(f"**LLM Model:** {settings.OLLAMA_MODEL} ({ollama_icon})")
    st.markdown(f"**Database:** {db_icon}")
    st.markdown("**VAD Engine:** Silero / RMS Threshold")
    st.markdown("**STT Engine:** Faster-Whisper / Google API")
    st.markdown("**TTS Engine:** gTTS / SAPI5 Native")

# ----------------- MAIN LAYOUT -----------------
st.markdown('<h1 class="main-title">🎙️ Voice Complaint Agent Console</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Multi-Agent system automating voice complaint extraction, analysis, and ticket planning</p>', unsafe_allow_html=True)

col_input, col_ticket = st.columns([1, 1.2])

# Processed Ticket state storage
if "active_ticket" not in st.session_state:
    st.session_state.active_ticket = None
if "active_audio" not in st.session_state:
    st.session_state.active_audio = None

# Callback trigger to process transcript
def run_agent_workflow(transcript_text: str):
    if not transcript_text.strip():
        return
        
    with st.status("🚀 Orchestrating Agent System...", expanded=True) as status:
        # Step 1: Speech-To-Text completed
        status.update(label="🎙️ Speech segment transcribed successfully.", state="running")
        time.sleep(0.5)
        
        # Step 2: Extractor Agent
        status.update(label="🔍 Agent 1 (Extractor) parsing customer name, contact & product details...", state="running")
        time.sleep(0.6)
        
        # Step 3: Analyzer Agent
        status.update(label="📊 Agent 2 (Analyzer) assessing emotional sentiment & severity priority...", state="running")
        time.sleep(0.5)
        
        # Step 4: Planner Agent
        status.update(label="📋 Agent 3 (Planner) generating resolution plan & empathetic audio script...", state="running")
        
        # Call agent manager to process
        ticket = agent_manager.process_transcript(transcript_text)
        
        # Step 5: Synthesize TTS
        status.update(label="🔊 Synthesizing spoken audio response...", state="running")
        audio_bytes = tts_service.synthesize(ticket["customer_response"])
        
        status.update(label="✅ Workflow complete! Ticket logged.", state="complete")
        
    st.session_state.active_ticket = ticket
    st.session_state.active_audio = audio_bytes
    st.rerun()

# ----------------- LEFT COLUMN: INPUT CHANNELS -----------------
with col_input:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="glass-card-header">📥 Complaint Intake Channels</div>', unsafe_allow_html=True)
    
    input_tab1, input_tab2, input_tab3 = st.tabs(["🎙️ Voice Recorder", "📂 Upload Audio File", "✍️ Manual Text"])
    
    # 1. Native Voice Recorder
    with input_tab1:
        st.write("Record your complaint directly using your browser's microphone:")
        # Native Streamlit audio input widget (v1.34+)
        audio_inp = st.audio_input("Record Voice Message")
        if audio_inp is not None:
            audio_bytes = audio_inp.read()
            if st.button("Analyze Recorded Voice", type="primary", key="btn_rec_analyze"):
                with st.spinner("Transcribing recording..."):
                    transcript = stt_service.transcribe_file(audio_bytes)
                run_agent_workflow(transcript)
                
    # 2. Audio File Uploader
    with input_tab2:
        st.write("Upload a pre-recorded audio statement:")
        uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a", "ogg"])
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            if st.button("Transcribe & Analyze File", type="primary", key="btn_file_analyze"):
                with st.spinner("Transcribing audio file..."):
                    transcript = stt_service.transcribe_file(file_bytes)
                run_agent_workflow(transcript)
                
    # 3. Manual Text Input Override
    with input_tab3:
        st.write("Input a manual text complaint transcript:")
        manual_text = st.text_area("Transcript text", placeholder="e.g. My name is Mark, I bought a toaster model T100 and it burned my bread today.")
        if st.button("Process Complaint Text", type="primary", key="btn_text_analyze"):
            run_agent_workflow(manual_text)
            
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- RIGHT COLUMN: ACTIVE TICKET DETAILS -----------------
with col_ticket:
    st.markdown('<div class="glass-card" style="min-height: 480px;">', unsafe_allow_html=True)
    st.markdown('<div class="glass-card-header">🎫 Active Ticket Inspection</div>', unsafe_allow_html=True)
    
    ticket = st.session_state.active_ticket
    audio = st.session_state.active_audio
    
    if ticket:
        priority = ticket.get("priority", "P2")
        badge_cls = f"badge badge-{priority.lower()}"
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
            <span style="font-family:'Outfit'; font-size:1.25rem; font-weight:700; color:white;">Ticket ID: {ticket.get('id')[:8]}</span>
            <span class="{badge_cls}">{priority}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Grid layout for fields
        col_field1, col_field2 = st.columns(2)
        with col_field1:
            st.markdown(f"""
            <div class="ticket-cell">
                <div class="ticket-lbl">Customer Name</div>
                <div class="ticket-val">{ticket.get('customer_name') or 'Anonymous'}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_field2:
            st.markdown(f"""
            <div class="ticket-cell">
                <div class="ticket-lbl">Contact Number</div>
                <div class="ticket-val">{ticket.get('contact_number') or 'Not Provided'}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class="ticket-cell" style="margin-top:0.75rem; margin-bottom:0.75rem;">
            <div class="ticket-lbl">Product or Service</div>
            <div class="ticket-val">{ticket.get('product_or_service') or 'General Item'}</div>
        </div>
        <div class="ticket-cell" style="margin-bottom:0.75rem;">
            <div class="ticket-lbl">Transcribed Complaint</div>
            <div class="ticket-val" style="font-size:0.875rem;">{ticket.get('complaint_description')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Subagent plan mapping
        st.markdown('<div class="ticket-cell" style="margin-bottom:0.75rem;">', unsafe_allow_html=True)
        st.markdown('<div class="ticket-lbl">Actionable Resolution Plan (Planner Agent)</div>', unsafe_allow_html=True)
        for step in ticket.get("resolution_plan", []):
            st.markdown(f'<div class="plan-item"><span class="plan-item-icon">⚡</span> <span>{step}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # TTS Audio response
        st.markdown('<div class="ticket-cell" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(99, 102, 241, 0.03) 100%); border: 1px solid rgba(99, 102, 241, 0.25);">', unsafe_allow_html=True)
        st.markdown('<div class="ticket-lbl">Spoken Response Script (TTS Engine)</div>', unsafe_allow_html=True)
        st.write(ticket.get("customer_response"))
        if audio:
            st.audio(audio, format="audio/mp3")
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.markdown(
            '<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:350px; color:#64748b;">'
            '<h3>No processed complaints yet</h3>'
            '<p style="font-size:0.9rem;">Record audio or enter text on the left to trigger the multi-agent console.</p>'
            '</div>', 
            unsafe_allow_html=True
        )
        
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- BOTTOM SECTION: DATABASE HISTORY -----------------
st.markdown("---")
st.markdown("## 📋 Complaint History Records (MongoDB / Fallback)")

# Fetch refreshed list
all_tickets = db.get_all_tickets()

if all_tickets:
    # Convert list of dicts to DataFrame
    df_data = []
    for t in all_tickets:
        df_data.append({
            "ID": t.get("id")[:8],
            "Customer": t.get("customer_name") or "Anonymous",
            "Contact": t.get("contact_number") or "Not Provided",
            "Product / Service": t.get("product_or_service") or "General",
            "Sentiment": t.get("sentiment") or "Neutral",
            "Priority": t.get("priority") or "P2",
            "Logged At": t.get("created_at")[:19].replace("T", " "),
            "Full ID": t.get("id") # Keep reference
        })
    df = pd.DataFrame(df_data)
    
    # Display table
    st.dataframe(
        df.drop(columns=["Full ID"]),
        use_container_width=True,
        hide_index=True
    )
    
    # Detail inspection and deletion tools
    col_detail, col_delete = st.columns([2, 1])
    
    with col_detail:
        inspect_id = st.selectbox("Select Ticket to Inspect Detail", options=[t["id"][:8] for t in all_tickets], index=0)
        selected_ticket = next((t for t in all_tickets if t["id"].startswith(inspect_id)), None)
        
        if selected_ticket:
            with st.expander(f"🔍 Detailed Plan & Spoken Script for Ticket {inspect_id}"):
                st.markdown(f"**Description:** {selected_ticket.get('complaint_description')}")
                st.markdown("**Resolution Plan:**")
                for s in selected_ticket.get("resolution_plan", []):
                    st.markdown(f"- {s}")
                st.markdown(f"**Customer Response Script:** {selected_ticket.get('customer_response')}")
                
    with col_delete:
        delete_id = st.selectbox("Select Ticket to Delete", options=[t["id"][:8] for t in all_tickets], index=0, key="select_delete")
        if st.button("🗑️ Delete Ticket Record", type="secondary", use_container_width=True):
            full_delete_ticket = next((t for t in all_tickets if t["id"].startswith(delete_id)), None)
            if full_delete_ticket:
                success = db.delete_ticket(full_delete_ticket["id"])
                if success:
                    st.success(f"Ticket {delete_id} deleted successfully.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to delete ticket record.")
else:
    st.info("No complaint records currently logged in the database.")
