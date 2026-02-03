"""
Utilitários de cache com TTL.
"""
import streamlit as st
from functools import wraps
from datetime import datetime, timedelta
from utils.constants import CACHE_TTL_SECONDS


def cache_with_ttl(ttl_seconds=CACHE_TTL_SECONDS):
    """
    Decorator para cache com TTL usando st.cache_data.
    """
    return st.cache_data(ttl=ttl_seconds)
