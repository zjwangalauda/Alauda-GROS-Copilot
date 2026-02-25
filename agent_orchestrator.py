import time
import json
import random
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class MultiAgentOrchestrator:
    """
    负责模拟并协调多个独立 Agent (搜寻者、评估者、触达者) 的工作流。
    这展示了系统从 Single-Agent 到 Multi-Agent Team 的演进。
    """
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    def run_sourcing_pipeline(self, jd_context, log_callback):
        """
        运行寻源工作流。
        log_callback 是一个函数，用于将 Agent 之间的对话和状态实时推送到 UI。
        """
        if not self.client:
            log_callback("❌ [System] 缺少大模型配置，无法启动 Agent Team。")
            return []

        # 阶段 1：Agent A (Sourcing Crawler)
        log_callback("🤖 [Agent A: 寻源爬虫] 收到 JD，正在生成 GitHub/StackOverflow 爬取策略...")
        time.sleep(1)
        
        # 模拟爬取的真实开源人才数据
        mock_candidates = [
            {"name": "David.Chen", "platform": "GitHub", "location": "Singapore", "bio": "Staff SWE @ Shopee | Go | Kubernetes Contributor", "repo_stars": 1240, "languages": ["Go", "Python", "Shell"]},
            {"name": "Wei_Li", "platform": "StackOverflow", "location": "Malaysia", "bio": "Cloud Architect | AWS Certified | OpenShift Specialist", "repo_stars": 320, "languages": ["Python", "Java", "HCL"]},
            {"name": "Alex_V", "platform": "GitHub", "location": "Singapore", "bio": "Frontend Dev | React & Vue ecosystem", "repo_stars": 890, "languages": ["TypeScript", "JavaScript", "HTML"]},
            {"name": "Sarah_K", "platform": "GitHub", "location": "Remote APAC", "bio": "DevOps Engineer | EKS | Helm | Prometheus", "repo_stars": 45, "languages": ["Go", "Yaml"]}
        ]
        
        log_callback(f"🤖 [Agent A: 寻源爬虫] 已在开源社区扫描到 4 名潜在候选人。正在将数据移交至分析师网络...")
        time.sleep(1)

        # 阶段 2：Agent B (Evaluator)
        log_callback("🧠 [Agent B: 评估分析师] 开始对 4 名候选人进行多维交叉比对，剔除不合格者...")
        
        evaluation_prompt = f"""
        你是一位顶级的候选人初筛 AI (Agent B)。
        以下是我们公司的招聘 JD 核心诉求：
        {jd_text_summary(jd_context)}
        
        以下是 Agent A 抓取到的候选人开源数据：
        {json.dumps(mock_candidates, ensure_ascii=False)}
        
        请你挑选出最匹配的 2 位候选人，并给出被淘汰者的淘汰理由。
        只输出一段简短的分析即可。
        """
        
        try:
            eval_res = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.2
            ).choices[0].message.content
            
            log_callback(f"🧠 [Agent B: 评估分析师] 分析完毕：\n{eval_res}")
        except Exception as e:
            log_callback(f"❌ [Agent B] 错误: {e}")
            return []

        time.sleep(1)

        # 阶段 3：Agent C (Outreach Specialist)
        log_callback("✍️ [Agent C: 文案大师] 收到最终的 2 名优质候选人名单。正在根据他们的开源代码库特征，编写千人千面的极客破冰邮件...")
        
        final_candidates = [mock_candidates[0], mock_candidates[1]] # 取前两个作为示例
        results = []
        
        for cand in final_candidates:
            outreach_prompt = f"""
            你是 Agent C (转化专家)。请针对候选人 {cand['name']} 写一封不超过 150 字的极度硬核的破冰私信。
            候选人背景: {cand['bio']}, 擅长: {cand['languages']}, Repo Stars: {cand['repo_stars']}
            招聘岗位: {jd_text_summary(jd_context)}
            
            要求：不要寒暄，直接用同行极客的口吻（比如赞赏他的开源项目），并抛出我们替换 OpenShift 的疯狂计划吸引他。
            """
            try:
                msg = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": outreach_prompt}],
                    temperature=0.6
                ).choices[0].message.content
                
                results.append({"candidate": cand['name'], "message": msg})
                log_callback(f"✍️ [Agent C] 已生成 {cand['name']} 的专属转化文案。")
            except Exception as e:
                log_callback(f"❌ [Agent C] 错误: {e}")

        log_callback("🏁 [Orchestrator] Multi-Agent 寻源工作流执行完毕。")
        return results

def jd_text_summary(jd):
    # 截取 JD 的前 500 个字避免 Token 过长
    return jd[:500] if jd else "寻找懂 K8s 的资深出海售前架构师，对标 OpenShift。"
