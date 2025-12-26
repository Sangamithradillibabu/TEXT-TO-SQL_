from backend.text_to_sql_langgraph_flow import run_text_to_sql

response = run_text_to_sql(
    user_input=" DELETE info of MEENA",
    role="ADMIN"
    user_id=103
)

print(response)

