from approval_system import approval_workflow
import os
import json
from datetime import datetime

def approval_node(state):
    """
    Nodo de aprobación.
    - Modo CLI (default): Interactivo con input()
    - Modo Dashboard: Guarda draft en archivo y termina.
    """
    print("--- [Node] Manual Approval ---")
    
    # Validar AUTO_APPROVE primero
    if os.getenv("AUTO_APPROVE") == "true":
        print("🤖 [Auto-Pilot] Auto-approving content...")
        state["approval_status"] = "approved"
        return state

    # Check if running in Dashboard mode (non-interactive)
    if os.getenv("DASHBOARD_MODE") == "true":
        print("ℹ️ DASHBOARD MODE: Saving draft and exiting graph.")
        
        # Ensure directory exists
        draft_dir = "./brain/drafts"
        os.makedirs(draft_dir, exist_ok=True)
        
        # Create unique filename with microseconds
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{draft_dir}/draft_{timestamp}.json"
        
        # Add ID to state for easier UI tracking
        state["id"] = timestamp
        
        # Save state to file
        with open(filename, "w", encoding="utf-8") as f:
            # Convert non-serializable objects (like products) if needed
            # State is mostly strings/dicts so should be fine
            json.dump(state, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Draft saved to: {filename}")
        
        # Mark as draft_saved to handle transition
        state["approval_status"] = "draft_saved"
        return state

    # Ejecutar workflow de aprobación interactivo (CLI)
    updated_state = approval_workflow(state)
    
    return updated_state

def should_publish(state):
    """
    Decide si publicar basado en el estado de aprobación.
    """
    approval_status = state.get("approval_status", "")
    
    if approval_status == "approved":
        return "publish"
    elif approval_status == "rejected":
        return "regenerate"
    elif approval_status == "draft_saved":
        return "end" # Stop execution for dashboard to pick up
    else:  # cancelled
        return "end"
