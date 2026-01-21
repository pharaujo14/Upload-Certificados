from pymongo import MongoClient
import streamlit as st

@st.cache_resource
def conectaBanco():
    client = MongoClient(
        f'mongodb+srv://{st.secrets["database"]["user"]}:'
        f'{st.secrets["database"]["password"]}'
        '@centurydatamongocluster.k5fsf.mongodb.net/'
        '?retryWrites=true&w=majority'
    )
    return client["CenturyData"]
