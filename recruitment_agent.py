from openai import OpenAI
import os
from dotenv import load_dotenv

# 强制覆盖系统环境变量，确保优先读取 .env 的 DeepSeek 配置
load_dotenv(override=True)

class RecruitmentAgent:
    def __init__(self):
        # 强制从系统环境变量（即我们的 .env）读取，防止被全局的 ollama 干扰
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        # 暂时用 Dummy Client，等你填入 Key 后生效
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None
        
        # 核心 System Prompt (浓缩自你的 txt 文件)
        self.system_prompt = """
        # Role: Global Elite Tech Recruiter & Systems Architect
        
        ## Profile
        你是一位拥有15年经验的全球顶级技术招聘专家，精通“系统化运作”。你擅长将模糊的招聘需求转化为精准的、可执行的“招聘工程学”系统。
        
        ## Context
        服务企业：Alauda (灵雀云) 
        - 背景：中国大陆容器/PaaS领域的 Top 1 提供商，产品对标 Red Hat OpenShift。
        - 现状：全球扩张（新加坡、马来西亚、南非等）。
        - 目标：构建标准化的全球售前架构师 & 交付工程师招聘体系。
        
        ## Capabilities
        1. 第一性原理思考：不仅关注“招人”，更关注“业务问题的解决”。
        2. X-Ray Search 专家：精通 Google/LinkedIn/GitHub 的布尔逻辑搜索（Boolean Strings）。
        3. 结构化面试设计：能够设计基于行为锚定（BARS）的评分卡。
        4. 极简主义输出：拒绝废话，只提供可落地的表格、脚本和代码块。
        """

    def generate_jd_and_xray(self, role_title, location, mission, tech_stack, deal_breakers, selling_point):
        """
        基于业务输入，生成极具吸引力的 JD 以及自动化的 X-Ray 搜索布尔语句。
        """
        if not self.client:
            return "⚠️ 请在 .env 文件中配置 OPENAI_API_KEY"

        prompt = f"""
        基于以下业务线提供的信息，请为我生成两个核心交付物：

        【输入信息】
        - 招聘职位: {role_title}
        - 目标地点: {location}
        - The Mission (核心任务): {mission}
        - The Tech Stack (必须技术栈): {tech_stack}
        - The Deal Breakers (红线要求): {deal_breakers}
        - The Selling Point (吸引力卖点): {selling_point}

        【输出要求】
        请使用 Markdown 格式输出以下两个模块：

        ### 1. 结构化高转化率 JD (Job Description)
        打破常规的“职责罗列”，要写出体现 Alauda 全球化战略和对标 OpenShift 挑战的吸引力。重点突出候选人能在第一年完成什么样令人兴奋的 Mission。语言需专业、简练。

        ### 2. The Sourcing Engine (自动化寻源武器库)
        基于上述信息，生成 3 组即插即用的 Google X-Ray Search Boolean Strings。
        要求：
        - 一组针对 LinkedIn 深度搜索 (含当前头衔、技能、地点，排除猎头)。
        - 一组针对 GitHub (查找高频提交 Kubernetes/云原生代码的开发者)。
        - 每组搜索词请用代码块 ` ` 包裹，并简短解释每个操作符的含义，让小白 HR 也能修改。
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 生成失败，错误信息: {str(e)}"

    def generate_interview_scorecard(self, jd_text):
        """
        基于 JD 文本，生成结构化面试评分卡及 STAR 面试题库
        """
        if not self.client:
            return "⚠️ 请在 .env 文件中配置 OPENAI_API_KEY"

        prompt = f"""
        为了解决“面试评价随机主观”的问题，请基于以下 JD 内容，设计一张【结构化面试评分卡 (Scorecard)】和对应的【STAR 行为面试题库】。

        【职位 JD】:
        {jd_text}

        【输出要求】
        请使用 Markdown 表格形式呈现评分卡。必须包含以下三个核心维度：
        1. 技术胜任力 (Technical Competency)
        2. 售前/交付能力 (Consulting/Delivery)
        3. 文化契合度 (Culture Add - 创业精神、全球化适应力)

        对于每个维度，需提供：
        - 1分（不合格）、3分（合格）、5分（卓越）的具体行为表现定义。
        - 2道犀利的 STAR 行为面试题（例如：“请分享一次你向非技术高管解释 Kubernetes 价值的经历？”）。
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, # 评分卡需要更严谨，降低发散性
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 生成失败，错误信息: {str(e)}"


    def generate_outreach_message(self, jd_text, candidate_info):
        """
        基于 JD 和候选人背景，生成高转化率的触达文案 (Outreach Message)
        """
        if not self.client:
            return "⚠️ 请在 .env 文件中配置 OPENAI_API_KEY"

        prompt = f"""
        你是一位顶级的国际科技猎头。你的任务是写一封极具转化率的【冷启动触达信 (Cold Outreach)】，吸引顶尖人才。

        【职位背景 (JD)】:
        {jd_text}

        【候选人情报】:
        {candidate_info}

        【撰写要求】:
        1. 拒绝传统的 HR 官话（如“我们在招人，你有兴趣吗”），采用 Alex Hormozi 的 Acquisition 风格：直接抛出巨大的价值主张和令其无法拒绝的挑战（比如颠覆行业巨头的机会）。
        2. 高度个性化：必须巧妙地结合【候选人情报】，说明为什么偏偏找他/她。
        3. 请提供两个版本：
           - 版本 A: **邮件版 (Email)** - 结构清晰，有感染力，带明确的 Call to Action (CTA)。
           - 版本 B: **LinkedIn InMail 版** - 极度简练，直击痛点，适合手机阅读（控制在 300 字以内）。
        4. 语言：请使用非常地道、专业的商务英语 (Business English)，因为这是针对海外架构师的触达。
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 生成失败，错误信息: {str(e)}"

    def answer_playbook_question(self, query, context_docs):
        """
        基于 RAG 检索到的文档片段（context_docs）回答用户问题
        """
        if not self.client:
            return "⚠️ 请在 .env 文件中配置 OPENAI_API_KEY"

        prompt = f"""
        你现在是 Alauda 灵雀云的“全球招聘与雇主品牌智能顾问”。
        请务必**仅基于**以下提供的《Alauda 全球招聘 Playbook》知识库片段来回答用户的问题。
        如果提供的片段中没有包含答案，请明确告知“根据目前的 Playbook 手册，没有找到相关信息”，不要自己凭空编造。

        【Playbook 知识片段】:
        {context_docs}

        【用户问题】:
        {query}
        
        【回答要求】:
        使用专业、有同理心的 HR BP 语气进行回答，并适当使用 Markdown 格式（如加粗、列表）使排版清晰。
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # 回答事实型问题，温度调低
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 检索问答失败，错误信息: {str(e)}"
