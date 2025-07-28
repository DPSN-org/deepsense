from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage
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
    final_schema: dict                   # Final schema output
    count:int

# ---- LLM & PROMPT SETUP ----

# model = ChatAnthropic(
#         model="claude-opus-4-0",  # or another Claude model
#         temperature=0,
#         anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
#     )
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
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
llm_chain: Runnable = prompt | model | JsonOutputParser()
# ---- NODES ----

def next_chunk(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    new_state = copy.deepcopy(state)
    if new_state["pending_chunks"]:
        new_state["current_chunk"] = new_state["pending_chunks"].pop(0)
        print("current chunk", len(new_state["current_chunk"]))
    return new_state

def schema_from_chunks(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    chunk = state["current_chunk"]
    print("chunk", len(chunk))
    # prompt_values = []
    # for chunk in state["pending_chunks"]:
    #     prompt_values.append(
    #     prompt.format_messages(**{"chunk": chunk}))

# Run them all in a single batch
    # result = model.generate(prompt_values)

# Extract parsed responses (you'll manually apply the JsonOutputParser)
    # parsed = [JsonOutputParser().invoke(gen) for gen in result.generations]
    # state.setdefault("partial_schemas", parsed)

    #manually running batches
    # max_length = len(state["pending_chunks"]) if len(state["pending_chunks"]) > 5 else 5
    # for i in range (0,max_length):
    result = llm_chain.invoke({"chunk": chunk,"partial_schema": state.get("partial_schemas", [-1])})
       #  "partial_schema": state.get("partial_schemas", [-1])})
    state.setdefault("partial_schemas", []).append(result)
    state["count"] += 1
    # Write parsed results to file
    # output_filename = "schema_discovery_results.json"
    # with open(output_filename, 'w', encoding='utf-8') as f:
    #     json.dump(parsed, f, indent=2)
    # print(f"Wrote schema discovery results to {output_filename}")
    
    return state

def check_done(state: SchemaDiscoveryState) -> str:
    return "end" if not state["pending_chunks"]  or state["count"] > 3 else "next"

def merge_and_emit_tool_message(state: SchemaDiscoveryState) -> SchemaDiscoveryState:
    final_schema = state.get("partial_schemas")[-1]
    output_filename = "schema_discovery_results.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(final_schema, f, indent=2)
    print(f"Wrote schema discovery results to {output_filename}")
    # merged_schema = {}
    # enums = {}

    # for entry in partials:
    #     schema = entry.get("schema", {})
    #     for k, v in schema.items():
    #         if k not in merged_schema:
    #             merged_schema[k] = v
    #         elif merged_schema[k] != v:
    #             merged_schema[k] = "mixed"

    #     enum_block = entry.get("enums", {})
    #     for k, values in enum_block.items():
    #         enums.setdefault(k, set()).update(values)

    # final_enums = {
    #     k: sorted(list(v)) for k, v in enums.items() if len(v) <= 10
    # }

    # final_output = {
    #     "schema": merged_schema,
    #     "enums": final_enums,
    #     "data_uri": "blob://placeholder"
    # }

    # Save to state

    # Emit ToolMessage for parent LLM node
    
    return {"final_schema": final_schema}


# ---- SUBGRAPH BUILDER ----

def build_schema_discovery_subgraph(state_type=SchemaDiscoveryState) -> Runnable:
    builder = StateGraph(state_type)
    builder.set_entry_point("next_chunk")

    builder.add_node("next_chunk", next_chunk)
    builder.add_node("llm_schema", schema_from_chunks)
    builder.add_node("merge", merge_and_emit_tool_message)

    builder.add_edge("next_chunk", "llm_schema")
   # builder.set_entry_point("llm_schema")
    #builder.add_edge("llm_schema", "merge")
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
    Wrapper function that translates AgentState to SchemaDiscoveryState,
    runs the schema discovery subgraph, and merges results back to AgentState.
    
    Args:
        agent_state: The AgentState containing tool_chunks and other fields
        
    Returns:
        Updated AgentState with schema discovery results
    """
    # 1. Extract relevant data from AgentState
    tool_output = agent_state.get("tool_output")
    tool_chunks = []  # Initialize with empty list
    data = None
    if tool_output and isinstance(tool_output, ToolMessage):
        print("Tool output content type:", type(tool_output.content))
        # if isinstance(tool_output.content, str):
        #     data = tool_output.content
        #     print('data is string')
            
        # else:
        #     data = tool_output.content.get("data", "")
        #     print('data is ' +type(data))
        data=tool_output.content
        # Write data to file before chunking
        # with open('data_before_chunking.json', 'w', encoding='utf-8') as f:
        #     if isinstance(data, str):
        #         try:
        #             # Try to parse and pretty print if it's a JSON string
        #             json_data = json.loads(data)
        #             json.dump(json_data, f, indent=2)
        #         except json.JSONDecodeError:
        #             # If not valid JSON, write raw string
        #             f.write(data)
        #     else:
        #         # If data is already a dict/list, pretty print as JSON
        #         json.dump(data, f, indent=2)
        # Use the utility function to chunk data by tokens
        tool_chunks = chunk_data_by_tokens(data, max_tokens=10000, model="claude-3-opus")
        print("Tool chunks:", len(tool_chunks))
    
    # 2. Create SchemaDiscoveryState
    schema_state = {
        "pending_chunks": tool_chunks,
        "partial_schemas": [],
        "final_schema": {},
        "tool_messages": [],
        "count": 0
    }
    
    # 3. Run the schema discovery subgraph
    schema_subgraph = build_schema_discovery_subgraph()
    response = schema_subgraph.invoke(schema_state)
    print(response.get("final_schema"))
    print(response.get("partial_schemas")[-1])
    result = {}
    # Upload tool output content to S3

    try:
            # Upload the JSON content to S3 and get the URI
        bucket_name = os.getenv('AWS_BUCKET', 'your-test-bucket-name')

        s3_upload = upload_json_to_s3(data=data,bucket_name=bucket_name,
        key=f"test-uploads/actual_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        result = {
            "data_schema": response.get("final_schema", {"Error": "No schema found"}),
            "data_uri": s3_upload.get('https_url')
        }
       
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        result = {
            "data_schema": response.get("final_schema", {"Error": "No schema found"}),
            "data_uri": ""
        }
    print(result)
    json_result=json.dumps(result)
    tool_call_id = agent_state['tool_output'].tool_call_id
    tool_msg = ToolMessage(
        tool_call_id=tool_call_id,
        content=json_result
    )
    print(tool_msg)
    print('===ttooolss===')
    # 4. Merge results back into AgentState
    
    # Save the schema discovery result message to database if session_id is available
    # This is optional since schema discovery is a nested subgraph
    session_id = agent_state.get("session_id")
    if session_id:
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
                    "data_uri": result.get("data_uri", ""),
                    "nested_subgraph": True,
                    "optional": True
                }
            )
            print(f"[SCHEMA_DISCOVERY] Saved schema discovery result to session {session_id}")
        except Exception as e:
            print(f"[SCHEMA_DISCOVERY] Failed to save schema discovery result: {e}")
    
    return {'tool_output':None,'messages':[tool_msg]}