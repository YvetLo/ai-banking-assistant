"""
LangGraph wiring — Sprint 6

    START
      │
      ▼
   router ──intent=card_loss──► card_loss ──────────────► END
      │
      ├──intent=handoff────────► handoff ──► logger ─────► END
      │
      └──intent=faq/account────► qa ──has log_entries?──► logger ─► END
                                    └──no─────────────────────────► END

Matches docs/agent_design.md §5, with FAQ and Account routed to the
same `qa` node (see nodes.py module docstring for why).
"""

from langgraph.graph import END, StateGraph

from . import nodes as N
from .state import AgentState


def build_graph(client, retrievers: dict, kb: dict, model: str, max_tokens: int):
    qa_node = N.make_qa_node(client, retrievers, kb, model, max_tokens)

    graph = StateGraph(AgentState)
    graph.add_node("router", N.router_node)
    graph.add_node("card_loss", N.card_loss_node)
    graph.add_node("handoff", N.handoff_node)
    graph.add_node("qa", qa_node)
    graph.add_node("logger", N.logger_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        lambda s: s["intent"],
        {"card_loss": "card_loss", "handoff": "handoff", "faq": "qa", "account": "qa"},
    )
    graph.add_edge("card_loss", END)
    graph.add_edge("handoff", "logger")
    graph.add_conditional_edges(
        "qa",
        lambda s: "logger" if s.get("log_entries") else END,
        {"logger": "logger", END: END},
    )
    graph.add_edge("logger", END)

    return graph.compile()
