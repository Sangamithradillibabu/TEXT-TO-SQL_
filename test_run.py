

from backend.text_to_sql_langgraph_flow import run_text_to_sql

m = input("Enter your query: ")

response = run_text_to_sql(
    user_input=m,
    role="INTERN",
    user_id=104
)

print("\nGenerated SQL Query:")
print(response["query"])
print("\nFinal Result:")
print(response["result"])



