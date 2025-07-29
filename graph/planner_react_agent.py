import os
import json
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage, SystemMessage
from typing import Dict, Any, List, Sequence, Annotated, Optional, TypedDict
from typing_extensions import TypedDict
from tools.helius_tools import helius_tools
from tools.datasource_tools import datasource_tools
from tools.sandbox_tool import sandbox_code_tool
from tools.weather_tool import get_weather
from tools.flight_tool import find_flights
from tools.location_tool import get_location_codes
from langchain_core.tools import tool
from graph.system_prompt import get_system_prompt
# You can add more tools, e.g., from tools.price_tools import price_tools
from langchain_anthropic import ChatAnthropic
from utils.token_utils import estimate_token_count, chunk_data_by_tokens
from graph.summarizer_graph import schema_discovery_wrapper
from utils.db_utils import save_message
from utils.db_utils import create_session



@tool
def weather_tool(city: str):
    """Get current weather information for a specific city."""
    return get_weather(city)

@tool
def flight_tool(origin: str, destination: str, date: str):
    """Find available flights between two cities on a specific date."""
    return find_flights(origin, destination, date)

@tool
def location_tool(keyword: str, sub_type: str = "CITY,AIRPORT"):
    """Get location codes for airports and cities using a keyword."""
    return get_location_codes(keyword, sub_type)

# Combine all tools - simple version to avoid rate limits
all_tools = helius_tools + datasource_tools + [sandbox_code_tool, weather_tool, flight_tool, location_tool]# Just the main Helius tool for Solana queries

# Create the tool node
tool_node = ToolNode(all_tools)

