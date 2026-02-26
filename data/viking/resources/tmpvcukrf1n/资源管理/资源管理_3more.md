# 资源管理

资源是智能体可以引用的外部知识。本指南介绍如何添加、管理和检索资源。

## 支持的格式

| 格式 | 扩展名 | 处理方式 |
|------|--------|----------|
| PDF | `.pdf` | 文本和图像提取 |
| Markdown | `.md` | 原生支持 |
| HTML | `.html`, `.htm` | 清洗后文本提取 |
| 纯文本 | `.txt` | 直接导入 |
| JSON/YAML | `.json`, `.yaml`, `.yml` | 结构化解析 |
| 代码 | `.py`, `.js`, `.ts`, `.go`, `.java` 等 | 语法感知解析 |
| 图像 | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | VLM 描述 |
| 视频 | `.mp4`, `.mov`, `.avi` | 帧提取 + VLM |
| 音频 | `.mp3`, `.wav`, `.m4a` | 语音转录 |
| 文档 | `.docx` | 文本提取 |

## 处理流程

```
Input -> Parser -> TreeBuilder -> AGFS -> SemanticQueue -> Vector Index
```

1. **Parser**：根据文件类型提取内容
2. **TreeBuilder**：创建目录结构
3. **AGFS**：将文件存储到虚拟文件系统
4. **SemanticQueue**：异步生成 L0/L1
5. **Vector Index**：建立语义搜索索引