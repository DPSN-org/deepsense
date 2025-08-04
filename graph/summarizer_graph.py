from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os
from utils.token_utils import estimate_token_count, chunk_data_by_tokens
from typing import TypedDict, List, Dict, Any
import json
import copy
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.s3_utils import  upload_json_to_s3
from utils.db_utils import save_message
from datetime import datetime

# ---- STATE TYPE ----

class SchemaDiscoveryState(TypedDict, total=False):
    pending_chunks: List[str]   
    current_chunk : str         # Raw JSON chunks (as strings)
    partial_schemas: List[dict]          # Intermediate schema JSONs
    final_schema: dict    
    final_summary: str 
    summaries : List[str]
     # Final schema output
    count:int
    ai_message_context: str              # Full context from the latest AI message
    processing_mode: str                 # "schema" or "summarize"
    llm_suggestions: List[str]          # LLM suggestions for processing
    db_store: bool                       # Flag to control database storage, defaults to True

# ---- LLM & PROMPT SETUP ----

# model = ChatAnthropic(
#         model="claude-opus-4-0",  # or another Claude model
#         temperature=0,
#         anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
#     )
model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
openai_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
# Decision prompt for choosing between schema discovery and summarization
decision_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI assistant that analyzes user queries and AI message context to determine the best processing approach."),
    ("human", """
Given the user's query and the AI message context, determine whether to:
1. Discover schema from the data (for data analysis, exploration, or understanding structure)
2. Summarize the data (for getting insights, key points, or conclusions)

Purpose of the data: {ai_message_context}
First Chunk : {chunk}

Consider:
- Schema discovery path only to be taken if data exploration, understanding structure, analysis tasks , technical examination can be done through code execution.
- Summarization is better for: getting insights, key findings, conclusions, overview, business intelligence ,listing data in human-readable format.

Return JSON with:
- "mode": "schema" or "summarize"
- "reasoning": brief explanation of the decision
- "suggestions": list of specific processing suggestions
""")
])

# Schema discovery prompt (existing)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a data structure analyzer."),
    ("human", """
Given a chunk of structured data (usually JSON / JSON STRINGIFIED /ARRAY OF JSON OBJECTS), return:

1. `"format"` — e.g., "list of JSON objects", "newline-delimited JSON", "CSV-like", "stringified JSON", etc.
2. `"schema"` — map of field names to data types ("string", "number", "boolean", "object", "array", or "null"). For any nested JSON fields, provide their structure recursively as nested schemas.
4. `"enums"` — fields with ≤10 distinct values. Output map of field → values.

Output JSON **only** like this:
```json
{{
  "format": "...",
  "schema": {{ "field1": "string", "field2": "number", "nested": {{ "subfield": "string" }} }},
  "enums": {{ "status": ["active", "inactive"] }},
  
}}
```
Given a chunk of structured data (usually JSON), return:

- If a partial schema from previous chunks is provided, use it as context and extend or update it as needed.
- Here is the partial schema from previous chunks (if any):
{partial_schema}

{chunk}
""")
])

# Summarization prompt
summarize_prompt = ChatPromptTemplate.from_messages([
    ("system", 
"You are a summarizer that processes partial or complete tool outputs, often in JSON or plain text."),
    ("human",
"""
The tool was called to address the user query below. You are given a data chunk which may be malformed or incomplete due to chunking.

Input:
- Purpose of the data: {ai_message_context}
- Previous Summary: {previous_summary}
-Suggestions for summarization: {llm_suggestions}


Your tasks:
1. Try to parse or extract valid JSON fields (even if the chunk is broken).
2. If it's part of an array or object, extract usable substructures.
3. If parsing fails, fallback to regex or heuristic extraction.
4. Add new data to the previous summary.
5. Note if the chunk resolves any previously missing fields or entries.
6. If no new data is extractable, retain empty string.
7. Focus on extracting the specific information that was requested in the suggestions.



Chunk:
{chunk}

Your Output:
- A concise structured summary using data from this chunk and the previous summary.
- If possible, format as JSON.
- If chunk is not useful or redundant, say so.
- If chunk fills missing fields from earlier summary, update them.
- Focus on the specific information requested in the user query.

""")
])


