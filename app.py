import streamlit as st
import json
from QueryGenerator import SQLQueryGenerator
import config
import pandas as pd

def add_custom_css():
    st.markdown(
        """
        <style>
        
        .main {
            background-color: #f0f2f6;
        }
        
        .stTextInput > div > div > input {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #dfe1e5;
            padding: 10px;
            font-size: 16px;
        }
        
        .stButton > button:hover {
            background-color: #45a049;
        }

        .stAlert {
            border-radius: 8px;
            padding: 20px;
            font-size: 16px;
        }

        .stAlert > div:first-child {
            font-size: 18px;
            font-weight: bold;
        }
        
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }

        </style>
        
        """,
        unsafe_allow_html=True
    )
    
def main():
    add_custom_css()

    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>SQLens</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Enter a natural language question to generate an SQL query.</p>", unsafe_allow_html=True)

    question = st.text_input("", placeholder="Type your question here...")

    examples_file = 'examples.json'
    sql_gen = SQLQueryGenerator(examples_file)

    if 'history' not in st.session_state:
        st.session_state.history = []

    exec_result = None

    if st.button("Generate SQL Query"):
        if not question.strip():
            st.warning("Please enter a question before generating a query.")
            return
        st.session_state.history.append({
            "question": question,
            "query": None,
            "exec_result": None,
            "corrected_query": None
        })

        with st.spinner("Generating SQL Query..."):
            try:
                query = sql_gen.generate_sql_query(question)
                query = query.replace("AI:", "").strip()
                st.session_state.history[-1]["query"] = query
                st.markdown(f"<div style='background-color: #e6ffee; padding: 10px; border-radius: 8px;'><b>Generated SQL Query:</b><br>{query}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating query: {str(e)}")
                print("Error generating query:", e)
                return  
                
        with st.spinner("Executing SQL Query..."):
            try:
                exec_result = sql_gen.execute_query(query)
                print("exec_result:", exec_result)
                st.session_state.history[-1]["exec_result"] = exec_result
                st.markdown(f'<div style="background-color: #f9f9f9; padding: 10px; border-radius: 8px;"><b>SQL query execution result:</b> {exec_result}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
                print("Error executing query:", e)
                return

    if exec_result and isinstance(exec_result, str) and 'You have an error in your SQL syntax' in exec_result:
        with st.spinner("Correcting SQL Query..."):
            try:
                corrected_query = sql_gen.correct_sql_query(question, query, exec_result)
                st.session_state.history[-1]["corrected_query"] = corrected_query
                st.markdown(f'<div style="background-color: #ffe6b9; padding: 10px; border-radius: 8px;"><b>Corrected SQL query:</b> {corrected_query}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error correcting query: {str(e)}")
                print("Error correcting query:", e)
                return

    if st.session_state.history:
        st.markdown("<h2>History</h2>", unsafe_allow_html=True)
        for item in st.session_state.history:
            st.markdown(f"**Question:** {item['question'] if item['question'] else 'N/A'}")
            st.markdown(f"**Generated SQL Query:** {item['query']}")
            st.markdown(f"**Execution Result:** {item['exec_result']}")
            if item['corrected_query']:
                st.markdown(f"**Corrected SQL Query:** {item['corrected_query']}")
            st.markdown("---")

if __name__ == "__main__":
    main()