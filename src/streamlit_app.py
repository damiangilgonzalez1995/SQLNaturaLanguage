import streamlit as st
from prompt import *
from generative_ai import SQLNaturaLanguage
import os
# streamlit config show > project/.streamlit/config.toml
import pandas as pd
import sqlalchemy as sql


class App_queries_naturallanguage():
    def __init__(self, sql_engine, API_KEY, temperature=0, model="gpt-3.5-turbo"):
        """
        Initialize the App_queries_naturallanguage class.

        :param sql_engine: The SQL engine to connect to the database.
        :type sql_engine: SQLAlchemy engine
        :param API_KEY: The API key for the NaturaLanguage service.
        :type API_KEY: str
        :param temperature: The temperature setting for text generation (default is 0).
        :type temperature: float
        :param model: The language model to use for natural language processing (default is "gpt-3.5-turbo").
        :type model: str
        """

        self.conn = sql_engine.connect()
        self.sql_engine = sql_engine
        self.API_KEY = API_KEY
        self.temperature=temperature
        self.model=model


    def _call_llm_sql(self, question=None, number_rows=10):
        """
        Call the SQLNaturaLanguage model to execute an SQL query based on the user's question.

        :param question: The user's input question to generate the SQL query.
        :type question: str
        :param number_rows: The number of rows to limit the SQL query results (default is 10).
        :type number_rows: int
        :return: The result of the SQL query execution.
        :rtype: dict
        """

        sql_model = SQLNaturaLanguage(API_KEY=self.API_KEY, sql_engine=self.sql_engine, temperature=self.temperature, model=self.model)

        prompt = PROMPT
        prompt = prompt.format(question=question, number_rows=number_rows)
        result = sql_model.execution(prompt=prompt)
        return result
    


    def execute(self):
        """
        Execute the main application.

        This function sets up the layout and handles user interactions to execute SQL queries and display results.
        """

        st.set_page_config(layout="wide",page_icon="🧊")
        st.title("Lead Scoring Analyzer")


        # Set up the layout with two columns
        # col1, col2 = st.columns([1, 1])
        col1, col2 = st.columns(2)

        # Column on the left for chat
        with col2:

            st.title("Inquiries")
            number_rows = self.__number_result()
            self.__init_session()

            # Create an input box for the user to type messages
            user_input = st.text_input(label=f"I want to know the **:red[{number_rows}]** ..." ,
                                        value="Best clients we have",
                                        key="placeholder")

            if st.button("ASK"):
                # Collect the message and store it in a variable
                output = self._call_llm_sql(question=user_input, number_rows=number_rows)

                st.session_state.past.append(user_input)
                st.session_state.generated.append(output)

            if st.session_state["generated"]:

                for i in range(len(st.session_state["generated"])-1, -1, -1):
                    self.__queryseparator(i)
                    chat_message = st.session_state["generated"][i]
                    
                    if "error" in chat_message:
                        self.__error_show(chat_message)
                        
                    else:
                        self.__show_result(chat_message)
                        

        # Column on the right for clients table view
        with col1:
            self.__show_tables()


    def __queryseparator(self, i):
        """
        Display a separator for each generated query.

        :param i: The index of the generated query.
        :type i: int
        """

        st.text(f"....................................... QUERY {i+1} .......................................")
        st.text( "QUESTION: " + st.session_state["past"][i])

    def __show_tables(self):
        """
        Display the database tables in different tabs.

        This function shows an overview of the client_info and features tables.
        """

        st.header("Data Base Tables")

        tab1, tab2, tab3 = st.tabs(["Overview", "client_info" , "features"])

        clients_df = pd.read_sql_table("client", self.conn)
        model_df = pd.read_sql_table("data_predict", self.conn)
        df_total = pd.concat([clients_df[["email"]], model_df[["prediction_label" , "prediction_score_0",  "prediction_score_1"]]], axis=1, join="inner")

        with tab1:
            st.dataframe(df_total)
        with tab2:
            st.dataframe(clients_df)
        with tab3:
            st.dataframe(model_df)

    def __error_show(self, chat_message):
        """
        Display an error message.

        :param chat_message: The error message to be displayed.
        :type chat_message: str
        """

        st.text( "ERROR: ")
        st.code(chat_message["error"], language="python", line_numbers=True)

    def __show_result(self, chat_message):
        """
        Display the response of the generated query.

        :param chat_message: The response of the generated query.
        :type chat_message: dict
        """

        st.text( "RESPONSE: ")
        for key in chat_message.keys():

            if "result"==key:
                st.text(chat_message[key])
            elif "query_sql"==key:
                st.code(chat_message[key], language="sql", line_numbers=True)
            elif "query_df"==key:
                st.dataframe(chat_message[key])


    def __number_result(self):
        """
        Prompt the user to choose the number of rows to display in the query results.

        :return: The number of rows selected by the user.
        :rtype: int
        """

        number_rows = st.slider(
            "How many result do you want?",
            value=5,
            step=1,
            max_value=10,
            min_value=1
            )

        return number_rows

    def __init_session(self):
        """
        Initialize the session state for generated queries and past user inputs.
        """

        if "generated" not in st.session_state:
                st.session_state["generated"] = []
            
        if "past" not in st.session_state:
            st.session_state["past"] = []


if __name__ == "__main__":

    # Connection with the database
    sql_engine = sql.create_engine("sqlite:///data/marketing.db")

    API_KEY = KEY_OPENAI

    app_class = App_queries_naturallanguage(sql_engine=sql_engine, API_KEY=API_KEY)

    app_class.execute()
