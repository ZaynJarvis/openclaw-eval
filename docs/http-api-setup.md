# OpenClaw HTTP API Configuration Guide

This guide explains how to configure OpenClaw to enable the HTTP API endpoints for programmatic access.

## Prerequisites

- OpenClaw installed and running
- Gateway service enabled
- Authentication token (password) from OpenClaw settings

---

## Step 1: Enable HTTP Endpoint

Edit your OpenClaw configuration file at `~/.openclaw/openclaw.json`:

```json
{
  "gateway": {
    "http": {
      "endpoints": {
        "chatCompletions": {
          "enabled": true
        },
        "responses": {
          "enabled": true
        }
      }
    }
  }
}
```

---

## Step 2: Get Gateway Token

Retrieve your authentication token from OpenClaw settings:

```bash
# View current config to find the token
cat ~/.openclaw/openclaw.json | grep -A 5 '"token"'
```

The token is used in the `Authorization: Bearer <token>` header for all API requests.

---

## Step 3: API Usage Examples

### Chat Completions API

The Chat Completions API is compatible with OpenAI's format:

```bash
curl http://127.0.0.1:18789/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer xxx" \
  -H "x-openclaw-session-key: chatcmpl_d518440f-6070-4601-b6a6-e10dfdca5f54" \
  -d '{
    "messages": [{"role": "user", "content": "Hi Im Zayn"}],
    "user": "eval-1"
  }'
```

**Follow-up message in same session:**

```bash
curl http://127.0.0.1:18789/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer xxx" \
  -d '{
    "messages": [{"role": "user", "content": "whats my name"}],
    "user": "eval-1"
  }'
```

### Responses API

The Responses API is OpenClaw's native endpoint:

```bash
curl -sS http://127.0.0.1:18789/v1/responses \
  -H "Authorization: Bearer xxx" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-session-key: claw-1" \
  -d '{
    "model": "openclaw",
    "input": "what did I just say?"
  }'
```

---

## Session Management

### Using `user` Parameter

If you include a `user` string in the request, the Gateway automatically derives a stable session key from it:

```bash
# Same user = same session
curl ... -d '{"user": "eval-1", ...}'
```

### Using Explicit Session Key

Alternatively, use the `x-openclaw-session-key` header:

```bash
curl -H "x-openclaw-session-key: my-session-123" ...
```

### Important Notes

1. **Responses & ChatCompletion sessions are not shared** - A session created via `/v1/responses` is separate from one created via `/v1/chat/completions`

2. **Session key not returned in response** - You must use either `user` or `x-openclaw-session-key` to maintain session continuity

3. **Resetting sessions** - To start fresh, change the `user` value or session key. The `/new` command via API is not currently functional.

4. **WebSocket limitation** - WebSocket functionality is not working via HTTP API. Other features should work normally.

---

## LanceDB Memory Plugin Configuration

To enable persistent memory with LanceDB:

### 1. Update Plugin Files

Update files in `/opt/homebrew/lib/node_modules/openclaw/extensions/memory-lancedb/` from the relevant PR.

### 2. Update Configuration

Add to `~/.openclaw/openclaw.json`:

```json
{
  "plugins": {
    "allow": ["memory-lancedb"],
    "slots": {
      "memory": "memory-lancedb"
    },
    "entries": {
      "memory-lancedb": {
        "enabled": true,
        "config": {
          "embedding": {
            "apiKey": "your-api-key",
            "model": "doubao-embedding-vision-251215",
            "provider": "doubao",
            "url": "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal"
          },
          "autoCapture": true,
          "autoRecall": true
        }
      }
    }
  }
}
```

### 3. Enable and Restart

```bash
openclaw plugins enable memory-lancedb
openclaw gateway restart
```

### 4. Verify Installation

Check that the LanceDB data directory exists:

```bash
ls ~/.openclaw/memory/lancedb/memories.lance/data
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure Gateway is running: `openclaw gateway status` |
| 401 Unauthorized | Check your bearer token is correct |
| Session not persisting | Verify you're using the same `user` or session key |
| LanceDB not working | Check plugin is enabled: `openclaw plugins list` |

---

## References

- [OpenClaw Documentation](https://docs.openclaw.ai)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat)
