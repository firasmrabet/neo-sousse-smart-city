#!/usr/bin/env python3
"""
Auto-refresh helper for Streamlit
Forces periodic updates for real-time data display
"""

import streamlit as st
import time

def add_auto_refresh(interval_seconds=1.5):
    """
    Add automatic page refresh every interval_seconds
    Uses placeholders and reruns
    """
    import time
    
    # Placeholder for rerun tick
    if 'rerun_tick' not in st.session_state:
        st.session_state.rerun_tick = time.time()
    
    # Check if we should rerun
    elapsed = time.time() - st.session_state.rerun_tick
    if elapsed >= interval_seconds:
        st.session_state.rerun_tick = time.time()
        st.rerun()


def show_refresh_status():
    """Show last refresh time in top right"""
    if 'last_data_refresh' not in st.session_state:
        st.session_state.last_data_refresh = time.time()
    
    elapsed = int(time.time() - st.session_state.last_data_refresh)
    
    if elapsed == 0:
        status = "🟢 Now"
    elif elapsed < 5:
        status = f"🟢 {elapsed}s ago"
    else:
        status = f"🟡 {elapsed}s ago"
    
    return status


def force_data_refresh():
    """Mark data as refreshed now"""
    st.session_state.last_data_refresh = time.time()
