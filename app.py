# app.py
import streamlit as st
from services.agent_graph import get_graph

st.set_page_config(page_title="Medical Symptom Analyzer", page_icon="🏥")

# Initialize
if 'symptoms' not in st.session_state:
    st.session_state.symptoms = set()
    st.session_state.question_count = 0
    st.session_state.conversation = []
    st.session_state.status = 'ongoing'

st.title("🏥 Medical Symptom Analyzer")

# Sidebar
with st.sidebar:
    st.metric("Questions", st.session_state.question_count)
    st.metric("Symptoms", len(st.session_state.symptoms))
    if st.button("🔄 New", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Chat
for msg in st.session_state.conversation:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

if st.session_state.status == 'ongoing':
    user_input = st.chat_input("Describe your symptoms...")
    
    if user_input:
        st.session_state.conversation.append({'role': 'user', 'content': user_input})
        
        with st.spinner("Analyzing..."):
            # Run graph
            graph = get_graph()
            result = graph.invoke({
                'symptoms': st.session_state.symptoms,
                'question_count': st.session_state.question_count,
                'user_input': user_input,
                'search_results': {},
                'agent_response': {},
                'specialist': '',
                'status': 'ongoing'
            })
            
            # Update state
            st.session_state.symptoms = result['symptoms']
            st.session_state.question_count = result['question_count']
            
            # Response
            if result['status'] == 'completed':
                st.session_state.status = 'completed'
                top = result['agent_response']['top_diseases'][0]
                
                # Get specialist from the disease result (their vector search provides it)
                specialist = top.get('specialist', result.get('specialist', 'General Practitioner'))
                
                response = f"""### 🎯 Diagnosis Complete

**Most Likely Condition:** {top['disease']}  
**Confidence:** {top['confidence']:.0%}  
**Category:** {top.get('category', 'Unknown')}

**Recommended Specialist:** {specialist}

---

**Matched Symptoms:** {', '.join(st.session_state.symptoms)}

**Note:** This is an AI-assisted preliminary assessment. Please consult a healthcare professional for proper diagnosis and treatment.
"""
            else:
                response = result['agent_response']['clarifying_question']
            
            st.session_state.conversation.append({'role': 'assistant', 'content': response})
        st.rerun()
else:
    st.success("✅ Diagnosis complete! Click 'New' in the sidebar to start a fresh diagnosis.")