import sqlite3
from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, END

from backend.config import DB_PATH
from backend.translation import translate_to_english
from backend.sql_validator import validate_user_input, validate_sql
from backend.llm_connector import openrouter_chat
from backend.role_access import apply_role_based_filter
from backend.user_db import get_cached_result, store_cached_result


# =========================
# GRAPH STATE
# =========================
class GraphState(TypedDict):
    user_input: str
    role: str
    user_id: Optional[int]
    translated_input: Optional[str]
    sql_query: Optional[str]
    raw_data: Optional[List[Dict]]
    filtered_data: Optional[List[Dict]]
    final_result: Optional[Dict]
    sql_explanation: Optional[str]


# =========================
# DB EXECUTION
# =========================
def execute_sql(sql):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================
# NODES
# =========================
def translate_node(state: GraphState):
    state["translated_input"] = translate_to_english(
        validate_user_input(state["user_input"])
    )
    return state


def llm_sql_node(state: GraphState):
    schema_context = """
You are an expert SQLite Text-to-SQL generator.

DATABASE SCHEMA:

TABLE employees:
- emp_id (INTEGER)
- emp_name (TEXT)
- dept_id (INTEGER)
- salary (INTEGER)

TABLE departments:
- dept_id (INTEGER)
- dept_name (TEXT)

RULES:
- ALWAYS include emp_id in SELECT for internal processing
- Generate ONLY ONE SELECT query
- NEVER generate DELETE, UPDATE, INSERT, DROP
- NEVER use '=' for names
- ALWAYS use:
  emp_name LIKE '%value%' COLLATE NOCASE
- Output ONLY SQL
"""

    messages = [
        {"role": "system", "content": schema_context},
        {"role": "user", "content": state["translated_input"]}
    ]

    sql_text = openrouter_chat(messages)

    if "emp_id" not in sql_text.lower():
        sql_text = sql_text.replace("SELECT", "SELECT emp_id,", 1)

    state["sql_query"] = validate_sql(sql_text)
    return state


def explain_sql_node(state: GraphState):
    messages = [
        {
            "role": "system",
            "content": "Explain this SQL query in ONE simple sentence for a non-technical user."
        },
        {
            "role": "user",
            "content": state["sql_query"]
        }
    ]
    state["sql_explanation"] = openrouter_chat(messages)
    return state


def execution_node(state: GraphState):
    cached = get_cached_result(state["sql_query"])
    data = cached if cached else execute_sql(state["sql_query"])

    if not cached:
        store_cached_result(state["sql_query"], data)

    state["raw_data"] = data
    return state


def role_filter_node(state: GraphState):
    state["filtered_data"] = apply_role_based_filter(
        state["raw_data"], state["role"], state["user_id"]
    )
    return state


def format_node(state: GraphState):
    requested_columns = [
        c.strip() for c in state["sql_query"]
        .split("FROM")[0].replace("SELECT", "").split(",")
        if c.strip() != "emp_id"
    ]

    final_data = []
    for row in state["filtered_data"]:
        filtered_row = {k: v for k, v in row.items() if k in requested_columns}
        final_data.append(filtered_row)

    if final_data:
        headers = list(final_data[0].keys())
        rows = [list(r.values()) for r in final_data]
    else:
        headers, rows = [], []

    state["final_result"] = {
        "columns": headers,
        "rows": rows
    }
    return state


# =========================
# LANGGRAPH DEFINITION
# =========================
graph = StateGraph(GraphState)

graph.add_node("translate", translate_node)
graph.add_node("llm", llm_sql_node)
graph.add_node("explain", explain_sql_node)
graph.add_node("execute", execution_node)
graph.add_node("filter", role_filter_node)
graph.add_node("format", format_node)

graph.set_entry_point("translate")

graph.add_edge("translate", "llm")
graph.add_edge("llm", "explain")
graph.add_edge("explain", END)

preview_app = graph.compile()


# execution-only graph
exec_graph = StateGraph(GraphState)
exec_graph.add_node("execute", execution_node)
exec_graph.add_node("filter", role_filter_node)
exec_graph.add_node("format", format_node)
exec_graph.set_entry_point("execute")
exec_graph.add_edge("execute", "filter")
exec_graph.add_edge("filter", "format")
exec_graph.add_edge("format", END)

execution_app = exec_graph.compile()


# =========================
# PUBLIC FUNCTIONS
# =========================
def run_text_to_sql_preview(user_input, role, user_id=None):
    state = {
        "user_input": user_input,
        "role": role,
        "user_id": user_id,
        "translated_input": None,
        "sql_query": None,
        "raw_data": None,
        "filtered_data": None,
        "final_result": None,
        "sql_explanation": None
    }

    result = preview_app.invoke(state)

    return {
        "sql": result["sql_query"],
        "explanation": result["sql_explanation"]
    }


def run_text_to_sql_execute(sql, role, user_id=None):
    state = {
        "user_input": "",
        "role": role,
        "user_id": user_id,
        "translated_input": None,
        "sql_query": sql,
        "raw_data": None,
        "filtered_data": None,
        "final_result": None,
        "sql_explanation": None
    }

    result = execution_app.invoke(state)
    return result["final_result"]
