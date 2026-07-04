from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tools import web_search, scrape_url

load_dotenv()

# =====================================================
# LLM
# =====================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

# =====================================================
# SEARCH AGENT
# =====================================================

def build_search_agent():

    return create_react_agent(
        model=llm,
        tools=[web_search],
        prompt="""
You are a Search Agent.

Your only job is searching.

Rules:

1. ALWAYS use the web_search tool.
2. NEVER answer using your own knowledge.
3. NEVER summarize search results.
4. NEVER rewrite search results.
5. Return tool output exactly as received.
6. Preserve every title.
7. Preserve every URL.
8. Preserve every snippet.
"""
    )


# =====================================================
# READER AGENT
# =====================================================

def build_reader_agent():

    return create_react_agent(
        model=llm,
        tools=[scrape_url],
        prompt="""
You are a Reader Agent.

Rules:

1. ALWAYS call scrape_url.
2. Read the webpage.
3. Ignore advertisements.
4. Ignore menus.
5. Ignore navigation.
6. Return only the webpage content.
"""
    )


# =====================================================
# WRITER CHAIN
# =====================================================

writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert technical research writer.

Rules:

- Use ONLY the supplied research.
- Never invent information.
- Never hallucinate.
- Write a clean professional report.
- Use proper markdown headings.
- Use bullet points where appropriate.
- End with a concise conclusion.
"""
        ),
        (
            "human",
            """
Topic:

{topic}

Research:

{research}
"""
        ),
    ]
)

writer_chain = (
    writer_prompt
    | llm
    | StrOutputParser()
)

# =====================================================
# CRITIC CHAIN
# =====================================================

critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a professional research reviewer.

Evaluate reports honestly.

Never rewrite the report.

Only review it.
"""
        ),
        (
            "human",
            """
Review this report.

{report}

Return EXACTLY this format.

Score: X/10

Strengths
- ...
- ...

Weaknesses
- ...
- ...

Suggestions
- ...
- ...

Final Verdict
...
"""
        ),
    ]
)

critic_chain = (
    critic_prompt
    | llm
    | StrOutputParser()
)