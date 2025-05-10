import config
from langchain_community.utilities import SQLDatabase
from langchain_community.llms import LlamaCpp
import os
import sqlglot
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class SQLQueryGenerator:
    def __init__(self, examples_file):
        self.target_dialect = config.Config.TARGET_DIALECT
        self.default_dialect = config.Config.DEFAULT_DIALECT
        self.db_uri = config.Config.DB_URI
        self.model_path = config.Config.MODEL_PATH
        self.temperature = config.Config.TEMPERATURE
        self.max_tokens = config.Config.MAX_TOKENS
        self.top_p = config.Config.TOP_P
        self.n_ctx = config.Config.N_CTX
        self.tables = config.Config.TABLES
        self.examples = config.Config.load_examples(examples_file)
        self.db = SQLDatabase.from_uri(self.db_uri, include_tables=self.tables, view_support=True)
        self.llm = self.initialize_llm()
        
    def get_table_info(self):
        try:
            cursor = self.db._engine.raw_connection().cursor() 
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            table_schemas = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                schema = f"{table_name}: " + ", ".join([col[0] + " " + col[1] for col in columns])
                table_schemas.append(schema)

            return "\n".join(table_schemas)
        except Exception as e:
            print(f"Failed to fetch table schema: {e}")
            return ""

    
    def initialize_llm(self):
        return LlamaCpp(
            model_path=self.model_path,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            verbose=True,
            n_ctx=self.n_ctx
        )

    def generate_prompt(self, question):
        # Get the table information
        table_info = self.get_table_info()

        # Create the example prompt
        example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{input}\nSQLQuery:"),
            ("ai", "{query}")
        ])

        # Create the few-shot prompt
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=self.examples,
            input_variables=["input", "top_k", "table_info"]
        )

        # Ensure the variables are correctly passed
        few_shot_prompt.format(input=question, top_k=5, table_info=table_info)

        # Final prompt template that includes the few-shot examples
        final_prompt = ChatPromptTemplate.from_messages([
            # ("system", f"You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run. Consider the following table schema: {table_info}\n\n"),
            # few_shot_prompt,
            # ("human", "{input}")
            ("system", 
            """You are an expert MySQL query generator. Your task is to generate a syntactically correct and optimized MySQL query based on the user’s input. 

            Consider the following database schema:
            {table_info}

            Guidelines:
            - Ensure the query adheres to MySQL syntax.
            - Only use tables and columns mentioned in the schema.
            - Optimize queries for efficiency, avoiding unnecessary joins or subqueries.
            - If the question lacks specificity, infer the best possible query while maintaining logical integrity.
            """),
            few_shot_prompt,
            ("human", "{input}")
        ])
        
        # Explicitly set the input variables for the final prompt
        # final_prompt.input_variables = ["input", "top_k", "table_info"]

        print("Generated final prompt:")
        print(final_prompt)

        return final_prompt

    def generate_sql_query(self, question):
        final_prompt = self.generate_prompt(question)
        query_gen_chain = create_sql_query_chain(self.llm, self.db, final_prompt)

        query = query_gen_chain.invoke({
            "question": question,
            "top_k": 5,
            "table_info": self.get_table_info()
        })

        try:
            parsed_query = sqlglot.parse_one(query, dialect=self.default_dialect).sql(dialect=self.target_dialect)
            print(f"Parsed original query : {query} from default dialect : {self.default_dialect} to target dialect : {parsed_query}")
        except Exception as e:
            print(f"Failed to parse query: {e}")
            parsed_query = None

        return parsed_query if parsed_query else query

    def execute_query(self, query):
        query_exec_chain = QuerySQLDataBaseTool(db=self.db)
        exec_result = query_exec_chain.invoke(query)
        return exec_result

    def correct_sql_query(self, question, query, exec_result):
        error_prompt = PromptTemplate.from_template(
            """Given the following user question, corresponding SQL query, and SQL result,
            rewrite the query such that its syntax error is fixed and its semantic meaning remain as it is
            as per user question.

            Question: {question}
            SQL Query: {query}
            SQL Result: {result}
            
            **Guidelines:**  
            - Identify and correct any syntax errors.  
            - Preserve the semantic meaning of the original query.  
            - Ensure compatibility with MySQL syntax and structure.  
            - If the query is logically incorrect, make minimal but effective adjustments to correct it.  

            Answer: """
        )
        
        error_correction_chain = error_prompt | self.llm | StrOutputParser()
        corrected_query = error_correction_chain.invoke({"question": question, "query": query, "result": exec_result})
        return corrected_query

def main():

    examples_file = 'examples.json'

    sql_gen = SQLQueryGenerator(examples_file)

    question = input("Please enter your question: ")
    print("Generating SQL Query...")

    query = sql_gen.generate_sql_query(question)
    print('Generated SQL Query:', query)

    print("Executing SQL Query...")