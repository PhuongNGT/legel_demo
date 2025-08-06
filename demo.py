import pandas as pd
import streamlit as st

df = pd.read_csv("outputs/merged_stories.tsv", sep='\t')

st.title("Legal Doctrines — LLM Generated Stories")

for idx, row in df.iterrows():
    st.subheader(f"{row['doctrine']}")
    st.write(f"**Definition:** {row['definition']}")
    st.write(f"**Mistral story:** {row['mistral_story']}")
    st.write(f"**LLaMA3 story:** {row['llama3_story']}")
    st.write(f"**GPT-3.5 story:** {row['gpt35_story']}")
    st.markdown("---")
