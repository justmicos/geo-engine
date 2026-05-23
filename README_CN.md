<p align="center">
  <img src="https://img.shields.io/badge/KEngine-知识引擎-blue?style=for-the-badge" alt="KEngine">
  <img src="https://img.shields.io/badge/许可证-MIT-green?style=for-the-badge" alt="MIT">
  <img src="https://img.shields.io/badge/Multi-Provider-FF8800?style=for-the-badge" alt="Multi-Provider">
</p>

<p align="center">
  <a href="README.md">English</a> · <b>中文</b>
</p>

<h1 align="center">KEngine</h1>
<p align="center"><b>开源知识库平台 — 多 Provider AI + 自主进化 + 本地微调</b></p>
<p align="center"><i>上传 · 整理 · 搜索 · 问答 — 你的私有、自托管、AI 驱动的知识引擎。</i></p>

---

## 什么是 KEngine？

KEngine 是一个自托管的开源知识库平台，将文档转化为可搜索、AI 增强的知识资产。上传文件后自动处理、切片、向量化并建立索引 —— 随时进行语义搜索和 AI 问答。

你的数据永远留在你的基础设施上。

---

## v2.1 新特性

### 🔄 多 Provider 支持

不再局限于 DeepSeek！支持所有主流大模型：

| Provider | 类型 | 模型示例 |
|----------|------|---------|
| OpenAI | 云端 | gpt-4o, gpt-4o-mini, o1 |
| Anthropic | 云端 | claude-sonnet-4, claude-opus-4 |
| Google | 云端 | gemini-2.5-pro, gemini-2.0-flash |
| DeepSeek | 云端 | deepseek-chat, deepseek-reasoner |
| Azure | 云端 | gpt-4o (Azure) |
| AWS Bedrock | 云端 | claude-sonnet-4-v2 |
| 硅基流动 | 云端 | DeepSeek-V3, Qwen2.5 |
| 智谱 AI | 云端 | GLM-4+, CogView |
| 月之暗面 | 云端 | moonshot-v1-8k |
| 阿里通义 | 云端 | qwen-max, qwen-turbo |
| 百度千帆 | 云端 | ERNIE 4.0 |
| **Ollama** | **本地** | **qwen2.5, llama3.1** |
| **LM Studio** | **本地** | **任意 GGUF 模型** |
| **vLLM** | **本地** | **任意 HF 模型** |
| **llama.cpp** | **本地** | **任意 GGUF 模型** |

两种模式：
- **AI Gateway 模式**（推荐）：所有 AI 请求通过 `ai-gateway:19090`，根据模型名前缀自动路由
- **直连模式**：GEOFlow 内置的数据库驱动方式（传统模式）

### 🧠 知识库自主进化

知识库 **随时间自我提升**：
- **质量评分**：AI 评估内容质量、相关性和时效性
- **去重合并**：自动检测并标记重复/相似片段
- **摘要生成**：长内容自动生成精简摘要
- **交叉引用**：发现并链接相关知识片段
- **过期归档**：长期未访问的低质量内容自动归档

```env
EVOLUTION_ENABLED=true
EVOLUTION_INTERVAL_HOURS=24
EVOLUTION_MODEL=deepseek-chat
```

### 🔧 本地模型微调

基于知识库内容微调本地大模型：
- **LoRA/QLoRA/全量微调**，支持 Unsloth（首选）和 PEFT
- **自动收集训练数据**，从知识库 chunks 生成 Alpaca/ShareGPT 格式
- **GPU 加速训练**，Docker 容器化一键启动
- **导出 LoRA 适配器**，可部署到本地推理引擎

```bash
make fine-tune-collect      # 收集训练数据
make fine-tune-start        # 启动微调
make fine-tune-logs         # 监控进度
```

---

## 快速开始

### 环境要求
Docker 24+, Docker Compose 2.20+, Git 2.30+, AI API Key（任意提供商）

### 安装
```bash
git clone https://github.com/justmicos/kengine.git
cd kengine
make dev-setup
# 编辑 .env -> 设置至少一个 AI Provider
make dev-up
```

Windows：
```powershell
.\scripts\setup.ps1
# 编辑 .env 文件
docker compose up -d
```

打开 http://localhost:18080/admin

### 配置 AI Provider

**A) AI Gateway（推荐）**：编辑 `.env`：
```env
AI_GATEWAY_ENABLED=true
DEEPSEEK_API_KEY=sk-xxx
make dev-up-gateway
```

**B) 本地模型**：
```env
AI_GATEWAY_ENABLED=true
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:72b
```

**C) 直连模式**：
```env
AI_GATEWAY_ENABLED=false
AI_API_KEY=sk-xxx
AI_API_URL=https://api.deepseek.com/v1
```

---

## 命令

```bash
make dev-up              # 启动核心服务
make dev-up-all          # 启动所有服务（含 Gateway + 微调）
make dev-up-gateway      # 启动核心 + AI Gateway
make dev-down            # 停止所有
make evolve-run          # 手动触发知识进化
make ai-gateway-test     # 测试 AI Gateway
make fine-tune-start     # 启动微调
```

## 项目结构

```
geo-engine/
├── ai-gateway/           # 多 Provider AI 路由网关
│   ├── server.py         # FastAPI 服务器
│   ├── router.py         # 基于模型名的路由
│   ├── config.py         # Provider 配置
│   ├── providers/        # Provider 实现
│   └── Dockerfile
├── fine-tune/            # 本地模型微调管道
│   ├── fine_tune.py      # 训练编排
│   ├── dataset.py        # 数据集处理
│   └── Dockerfile
├── patches/              # GEOFlow 补丁
├── config/               # Nginx 等配置
├── scripts/              # 安装脚本
├── .env.example          # 完整配置参考
├── docker-compose.yml    # Docker 编排
└── Makefile              # 命令入口
```

## 许可证

MIT License
