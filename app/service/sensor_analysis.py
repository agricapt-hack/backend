import os
import hashlib
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, Column, String, text, Integer, Float, DateTime
from app.agent_utils.agent_option_selector import AgentIndependentOptionSelector
from app.agent_utils.agent_option import AgentOption
from app.llms.openai import LangchainOpenaiJsonEngine
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.postgres.rds import RDS_POSTGRES_DB
load_dotenv()



class SqlQuery(BaseModel):
    sql_code : str = Field(...,
        description="The SQL code to be executed. It should be a valid SQL query string.",
        example="SELECT * FROM arduino_data WHERE temperature > 25"
    )

class Insights(BaseModel):
    insights: List[str] = Field(...,
        description="Insights generated from the SQL query results, including statistical analysis and trends.",
        example="Drop of significant changes in temperature by 10 degrees Celsius in the last 24 hours."
    )




class SensorSqlLlmEngine:
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.db = RDS_POSTGRES_DB
        self.db.create_table("arduino_data", [
            ("timestamp", String),
            ("sensor_hub_id", String),
            ("nitrogen_level", Float),
            ("phosphorus_level", Float),
            ("potassium_level", Float),
            ("temperature", Float),
            ("humidity", Float),
            ("ph_level", Float)
        ])
        self.schema = self.db.metadata.tables["arduino_data"]
        head_cols, head_rows = self.db.query_data("SELECT * FROM arduino_data LIMIT 5")
        self.head = pd.DataFrame(head_rows, columns=head_cols)
        self.prompt = f"""
You are an expert SQL developer specializing in PostgreSQL databases hosted on AWS RDS.

The database has a table named '{self.schema.name}' with the following columns:
{', '.join(self.schema.columns.keys())}

Here are the first 5 rows of this table to provide context for the data:
{self.head.to_string(index=False)}

Your task is:
- To translate natural language descriptions into valid, efficient, and optimized PostgreSQL SQL queries.
- Ensure your SQL queries use the correct column names and return the requested data accurately.

Please generate only the SQL query without any additional explanation.
"""
        self.query_gen_engine = LangchainOpenaiJsonEngine(
            model_name=self.model_name,
            temperature=self.temperature,
            sampleBaseModel=SqlQuery,
            systemPromptText=self.prompt,
        )
        self.options = {
            0:AgentOption(
                option_name="SQL Query Generator",
                option_intention="Convert user's natural language query into a SQL query.",
                option_output_model=SqlQuery,
                option_callable=self.__call__
            )
        }
        self.option_selector = AgentIndependentOptionSelector(
            option_list=self.options,
            model_name=self.model_name,
            temperature=self.temperature,
        )
        self.post_process_engine = LangchainOpenaiJsonEngine(
            model_name=self.model_name,
            temperature=self.temperature,
            sampleBaseModel=Insights,
            systemPromptText="You are an expert data analyst. Generate insights from the SQL query results. The insight should be very brief and concise with specific focus on statistical analysis and trends."
        )

    def select_options(self, task_description: str):
        prompt = f"""
You are a data analytics agent responsible for decomposing a complex user request into smaller, manageable data analysis tasks.

Consider the following database schema:
Table: {self.schema.name}
Columns: {', '.join(self.schema.columns.keys())}

You have a single tool available (option 0) that converts natural language sub-queries into SQL queries.

Your task:
- Break down the user’s request into multiple natural language sub-queries.
- Each sub-query should describe a distinct data retrieval or calculation task related to the database.
- Assign all sub-queries to option 0 since it is the only available tool.
- You are encouraged to consolidate multiple related tasks into a single sub-query (like min, max, average or any other aggregate function) if they are closely related.
- Don't make up any sub-queries or anything that is not related to the database schema.
- Always try to limit the result set to a reasonable size, e.g., using LIMIT 10 or conditions clauses.
- Always try to include the average column as I am specifically interested whether the current data is above or below average. Like `average temperature`, `average standard deviation of humidity`, etc.
- Don't select too many options. Try to keep it under 5.

User's overall task description:
{task_description}

Please output a list of sub-queries as described above, without any explanation. You are encouraged to create multiple complex queries if needed, but prioritize relevance.

Example output:
<option_index> 0: Generate SQL query to find the min,max,average factor1 in the arduino_data table
<option_index> 0: Generate SQL query to find the standard deviation of factor1 in the arduino_data table where factor2 is greater than 10
"""
        return self.option_selector(prompt)
    
    def __call__(self, user_query):
        user_prompt = f"""
You are an expert PostgreSQL developer.

Given the natural language sub-query:
\"\"\"{user_query}\"\"\"

Generate a valid, efficient, and optimized PostgreSQL SQL query that retrieves the required data from the '{self.schema.name}' table.

- Use correct column names.
- Always filter the data first using 'sensor_hub_id' 
- Write complex queries if needed, but prioritize readability and performance.
- Do not include any explanation, only output the SQL query.
- Don't make up any sub-queries or anything that is not related to the database schema.
- Don't include any function or method calls which is not there in AWS RDS PostgreSQL.
- Strictly follow the database schema provided. Do not assume any additional columns or tables.
- Always try to limit the result set to a reasonable size, e.g., using LIMIT 10 or WHERE clauses.
- Always try to include the average column as I am specifically interested whether the current data is above or below average.

SQL Query:
"""
        result = self.query_gen_engine.run(user_prompt)
        return result[0]
    
    def run_query(self, sql_query: str):
        """Executes a SQL query and returns the results."""
        try:
            columns, data = self.db.query_data(sql_query)
            return pd.DataFrame(data, columns=columns)
        except Exception as e:
            raise ValueError(f"Error executing SQL query: {e}")


    def post_process_results(self, task_description, results):
        """Post-processes the query results ro generate muliple insights."""
        user_prompt = f"""Here is the task description:
{task_description}
And the SQL query results:"""
        for result in results:
            if result['query_result'] is not None:
                user_prompt += f"\n\nSQL Query Result for option index {result['option_index']}:\n"
                user_prompt += f"Sub-query: {result['subquery']}\n"
                user_prompt += f"Query Result:\n{result['query_result'].to_string(index=False)}\n"
                user_prompt += f"----------------------------\n"
        user_prompt += """
Now, generate insights based on the SQL query results. The insights should be very brief and concise with specific focus on statistical analysis and trends. 
The insights should be in the form of a 1-2 sentence that summarizes the key findings from the data.
Generate 2-3 insights based on the SQL query results provided above.
Each insight firstly consist of technical terms and then a brief explanation in layman's terms.
"""
        insights = self.post_process_engine.run(user_prompt)[0]
        if not insights:
            raise ValueError("No insights generated. Please ensure the SQL query results are valid.")
        print(f"{len(insights)} insights generated.")
        return insights['insights']
                
    def run_pipeline(self, task_description: str, sensor_hub_id: str):
        options = self.select_options(task_description)
        print(f"{len(options)} options selected.")
        if not options:
            raise ValueError("No options selected. Please ensure the task description is valid.")
        option_results = []
        for option in options:
            obj = {}
            opt_index = option.option_index
            sub_query = option.subquery
            if opt_index in self.options:
                # print(f"Processing option index: {opt_index} with sub-query: {sub_query[:50]}")
                callable_result = self.options[opt_index](sub_query+f" WHERE sensor_hub_id = '{sensor_hub_id}'")
                obj['option_index'] = opt_index
                obj['option_name'] = self.options[opt_index].option_name
                obj['option_intention'] = self.options[opt_index].option_intention
                obj['subquery'] = sub_query
                obj['sql_code'] = callable_result['sql_code']
                # print(f"Generated SQL code: {str(obj['sql_code'])[:50]}")
                print(f"Running SQL query...")
                try:
                    query_result = self.run_query(obj['sql_code'])
                    obj['query_result'] = query_result
                    print(f"Query executed successfully. Result shape: {query_result.shape}")
                except ValueError as e:
                    print(f"Error executing SQL query: {e}")
                    obj['query_result'] = None
                option_results.append(obj)
            else:
                raise ValueError(f"Invalid option index: {opt_index}")
            
        if not option_results:
            raise ValueError("No results generated. Please ensure the options are valid and the SQL queries are correct.")
        print(f"Post-processing results to generate insights...")
        insights = self.post_process_results(task_description, option_results)
        results = {
            "option_results": option_results,
            "insights": insights
        }
        return results
    

SENSOR_SQL_LLM_ENGINE = SensorSqlLlmEngine(model_name="gpt-4o-mini", temperature=0.5)
                        