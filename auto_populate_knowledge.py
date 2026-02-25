import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from knowledge_manager import KnowledgeManager

load_dotenv(override=True)

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

client = OpenAI(api_key=api_key, base_url=base_url)
km = KnowledgeManager()

regions = ["Singapore", "Malaysia", "South Africa", "Hong Kong"]
categories = ["薪酬福利与发薪", "签证与工作许可 (Visa/EP)", "劳动法与试用期规定", "候选人寻源渠道"]

print("🚀 启动 AI 自动填充出海知识库...")

for region in regions:
    print(f"\n🌍 挖掘 {region} ...")
    for category in categories:
        prompt = f"你是全球HRBP专家。请针对【{region}】的【{category}】，列出2-3条最核心的招聘合规政策、法律门槛或职场潜规则。不废话，直接列出具体数字或法案名称，用一段话输出。"
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content.strip()
            tags = f"{region}, {category.split(' ')[0]}, 合规"
            km.add_fragment(region=region, category=category, content=content, tags=tags)
            print(f"  ✅ [{category}] ok")
            time.sleep(1) # 短暂延迟避免限流
        except Exception as e:
            print(f"  ❌ [{category}] error: {str(e)}")

print("\n🎉 抓取完毕，编译中...")
km.compile_to_markdown()
print("✅ Done")
