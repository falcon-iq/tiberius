"""LangGraph implementation for PR Analytics Agent."""

import json
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import OPENAI_MODEL, OPENAI_TEMPERATURE, DEFAULT_USERNAME, get_api_key
from app.tools_sqlite import get_schema, run_query
from app.sql_guard import validate_sql, suggest_fix, SQLValidationError
from app.prompts import (
    SYSTEM_PROMPT,
    get_parse_prompt,
    get_generate_sql_prompt,
    get_summarize_prompt
)


# Define the state
class AgentState(TypedDict):
    """State for the PR Analytics Agent."""
    question: str  # User's question
    username: str  # Username for query
    entities: dict  # Extracted entities
    sql: str  # Generated SQL
    sql_error: str  # SQL validation error (if any)
    results: list  # Query results
    summary: str  # Final summary
    retries: int  # Number of SQL generation retries
    max_retries: int  # Maximum retries allowed


def parse_question_node(state: AgentState) -> AgentState:
    """Parse user question to extract entities and intent."""
    print("🔍 Parsing question...")
    
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OpenAI API key not found. Please configure it in your settings file.")
    
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=OPENAI_TEMPERATURE, api_key=api_key)
    
    prompt = get_parse_prompt(state["question"], state.get("username", DEFAULT_USERNAME))
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    try:
        entities = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        entities = {
            "username": state.get("username", DEFAULT_USERNAME),
            "intent": "general_query"
        }
    
    print(f"   Entities: {entities}")
    
    return {
        **state,
        "entities": entities,
        "retries": 0,
        "max_retries": 3
    }


def generate_sql_node(state: AgentState) -> AgentState:
    """Generate SQL query from question and entities."""
    print("⚙️  Generating SQL...")
    
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OpenAI API key not found. Please configure it in your settings file.")
    
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=OPENAI_TEMPERATURE, api_key=api_key)
    
    # Get schema (cached for efficiency)
    schema = get_schema()
    
    # Prepare error feedback if this is a retry
    error_feedback = ""
    if state.get("sql_error"):
        error_feedback = f"Previous SQL failed validation: {state['sql_error']}\n"
        error_feedback += f"Suggestion: {suggest_fix(state.get('sql', ''), state['sql_error'])}"
    
    prompt = get_generate_sql_prompt(
        question=state["question"],
        entities=state.get("entities", {}),
        schema=schema,
        error_feedback=error_feedback
    )
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    sql = response.content.strip()
    
    # Clean up SQL (remove markdown code blocks if present)
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1]) if len(lines) > 2 else sql
    
    sql = sql.strip()
    
    print(f"   Generated SQL:")
    print(f"   {sql}")
    
    return {
        **state,
        "sql": sql,
        "sql_error": "",  # Clear previous error
        "retries": state.get("retries", 0) + 1
    }


def validate_sql_node(state: AgentState) -> AgentState:
    """Validate that SQL is safe and read-only."""
    print("✅ Validating SQL...")
    
    sql = state["sql"]
    is_valid, error = validate_sql(sql)
    
    if is_valid:
        print("   ✅ SQL is valid and safe")
        return {**state, "sql_error": ""}
    else:
        print(f"   ❌ Validation failed: {error}")
        return {**state, "sql_error": error}


def should_retry(state: AgentState) -> Literal["generate_sql", "run_sql", "error"]:
    """Decide whether to retry SQL generation or proceed."""
    if state.get("sql_error"):
        if state.get("retries", 0) < state.get("max_retries", 3):
            print(f"   🔄 Retrying SQL generation (attempt {state['retries'] + 1}/{state['max_retries']})")
            return "generate_sql"
        else:
            print(f"   ❌ Max retries reached")
            return "error"
    return "run_sql"


def run_sql_node(state: AgentState) -> AgentState:
    """Execute the SQL query."""
    print("🔄 Executing SQL...")
    
    try:
        results = run_query(state["sql"], validate=False)  # Already validated
        print(f"   ✅ Query returned {len(results)} rows")
        
        return {
            **state,
            "results": results
        }
    except Exception as e:
        print(f"   ❌ Query execution failed: {e}")
        return {
            **state,
            "sql_error": f"Query execution failed: {str(e)}",
            "results": []
        }


def summarize_node(state: AgentState) -> AgentState:
    """Summarize results for the user."""
    print("📊 Summarizing results...")
    
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OpenAI API key not found. Please configure it in your settings file.")
    
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.3, api_key=api_key)
    
    prompt = get_summarize_prompt(
        question=state["question"],
        sql=state["sql"],
        results=state.get("results", []),
        row_count=len(state.get("results", []))
    )
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    summary = response.content
    
    print("   ✅ Summary generated")
    
    return {
        **state,
        "summary": summary
    }


def error_node(state: AgentState) -> AgentState:
    """Handle errors."""
    error_msg = state.get("sql_error", "Unknown error")
    summary = f"""❌ Unable to answer your question after {state.get('retries', 0)} attempts.

Error: {error_msg}

Please try rephrasing your question or being more specific about what you're looking for.
"""
    
    return {
        **state,
        "summary": summary
    }


def build_graph() -> StateGraph:
    """Build the LangGraph for PR Analytics Agent."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_question", parse_question_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("run_sql", run_sql_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("error", error_node)
    
    # Add edges
    workflow.set_entry_point("parse_question")
    workflow.add_edge("parse_question", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    
    # Conditional edge after validation
    workflow.add_conditional_edges(
        "validate_sql",
        should_retry,
        {
            "generate_sql": "generate_sql",
            "run_sql": "run_sql",
            "error": "error"
        }
    )
    
    workflow.add_edge("run_sql", "summarize")
    workflow.add_edge("summarize", END)
    workflow.add_edge("error", END)
    
    return workflow.compile()


def run_agent(question: str, username: str = DEFAULT_USERNAME) -> dict:
    """
    Run the PR Analytics Agent.
    
    Args:
        question: User's natural language question
        username: Username for query context (default from config)
    
    Returns:
        Final state with results and summary
    """
    graph = build_graph()
    
    initial_state = {
        "question": question,
        "username": username,
        "entities": {},
        "sql": "",
        "sql_error": "",
        "results": [],
        "summary": "",
        "retries": 0,
        "max_retries": 3
    }
    
    final_state = graph.invoke(initial_state)
    
    return final_state
