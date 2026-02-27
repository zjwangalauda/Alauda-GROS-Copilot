import io
import logging
from pypdf import PdfReader
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

load_dotenv(override=True)

# ~200k chars ≈ ~50k tokens — safe ceiling for most LLM context windows
MAX_INPUT_CHARS = 200_000


class TranslatedHCFields(BaseModel):
    role_title: str
    location: str
    mission: str
    tech_stack: str
    deal_breakers: str
    selling_point: str

class RecruitmentAgent:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        # Fast model: outreach drafts, Q&A, resume scoring
        self.model = os.environ.get("LLM_MODEL", "claude-haiku-4-5-20251001")
        # Strong model: JD generation, interview scorecard, knowledge extraction
        # Falls back to self.model if STRONG_MODEL is not configured
        self.strong_model = os.environ.get("STRONG_MODEL", self.model)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

        self.system_prompt = """
# Role: Global Elite Tech Recruiter & Recruitment Systems Architect

## Profile
You are a world-class technical recruiter with 15 years of global talent acquisition experience,
specializing in "systematic recruitment engineering." You transform vague hiring needs into precise,
executable recruitment pipelines — especially for cloud-native and enterprise infrastructure roles.

## Client Context
Company: Alauda (灵雀云)
- China's #1 container/PaaS platform provider, benchmarked directly against Red Hat OpenShift.
- Actively expanding globally: Singapore, Malaysia, South Africa, Hong Kong.
- Goal: Build a standardized, repeatable global hiring system for presales architects and delivery engineers.

## Core Capabilities
1. First-Principles Thinking: Focus on solving the underlying business problem, not just filling headcount.
2. X-Ray Search Mastery: Boolean logic for Google/LinkedIn/GitHub deep sourcing.
3. Structured Interview Design: BARS (Behaviorally Anchored Rating Scale) scorecards that eliminate subjectivity.
4. Minimalist Output: No fluff — only actionable tables, search strings, and structured templates.
"""

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _call_llm(self, *, model, messages, temperature):
        """Call the LLM with automatic retry on transient errors."""
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )

    def generate_jd_and_xray(self, role_title, location, mission, tech_stack, deal_breakers, selling_point):
        """Generate high-conversion JD + X-Ray Boolean search strings."""
        if not self.client:
            return "⚠️ OPENAI_API_KEY not configured. Please set it in the .env file."

        total_len = sum(len(s) for s in [role_title, location, mission, tech_stack, deal_breakers, selling_point])
        if total_len > MAX_INPUT_CHARS:
            return f"⚠️ Input too long ({total_len:,} chars). Please shorten to under {MAX_INPUT_CHARS:,} chars."

        prompt = f"""
Based on the following inputs, generate two core deliverables:

[INPUT]
- Role Title: {role_title}
- Location: {location}
- The Mission (Year-1 business objectives): {mission}
- The Tech Stack (required): {tech_stack}
- The Deal Breakers (hard disqualifiers): {deal_breakers}
- The Selling Point (why top talent should join): {selling_point}

[OUTPUT — use Markdown]

### 1. High-Conversion Job Description (JD)
Break away from conventional duty lists. Write a compelling JD that highlights Alauda's global expansion
strategy and its direct challenge to Red Hat OpenShift. Lead with what exciting Mission the candidate will
accomplish in Year 1 — make it sound like the opportunity of a decade.
Language: professional, concise Business English targeted at senior overseas engineers.

### 2. The Sourcing Engine — X-Ray Boolean Search Strings
Generate 3 ready-to-use Google X-Ray Boolean search string sets:
- Set 1: LinkedIn deep search (current title + skills + location, exclude recruiters)
- Set 2: GitHub search (high-commit Kubernetes/cloud-native contributors)
- Set 3: Generic Google (broad talent discovery across job boards and profiles)

Wrap each string in a code block. Add a one-line annotation per operator so non-technical
HR staff can easily modify and reuse them.
"""

        try:
            response = self._call_llm(
                model=self.strong_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Generation failed: {str(e)}"

    def generate_interview_scorecard(self, jd_text):
        """Generate a BARS structured interview scorecard + STAR question bank from the JD."""
        if not self.client:
            return "⚠️ OPENAI_API_KEY not configured."

        if len(jd_text) > MAX_INPUT_CHARS:
            return f"⚠️ JD text too long ({len(jd_text):,} chars). Please shorten to under {MAX_INPUT_CHARS:,} chars."

        prompt = f"""
Design a Structured Interview Scorecard (BARS) and STAR Question Bank based on the JD below.
The goal is to eliminate subjective interviewing and align all interviewers to a single standard.

[JD Content]:
{jd_text}

[OUTPUT REQUIREMENTS — use Markdown tables]
Cover exactly these three dimensions:
1. Technical Competency (architecture depth, K8s internals, cloud-native stack)
2. Consulting / Delivery Capability (presales, client communication, project leadership)
3. Culture Add (entrepreneurial mindset, global adaptability, self-directed growth)

For each dimension provide:
- 1-point anchor (Unqualified): specific observable unacceptable behaviors
- 3-point anchor (Qualified): specific observable acceptable behaviors
- 5-point anchor (Excellent): specific outstanding differentiators
- 2 sharp STAR behavioral interview questions that probe for evidence, not opinions
"""

        try:
            response = self._call_llm(
                model=self.strong_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Generation failed: {str(e)}"

    def generate_outreach_message(self, jd_text, candidate_info):
        """Generate high-conversion cold outreach (Email + LinkedIn InMail)."""
        if not self.client:
            return "⚠️ OPENAI_API_KEY not configured."

        total_len = len(jd_text) + len(candidate_info)
        if total_len > MAX_INPUT_CHARS:
            return f"⚠️ Input too long ({total_len:,} chars). Please shorten to under {MAX_INPUT_CHARS:,} chars."

        prompt = f"""
You are a top-tier international tech headhunter. Write a high-conversion cold outreach message
to attract elite senior engineers.

[Job Context (JD)]:
{jd_text}

[Candidate Intelligence]:
{candidate_info}

[WRITING REQUIREMENTS]:
1. Reject generic HR language ("We're hiring, are you interested?").
   Use Alex Hormozi's Acquisition style: open with a massive value proposition and
   an irresistible challenge (e.g., the rare opportunity to directly disrupt an industry giant like Red Hat).
2. Highly personalized: reference the candidate's specific background from the intelligence provided —
   make it clear WHY this specific person is being contacted, not a mass message.
3. Deliver two versions:
   - Version A — Email: structured narrative, compelling arc, clear Call to Action (CTA)
   - Version B — LinkedIn InMail: ultra-concise, punchy, mobile-optimized, under 250 words
4. Language: native-level professional Business English. Written for senior overseas engineers
   who receive dozens of recruiter messages per month — cut through the noise.
"""

        try:
            response = self._call_llm(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Generation failed: {str(e)}"

    def evaluate_resume(self, jd_text, resume_text):
        """Evaluate resume against JD using a hard 100-point quantitative rubric."""
        if not self.client:
            return "⚠️ OPENAI_API_KEY not configured."

        total_len = len(jd_text) + len(resume_text)
        if total_len > MAX_INPUT_CHARS:
            return f"⚠️ Input too long ({total_len:,} chars). Please shorten to under {MAX_INPUT_CHARS:,} chars."

        prompt = f"""
You are an exceptionally rigorous and objective technical interviewer at Alauda.
Evaluate this candidate's resume against the JD using the hard quantitative scoring rubric below.
No gut-feeling scores — strict mathematical addition only. Show your reasoning per dimension.

[Job Description (JD)]:
{jd_text}

[Candidate Resume (Parsed Text)]:
{resume_text}

[MANDATORY SCORING RUBRIC — 100 points total]:

1. Mission Match (0–40 pts)
   - 40 pts: End-to-end ownership of solving an identical business problem
             (e.g., led OpenShift replacement, drove $1M+ enterprise migrations as DRI)
   - 30 pts: Led similar projects with measurable outcomes, slightly narrower scope
   - 20 pts: Participated in similar projects but was NOT the decision-maker or lead
   - 10 pts: Tangentially related background; relevant industry but wrong role type
   -  0 pts: No relevant B2B enterprise delivery experience whatsoever

2. Tech Stack Depth (0–40 pts)
   - 40 pts: Expert-level architecture depth in ALL required technologies
             (designs systems, not just operates them; K8s internals, CNI, custom controllers)
   - 30 pts: Strong hands-on across most required tech; architect-level in core areas
   - 20 pts: Hands-on K8s/cloud but limited to application/ops layer — not architecture depth
   - 10 pts: Basic exposure; familiar with the stack but lacks production-scale evidence
   -  0 pts: Tech stack severely misaligned with JD requirements

3. Deal Breaker Avoidance (0 or 20 pts — binary, NO partial credit)
   - 20 pts: Triggers ZERO deal breakers (B2B confirmed, English fluency evident, travel acceptable)
   -  0 pts: Violates ANY single deal breaker → automatic disqualification flag, stop here

[OUTPUT FORMAT — strictly follow this structure]:

### 📊 Quantified Assessment
- **Total Score**: [sum of 3 dimensions] / 100
- **Score Breakdown**:
  - Mission Match: [X] / 40 — Reasoning: ...
  - Tech Stack Depth: [X] / 40 — Reasoning: ...
  - Deal Breaker Avoidance: [X] / 20 — Reasoning: ...
- **Verdict**: Strong Match (≥80) | Borderline Pass (60–79) | Disqualified (<60)

### ✨ Core Highlights
- [1–2 genuine strengths directly aligned with the JD Mission and Tech Stack]
- (Write "No standout highlights identified." if none exist)

### 🚨 Red Flags & Deal Breaker Warnings
- [Explicitly state whether any deal breaker is triggered — bold it if yes]
- [Flag vague or likely-inflated language: e.g., wrote "managed" but never "architected"]

### 🎯 Phone Screen Probing Questions
- [2 sharp, targeted questions to verify suspicious claims or fill evidence gaps]
"""

        try:
            response = self._call_llm(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Resume evaluation failed: {str(e)}"

    def answer_playbook_question(self, query, context_docs):
        """Answer user questions grounded strictly in the retrieved Playbook segments."""
        if not self.client:
            return "⚠️ OPENAI_API_KEY not configured."

        total_len = len(query) + len(context_docs)
        if total_len > MAX_INPUT_CHARS:
            return f"⚠️ Input too long ({total_len:,} chars). Please shorten your query or reduce knowledge base size."

        prompt = f"""
You are Alauda's Global Recruitment & Employer Brand Intelligence Advisor.
Answer the user's question based STRICTLY on the Playbook knowledge segments provided below.
If the answer is not contained in the provided segments, explicitly state:
"The current Playbook does not contain information on this topic."
Do NOT fabricate, generalize, or infer beyond what is documented.

[Playbook Knowledge Segments]:
{context_docs}

[User Question]:
{query}

[RESPONSE REQUIREMENTS]:
- Tone: Professional HR Business Partner — empathetic, precise, actionable
- Format: Use Markdown (bold, bullet lists) for clarity
- If citing a specific regulation, salary figure, or policy rule, note which section it comes from
"""

        try:
            response = self._call_llm(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Q&A failed: {str(e)}"

    def translate_hc_fields(self, fields: dict) -> dict:
        """
        Translate HC request fields from Chinese (or mixed) to English.
        Technical terms (Kubernetes, Docker, etc.) are preserved as-is.
        Returns the original fields unchanged if translation fails.
        """
        import json as _json
        if not self.client:
            return fields

        prompt = f"""You are a professional technical recruiter translator.
Translate the following recruitment HC request fields into natural, professional Business English.
Rules:
- Keep all technical terms as-is (Kubernetes, Docker, OpenShift, CI/CD, CKA, etc.)
- Keep proper nouns as-is (Singapore, Alauda, Red Hat, etc.)
- Output ONLY a valid JSON object with the exact same keys — no explanation, no markdown fences

Input JSON:
{_json.dumps(fields, ensure_ascii=False, indent=2)}
"""
        try:
            response = self._call_llm(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if the model wraps output
            if content.startswith("```"):
                content = content[content.find("\n") + 1:]
                content = content[:content.rfind("```")].strip()
            parsed = TranslatedHCFields.model_validate_json(content)
            return parsed.model_dump()
        except Exception:
            logger.warning("HC field translation failed, returning originals", exc_info=True)
            return fields

    def extract_web_knowledge(self, target_url, region, category, raw_text):
        """Extract structured knowledge from scraped web text using LLM."""
        if not self.client:
            return None
        prompt = f"""
You are an expert in global compliance and recruitment intelligence extraction.
I have scraped the following webpage: {target_url}

From the raw text below, extract 1 to 3 of the most actionable, concrete rules or facts
relevant to [{region}] in the category [{category}].

Requirements:
- Strip all filler content, navigation text, and promotional language
- Output precise, dated facts (salary thresholds, visa quotas, notice periods, etc.)
- If no relevant information is found, respond exactly with: "EXTRACTION_FAILED"
- Respond in English

[Raw scraped text (truncated)]:
{raw_text[:8000]}
"""
        response = self._call_llm(
            model=self.strong_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content

    def extract_text_from_file(self, file_name, file_bytes):
        """Parse uploaded resume file (PDF, DOCX, or TXT) and return extracted text."""
        try:
            if file_name.lower().endswith('.pdf'):
                reader = PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            elif file_name.lower().endswith('.docx'):
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
            elif file_name.lower().endswith('.txt'):
                return file_bytes.decode('utf-8')
            else:
                return "Unsupported file format. Supported: PDF, DOCX, TXT."
        except Exception as e:
            return f"File parsing failed: {str(e)}"
