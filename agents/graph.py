"""LangGraph retrieval and answer workflow."""

from functools import lru_cache
from typing import Any

from flask import current_app
from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from agents.tools.web_search import search_web
from services.answer_service import generate_answer
from services.retrieval_service import retrieve_documents


@lru_cache(maxsize=1)
def _compiled_graph() -> Any:
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", _retrieve)
    workflow.add_node("answer", _answer)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "answer")
    workflow.add_edge("answer", END)
    return workflow.compile()


def run_agent(
    question: str,
    user_code: str,
    token: str,
    history: list[str],
    strict: bool,
    web_search: bool = False,
) -> dict[str, Any]:
    result = _compiled_graph().invoke(
        {
            "question": question,
            "user_code": user_code,
            "token": token,
            "history": history,
            "strict": strict,
            "web_search": web_search,
        }
    )
    return {"answer": result["answer"], "sources": result.get("sources", [])}


def _retrieve(state: AgentState) -> dict[str, Any]:
    context, sources = retrieve_documents(
        state["question"],
        current_app.config["INDEX_DIR"],
        state["user_code"],
        state["token"],
        current_app.config["EMBEDDING_MODEL"],
        current_app.config["RERANKER_MODEL"],
    )
    tavily_api_key = current_app.config.get("TAVILY_API_KEY")
    should_search_web = not state.get("strict", True) and (
        state.get("web_search", False) or (not context and bool(tavily_api_key))
    )
    if should_search_web:
        web_context, web_sources = search_web(
            state["question"], tavily_api_key
        )
        context.extend(web_context)
        sources.extend(web_sources)
    return {"context": context, "sources": sources}


def _answer(state: AgentState) -> dict[str, str]:
    return {
        "answer": generate_answer(
            state["question"],
            state.get("context", []),
            state.get("history", []),
            state.get("strict", True),
        )
    }
