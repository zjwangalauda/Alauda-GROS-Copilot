import io
from pypdf import PdfReader
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
        self.model = os.environ.get("LLM_MODEL", "deepseek-chat")
        
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
                model=self.model,
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
                model=self.model,
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
                model=self.model,
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
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # 回答事实型问题，温度调低
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 检索问答失败，错误信息: {str(e)}"


    def extract_text_from_file(self, file_name, file_bytes):
        """解析上传的简历文件文本"""
        try:
            if file_name.lower().endswith('.pdf'):
                reader = PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            elif file_name.lower().endswith('.txt'):
                return file_bytes.decode('utf-8')
            else:
                return "Unsupported file format."
        except Exception as e:
            return f"文件解析失败: {str(e)}"

    def evaluate_resume(self, jd_text, resume_text):
        """
        将候选人简历与 JD 进行硬核比对，使用硬性算分卡 (Scoring Rubric) 防止评估漂移
        """
        if not self.client:
            return "⚠️ 请在 .env 文件中配置 OPENAI_API_KEY"

        prompt = f"""
        你是一位极其严苛且极度客观的 Alauda (灵雀云) 全球顶尖技术面试官。
        你的任务是审阅候选人简历，并严格对照 JD 进行量化初筛。

        【职位核心诉求 (JD)】:
        {jd_text}

        【候选人简历 (Parsed Text)】:
        {resume_text}

        【强制量化算分卡 (Scoring Rubric)】:
        为了保证评估的绝对客观，请严格按照以下三大维度进行数学加法算分，切勿凭感觉给总分：
        1. 🎯 使命契合度 (Mission Match) - 满分 40 分
           - 40分：完美拥有主导解决同类痛点（如替换竞品、主导千万级项目）的端到端经验。
           - 20分：参与过类似项目，但并非主导者或经验略有偏差。
           - 0分：完全没有相关商业打单或同等量级交付经验。
        2. 💻 技术栈硬实力 (Tech Stack) - 满分 40 分
           - 40分：精通 JD 要求的全部核心技术（特别是 K8s/云原生底层）。
           - 20分：会用其中大部分技术，但停留在应用层/运维层，缺乏架构或源码级深度。
           - 0分：技术栈严重不符。
        3. 🚫 红线规避 (Deal Breaker) - 满分 20 分
           - 20分：完全没有触犯任何红线（如：拥有 B2B 经验、英文极好等）。
           - 0分：触犯了任何一条绝对红线（Deal Breaker 是有一票否决权的，只要触犯一项此处即为 0 分，并在下面预警）。

        【输出要求】:
        请严格按此结构输出，先给出各项得分的推导过程，再得出总分：
        
        ### 📊 结构化量化评估
        - **总分**: [计算上述三项得分之和，满分 100]
        - **得分拆解**:
          - 使命契合度: [X] / 40 分 (理由：...)
          - 技术栈硬实力: [X] / 40 分 (理由：...)
          - 红线规避: [X] / 20 分 (理由：...)
        - **定性结论**: (高度匹配 ≥80 / 勉强及格 60-79 / 严重不符 <60)

        ### ✨ 核心亮点 (Highlights)
        - 列出简历中最契合的 1-2 个闪光点。如果没有，直接写“无突出亮点”。

        ### 🚨 红线与水分预警 (Red Flags)
        - 明确指出是否触碰了 Deal Breakers（如果触碰了，必须强烈警告）。
        - 挑出简历中用词含糊、可能存在过度包装的地方（例如只写了“管理”，没写“架构”）。

        ### 🎯 初面查验建议 (Interview Probing)
        - 针对上述“水分预警”或缺失的能力，提供 2 个极度犀利的电话初筛追问。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0, 
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 简历评估失败: {str(e)}"

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
                model=self.model,
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
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # 回答事实型问题，温度调低
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 检索问答失败，错误信息: {str(e)}"


    def extract_text_from_file(self, file_name, file_bytes):
        """解析上传的简历文件文本"""
        try:
            if file_name.lower().endswith('.pdf'):
                reader = PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            elif file_name.lower().endswith('.txt'):
                return file_bytes.decode('utf-8')
            else:
                return "Unsupported file format."
        except Exception as e:
            return f"文件解析失败: {str(e)}"

    def evaluate_resume(self, jd_text, resume_text):
        """
        将候选人简历与 JD 进行硬核比对，生成打分与红线预警
        """
        if not self.client:
            return "⚠️ 请在 .env 文件中配置 OPENAI_API_KEY"

        prompt = f"""
        你是一位极其严苛的 Alauda (灵雀云) 全球顶尖技术面试官。
        你的任务是审阅外部猎头推荐的候选人简历，并严格对照我们的职位画像(JD)进行初筛。

        【职位核心诉求 (JD)】:
        {jd_text}

        【候选人简历 (Parsed Text)】:
        {resume_text}

        【输出要求】:
        请使用 Markdown 格式，专业、无情、直击痛点地输出以下 4 个板块：
        
        ### 📊 综合匹配度打分
        - **匹配度**: [0 - 100 分] 
        - **定性结论**: (例如：高度匹配 / 勉强及格 / 严重不符，并用一句话概括核心原因)

        ### ✨ 核心亮点 (Highlights)
        - 列出简历中与 JD "The Mission" 和 "Tech Stack" 完美契合的 2-3 个闪光点。如果没有，直接写“无突出亮点”。

        ### 🚨 红线预警 (Red Flags / Deal Breakers)
        - 极其重要！候选人是否触犯了 JD 中的 Deal Breakers？
        - 候选人在特定技术栈（如 Kubernetes, AWS）或过往经历中可能存在的“水分”或缺失。

        ### 🎯 初面查验建议 (Interview Probing)
        - 针对简历中的可疑点或不足，提供 1-2 个极度犀利的电话初筛问题，帮助 HR 瞬间戳破候选人的包装。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # 打分和评估需要极度客观冷静
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 简历评估失败: {str(e)}"
