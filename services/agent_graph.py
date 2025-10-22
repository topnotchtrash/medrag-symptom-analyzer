from langgraph.graph import StateGraph, END
from typing import TypedDict, Set
from services.symptom_extractor import extract_symptoms
from services.vector_search import search_all_categories
from services.agent import DiagnosticAgent

class ConversationState(TypedDict):
    symptoms: Set[str]
    question_count: int
    user_input: str
    search_results: dict
    agent_response: dict
    specialist: str
    status: str

# Define nodes
def extract_node(state: ConversationState):
    """Extract symptoms from user input"""
    extracted = extract_symptoms(state['user_input'])
    state['symptoms'].update(extracted['present'])
    state['question_count'] += 1
    return state

def search_node(state: ConversationState):
    """Search vector DBs"""
    results = search_all_categories(state['symptoms'])
    state['search_results'] = results
    return state

def agent_node(state: ConversationState):
    """LLM agent processes results"""
    agent = DiagnosticAgent()
    response = agent.process(state['search_results'], {
        'symptoms': state['symptoms'],
        'question_count': state['question_count']
    })
    state['agent_response'] = response
    return state

def lookup_specialist_node(state: ConversationState):
    """Get specialist from disease result"""
    top_disease = state['agent_response']['top_diseases'][0]
    # Get specialist from the disease dict (their vector search provides it)
    state['specialist'] = top_disease.get('specialist', 'General Practitioner')  # ← FIX THIS
    state['status'] = 'completed'
    return state

# Routing logic
def should_continue(state: ConversationState):
    """Decide next step"""
    if state['agent_response']['should_continue']:
        return "continue"
    else:
        return "complete"

# Build graph
def create_graph():
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("search", search_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("get_specialist", lookup_specialist_node)
    
    # Define edges
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "search")
    workflow.add_edge("search", "agent")
    
    # Conditional edge
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": END,
            "complete": "get_specialist"
        }
    )
    
    workflow.add_edge("get_specialist", END)
    
    return workflow.compile()

# Singleton
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = create_graph()
    return _graph