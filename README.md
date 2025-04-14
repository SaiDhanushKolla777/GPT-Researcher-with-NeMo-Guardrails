
<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

###

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)

</div>

---

# 🔍 Multi-Agent GPT Researcher with NeMo Guardrails

> ⚙️ **Multi-Agent research system built on top of GPT-Researcher using LangGraph**  
> 🔐 **This fork integrates NeMo Guardrails for real-time safety, ethical filtering, and content validation**  
> 🧠  Integrated NeMo Guardrails into the existing Multi-Agent Framework, modifying agent logic and orchestration to enforce safety and context-aware filtering — by  [**Sai Dhanush Kolla**](https://github.com/SaiDhanushKolla777)
> 
> 🙌 Original multi-agent architecture developed by [**Assaf Elovic**](https://github.com/assafelovic)

---

## 🚀 Overview

**Multi-Agent GPT Researcher** is a research automation framework that orchestrates multiple specialized agents to collaboratively produce high-quality research reports using large language models. This fork introduces **NVIDIA NeMo Guardrails** to bring **fact-checking, safety validation, and ethical filtering** into the workflow.

The system leverages [LangGraph](https://python.langchain.com/docs/langgraph) for dynamic control flow between agents, simulating a research team with distinct roles — from planning and researching to writing, reviewing, and publishing.

> 🛡️ Safety. 🧠 Intelligence. 🤖 Collaboration.

---

## ✨ Highlights

- 🔄 **Multi-Agent System**: Agents for research, planning, revision, writing, and publishing operate in a parallel & coordinated fashion
- 🧠 **LangGraph State Graph**: Models dynamic workflows using conditional routing, looping, and feedback
- 🛡️ **NVIDIA NeMo Guardrails Integration**: End-to-end input/output filtering using `LLMRails` with YAML-based policy
- 🗃️ **Central GuardrailsManager**: Applies guardrails dynamically based on agent context (editor, reviewer, publisher, etc.)
- 📝 **Human-in-the-loop Feedback**: Optional user feedback injected during planning for real-time guidance
- 📄 **APA-Formatted, Multi-Source Research Reports**: Output is clean, cited, and ready for delivery
- 🔄 **Parallelized Subtopic Research**: Subtopics are independently explored to optimize research quality and speed
- 🔧 **Plug-and-play Components**: Easily extensible agent architecture using LangGraph nodes and async I/O

---

## 🧪 Key Use Cases

- 📚 **Academic Research Assistants**
- 🏢 **Enterprise Knowledge Agents**
- 📰 **Media Fact Verification Tools**
- 💡 **R&D Summarizers for Tech/Finance**
- ⚖️ **Ethical AI Content Filtering**

---

## 🧩 The Research Team (Agents)

| Agent         | Responsibility |
|---------------|----------------|
| 👑 **ChiefEditorAgent** | Master controller and LangGraph orchestrator |
| 🧠 **EditorAgent**      | Generates structured outlines |
| 🔎 **ResearchAgent**    | Gathers data from web/local sources |
| 🧪 **ReviewerAgent**    | Validates against user guidelines |
| 🛠️ **ReviserAgent**     | Refines drafts based on reviewer notes |
| ✍️ **WriterAgent**       | Composes final content: intro, conclusion, APA |
| 📤 **PublisherAgent**    | Exports research to PDF, DOCX, Markdown |
| 👤 **HumanAgent**        | Accepts real-time feedback (optional) |

All agents apply guardrails where applicable to input and output.

---

## 🧱 Architecture Diagram

<div align="center">
<img align="center" height="600" src="https://github.com/user-attachments/assets/ef561295-05f4-40a8-a57d-8178be687b18" alt="LangGraph Multi-Agent Architecture"/>
</div>

---

## 🔁 Sample Workflow

1. 🧠 Initial research by `ResearchAgent`
2. ✍️ Outline planned by `EditorAgent`
3. 👤 (Optional) `HumanAgent` feedback
4. 🔄 Parallel subtopic exploration → draft generation
5. 🧪 Review → 🛠️ Revise until satisfied
6. ✨ Final layout composed by `WriterAgent`
7. 📤 Exported to selected formats by `PublisherAgent`

---

## ⚙️ How to Run It

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add API Keys in `.env`
```env
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key
```

### 3. Configure the Task
Edit `multi_agents/task.json`:

```json
{
  "query": "Impact of generative AI on cybersecurity",
  "model": "gpt-4o",
  "max_sections": 5,
  "include_human_feedback": true,
  "publish_formats": {
    "pdf": true,
    "markdown": true,
    "docx": true
  },
  "source": "web",
  "follow_guidelines": true,
  "guidelines": [
    "Use APA style",
    "Avoid speculative content",
    "Cite all sources properly"
  ],
  "verbose": true
}
```

### 4. Launch the System
```bash
python multi_agents/main.py
```

---

## 🛡️ Guardrails Config

The NeMo Guardrails policy is defined in:

```
multi_agents/config/config.yml
```

This includes:
- ✅ `self_check_input`: Blocks unethical, unsafe, or PII-based prompts
- ✅ `self_check_output`: Filters hallucinated, biased, or fabricated content
- 🎯 Agent-type targeting (e.g., only apply review filtering to `ReviewerAgent`)

---

## 🧠 Sample Research Report Output

> ✅ 5-6 page reports  
> ✅ APA-formatted  
> ✅ Table of Contents  
> ✅ Real sources with links  
> ✅ Clean formatting for DOCX, PDF, MD  

Exported to `/outputs/run_{timestamp}_{query}`.

---

## 👨‍💻 Author & Maintainer

**Sai Dhanush Kolla**  
🎓 Master's in Data Science, Indiana University  
💻 Research Assistant — AI & Ethics  
🌐 [LinkedIn](https://www.linkedin.com/in/kolla-saidhanush) | [GitHub](https://github.com/SaiDhanushKolla777)  
📧 saidhanushkolla1990@gmail.com

---

## 🙌 Acknowledgements

This project is a fork and extension of the fantastic [GPT-Researcher](https://github.com/assafelovic/gpt-researcher) by [Assaf Elovic](https://twitter.com/assaf_elovic), a pioneering open-source contribution in the autonomous agent space.  
LangGraph and NeMo Guardrails form the backbone of this secure orchestration.

---

## 📌 Future Ideas

- 🧠 Memory Agent for context persistence  
- 🧾 LangSmith-powered evaluations  
- 🌍 Native multilingual support  
- 🔒 External safety audits via Giskard or similar  

---

<p align="center">
<a href="#top">⬆️ Back to Top</a>
</p>