# --- Model selection: OpenAI or Claude ---
# model = ChatAnthropic(
#         model="claude-opus-4-0",  # or another Claude model
#         temperature=0,
#         anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
#     )
model = ChatOpenAI(
    model="gpt-4o",  # Current version, higher rate limits
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Cache for bound models to prevent duplication
bound_model_cache = {}

# Agent state definition
class AgentState(TypedDict):
    session_id: str  # Add session_id to state
    tool_output: ToolMessage | None
    tool_outputs: List[ToolMessage] | None
    summaries: List[str]
    final_summary: Optional[str]
    messages: Annotated[Sequence[BaseMessage], lambda left, right: left + right]
    tools: List[Dict[str, Any]]
    selected_tools: List[Any]  # Add selected_tools to state
    bound_model: Any  # Track bound model in state
    tools_bound: bool  # Flag to track if tools are already bound
    current_tool_index: int





def tool_node_wrapper(state):
    print('------tool_node_wrapper------')
    session_id = state.get("session_id")
    result = tool_node.invoke(state)

    # This already contains ToolMessage(s)
    tool_messages = result.get("messages")
    print('------tool_messages------')
    print(tool_messages)
    # Check last message was the assistant with tool_calls
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls"):
        raise ValueError("Expected last message to have tool_calls")
   
    # Convert tool_messages to list if it's not already
    if tool_messages:
        tool_outputs = tool_messages
        print(f'set tool_outputs with {len(tool_outputs)} tool messages')
    else:
        tool_outputs = []
        print('no tool messages found')
    
    
    return {'tool_outputs': tool_outputs,"current_tool_index" :-1}
def select_tool_output(state):
    print('------select_tool_output------')
    print(len(state['tool_outputs']))
   
    current_tool_index = state['current_tool_index'] 
    tool_outputs = state['tool_outputs']
    current_tool_index +=1
    tool_output =None
    if len(tool_outputs) !=0  and  len(tool_outputs) > current_tool_index:
        tool_output = tool_outputs[current_tool_index]
    
    return {'tool_output': tool_output,"current_tool_index": current_tool_index}

def process_tool_output(state):
    if state['tool_output'] is None:
        state['current_tool_index'] = -1
        state['tool_output'] = None
        state['tool_outputs']=[]
        return "model"
    data= state['tool_output'].content
    print('------data------')
    print(data)
    token_count = estimate_token_count(data)
    print('------token_count------')
    print(token_count)
    if token_count > 10000:
        return "chunking"
    else:
        return "normal"
  

# Tool selection node - checks tools one by one
def tool_selection_node(state):
    """Node that determines which tools are needed for the query."""
    messages = state["messages"]
    
    # Get the user query
    user_query = ""
    for msg in messages:
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            user_query = msg.content
            break
    
    # Since we bind tools only once, we can bind ALL tools
    all_available_tools = helius_tools + datasource_tools + [sandbox_code_tool, weather_tool, flight_tool, location_tool]
    
    print(f"[TOOL_SELECTION] Binding all {len(all_available_tools)} tools for comprehensive access")
    
    # Bind ALL tools once here - no duplication issue since it's only called once
    bound_model = model.bind_tools(all_available_tools)
    print(f"[TOOL_SELECTION] Bound {len(all_available_tools)} tools to model")
    
    # No need to add system prompt here, it's already at the start
    return {
         # Use messages as-is
        "selected_tools": all_available_tools,  # All tools available
        "bound_model": bound_model,
        "tools_bound": True
    }

# Model node (planner) - now uses pre-bound model from state
def model_node(state):
    messages = state["messages"]
    session_id = state.get("session_id")
    print('------messages------')
    log_messages(messages)
    bound_model = state.get("bound_model")
    
    if not bound_model:
        print("[MODEL_NODE] No bound model found, using base model")
        bound_model = model
    
    # System prompt is already added in tool_selection_node, use messages as is
   
    # Use the pre-bound model
    response = bound_model.invoke(messages)

    # Save the new AI message to database if session_id is available
    if session_id:
        try:
            save_message(
                session_id=session_id,
                message_type="AIMessage",
                content={"content": response.content},
                metadata={"node": "model_node", "timestamp": str(datetime.now())}
            )
            print(f"[MODEL_NODE] Saved AI message to session {session_id}")
        except Exception as e:
            print(f"[MODEL_NODE] Failed to save AI message: {e}")
    
    return {"messages": [response]}
# Router node
def log_messages(messages):
    log_file_name = f"workflow_log.json"

    serializable_messages = []
    for msg in messages:
        msg_dict = {
            "type": msg.__class__.__name__,
            "content": msg
        }
        serializable_messages.append(msg_dict)

    # Add AI response to serializable messages
    
    
    with open(log_file_name, "w") as f:
        json.dump(serializable_messages, f, indent=4, default=str)
    print(f"[MODEL_NODE] Logged {len(serializable_messages)} messages (including AI response) to {log_file_name}")

def router(state):
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM is calling a tool, go to tools
    # if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
    #     print("[ROUTER] Routing to tools")
    
    # # If the LLM says it's done, go to END
    # elif hasattr(last_message, "content") and (
    #     "final answer" in last_message.content.lower() or
    #     "here is the answer" in last_message.content.lower() or
    #     "summary" in last_message.content.lower()
    # ):
    #     print("[ROUTER] Routing to END (final answer detected)")
    
    return {}
def edge_router(state):
    messages = state["messages"]
    last_message = messages[-1]

    # Check if the last message has tool calls that haven't been processed yet
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # Check for final answer indicators
    if hasattr(last_message, "content") and (
        "final answer" in last_message.content.lower() or
        "here is the answer" in last_message.content.lower() or
        "summary" in last_message.content.lower()
    ):
        print("[EDGE_ROUTER] Final answer detected. Routing to end.")
        return "end"

    print("[EDGE_ROUTER] No tool calls or final answer. Routing to end.")
    return "end"

def add_tool_messages_node(state):
    """Add tool messages to conversation and clear tool output"""
    print('------add_tool_messages_node------')
    session_id = state.get("session_id")
    
    # Handle tool_output as array of ToolMessage objects
    tool_message = state['tool_output'] if state['tool_output'] else None
    print('------tool_messages------')
    if tool_message is None:
        return {}
    # Save tool messages to database if session_id is available
    if session_id and tool_message:
        try:
            save_message(
                session_id=session_id,
                message_type="ToolMessage",
                content={
                    "content": tool_message.content,
                    "tool_call_id": getattr(tool_message, 'tool_call_id', '')
                },
                metadata={"node": "add_tool_messages_node", "timestamp": str(datetime.now())}
            )
            print(f"[ADD_TOOL_MESSAGE] Saved  tool message to session {session_id}")
        except Exception as e:
            print(f"[ADD_TOOL_MESSAGE] Failed to save tool message: {e}")
    
    return {
        "tool_output": None,
        "messages":  [tool_message]
    }
# Create the graph
workflow = StateGraph(AgentState)
workflow.add_node("tool_selection", tool_selection_node)
workflow.add_node("model", model_node)
workflow.add_node("tools", tool_node_wrapper)
workflow.add_node("router", router)
workflow.add_node("discover_schema", schema_discovery_wrapper)
workflow.add_node("add_tool_messages", add_tool_messages_node)
workflow.add_node("select_tool_output", select_tool_output)
# Set up the workflow: tool_selection -> model -> router -> tools -> model
workflow.add_edge("tool_selection", "model")
workflow.add_edge("model", "router")
workflow.add_conditional_edges(
      "router",
      edge_router,
      {
          "tools": "tools",
          "end": END
      }
  )
workflow.add_edge("tools", "select_tool_output")
workflow.add_conditional_edges(
    "select_tool_output",
    process_tool_output,
    {"model": "model",
        "chunking": "discover_schema",
        "normal": "add_tool_messages"
    }
)

workflow.add_edge("discover_schema","select_tool_output")
workflow.add_edge("add_tool_messages", "select_tool_output")
# workflow.add_edge("tools", "model")
workflow.set_entry_point("tool_selection")
app = workflow.compile()

def run_planner_react_agent(user_input: str, session_id: str = None, existing_messages: List[BaseMessage] = None) -> str:
    try:
        # Generate session_id if not provided and create session in database
        if not session_id:
            session_id = create_session()
       
        
        # Initialize messages
        if existing_messages:
            messages = [SystemMessage(content=get_system_prompt())]+ existing_messages + [HumanMessage(content=user_input)]
        else:
            messages = [
                SystemMessage(content=get_system_prompt()),
                HumanMessage(content=user_input)
            ]
        
        state = {
            "session_id": session_id,
            "messages": messages,
            "tools": [],
            "tool_output": []  # Initialize as empty array instead of None
        }
        # Save the human message to database
        result = app.invoke(state, config={"recursion_limit": 50})
        print("[WORKFLOW] Finished. Result:", result.get("messages")[-1].content)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return f"Error:"

