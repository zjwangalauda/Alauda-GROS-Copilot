# Alauda Global Recruitment OS (GROS) Copilot
## v1.3.0 Release Notes
**Release Date:** 2026-02-25

### 🌟 Overview (System Overview)
Alauda GROS Copilot 是一款将灵雀云《全球技术精英招聘操作系统》静态方法论全面智能化的 AI 招聘工作台。该系统通过先进的生成式 AI 技术（Generative AI）和检索增强生成（RAG），帮助业务主管与 HR 在出海招聘中实现“流水线式精准捕获”。

这不是一个简单的“写职位描述”的工具，而是一个**固化了顶级猎头与前沿组织设计方法论的“企业出海招聘引擎”**。目前，系统已成功部署至云端，实现 7x24 小时全球可用，并在全新版本中彻底打通了“业务线需求 -> JD 生成 -> 简历智能初筛 -> 面试官赋能”的闭环。

### 🚀 Key Features (核心功能模块)

#### 1. 业务线 HC 需求提报与流转审批 (Module 0)
- **打破部门壁垒**：业务线主管只需用大白话填入“核心挑战”和“业务红线”即可提交 headcount (HC) 申请。
- **HRBP 在线审批工作台**：HRBP 拥有独立视角，可以对业务提交的 HC 申请进行一键批准或驳回。

#### 2. JD 逆向工程与自动化寻源引擎 (Module 1)
- **精准画像输入协议 (Calibration Protocol)**：通过四维业务拷问（Mission, Tech Stack, Deal Breakers, Selling Point）倒推候选人真实画像，并自动承接被批准的 HC 信息。
- **高转化率 JD 生成与寻源外挂**：一键生成高级英文职位描述，并输出针对 LinkedIn, GitHub 深度检索的布尔逻辑搜索代码，提升 HR 主动搜寻效率 10 倍。

#### 3. 自动化触达引擎 (Module 2: Outreach)
- **拒绝无效破冰**：采用 Alex Hormozi 的 Acquisition 营销框架，根据候选人的特定背景生成直击痛点的邮件（Email）与领英短文（InMail），极大提升海外资深架构师的回复率。

#### 4. 结构化面试评估系统 (Module 3)
- **统一全球面试“度量衡”**：基于生成的 JD 自动拆解并输出可量化的“行为锚定评分卡（BARS Scorecard）”，消除考官的主观偏见。

#### 5. 知识库自生长与 RAG 智库 (Module 4 & 5)
- **动态沉淀体系 (Knowledge Builder)**：在实战中将零碎的踩坑经验录入系统，一键汇编并自动向量化。
- **混合检索问答 (Dynamic RAG)**：结合旧版静态 PDF 与动态经验库，HR 随时提问，AI 精准解答并支持溯源查证。

#### 6. 猎头简历智能雷达 (Module 6: Resume Matcher) *[NEW in v1.3.0]*
- **一键脱水挤分**：HR 收到的海量外部渠道简历（PDF/TXT）可直接上传。系统内置底层文本解析器（PyPDF）。
- **极度严苛的 AI 考官**：系统会自动抓取当前职位的 JD，让 AI 扮演严苛的技术面试官与候选人的简历进行深度“硬核交叉比对”。
- **四维诊断报告**：瞬间输出 [0-100的匹配度打分]、[核心亮点]、[红线与造假预警] 以及专为该候选人定制的 [初面电话查验犀利追问]。彻底解决 HR “看不懂海外技术简历”、“被候选人包装忽悠”的痛点。

### 🛠️ Technical Architecture & Deployment (架构与部署)
- **前端交互框架**：基于 Streamlit 构建，采用 Alauda 视觉规范强制浅色主题渲染。
- **公有云部署**：系统已成功全量部署至 `Streamlit Community Cloud`，实现了免运维、高可用。
