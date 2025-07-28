from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import Tool
from config import config
from tools.weather_tool import get_weather, WEATHER_TOOL_SCHEMA
from tools.flight_tool import find_flights, FLIGHT_TOOL_SCHEMA
from tools.location_tool import get_location_codes, LOCATION_TOOL_SCHEMA
from tools.sandbox_tool import sandbox_code_tool
from tools.datasource_tools import datasource_tools
from tools.helius_tools import helius_tools
from .system_prompt import get_system_prompt

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[List, "The messages in the conversation"]
    user_query: Annotated[str, "The user's original query"]
    tool_results: Annotated[List, "Results from tool executions"]
    final_response: Annotated[str, "The final response to the user"]

def create_assistant_graph():
    """Create the LangGraph DAG for the assistant."""
    
    # Initialize the LLM with system prompt for better date handling
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0,
        openai_api_key=config.OPENAI_API_KEY
    )

    # Create the old hardcoded tools
    hardcoded_tools = [
        Tool(
            func=get_weather,
            name=WEATHER_TOOL_SCHEMA["name"],
            description=WEATHER_TOOL_SCHEMA["description"],
            args_schema=WEATHER_TOOL_SCHEMA["parameters"]
        ),
        Tool(
            func=find_flights,
            name=FLIGHT_TOOL_SCHEMA["name"],
            description=FLIGHT_TOOL_SCHEMA["description"],
            args_schema=FLIGHT_TOOL_SCHEMA["parameters"]
        ),
        Tool(
            func=get_location_codes,
            name=LOCATION_TOOL_SCHEMA["name"],
            description=LOCATION_TOOL_SCHEMA["description"],
            args_schema=LOCATION_TOOL_SCHEMA["parameters"]
        )
    ]
    
    # Combine all tools into one set
    all_tools = hardcoded_tools + datasource_tools + helius_tools + [sandbox_code_tool]
    
    # Bind the combined set to the LLM
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Define the nodes
    def call_llm(state: AgentState) -> AgentState:
        """Call the LLM to process the user query and potentially call tools."""
        messages = state["messages"]
        
        # Get response from LLM (system prompt is already included in messages)
        response = llm_with_tools.invoke(messages)
        
        # Add the AI response to messages
        new_messages = messages + [response]
        
        return {
            **state,
            "messages": new_messages
        }

    def generate_final_response(state: AgentState) -> AgentState:
        """Generate the final response to the user."""
        messages = state["messages"]
        # Get final response from LLM (system prompt is already included in messages)
        response = llm.invoke(messages)
        # Format the response nicely
        final_response = response.content
        return {
            **state,
            "final_response": final_response
        }

    # --- Generic tool execution node for OpenAI function calling protocol ---
    def use_tool(state: AgentState) -> AgentState:
        """Execute tool calls from the last AI message using the tool registry and insert ToolMessages."""
        messages = state["messages"]
        tool_results = state.get("tool_results", [])
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
            return state
        # Build a registry from tool name to tool object
        tool_registry = {tool.name: tool for tool in all_tools}
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            if tool_name in tool_registry:
                try:
                    print(tool_args)
                    result = tool_registry[tool_name].invoke(tool_args)
                except Exception as e:
                    result = {"error": str(e)}
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_id
            )
            messages.append(tool_message)
            tool_results.append({
                "tool_name": tool_name,
                "args": tool_args,
                "result": result
            })
        return {
            **state,
            "messages": messages,
            "tool_results": tool_results
        }

    # --- New automatic tool invocation workflow with tool execution node ---
    def should_use_tool(state: AgentState) -> str:
        messages = state["messages"]
        if messages and isinstance(messages[-1], AIMessage):
            if getattr(messages[-1], "tool_calls", None):
                return "use_tool"
        return "maybe_end"

    def should_end(state: AgentState) -> str:
        messages = state["messages"]
        if messages and isinstance(messages[-1], AIMessage):
            if not getattr(messages[-1], "tool_calls", None):
                return "end"
        return "call_llm"

    workflow = StateGraph(AgentState)
    workflow.add_node("call_llm", call_llm)
    workflow.add_node("use_tool", use_tool)
    workflow.add_node("generate_final_response", generate_final_response)
    workflow.add_conditional_edges(
        "call_llm",
        should_use_tool,
        {
            "use_tool": "use_tool",
            "maybe_end": "generate_final_response"
        }
    )
    workflow.add_edge("use_tool", "call_llm")
    workflow.add_edge("generate_final_response", END)
    workflow.set_entry_point("call_llm")
    return workflow.compile()

    # --- Old workflow code (commented out) ---
    # workflow = StateGraph(AgentState)
    # workflow.add_node("call_llm", call_llm)
    # workflow.add_node("use_tool", use_tool)
    # workflow.add_node("generate_final_response", generate_final_response)
    # workflow.add_conditional_edges(
    #     "call_llm",
    #     should_use_tool,
    #     {
    #         "use_tool": "use_tool",
    #         "end": "generate_final_response"
    #     }
    # )
    # workflow.add_edge("use_tool", "call_llm")
    # workflow.add_edge("generate_final_response", END)
    # workflow.set_entry_point("call_llm")
    # return workflow.compile()

def process_query(query: str) -> Dict[str, Any]:
    """
    Process a user query through the LangGraph workflow.
    
    Args:
        query (str): The user's natural language query
        
    Returns:
        Dict[str, Any]: The result containing the final response and any tool results
    """
    # Create the graph
    graph = create_assistant_graph()
    
    # Get the system prompt for context
    from langchain_core.messages import SystemMessage
    
    system_prompt = get_system_prompt()
    
    # Initialize state with system message included from the start
    system_message = SystemMessage(content=system_prompt)
    initial_state = {
        "messages": [system_message, HumanMessage(content=query)],
        "user_query": query,
        "tool_results": [],
        "final_response": ""
    }
    
    # Run the graph
    result = graph.invoke(initial_state)
    
    return {
        "query": query,
        "response": result["final_response"],
        "tool_results": result["tool_results"],
        "conversation_length": len(result["messages"])
    } 