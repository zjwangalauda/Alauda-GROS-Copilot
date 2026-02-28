# Alauda Global Recruitment OS (GROS) Copilot — Release Notes

---

## V2.0 — 生产级加固：SQLite 迁移、安全防护、CI/CD 与容器化部署
**Release Date:** 2026-02-28

### 🛡️ 安全加固 (Security Hardening)
- **Prompt 注入防御**：全部 7 个 LLM 方法中，所有用户输入均以 `<user_input>` XML 标签包裹隔离。System Prompt 末尾新增防御指令，明确标记标签内容为不可信数据，阻止恶意指令穿透。
- **内容哈希升级**：知识库去重哈希从 MD5 升级为 SHA-256，提升碰撞安全性。
- **输入长度校验**：所有 LLM 入口统一强制执行 200,000 字符上限，超限时前端即时反馈错误信息。

### 🗄️ 数据层重构：JSON → SQLite (Data Layer Migration)
- **三大管理器全面迁移**：HC 管理器、候选人管理器、知识库管理器从 JSON + fcntl 文件锁迁移至 **SQLite WAL 模式**，彻底消除并发读写冲突风险。
- **单例连接池**：新增 `db.py` 模块，提供线程安全的单例数据库连接，支持外键约束与 WAL 日志模式。
- **自动数据迁移**：系统启动时自动检测旧版 JSON 文件，若存在则一次性导入 SQLite，实现无缝升级。
- **候选人历史记录**：阶段流转历史从嵌套 JSON 数组改为独立的 `candidate_history` 关系表（1:N），支持级联删除。

### 🤖 AI 引擎增强 (LLM Engine Enhancements)
- **自动重试机制**：LLM 调用新增指数退避重试策略（`tenacity`），自动处理 RateLimitError / APITimeoutError / APIConnectionError，最多重试 3 次，等待时间 1-10 秒指数递增。
- **Token 用量追踪**：每次 LLM 调用后自动记录 prompt_tokens / completion_tokens / total_tokens 至内存日志（最近 50 条），招聘数据看板新增"近期 LLM 调用记录"面板，实时展示 Token 消耗。
- **Pydantic 结构化输出**：HC 字段翻译接口采用 Pydantic Schema 强类型校验，确保 LLM 输出 JSON 严格符合 6 字段预期结构。

### 📊 业务逻辑强化 (Business Logic Hardening)
- **HC 状态机**：审批流程引入有限状态机（Pending → Approved / Rejected），终态不可逆转，非法转换抛出明确异常。
- **候选人阶段校验**：向后移动阶段或从 Rejected 恢复时强制要求填写备注，防止误操作。
- **看板一键淘汰**：Kanban 卡片新增独立"Reject"按钮，支持快速标记淘汰候选人。

### 🏗️ 工程化基建 (Infrastructure)
- **GitHub Actions CI/CD**：新增 `.github/workflows/ci.yml`，每次 Push / PR 自动执行 `ruff` 代码检查 + `pytest` 全量测试（39 个用例），确保主干稳定。
- **Docker 容器化**：新增 `Dockerfile` + `.dockerignore`，基于 `python:3.11-slim` 的轻量化镜像，一条命令即可部署。
- **CSS 分离**：215 行内联 CSS 提取至独立 `assets/theme.css` 文件，UI 调整无需修改 Python 代码。
- **类型标注**：5 个核心模块的所有公共方法全面添加参数与返回值类型标注，提升 IDE 补全与重构安全性。
- **测试套件**：39 个单元测试覆盖 HC 管理器、候选人管理器、知识库管理器、LLM 重试逻辑、Pydantic 校验与网页知识提取。
- **依赖版本锁定**：`requirements.txt` 全部采用 `==` 精确版本锁定，避免部署时因上游更新导致不可复现的构建失败。
- **README.md**：新增标准项目 README，含功能概述、快速启动、项目结构与测试指南。

---

## V1.7 — 系统完整性跃升：候选人看板、DOCX 支持、知识时效与访问认证
**Release Date:** 2026-02-27

### 🆕 P2-1：候选人 Pipeline 看板 (模块七)
- **7 阶段招聘漏斗**：Sourced → Contacted → Phone Screen → Interview → Offer → Hired / Rejected，每阶段以独立颜色编码呈现。
- **Kanban 看板视图**：每位候选人以卡片形式展示姓名、目标岗位、简历评分、最后更新日期；支持内联下拉菜单一键推进阶段。
- **顶部统计横幅**：实时显示各阶段候选人数量，HR 总监可秒读漏斗健康度。
- **候选人详情面板**：关联 HC 需求 ID、LinkedIn 主页直链、备注追加（带时间戳）、完整阶段历史记录，支持一键删除。

### 🆕 P2-2：知识片段时效性管理
- **自动设置有效期**：每条知识碎片写入时自动计算 `expires_at`（默认 90 天），可在调用时自定义 `ttl_days` 参数。
- **三级过期状态**：`expired` / `expiring_soon` / `ok`，分别以红色 / 琥珀色 / 蓝色边框和标签在模块六展示。
- **Playbook 中内联标注**：编译为 Markdown 时，过期条目自动附加 `[EXPIRED — may be outdated]` 标注。

### 🆕 P2-3：DOCX 简历格式支持
- 简历评分模块（模块三）新增 `.docx` 支持，通过 `python-docx` 逐段提取正文文本。支持格式：PDF、DOCX、TXT。

### 🔒 P2-4：访问密码门控
- 通过 Streamlit Secrets (`APP_PASSWORD`) 或环境变量配置访问密码。零侵入设计，通过 `st.stop()` 阻断未认证访问。

---

## V1.6 — 全链路生产加固：双模型路由、跨会话持久化与知识库去重
**Release Date:** 2026-02-27

### 🔥 P0 — 关键缺陷修复
- **AI 引擎：双模型路由**：新增 `STRONG_MODEL` 环境变量，快模型 `claude-haiku-4-5` 负责外展/评分/Q&A，强模型负责 JD 生成与面试评分卡。
- **RAG 知识库：FAISS 持久化**：向量索引首次构建后保存至磁盘，后续启动直接加载。
- **模块零：中英文自动翻译**：HC 需求表单支持中文填写，提交时自动翻译为专业英文。

### ✨ P1 — 体验增强
- **模块一：X-Ray 搜索一键直达**：自动提取 Boolean 搜索字符串，渲染"直接在 Google 中搜索"按钮。
- **模块一至四：JD 跨会话持久化**：JD 内容同步写入 `data/generated/latest_jd.json`，下游模块智能恢复。
- **模块六：知识碎片去重保护**：内容哈希去重 + `source_url` 来源追踪。

---

## V1.5 — AI 引擎升级与生产加固
**Release Date:** 2026-02-26

### AI 引擎全面升级
- **底座模型切换**：从 DeepSeek 全面切换至 **Claude Haiku** (`claude-haiku-4-5-20251001`)。
- **内置免费 AI 引擎**：无需配置 API Key 即可使用。
- **模型名称可配置化**：新增 `LLM_MODEL` 环境变量。

### 安全与工程化
- **敏感信息防泄漏**：`.gitignore` 强化。
- **Alauda 企业主题**：统一品牌色 `#004D99`。

---

## V1.4.1 — Final RC：全流程闭环与云端部署
**Release Date:** 2026-02-26

Alauda GROS Copilot 首版完整发布。包含模块零至模块六共 7 个核心功能模块，部署至 Streamlit Community Cloud。
