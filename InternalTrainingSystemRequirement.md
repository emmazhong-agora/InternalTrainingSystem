# 内部技术支持团队培训资料管理系统 — 需求规格说明书

**版本**：1.0  
**日期**：2025年10月20日  
**作者**：产品与工程团队

---

## 1. 概述

本系统旨在为内部技术支持团队提供一个集中化、智能化的培训资料管理与学习平台。系统支持视频上传、组织、播放，并集成基于 Agora Conversational AI 引擎的语音聊天助手，结合 RAG（Retrieval-Augmented Generation）技术，实现上下文感知的智能问答，提升学习效率与体验。

---

## 2. 功能需求

### 2.1 用户认证与权限管理

- **用户注册/登录**：
  - 用户通过邮箱和密码注册账户。
  - 支持登录、登出、密码重置。
  - 所有页面（除登录页外）需身份验证。

- **用户角色**：
  - 初始仅支持 **普通用户**（技术支持工程师）。
  - 后续可扩展管理员角色（本版本暂不实现）。

- **学习进度追踪**：
  - 系统记录每个用户对每个视频的：
    - 最后播放时间戳（秒）
    - 是否完成观看（≥95% 视频时长视为完成）
    - 首次/最近观看时间
  - 数据持久化存储于数据库。

---

### 2.2 视频管理

- **视频上传**：
  - 用户可上传 `.mp4` 格式视频文件。
  - 同时必须上传一个同名 `.json` 文件作为 **知识库转录文件**（例如：`training1.mp4` + `training1.json`）。
  - 前端校验：文件扩展名、非空、大小限制（建议 ≤500MB）。
  - 后端校验：MIME 类型、文件完整性。

- **视频组织**：
  - 支持创建/重命名/删除**目录（文件夹）**。
  - 用户可将视频**移动**到任意目录。
  - 目录结构为树形，支持嵌套（深度不限）。
  - 视频在系统中以“路径”唯一标识（如 `/onboarding/network-basics.mp4`）。

- **视频删除**：
  - 用户可删除自己上传的视频及其关联的 JSON 文件。
  - 删除操作需二次确认。

- **视频列表与播放**：
  - 按目录层级展示视频列表。
  - 点击视频进入**播放页面**。
  - 播放器支持：播放/暂停、进度条、音量控制、全屏。

---

### 2.3 视频播放页面

- **视频播放器**：
  - 使用 HTML5 `<video>` 标签或开源播放器（如 Video.js）。
  - 实时上报播放进度（每 10 秒或用户暂停时）至后端，用于更新学习进度。

- **AI 语音聊天助手面板**：
  - 右侧固定侧边栏，包含：
    - 语音输入按钮（麦克风）
    - 文字聊天窗口（显示历史对话）
    - 文字输入框（备用）
  - 用户可通过**语音或文字**向助手提问。

- **AI 助手集成**：
  - 使用 **Agora Conversational AI Engine** 实现语音识别（ASR）、语音合成（TTS）和对话管理。
  - 后端调用 Agora Convo AI API，配置如下链路（示例）：
    - ASR: Azure
    - LM: GPT-4o 或客户指定模型
    - TTS: Azure
  - Agora 会话需绑定当前用户的上下文（如 `user_id`, `video_path`）。

---

### 2.4 知识库与 RAG 系统

- **知识库上传**：
  - 每个视频必须关联一个 `.json` 文件，格式如下：
    ```json
    {
      "video_id": "unique_id_or_path",
      "transcript": [
        {"start": 0.0, "end": 5.2, "text": "Welcome to the training..."},
        {"start": 5.3, "end": 12.1, "text": "Today we'll cover networking basics..."}
      ],
      "metadata": {
        "title": "Networking Fundamentals",
        "author": "Jane Doe",
        "tags": ["network", "TCP/IP"]
      }
    }
    ```

- **向量化与存储**：
  - 视频上传成功后，后端自动：
    1. 解析 JSON 文件
    2. 将 `transcript.text` 分块（chunking）
    3. 使用嵌入模型（如 `text-embedding-3-small` 或开源 `bge-small`）生成向量
    4. 存入向量数据库（如 **Pinecone**, **Weaviate**, 或 **Qdrant**）
    5. 关联 `video_id` 和元数据

- **RAG 检索**：
  - 当用户向 AI 助手提问时，后端执行：
    1. 获取当前视频的 `video_id`
    2. 对用户问题进行向量化
    3. 在向量库中**按 `video_id` 过滤**，检索 Top-3 相关文本片段
    4. 将检索结果作为上下文注入 LLM Prompt
  - LLM 回答必须基于检索内容，避免幻觉。

- **Prompt 示例（供 LLM 使用）**：
  ```
  你是一位技术支持培训助手。请根据以下从当前培训视频中检索到的内容回答问题。
  如果内容不相关或无法回答，请说“根据当前视频内容，我无法回答该问题”。

  检索内容：
  {retrieved_chunks}

  用户问题：{user_query}
  ```

---

### 2.5 数据模型（关键实体）

| 实体 | 字段 |
|------|------|
| `User` | `id`, `email`, `password_hash`, `created_at` |
| `Folder` | `id`, `name`, `parent_id`, `owner_id` |
| `Video` | `id`, `filename`, `path`, `folder_id`, `owner_id`, `duration`, `created_at` |
| `LearningProgress` | `user_id`, `video_id`, `last_position`, `completed`, `last_watched_at` |
| `KnowledgeBase` | `video_id`, `json_content`, `vector_ids`（可选） |

---

## 3. 非功能需求

- **安全性**：
  - 密码加密存储（bcrypt）
  - 文件上传防恶意脚本（仅允许 .mp4/.json）
  - 用户只能访问/操作自己上传的视频

- **性能**：
  - 视频播放流畅（支持 HTTP Range 请求）
  - RAG 检索响应时间 < 1 秒
  - 支持并发用户 ≥ 50

- **技术栈建议**：
  - 前端：React + TypeScript + Tailwind CSS
  - 后端：Python (FastAPI) 或 Node.js (NestJS)
  - 数据库：PostgreSQL
  - 向量库：Pinecone（云）或 Qdrant（自托管）
  - 文件存储：本地磁盘（开发） / AWS S3（生产）
  - Agora SDK：使用 Agora Conversational AI REST/WebSocket API

- **部署**：
  - 支持 Docker 容器化部署
  - 环境变量管理敏感配置（Agora API Key、LLM Key、DB URL 等）

---

## 4. 待定事项（TBD）

- [ ] Agora Convo AI 的具体 API 接入方式（需参考 Agora 文档）
- [ ] 是否支持视频自动转录（当前要求用户上传 JSON）
- [ ] 管理员功能范围（后续迭代）

---

## 5. 附录：Agora Conversational AI 集成要点

- 使用 Agora 提供的 **Conversational AI Studio** 配置 ASR/LM/TTS 链路。
- 每个视频播放会话应创建独立的 Agora **Agent Session**。
- 会话上下文需传递 `video_id`，用于 RAG 检索过滤。
- 语音输入通过浏览器 `Web Audio API` → 发送至 Agora ASR。
- TTS 音频流通过 Web Audio 播放。

---

> ✅ 此文档可直接用于指导 LLM 生成系统架构、API 设计、前端组件及后端服务代码。建议分模块开发：1) 用户系统 2) 视频管理 3) 播放器 4) RAG 后端 5) Agora 集成。