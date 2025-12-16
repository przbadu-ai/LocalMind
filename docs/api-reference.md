# LocalMind API Reference

Base URL: `http://127.0.0.1:52817/api/v1`

## Authentication

Currently, the API does not require authentication as it's designed for local use only.

---

## Chat Endpoints

### Stream Chat Response

Stream a chat response using Server-Sent Events (SSE).

```http
POST /chat/stream
Content-Type: application/json
```

**Request Body:**

```json
{
  "message": "string",
  "conversation_id": "string (optional)",
  "temperature": 0.7,
  "include_transcript": true
}
```

**Response:** `text/event-stream`

SSE events emitted:

| Event Type | Data | Description |
|------------|------|-------------|
| `youtube_detected` | `{"video_id": "...", "url": "..."}` | YouTube URL found in message |
| `transcript_status` | `{"success": true/false, "error": "..."}` | Transcript fetch result |
| `content` | `{"content": "..."}` | Streaming response chunk |
| `done` | `{"message_id": "..."}` | Response complete |
| `error` | `{"error": "..."}` | Error occurred |

**Example:**

```bash
curl -X POST http://127.0.0.1:52817/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}' \
  --no-buffer
```

---

## Chats Endpoints

### List Recent Chats

```http
GET /chats?limit=20&include_archived=false
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Maximum chats to return |
| `include_archived` | boolean | false | Include archived chats |

**Response:**

```json
[
  {
    "id": "chat_abc123",
    "title": "Chat about Python",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T11:00:00Z",
    "message_count": 5,
    "is_archived": false,
    "is_pinned": true
  }
]
```

### Create Chat

```http
POST /chats
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "New Chat (optional)",
  "description": "optional description",
  "system_prompt": "optional system prompt"
}
```

**Response:**

```json
{
  "id": "chat_xyz789",
  "title": "New Chat",
  "created_at": "2025-01-15T12:00:00Z",
  "message_count": 0,
  "is_archived": false,
  "is_pinned": false
}
```

### Get Chat with Messages

```http
GET /chats/{chat_id}?include_messages=true
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `chat_id` | string | Chat ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_messages` | boolean | true | Include messages |

**Response:**

```json
{
  "id": "chat_abc123",
  "title": "Chat about Python",
  "created_at": "2025-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "What is Python?",
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Python is a high-level programming language...",
      "created_at": "2025-01-15T10:30:05Z",
      "artifact_type": null,
      "artifact_data": null
    }
  ]
}
```

### Update Chat

```http
PUT /chats/{chat_id}
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "Updated Title",
  "is_archived": false,
  "is_pinned": true
}
```

### Delete Chat

```http
DELETE /chats/{chat_id}
```

**Response:** `204 No Content`

### Archive Chat

```http
POST /chats/{chat_id}/archive
```

### Pin/Unpin Chat

```http
POST /chats/{chat_id}/pin    # Pin
DELETE /chats/{chat_id}/pin  # Unpin
```

---

## YouTube Endpoints

### Extract Transcript

Fetch and cache a YouTube video transcript.

```http
POST /youtube/transcript
Content-Type: application/json
```

**Request Body:**

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "language_code": "en (optional)"
}
```

**Response:**

```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "transcript": {
    "id": "tr_abc123",
    "video_id": "dQw4w9WgXcQ",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language_code": "en",
    "is_generated": false,
    "segments": [
      {
        "text": "We're no strangers to love",
        "start": 0.0,
        "duration": 2.5
      },
      {
        "text": "You know the rules and so do I",
        "start": 2.5,
        "duration": 3.0
      }
    ],
    "full_text": "We're no strangers to love You know the rules...",
    "created_at": "2025-01-15T12:00:00Z"
  }
}
```

**Error Response:**

```json
{
  "success": false,
  "video_id": "dQw4w9WgXcQ",
  "error_type": "transcripts_disabled",
  "error_message": "Subtitles are disabled for this video"
}
```

### Get Cached Transcript

```http
GET /youtube/transcript/{video_id}
```

**Response:** Same as above

### Delete Cached Transcript

```http
DELETE /youtube/transcript/{video_id}
```

