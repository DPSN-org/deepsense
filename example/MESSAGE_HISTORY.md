# Message History vs Checkpointer State

## Overview

The example server maintains **two completely separate systems** for different purposes:

1. **Message History** - Managed by `server.py` via `MessageHistory` class
   - User and agent messages for conversation display
   - Stored in `messages` collection
   
2. **Checkpointer State** - Managed by `checkpointer.py` (LangGraph)
   - Full LangGraph workflow state for workflow resumption
   - Stored in `checkpoints` collection

## Message History

### Purpose
- Display conversation history to users
- Show user queries and agent responses
- Simple, readable format for UI/API consumption

### Implementation
- **Managed by**: `server.py` - `MessageHistory` class
- **Completely separate** from `checkpointer.py`
- **Collection**: `messages`
- **Fields**:
  - `message_id`: Unique message identifier
  - `session_id`: Session identifier
  - `message_type`: `'user'` or `'agent'`
  - `content`: Message content (simple text)
  - `timestamp`: When the message was created
  - `sequence_order`: Order in conversation
  - `metadata`: Additional metadata

### API Endpoints

#### Get Message History
```http
GET /sessions/{session_id}/messages?limit=100
```

Returns:
```json
[
  {
    "message_id": "uuid",
    "session_id": "session-123",
    "message_type": "user",
    "content": {"text": "What is bitcoin?"},
    "timestamp": "2024-01-01T12:00:00",
    "sequence_order": 1
  },
  {
    "message_id": "uuid",
    "session_id": "session-123",
    "message_type": "agent",
    "content": {"text": "Bitcoin is a cryptocurrency..."},
    "timestamp": "2024-01-01T12:00:05",
    "sequence_order": 2
  }
]
```

## Checkpointer State

### Purpose
- Store complete LangGraph workflow state
- Enable workflow resumption from checkpoints
- Maintain all state variables, node history, tool results

### Implementation
- **Managed by**: `deepsense/checkpointer.py` - `MongoDBCheckpointer` class
- **Uses**: LangGraph's `MongoDBSaver`
- **Collection**: `checkpoints` (managed by LangGraph)
- **Contains**:
  - Complete workflow state
  - All messages (System, Human, AI, Tool)
  - State variables
  - Node execution history
  - Tool call results

### API Endpoints

#### Get Workflow State
```http
GET /sessions/{session_id}/state
```

Returns:
```json
{
  "session_id": "session-123",
  "state": {
    "messages": [...],
    "session_id": "...",
    "tool_outputs": [...]
  },
  "checkpoint_id": "...",
  "checkpoint_ns": "..."
}
```

## Key Differences

| Feature | Message History | Checkpointer State |
|---------|----------------|-------------------|
| **Purpose** | Display conversation | Workflow resumption |
| **Format** | Simple user/agent messages | Complete workflow state |
| **Storage** | `messages` collection | `checkpoints` collection |
| **Content** | User queries + agent responses | All messages + state variables |
| **Use Case** | UI display, API responses | Workflow execution |
| **Managed By** | `server.py` (`MessageHistory`) | `checkpointer.py` (LangGraph) |
| **Decoupled** | ✅ Yes - completely separate | ✅ Yes - completely separate |

## How They Work Together

1. **User sends query** → Saved to message history as `'user'` message
2. **Workflow executes** → LangGraph checkpointer saves workflow state
3. **Agent responds** → Saved to message history as `'agent'` message
4. **Next query** → 
   - Message history provides conversation context
   - Checkpointer state enables workflow resumption

## Example Flow

```python
# 1. User sends query
POST /query
{
  "query": "What is bitcoin?",
  "session_id": "session-123"
}

# Server saves to message history (via MessageHistory):
message_history.save_message(
    session_id="session-123",
    message_type="user",
    content={"text": "What is bitcoin?"}
)

# 2. Workflow executes
# LangGraph checkpointer automatically saves state (via checkpointer)

# 3. Agent responds
# Server saves to message history (via MessageHistory):
message_history.save_message(
    session_id="session-123",
    message_type="agent",
    content={"text": "Bitcoin is..."}
)

# 4. Retrieve conversation history
GET /sessions/session-123/messages
# Returns user and agent messages (from MessageHistory)

# 5. Retrieve workflow state (if needed)
GET /sessions/session-123/state
# Returns complete LangGraph state (from checkpointer)
```

## Benefits of Separation

1. **Clean API**: Message history is simple and readable
2. **Efficient**: Don't need to parse complex state for display
3. **Flexible**: Can format messages differently for UI
4. **Maintainable**: Clear separation of concerns
5. **Performance**: Faster retrieval of conversation history

