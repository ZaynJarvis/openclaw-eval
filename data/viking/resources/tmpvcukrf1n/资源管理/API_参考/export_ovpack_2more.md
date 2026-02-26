### export_ovpack()

将资源树导出为 `.ovpack` 文件。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | 要导出的 Viking URI |
| to | str | 是 | - | 目标文件路径 |

**Python SDK (Embedded / HTTP)**

```python
path = client.export_ovpack(
    "viking://resources/my-project/",
    "./exports/my-project.ovpack"
)
print(f"Exported to: {path}")
```

**HTTP API**

```
POST /api/v1/pack/export
```

```bash
curl -X POST http://localhost:1933/api/v1/pack/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "uri": "viking://resources/my-project/",
    "to": "./exports/my-project.ovpack"
  }'
```

**CLI**

```bash
openviking export viking://resources/my-project/ ./exports/my-project.ovpack
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "file": "./exports/my-project.ovpack"
  },
  "time": 0.1
}
```

---

### import_ovpack()

导入 `.ovpack` 文件。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file_path | str | 是 | - | 本地 `.ovpack` 文件路径 |
| parent | str | 是 | - | 目标父级 URI |
| force | bool | 否 | False | 覆盖已有资源 |
| vectorize | bool | 否 | True | 导入后触发向量化 |

**Python SDK (Embedded / HTTP)**

```python
uri = client.import_ovpack(
    "./exports/my-project.ovpack",
    "viking://resources/imported/",
    force=True,
    vectorize=True
)
print(f"Imported to: {uri}")

client.wait_processed()
```

**HTTP API**

```
POST /api/v1/pack/import
```

```bash
curl -X POST http://localhost:1933/api/v1/pack/import \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "file_path": "./exports/my-project.ovpack",
    "parent": "viking://resources/imported/",
    "force": true,
    "vectorize": true
  }'
```

**CLI**

```bash
openviking import ./exports/my-project.ovpack viking://resources/imported/ --force
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "uri": "viking://resources/imported/my-project/"
  },
  "time": 0.1
}
```

---