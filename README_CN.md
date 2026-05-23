# GEOEngine — GEO 内容工程基础设施

[![状态](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)]()
[![许可证](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)]()
[![PHP](https://img.shields.io/badge/PHP_8.2+-777BB4?style=for-the-badge&logo=php)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_pgvector-336791?style=for-the-badge&logo=postgresql)]()

> [English](README.md) | **中文**

**知识沉淀 → AI 生成 → 审核发布 → 多站分发 → 效果追踪** — 将可信知识转化为可管理、可发布、可追踪、可同步到多端的 GEO 内容资产。

---

## 系统架构

```mermaid
flowchart TB
    subgraph User["用户层"]
        A[管理员] --> B[Web 后台]
        C[API 客户端] --> D[REST API]
    end
    subgraph Core["核心引擎"]
        B --> E[Laravel 12]
        D --> E
        E --> F[(PostgreSQL + pgvector)]
        E --> G[(Redis 缓存/队列)]
    end
    subgraph Workers["后台任务"]
        H[调度器] --> I[队列工人]
        I --> J[AI API]
        I --> K[(知识库向量)]
    end
    subgraph Output["输出管线"]
        L[审核发布] --> M[文章库]
        M --> N[分发队列]
        N --> O[目标站点]
    end
    subgraph Analytics["分析"]
        R[访问日志] --> S[仪表盘]
        T[AI 爬虫] --> S
    end
    E --> L; J --> M; K --> I; S --> E
```

## 端到端工作流

```mermaid
flowchart LR
    subgraph In["输入"]
        KB[知识库] --> VC[向量化]
        TL[标题库] --> TP[标题池]
        KL[关键词库] --> KP[关键词池]
    end
    subgraph P["处理"]
        VC --> RAG; TP --> TASK[任务引擎]
        KP --> TASK; RAG --> TASK
        TASK --> AI[AI 生成 + RAG]
    end
    subgraph Rv["审核"]
        AI --> DRAFT[草稿] --> REVIEW[审核] --> PUBLISH{通过?}
        PUBLISH -->|是| PUB[已发布]
        PUBLISH -->|否| REJ[已拒绝]
    end
    subgraph O["输出"]
        PUB --> LOCAL[本地] --> STATS[分析]
        PUB --> DIST[分发] --> SITES[目标站点] --> STATS
    end
```

## 任务生命周期

```mermaid
stateDiagram-v2
    [*] --> 已创建: 管理员创建
    已创建 --> 已调度: 调度器拾取
    已调度 --> 生成中: 队列启动
    生成中 --> 草稿就绪: AI 返回
    生成中 --> 失败: API 错误
    失败 --> 已调度: 重试
    草稿就绪 --> 审核中: 管理员审查
    审核中 --> 已发布: 批准
    审核中 --> 已拒绝: 驳回
    已发布 --> 已分发: 推送目标站
    已发布 --> 已归档: 手动
    已归档 --> [*]
```

## 功能

### 知识引擎
上传文档 → 自动切片 → 向量嵌入 → pgvector 存储 → RAG 召回 → AI 生成

### 内容工厂
| 模块 | 功能 |
|------|------|
| 标题库 | AI/手动标题，智能采样 |
| 关键词库 | SEO 关键词分组 |
| 图片库 | 图片管理，自动同步 |
| 任务自动化 | 定时生成 + 审核关卡 |

### 分发网络
创建渠道 → 生成目标包 → 部署 Agent → 内容推送 → 健康监控

## 快速开始

```bash
git clone https://github.com/justmicos/geo-engine.git
cd geo-engine
# 编辑 .env → 设置 AI_API_KEY
make dev-setup
make dev-up
# 打开 http://localhost:18080/geo_admin
```

## 配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| AI_API_KEY | **是** | - | AI API 密钥 |
| AI_API_URL | 否 | https://api.deepseek.com/v1 | AI 端点 |
| AI_MODEL | 否 | deepseek-chat | 生成模型 |
| APP_PORT | 否 | 18080 | Web 端口 |

## 许可证

MIT License
