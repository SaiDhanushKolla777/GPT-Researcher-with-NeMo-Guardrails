
# 🧠 LangGraph x GPT Researcher (Enhanced with NeMo Guardrails)

This is a security-enhanced fork of the [GPT-Researcher x LangGraph](https://github.com/assafelovic/gpt-researcher) project, designed to ensure reliable, fact-based, and safe research generation using large language models (LLMs).

> ✨ **Maintained by [@SaiDhanushKolla777](https://github.com/SaiDhanushKolla777)**  
> This version integrates **NVIDIA NeMo Guardrails** across the entire multi-agent system to safeguard against hallucinations, misinformation, and unsafe outputs.

---

## 🔍 Use Case

Using [LangGraph](https://python.langchain.com/docs/langgraph) and multiple LLM agents, this system conducts full-length research projects automatically—from task planning to final publication.

Inspired by the [STORM](https://arxiv.org/abs/2402.14207) paper, the architecture mimics a real-world editorial pipeline using autonomous agents, enhanced now with **AI safety measures** powered by NeMo Guardrails.

> Average output: **5–6 pages** of research in PDF, DOCX, and Markdown formats.

---

## 🔐 What’s New in This Fork

- 🛡️ Integrated **NVIDIA NeMo Guardrails** at every agent level
- 🧠 Centralized `GuardrailsManager` for consistent safety enforcement
- ✅ Input/output validation for query prompts, generated content, and final reports
- 📜 YAML-configured policy for blocking unsafe content and enforcing fact-checking
- 👥 Seamless human-in-the-loop or fully autonomous modes

---

## 🧩 Multi-Agent Research Team

| Role         | Description |
|--------------|-------------|
| 👤 **Human**        | Provides optional feedback during the planning stage |
| 🧑‍💼 **Chief Editor** | Orchestrates all agents and applies top-level safety logic |
| 🔎 **Researcher**   | Performs initial and subtopic research |
| ✍️ **Editor**       | Designs the research plan and outline |
| 🧪 **Reviewer**     | Reviews research based on user guidelines |
| 🛠️ **Reviser**      | Updates drafts based on reviewer feedback |
| 📄 **Writer**       | Compiles intro, body, conclusion, citations |
| 📤 **Publisher**    | Outputs the report to PDF, DOCX, and Markdown |
  
All agents are **guardrail-aware** and automatically sanitize both input and output.

---

## 🧠 Architecture

<div align="center">
<img align="center" height="600" src="https://github.com/user-attachments/assets/ef561295-05f4-40a8-a57d-8178be687b18" alt="LangGraph Multi-Agent Architecture"/>
</div>
<br clear="all"/>

---

## 🔁 How It Works (Step-by-Step)

1. **Initial Research**  
   The `Researcher` agent conducts a web-based scan on the query.
   
2. **Planning**  
   The `Editor` designs an outline based on the research.
   
3. **Optional Feedback**  
   The `Human` agent can approve or revise the outline.

4. **Parallel Research**  
   Each subtopic is handled independently by `Researcher → Reviewer → Reviser`.

5. **Final Report**  
   The `Writer` composes the introduction, conclusion, citations, and layout.

6. **Publishing**  
   The `Publisher` exports results to multiple formats after a final guardrails check.

---

## ⚙️ How to Run

### 🛠️ 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 🔑 2. Setup Environment
Update your `.env` file with the necessary API keys (OpenAI, Tavily, etc.) and model config.

### ▶️ 3. Launch the App
```bash
python multi_agents/main.py
```

---

## 📝 Configuring the Research (`task.json`)

Modify `multi_agents/task.json` to customize behavior:

```json
{
  "query": "Is AI in a hype cycle?",
  "model": "gpt-4o",
  "max_sections": 3,
  "publish_formats": {
    "markdown": true,
    "pdf": true,
    "docx": true
  },
  "include_human_feedback": false,
  "source": "web",
  "follow_guidelines": true,
  "guidelines": [
    "The report MUST fully answer the original question",
    "The report MUST be written in apa format",
    "The report MUST be written in english"
  ],
  "verbose": true
}
```

---

## 🧱 Guardrails Configuration

Located in `multi_agents/config/config.yml`, the policy includes:

- ✅ Input self-checks for harmful or disallowed queries
- ✅ Output validation to prevent hallucinated citations or unsafe text
- 📚 Whitelisted educational queries and blocked security-sensitive prompts

```yaml
rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output
```

---

## ☁️ Optional: Deploy with LangGraph Cloud

```bash
pip install langgraph-cli
langgraph up
```

For playground UI, streaming endpoints, and logging support, see [LangGraph Cloud Docs](https://github.com/langchain-ai/langgraph-example).

---

## 🙌 Acknowledgments

- Original project by [@assafelovic](https://github.com/assafelovic)
- Guardrails framework powered by [NVIDIA NeMo Guardrails](https://developer.nvidia.com/nemo)
- Infrastructure orchestrated via [LangGraph](https://github.com/langchain-ai/langgraph)

---

## 📬 Contact & Collaboration

Built and maintained by [Sai Dhanush Kolla](https://github.com/SaiDhanushKolla777)  
💼 [LinkedIn](https://www.linkedin.com/in/kolla-saidhanush/)  
📬 [Email](mailto:saidhanushkolla1880@gmail.com)

---

**🔒 Secure AI for responsible research — from start to finish.**
