import os
import operator
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

# Imported Nodes
from nodes.woocommerce_node import woocommerce_intake
from nodes.researcher_node import research_product
from nodes.copywriter_node import draft_content
from nodes.critic_node import quality_control
from nodes.approval_node import approval_node, should_publish
from nodes.publisher_node import publish_to_instagram

# Define the State of the Graph
class AgentState(TypedDict):
    status: str
    recent_products: List[dict]
    selected_product: dict
    research_summary: str
    draft_caption: str
    image_prompt: str
    image_url: str
    publish_time_iso: str  # For smart scheduling
    critique_feedback: str
    retry_count: int
    approval_status: str  # 'approved', 'rejected', 'cancelled'

# Initialize the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("woocommerce", woocommerce_intake)
workflow.add_node("researcher", research_product)
workflow.add_node("copywriter", draft_content)
workflow.add_node("critic", quality_control)
workflow.add_node("approval", approval_node)
workflow.add_node("publisher", publish_to_instagram)

# Define Edges (The Flow)
workflow.set_entry_point("woocommerce")

workflow.add_edge("woocommerce", "researcher")
workflow.add_edge("researcher", "copywriter")
workflow.add_edge("copywriter", "critic")

# Conditional Logic for the Critic
def check_critique(state):
    if state.get("critique_feedback") == "APPROVED":
        return "approval"  # Ir a aprobación manual
    elif state.get("retry_count", 0) > 2:
        # Si falló 3 veces, ir a aprobación manual de todos modos
        print("⚠️ Max retries reached. Sending to manual approval.")
        return "approval"
    else:
        return "copywriter"

workflow.add_conditional_edges(
    "critic",
    check_critique,
    {
        "approval": "approval",
        "copywriter": "copywriter"
    }
)

# Conditional Logic for Approval
workflow.add_conditional_edges(
    "approval",
    should_publish,
    {
        "publish": "publisher",
        "regenerate": "copywriter",
        "end": END
    }
)

workflow.add_edge("publisher", END)

# Compile
app = workflow.compile()
