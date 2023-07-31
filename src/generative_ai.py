import pandas as pd
import sqlalchemy as sql
from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain.chains import SQLDatabaseChain
from utilities.config import *



class SQLNaturaLanguage():
    def __init__(self, sql_engine, API_KEY, temperature=0, model="gpt-3.5-turbo") -> None:
        """
        Initialize the SQLNaturaLanguage class.

        :param sql_engine: The SQL engine to connect to the database.
        :type sql_engine: SQLAlchemy engine
        :param API_KEY: The API key for the NaturaLanguage service.
        :type API_KEY: str
        :param temperature: The temperature setting for text generation (default is 0).
        :type temperature: float
        :param model: The language model to use for natural language processing (default is "gpt-3.5-turbo").
        :type model: str
        """
        self.db = SQLDatabase(engine=sql_engine)
        self.conn = sql_engine.connect()
        self.API_KEY = API_KEY
        self.temperature=temperature
        self.model=model
        self.sql_model = self.__create_sqlchain()

    def __create_model(self):
        """
        Create and initialize the language model.

        :return: The language model 
        for natural language processing.
        :rtype: ChatOpenAI
        """
        llm = ChatOpenAI(
            temperature=self.temperature,
            model=self.model,
            openai_api_key=self.API_KEY
        )
        return llm

    def __create_sqlchain(self):
        """
        Create and initialize the SQLDatabaseChain.

        :return: The SQLDatabaseChain for executing 
        SQL queries based on natural language.
        :rtype: SQLDatabaseChain
        """
        db_chain = SQLDatabaseChain.from_llm(
            llm=self.__create_model(),
            db=self.db,
            verbose=True,
            return_intermediate_steps=True
        )
        return db_chain
    
    def __execution_query(self, prompt=None):
        """
        Execute the SQL query generation and database execution.

        :param prompt: The natural language prompt to generate the SQL query.
        :type prompt: str
        :return: The result of the SQL query execution.
        :rtype: dict
        """
        prompt = prompt if prompt is not None else QUESTION_GENERATIVE_AI

        try:
            res = self.sql_model(prompt)
            result = res["result"]
            query_sql = [elem["sql_cmd"] for elem in res["intermediate_steps"] if "sql_cmd" in elem][0]
            query_df = pd.read_sql_query(sql.text(query_sql), self.conn)

            return {
                "result": result,
                "query_sql": query_sql,
                "query_df": query_df
            }

        except Exception as error:
            return {"error": error}

        
    def execution(self, prompt=None):
        """
        Execute the main query execution process.

        :param prompt: The natural language prompt to generate the SQL query.
        :type prompt: str
        :return: The final result of the SQL query execution.
        :rtype: dict
        """
        final_result = self.__execution_query(prompt=prompt)
        return final_result

    

   

# sql_engine = sql.create_engine("sqlite:///data/marketing.db")

# API_KEY = API_KEY

# sqlnaturalanguage_object = SQLNaturaLanguage(sql_engine=sql_engine, API_KEY=API_KEY)

# response = sqlnaturalanguage_object.execution(prompt="What are the best clients?")

# print(response)

