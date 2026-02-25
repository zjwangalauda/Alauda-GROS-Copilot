# Alauda Global Recruitment OS (GROS) Copilot
## v1.2.0 Release Notes
**Release Date:** 2026-02-25

### 🌟 Overview (System Overview)
Alauda GROS Copilot 是一款将灵雀云《全球技术精英招聘操作系统》静态方法论全面智能化的 AI 招聘工作台。该系统通过先进的生成式 AI 技术（Generative AI）和检索增强生成（RAG），帮助业务主管与 HR 在出海招聘中实现“流水线式精准捕获”。

这不是一个简单的“写职位描述”的工具，而是一个**固化了顶级猎头与前沿组织设计方法论的“企业出海招聘引擎”**。目前，系统已成功部署至云端，实现 7x24 小时全球可用，并在全新版本中彻底打通了“业务线-HRBP”的线上协同审批闭环。

### 🚀 Key Features (核心功能模块)

#### 1. 业务线 HC 需求提报与流转审批 (Module 0) *[NEW in v1.2.0]*
- **打破部门壁垒**：彻底颠覆传统业务线丢一句“我要招人”或写一篇不痛不痒的八股文 JD 的模式。业务线主管只需用大白话填入“核心挑战”和“业务红线”即可提交 headcount (HC) 申请。
- **HRBP 在线审批工作台**：HRBP 拥有独立视角，可以对业务提交的 HC 申请进行一键批准或驳回。
- **数据流自动穿透**：一旦 HC 申请被批准，数据将自动流转至“JD 生成引擎”。HR 在生成 JD 时，只需在下拉菜单中选中该 HC，系统便会自动读取业务需求作为 AI 的基础上下文，实现“从需求到JD”的零信息损耗。

#### 2. JD 逆向工程与自动化寻源引擎 (Module 1)
- **精准画像输入协议 (Calibration Protocol)**：通过四维业务拷问（Mission, Tech Stack, Deal Breakers, Selling Point）倒推候选人真实画像。
- **高转化率 JD 生成**：一键生成重点突出 Alauda 产品力（对标 OpenShift）的高级英文职位描述。
- **Google X-Ray 自动化寻源 (The Sourcing Engine)**：智能生成针对 LinkedIn, GitHub 深度检索的布尔逻辑搜索代码，提升 HR 主动搜寻效率 10 倍。

#### 3. 自动化触达引擎 (Module 2: Outreach)
- **拒绝无效破冰**：采用 Alex Hormozi 的 Acquisition 营销框架，根据候选人的特定背景生成直击痛点的邮件（Email）与领英短文（InMail），极大提升海外资深架构师的回复率。

#### 4. 结构化面试评估系统 (Module 3)
- **统一全球面试“度量衡”**：基于生成的 JD 自动拆解并输出可量化的“行为锚定评分卡（BARS Scorecard）”。
- **STAR 题库生成**：按能力维度智能分配深度追问考题，并提供 1-5 分的判定基准，消除考官的主观偏见。

#### 5. 知识库自生长与 RAG 智库 (Module 4 & 5)
- **动态沉淀体系 (Knowledge Builder)**：在实战中将零碎的踩坑经验（如特定国家签证政策）录入系统，一键汇编并自动向量化。
- **混合检索问答 (Dynamic RAG)**：结合旧版静态 PDF 与动态经验库，HR 随时提问，AI 精准解答并支持溯源查证。

### 🛠️ Technical Architecture & Deployment (架构与部署)
- **前端交互框架**：基于 Streamlit 构建，采用 Alauda 视觉规范强制浅色主题渲染，攻克了原生组件黑暗模式污染问题，呈现完美的白底蓝调企业级 UI。
- **公有云部署**：系统已成功全量部署至 `Streamlit Community Cloud`，实现了免运维、高可用、多端自适应的云端托管访问模式。
- **本地数据持久化**：针对新加入的 HC 审批模块（Module 0）和动态知识库模块（Module 5），设计了轻量级的 JSON 本地持久化存储方案，确保云端重启数据不丢失。