llm_chain: Runnable = prompt | model | JsonOutputParser()
decision_chain: Runnable = decision_prompt | openai_model | JsonOutputParser()
summarize_chain: Runnable = summarize_prompt | model | JsonOutputParser()

# ---- NODES ----

def get_latest_ai_message_context(agent_state: dict) -> str:
    """Get the full context from the latest AI message."""
    latest_ai_message = agent_state.get("latest_ai_message")
    tool_output = agent_state.get("tool_output")
    
    print('------latest_ai_message------')
    print(latest_ai_message)
   
    if latest_ai_message and tool_output:
        # Get tool ID from tool output
        tool_id = tool_output.tool_call_id
        
        # Find matching tool call in latest AI message
        for tool_call in latest_ai_message.tool_calls:
            temp=tool_call.get('id')
           
            if temp == tool_id:
                # Check if tool call args has reason
                try:
                    args =tool_call.get('args')
                 
                    if "reason" in args:
                        print('------reason------')
                        print(args["reason"])
                        return args["reason"]
                except Exception as e:
                    print(f"Error in tool call args: {e}")
                    
                    
    return ""

def decide_processing_mode(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    """Decide whether to do schema discovery or summarization based on the AI message context."""
    ai_message_context = state.get("ai_message_context", "")
    # user_query = state.get("user_query", "")
    
    # Get first chunk safely
    pending_chunks = state.get("pending_chunks", [])
    first_chunk = pending_chunks[0] if len(pending_chunks) > 0 else ""
    
    # Make decision using LLM
    decision_result = decision_chain.invoke({
        # "user_query": user_query,
        "ai_message_context": ai_message_context,
        "chunk": first_chunk
    })
    
    state["processing_mode"] = decision_result.get("mode", "schema")
    state["llm_suggestions"] = decision_result.get("suggestions", [])
    
    print(f"[DECISION] Mode: {state['processing_mode']}")
    print(f"[DECISION] Reasoning: {decision_result.get('reasoning', '')}")
    print(f"[DECISION] Suggestions: {state['llm_suggestions']}")
    
    return state

def next_chunk(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    new_state = copy.deepcopy(state)
    if new_state["pending_chunks"]:
        new_state["current_chunk"] = new_state["pending_chunks"].pop(0)
        print("current chunk", len(new_state["current_chunk"]))
        
        # If we have LLM suggestions, apply them to the current chunk
        # if new_state.get("llm_suggestions"):
        #     suggestions = new_state["llm_suggestions"]
        #     print(f"[NEXT_CHUNK] Applying suggestions: {suggestions}")
            
        #     # You can add logic here to modify the chunk based on suggestions
        #     # For now, we'll just log them
        #     new_state["applied_suggestions"] = suggestions
    
    return new_state

def schema_from_chunks(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    chunk = state["current_chunk"]
    print("chunk", len(chunk))
    
    # Check if we should do schema discovery or summarization
    processing_mode = state.get("processing_mode", "schema")
    print(f"Processing mode: {processing_mode}")
    
    if processing_mode == "schema":
        # Original schema discovery logic
        partial_schemas = state.get("partial_schemas", [])
        partial_schema = partial_schemas[-1] if len(partial_schemas) > 0 else {}
        
        result = llm_chain.invoke({"chunk": chunk, "partial_schema": partial_schema})
        state.setdefault("partial_schemas", []).append(result)
        print(f"Added schema result, total schemas: {len(state.get('partial_schemas', []))}")
    else:
        # Summarization logic
        ai_message_context = state.get("ai_message_context", "")
        # user_query = state.get("user_query", "")
        print(ai_message_context)
        # print(user_query)
        # Get previous summary safely
        summaries = state.get("summaries", [])
        previous_summary = summaries[-1] if len(summaries) > 0 else ""
        
        # Get LLM suggestions safely
        llm_suggestions = state.get("llm_suggestions", [])
        current_suggestion = llm_suggestions[-1] if len(llm_suggestions) > 0 else ''
        
        print(f"Summarizing chunk, previous summaries: {len(summaries)}")
        
        
        
        try:
            summarize_result = summarize_chain.invoke({
                "chunk": chunk,
                "ai_message_context": ai_message_context,
                # "user_query": user_query,
                "llm_suggestions": current_suggestion,
                "previous_summary": previous_summary,
            })
        except Exception as e:
            print(f"Error in summarization chain: {e}")
            # Create a fallback summary
            summarize_result ={
                "summary": f"Error processing chunk: {str(e)}",
              
            }
            print(f"Created fallback summary: {summarize_result}")
        
        state.setdefault("summaries", []).append(json.dumps(summarize_result))
        print(f"Added summary result, total summaries: {len(state.get('summaries', []))}")
    
    state["count"] += 1
    return state

def check_done(state: SchemaDiscoveryState) -> str:
    processing_mode = state.get("processing_mode", "schema")
    
    if processing_mode == "schema":
        # For schema discovery, check if we have enough chunks or reached limit
        return "end" if not state["pending_chunks"] or state["count"] > 3 else "next"
    else:
        # For summarization, process all chunks
        return "end" if not state["pending_chunks"] else "next"

def merge_and_emit_tool_message(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    print("merging and emitting tool message")
    processing_mode = state.get("processing_mode", "schema")
    print("processing_mode", processing_mode)
    print("state keys:", list(state.keys()))
    print("summaries length:", len(state.get("summaries", [])))
    print("partial_schemas length:", len(state.get("partial_schemas", [])))
    if processing_mode == "schema":
        # Original schema discovery logic
        final_schema = state.get("partial_schemas")[-1]
        output_filename = "schema_discovery_results.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_schema, f, indent=2)
        print(f"Wrote schema discovery results to {output_filename}")
        return {"final_schema": final_schema}
    else:
        # Summarization logic
        summaries = state.get("summaries", [])
        if len(summaries) > 0:
            final_summary = summaries[-1]
            print("final_summary", final_summary)
            return {"final_summary": final_summary}
        else:
            print("No summaries found, returning empty summary")
            return {"final_summary": "No summary generated"}

# ---- SUBGRAPH BUILDER ----

def build_schema_discovery_subgraph(state_type=SchemaDiscoveryState) -> Runnable:
    builder = StateGraph(state_type)
    builder.set_entry_point("decide_mode")

    builder.add_node("decide_mode", decide_processing_mode)
    builder.add_node("next_chunk", next_chunk)
    builder.add_node("llm_schema", schema_from_chunks)
    builder.add_node("merge", merge_and_emit_tool_message)

    builder.add_edge("decide_mode", "next_chunk")
    builder.add_edge("next_chunk", "llm_schema")
    
    builder.add_conditional_edges(
        "llm_schema",
        check_done,
        {
            "next": "next_chunk",
            "end": "merge"
        }
    )

    builder.add_edge("merge", END)
    return builder.compile()

# ---- WRAPPER FOR AGENT STATE COMPATIBILITY ----

def schema_discovery_wrapper(agent_state: dict) -> dict:
    """
    Enhanced wrapper function that uses full AI message context and decides between
    schema discovery and summarization.
    
    Args:
        agent_state: The AgentState containing tool_chunks and other fields
        
    Returns:
        Updated AgentState with schema discovery or summarization results
    """
    # 1. Get full AI message context from the latest AI message
    ai_message_context = get_latest_ai_message_context(agent_state)
    print(f"[SCHEMA_DISCOVERY] AI message context: {ai_message_context}...")
    
    # 2. Extract relevant data from AgentState
    tool_output = agent_state.get("tool_output")
    tool_chunks = []  # Initialize with empty list
    data = None
    if tool_output and isinstance(tool_output, ToolMessage):
        print("Tool output content type:", type(tool_output.content))
        data = tool_output.content
        
        # Use the utility function to chunk data by tokens
        tool_chunks = chunk_data_by_tokens(data, max_tokens=10000, model="claude-3-opus")
        print("Tool chunks:", len(tool_chunks))
    
    # 3. Extract user query from messages
    # user_query = ""
    # messages = agent_state.get("messages", [])
    # for msg in messages:
    #     if hasattr(msg, 'content') and isinstance(msg.content, str):
    #         user_query = msg.content
    #         break
    
    # 4. Calculate data size
    data_size = estimate_token_count(data) if data else 0
    
    # 5. Create enhanced SchemaDiscoveryState
    schema_state = {
        "pending_chunks": tool_chunks,
        "partial_schemas": [],
        "final_schema": {},
        "summaries": [],
        "final_summary": "",
        "tool_messages": [],
        "count": 0,
        "ai_message_context": ai_message_context,
        # "user_query": user_query,
        "data_size": data_size,
        "processing_mode": "schema",  # Default, will be decided by LLM
        "llm_suggestions": [],
        "db_store": agent_state.get("db_store", True)  # Use db_store from agent state, default to True
    }
    
    # 6. Run the enhanced schema discovery subgraph
    schema_subgraph = build_schema_discovery_subgraph()
    response = schema_subgraph.invoke(schema_state)
    
        # 7. Prepare result based on processing mode
    processing_mode = response.get("processing_mode", "schema")
    result = {}
    
    print(f"Response keys: {list(response.keys())}")
    print(f"Processing mode from response: {processing_mode}")
    
    if processing_mode == "schema":
        final_schema = response.get("final_schema", {"Error": "No schema found"})
        result = {
            "data_schema": final_schema,
        }
        try:
            bucket_name = os.getenv('AWS_BUCKET', 'your-test-bucket-name')
            s3_upload = upload_json_to_s3(
                data=data,
                bucket_name=bucket_name,
                key=f"test-uploads/actual_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            result["data_uri"] = s3_upload.get('https_url')
        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
            result["data_uri"] = ""
    else:
        final_summary = response.get("final_summary", {"Error": "No summary found"})
        result = {
            "data_summary": final_summary,
            "processing_mode": "summarize",
        }
    
    # Upload tool output content to S3
   
    
    print(f"[SCHEMA_DISCOVERY] Processing mode: {processing_mode}")
    print(f"[SCHEMA_DISCOVERY] Result: {result}")
    
    json_result = json.dumps(result)
    tool_call_id = agent_state['tool_output'].tool_call_id
    tool_msg = ToolMessage(
        tool_call_id=tool_call_id,
        content=json_result
    )
    
    # 8. Save the enhanced result message to database (only if db_store is True)
    session_id = agent_state.get("session_id")
    db_store = agent_state.get("db_store", True)
    
    if session_id and db_store:
        try:
            save_message(
                session_id=session_id,
                message_type="ToolMessage",
                content={
                    "content": json_result,
                    "tool_call_id": tool_call_id
                },
                metadata={
                    "node": "schema_discovery_wrapper", 
                    "timestamp": str(datetime.now()),
                    "schema_discovery": True,
                    "processing_mode": processing_mode,
                    "data_uri": result.get("data_uri", ""),
                    "nested_subgraph": True,
                    "optional": True
                }
            )
            print(f"[SCHEMA_DISCOVERY] Saved {processing_mode} result to session {session_id}")
        except Exception as e:
            print(f"[SCHEMA_DISCOVERY] Failed to save result: {e}")
    elif not db_store:
        print(f"[SCHEMA_DISCOVERY] Database storage disabled (db_store=False)")
    
    return {'tool_output': None, 'messages': [tool_msg]}