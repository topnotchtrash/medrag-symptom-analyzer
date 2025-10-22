import streamlit as st
def get_state():
    for k,v in [('user_text',''),('symptoms',[]),('search_results',[]),('ddx',[]),('recommendations',[])]:
        if k not in st.session_state: st.session_state[k]=v
    return st.session_state
