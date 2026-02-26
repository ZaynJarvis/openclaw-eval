### add_resource()

向知识库添加资源。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | str | 是 | - | 本地文件路径、目录路径或 URL |
| target | str | 否 | None | 目标 Viking URI（必须在 `resources` 作用域内） |
| reason | str | 否 | "" | 添加该资源的原因（可提升搜索相关性） |
| instruction | str | 否 | "" | 特殊处理指令 |
| wait | bool | 否 | False | 等待语义处理完成 |
| timeout | float | 否 | None | 超时时间（秒），仅在 wait=True 时生效 |

**Python SDK (Embedded / HTTP)**

```python
result = client.add_resource(
    "./documents/guide.md",
    reason="User guide documentation"
)
print(f"Added: {result['root_uri']}")

client.wait_processed()
```

**HTTP API**

```
POST /api/v1/resources
```

```bash
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "path": "./documents/guide.md",
    "reason": "User guide documentation"
  }'
```

**CLI**

```bash
openviking add-resource ./documents/guide.md --reason "User guide documentation"
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "status": "success",
    "root_uri": "viking://resources/documents/guide.md",
    "source_path": "./documents/guide.md",
    "errors": []
  },
  "time": 0.1
}
```

**示例：从 URL 添加**

**Python SDK (Embedded / HTTP)**

```python
result = client.add_resource(
    "https://example.com/api-docs.md",
    target="viking://resources/external/",
    reason="External API documentation"
)
client.wait_processed()
```

**HTTP API**

```bash
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "path": "https://example.com/api-docs.md",
    "target": "viking://resources/external/",
    "reason": "External API documentation",
    "wait": true
  }'
```

**CLI**

```bash
openviking add-resource https://example.com/api-docs.md --to viking://resources/external/ --reason "External API documentation"
```

**示例：等待处理完成**

**Python SDK (Embedded / HTTP)**

```python
# 方式 1：内联等待
result = client.add_resource("./documents/guide.md", wait=True)
print(f"Queue status: {result['queue_status']}")

# 方式 2：单独等待（适用于批量处理）
client.add_resource("./file1.md")
client.add_resource("./file2.md")
client.add_resource("./file3.md")

status = client.wait_processed()
print(f"All processed: {status}")
```

**HTTP API**

```bash
# 内联等待
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"path": "./documents/guide.md", "wait": true}'

# 批量添加后单独等待
curl -X POST http://localhost:1933/api/v1/system/wait \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{}'
```

**CLI**

```bash
openviking add-resource ./documents/guide.md --wait
```

---