**Response:** `204 No Content`

### Get Available Languages

```http
GET /youtube/languages/{video_id}
```

**Response:**

```json
{
  "video_id": "dQw4w9WgXcQ",
  "languages": [
    {
      "code": "en",
      "name": "English",
      "is_generated": false,
      "is_translatable": true
    },
    {
      "code": "en-auto",
      "name": "English (auto-generated)",
      "is_generated": true,
      "is_translatable": false
    }
  ]
}
```

---

## MCP Server Endpoints

### List MCP Servers

```http
GET /mcp/servers
```

**Response:**

```json
[
  {
    "id": "mcp_001",
    "name": "filesystem",
    "description": "File system access",
    "server_type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
    "is_enabled": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
]
```

### Create MCP Server

```http
POST /mcp/servers
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "filesystem",
  "description": "File system access",
  "server_type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem"],
  "env": {
    "ALLOWED_DIRS": "/home/user/documents"
  },
  "is_enabled": true
}
```

### Update MCP Server

```http
PUT /mcp/servers/{server_id}
Content-Type: application/json
```

### Delete MCP Server

```http
DELETE /mcp/servers/{server_id}
```

### Start MCP Server

```http
POST /mcp/servers/{server_id}/start
```

**Response:**

```json
{
  "server_id": "mcp_001",
  "is_running": true,
  "tools_count": 5
}
```

### Stop MCP Server

```http
POST /mcp/servers/{server_id}/stop
```

### Get Server Status

```http
GET /mcp/servers/{server_id}/status
```

**Response:**

```json
{
  "server_id": "mcp_001",
  "is_running": true,
  "tools_count": 5
}
```

### List Server Tools

```http
GET /mcp/servers/{server_id}/tools
```

**Response:**

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read contents of a file",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {"type": "string"}
        },
        "required": ["path"]
      }
    }
  ]
}
```

### Call Server Tool

```http
POST /mcp/servers/{server_id}/tools/{tool_name}
Content-Type: application/json
```

**Request Body:**

```json
{
  "arguments": {
    "path": "/home/user/file.txt"
  }
}
```

**Response:**

```json
{
  "success": true,
  "result": "File contents here..."
}
```

---

## Settings Endpoints

### Get All Settings

```http
GET /settings
```

**Response:**

```json
{
  "llm": {
    "provider": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama3:instruct",
    "temperature": 0.7
  },
  "features": {
    "youtube_enabled": true,
    "mcp_enabled": true
  }
}
```

### Update Settings

```http
PUT /settings
Content-Type: application/json
```

**Request Body:**

```json
{
  "llm": {
    "model": "gpt-4"
  }
}
```

### Get LLM Configuration

```http
GET /settings/llm
```

**Response:**

```json
{
  "provider": "ollama",
  "base_url": "http://localhost:11434/v1",
  "api_key": "***masked***",
  "model": "llama3:instruct",
  "temperature": 0.7
}
```

### Update LLM Configuration

```http
PUT /settings/llm
Content-Type: application/json
```

**Request Body:**

```json
{
  "provider": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

### List Available Models

```http
GET /settings/llm/models
```

**Response:**

```json
{
  "models": [
    {"id": "llama3:instruct", "name": "Llama 3 Instruct"},
    {"id": "gpt-oss:latest", "name": "GPT-OSS Latest"},
    {"id": "mistral:latest", "name": "Mistral Latest"}
  ]
}
```

### Check LLM Health

```http
GET /settings/llm/health
```

**Response:**

```json
{
  "available": true,
  "model": "llama3:instruct"
}
```

**Error Response:**

```json
{
  "available": false,
  "error": "Connection refused"
}
```

### Test LLM Configuration

Test a configuration before saving.

```http
POST /settings/llm/test
Content-Type: application/json
```

**Request Body:**

```json
{
  "provider": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

**Response:**

```json
{
  "available": true,
  "model": "gpt-4"
}
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Rate Limiting

No rate limiting is applied for local use. For production deployments, consider adding rate limiting middleware.

---

## WebSocket Support

Currently not implemented. All real-time communication uses Server-Sent Events (SSE).
