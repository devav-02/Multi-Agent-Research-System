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


# SEARCH AGENT
# =====================================================

def build_search_agent():

    return create_react_agent(
        model=llm,
        tools=[web_search],
        prompt="""
You are a Search Agent.

Rules:

1. ALWAYS call the web_search tool.

2. NEVER answer from your own knowledge.

3. NEVER summarize.

4. NEVER rewrite tool output.

5. Return the tool output exactly as received.

6. Preserve every URL.

7. Preserve every snippet.

8. Preserve every title.
"""
    )



# READER AGENT
# =====================================================

def build_reader_agent():

    return create_react_agent(
        model=llm,
        tools=[scrape_url],
        prompt="""
You are a Reader Agent.

Rules:

- ALWAYS call scrape_url.
- Read the complete webpage.
- Ignore advertisements.
- Ignore navigation.
- Return only extracted webpage content.
"""
    )


# =====================================================
# WRITER
# =====================================================

writer_prompt = ChatPromptTemplate.from_messages([
(
"system",
"""
You are an expert research writer.

Write professional reports.

Never invent facts.

Use only the supplied research.
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
)
])

writer_chain = writer_prompt | llm | StrOutputParser()


# =====================================================
# CRITIC
# =====================================================

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()