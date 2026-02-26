### 列出资源

**Python SDK (Embedded / HTTP)**

```python
# 列出所有资源
entries = client.ls("viking://resources/")

# 列出详细信息
for entry in entries:
    type_str = "dir" if entry['isDir'] else "file"
    print(f"{entry['name']} - {type_str}")

# 简单路径列表
paths = client.ls("viking://resources/", simple=True)
# Returns: ["project-a/", "project-b/", "shared/"]

# 递归列出
all_entries = client.ls("viking://resources/", recursive=True)
```

**HTTP API**

```
GET /api/v1/fs/ls?uri={uri}&simple={bool}&recursive={bool}
```

```bash
# 列出所有资源
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=viking://resources/" \
  -H "X-API-Key: your-key"

# 简单路径列表
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=viking://resources/&simple=true" \
  -H "X-API-Key: your-key"

# 递归列出
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=viking://resources/&recursive=true" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
# 列出所有资源
openviking ls viking://resources/

# 简单路径列表
openviking ls viking://resources/ --simple

# 递归列出
openviking ls viking://resources/ --recursive
```

**响应**

```json
{
  "status": "ok",
  "result": [
    {
      "name": "project-a",
      "size": 4096,
      "isDir": true,
      "uri": "viking://resources/project-a/"
    }
  ],
  "time": 0.1
}
```

---

### 读取资源内容

**Python SDK (Embedded / HTTP)**

```python
# L0：摘要
abstract = client.abstract("viking://resources/docs/")

# L1：概览
overview = client.overview("viking://resources/docs/")

# L2：完整内容
content = client.read("viking://resources/docs/api.md")
```

**HTTP API**

```bash
# L0：摘要
curl -X GET "http://localhost:1933/api/v1/content/abstract?uri=viking://resources/docs/" \
  -H "X-API-Key: your-key"

# L1：概览
curl -X GET "http://localhost:1933/api/v1/content/overview?uri=viking://resources/docs/" \
  -H "X-API-Key: your-key"

# L2：完整内容
curl -X GET "http://localhost:1933/api/v1/content/read?uri=viking://resources/docs/api.md" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
# L0：摘要
openviking abstract viking://resources/docs/

# L1：概览
openviking overview viking://resources/docs/

# L2：完整内容
openviking read viking://resources/docs/api.md
```

**响应**

```json
{
  "status": "ok",
  "result": "Documentation for the project API, covering authentication, endpoints...",
  "time": 0.1
}
```

---

### 移动资源

**Python SDK (Embedded / HTTP)**

```python
client.mv(
    "viking://resources/old-project/",
    "viking://resources/new-project/"
)
```

**HTTP API**

```
POST /api/v1/fs/mv
```

```bash
curl -X POST http://localhost:1933/api/v1/fs/mv \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "from_uri": "viking://resources/old-project/",
    "to_uri": "viking://resources/new-project/"
  }'
```

**CLI**

```bash
openviking mv viking://resources/old-project/ viking://resources/new-project/
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "from": "viking://resources/old-project/",
    "to": "viking://resources/new-project/"
  },
  "time": 0.1
}
```

---