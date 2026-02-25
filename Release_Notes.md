# Alauda Global Recruitment OS (GROS) Copilot
## v1.4.0 Release Notes
**Release Date:** 2026-02-25

### 🌟 Overview (System Overview)
Alauda GROS Copilot 是一款将灵雀云《全球技术精英招聘操作系统》静态方法论全面智能化的 AI 招聘工作台。该系统通过先进的生成式 AI 技术（Generative AI）和检索增强生成（RAG），帮助业务主管与 HR 在出海招聘中实现“流水线式精准捕获”。

这不是一个简单的“写职位描述”的工具，而是一个**固化了顶级猎头与前沿组织设计方法论的“企业级出海招聘引擎”**。目前，系统已成功部署至云端，实现 7x24 小时全球可用，彻底打通了“业务线需求 -> JD 生成 -> 自动化触达 -> 简历智能初筛 -> 面试官赋能 -> 知识库沉淀”的生产级闭环。

### 🚀 Key Features (核心功能模块)

#### 0. 业务线 HC 需求提报与流转审批 (Module 0)
- 彻底颠覆口头沟通。业务线主管只需用大白话填入“核心挑战”和“业务红线”即可提交 headcount (HC) 申请。数据流自动穿透至后续 AI 引擎。

#### 1. JD 逆向工程与自动化寻源引擎 (Module 1)
- 通过四维业务拷问倒推候选人真实画像，一键生成重点突出 Alauda 战略高度的高级英文职位描述，并输出用于 Google X-Ray 深度检索的布尔逻辑代码。

#### 2. 自动化触达引擎 (Module 2: Outreach)
- 摒弃废话模板，采用 Alex Hormozi 的 Acquisition 营销框架，根据候选人的特定背景生成直击痛点的高级破冰邮件与 InMail。

#### 3. 猎头简历智能雷达 (Module 3: Resume Matcher)
- **硬性数学算分卡防御模型**：AI 面试官在后台执行 `Temperature=0.0` 的绝对客观推理，将定性评估转为纯粹的“维度减法”，彻底消除大模型的“打分漂移（Evaluation Drift）”。精准剥离简历水分并生成电话查验追问。

#### 4. 结构化面试评估系统 (Module 4)
- 自动提取关键维度，生成带 1-5 分严格定义标准的【行为锚定评分卡 (BARS)】以及 STAR 题库，统一全球面试官的评价口径。

#### 5. 知识库自生长与 RAG 智库 (Module 5 & 6)
- **破除冷启动：全自动网页情报收割机 (Web Auto-Harvester)** *[NEW in v1.4.0]*：彻底淘汰传统的手工录入模式。HR 只需粘贴网页链接（内置新加坡 MOM、马来西亚劳工部等权威源快捷选项），AI 爬虫即可瞬间提取长篇外文网页，剥离废话，精准萃取当地签证底线、公积金比例等合规红线，一键编译为动态 Markdown 入库。
- **混合检索问答 (Dynamic RAG)**：结合旧版静态 PDF 与自动收割的最新情报，实现精准的混合检索问答溯源，杜绝 AI 幻觉。

### 🛠️ Technical Architecture & Deployment (架构与部署)
- **前端交互框架**：基于 Streamlit 构建，完美白底蓝调企业级 UI，内置一键缓存强刷机制。
- **公有云部署**：系统已全量部署至 Streamlit Community Cloud，免运维高可用。
