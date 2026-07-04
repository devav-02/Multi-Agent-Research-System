# ── Standard library ──────────────────────────────────────────────────────
import os
import re

# ── Local ─────────────────────────────────────────────────────────────────
from tools import scrape_url
from agents import (
    build_search_agent,
    writer_chain,
    critic_chain,
)


# --------------------------------------------------------------------------
# Helper — safely convert ANY chain/agent output to a plain str.
#
# LangChain chains can return:
#   • a plain str                 → use as-is
#   • an AIMessage object         → extract .content
#   • a list of content blocks    → join all text blocks
#   • anything else               → str() fallback
# --------------------------------------------------------------------------
def _to_str(value) -> str:
    """Return a guaranteed plain-string representation of a chain output."""
    if isinstance(value, str):
        return value

    # LangChain AIMessage (and BaseMessage subclasses)
    if hasattr(value, "content"):
        content = value.content
        # content itself can be a list of dicts e.g. [{"type":"text","text":"..."}]
        if isinstance(content, list):
            return "\n".join(
                block.get("text", str(block))
                for block in content
                if isinstance(block, dict)
            )
        return str(content)

    # Raw list of strings or dicts
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", str(item)))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    # Fallback
    return str(value)


class ResearchPipeline:

    def __init__(self):

        # ============================
        # Agents
        # ============================

        self.search_agent = build_search_agent()

        # ============================
        # Chains
        # ============================

        self.writer = writer_chain
        self.critic = critic_chain

        # ============================
        # Shared State
        # ============================

        self.state = {
            "topic":             "",
            "search_results":    "",
            "urls":              [],
            "scraped_content":   [],
            "combined_research": "",
            "report":            "",
            "feedback":          "",
        }

    # ==========================================================
    # STEP 1 : SEARCH
    # ==========================================================

    def search(self, topic: str):

        print("\n" + "=" * 80)
        print("🔍 STEP 1 : SEARCH AGENT")
        print("=" * 80)

        self.state["topic"] = topic

        response = self.search_agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"""
Find recent, reliable and detailed information about:

{topic}

IMPORTANT RULES:

1. Use ONLY the web_search tool.

2. Return ALL search results.

3. Keep every Title.

4. Keep every URL.

5. Keep every Snippet.

6. Do NOT summarize.

7. Return the tool output exactly.
"""
                    )
                ]
            }
        )

        self.state["search_results"] = response["messages"][-1].content
        raw_result = str(self.state["search_results"])

        match = re.search(
            r'"output":"(.*?)"\}\}?$',
            raw_result,
            re.DOTALL,
        )

        if match:
            clean_text = match.group(1)
            clean_text = clean_text.replace("\\n", "\n")
            clean_text = clean_text.replace('\\"', '"')
            self.state["search_results"] = clean_text

        print("\n✅ Search Completed\n")
        print(self.state["search_results"])

        return self.state["search_results"]

    # ==========================================================
    # STEP 2 : EXTRACT URLS
    # ==========================================================

    def extract_urls(self):

        print("\n" + "=" * 80)
        print("🔗 STEP 2 : EXTRACT URLS")
        print("=" * 80)

        search_data = self.state["search_results"]

        if isinstance(search_data, list):
            search_data = "\n".join(str(item) for item in search_data)

        urls = re.findall(
            r"https?://[^\s\]\}]+",
            search_data,
        )

        cleaned_urls = []

        for url in urls:
            url = url.strip()
            url = url.rstrip(".,);]}>")
            if url not in cleaned_urls:
                cleaned_urls.append(url)

        self.state["urls"] = cleaned_urls

        print(f"\n✅ Total URLs Found : {len(cleaned_urls)}\n")

        for index, url in enumerate(cleaned_urls, start=1):
            print(f"{index}. {url}")

        return cleaned_urls

    # ==========================================================
    # STEP 3 : SCRAPE URLS
    # ==========================================================
    # FIX 1 ── This method was accidentally indented INSIDE extract_urls(),
    #           placed after its `return` statement, making it completely
    #           unreachable and never registered as a class method.
    #           Moved to correct class-level indentation.
    # ==========================================================

    def scrape_urls(self):

        print("\n" + "=" * 80)
        print("📖 STEP 3 : SCRAPING WEBPAGES")
        print("=" * 80)

        scraped_documents = []

        total_urls = len(self.state["urls"])

        if total_urls == 0:
            print("❌ No URLs Found.")
            return []

        for index, url in enumerate(self.state["urls"], start=1):

            print(f"\n[{index}/{total_urls}] Scraping")
            print(f"URL : {url}")

            try:
                markdown = scrape_url.invoke(url)

                if not markdown:
                    print("⚠️ Empty Response")
                    continue

                # FIX 2 ── Key was "source" but app.py expects "url" as the
                #           primary key. Changed to "url" for consistency.
                scraped_documents.append({
                    "url":     url,
                    "content": markdown,
                })

                print("✅ Success")

            except Exception as e:
                print(f"❌ Failed : {e}")

        self.state["scraped_content"] = scraped_documents

        print("\n" + "=" * 80)
        print(f"✅ Successfully Scraped {len(scraped_documents)} Webpages")
        print("=" * 80)

        return scraped_documents

    # ==========================================================
    # STEP 4 : COMBINE RESEARCH
    # ==========================================================

    def combine_research(self):

        print("\n" + "=" * 80)
        print("🧠 STEP 4 : COMBINING RESEARCH")
        print("=" * 80)

        combined_text = ""

        for index, document in enumerate(
            self.state["scraped_content"],
            start=1,
        ):
            combined_text += (
                f"\n\n"
                f"SOURCE {index}\n\n"
                f"URL:\n{document['url']}\n\n"
                f"CONTENT\n\n{document['content']}\n\n"
                f"{'-' * 80}\n"
            )

        self.state["combined_research"] = combined_text

        print(f"✅ Combined {len(self.state['scraped_content'])} Documents.")

        return combined_text

    # ==========================================================
    # STEP 5 : GENERATE REPORT
    # ==========================================================
    # FIX 3 ── Removed the duplicate print(type(report)) / print(report)
    #           block that appeared both before and after storing the result.
    #           Kept the single post-assignment confirmation print only.
    # ==========================================================

    def generate_report(self):

        print("\n" + "=" * 80)
        print("✍️ STEP 5 : GENERATING RESEARCH REPORT")
        print("=" * 80)

        raw_report = self.writer.invoke(
            {
                "topic":    self.state["topic"],
                "research": self.state["combined_research"],
            }
        )

        # FIX ── writer_chain may return AIMessage or list, not a plain str.
        #         _to_str() safely extracts the text in all cases.
        report = _to_str(raw_report)
        self.state["report"] = report

        print("✅ Report Generated Successfully")

        return report

    # ==========================================================
    # STEP 6 : REVIEW REPORT
    # ==========================================================

    def review_report(self):

        print("\n" + "=" * 80)
        print("🧐 STEP 6 : REVIEWING REPORT")
        print("=" * 80)

        raw_feedback = self.critic.invoke(
            {
                "report": self.state["report"],
            }
        )

        # FIX ── critic_chain may return AIMessage or list, not a plain str.
        #         _to_str() safely extracts the text in all cases.
        feedback = _to_str(raw_feedback)
        self.state["feedback"] = feedback

        print("✅ Critic Review Completed")

        return feedback

    # ==========================================================
    # STEP 7 : SAVE OUTPUTS
    # ==========================================================
    # FIX 4 ── `import os` was inside this method body.
    #           Moved to the top of the file where all imports belong.
    # ==========================================================

    def save_outputs(self):

        print("\n" + "=" * 80)
        print("💾 STEP 7 : SAVING OUTPUTS")
        print("=" * 80)

        os.makedirs("outputs", exist_ok=True)

        report_path = "outputs/report.md"
        critic_path = "outputs/critic.md"
        search_path = "outputs/search_results.txt"
        scrape_path = "outputs/scraped_content.md"

        # FIX ── f.write() only accepts str. _to_str() guards every field in
        #         case any chain returned a non-string type (list, AIMessage…).
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(_to_str(self.state["report"]))

        with open(critic_path, "w", encoding="utf-8") as f:
            f.write(_to_str(self.state["feedback"]))

        with open(search_path, "w", encoding="utf-8") as f:
            f.write(_to_str(self.state["search_results"]))

        with open(scrape_path, "w", encoding="utf-8") as f:
            f.write(_to_str(self.state["combined_research"]))

        print("✅ Outputs Saved Successfully")

    # ==========================================================
    # STEP 8 : RUN PIPELINE
    # ==========================================================

    def run(self, topic: str) -> dict:

        self.search(topic)

        self.extract_urls()

        self.scrape_urls()

        self.combine_research()

        self.generate_report()

        self.review_report()

        self.save_outputs()

        print("\n" + "=" * 80)
        print("🎉 RESEARCH PIPELINE COMPLETED")
        print("=" * 80)

        return self.state


# --------------------------------------------------------------------------
# CLI entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":

    topic = input("\nEnter Research Topic : ")

    pipeline = ResearchPipeline()

    result = pipeline.run(topic)

    print("\n" + "=" * 80)
    print("📄 FINAL REPORT")
    print("=" * 80)
    print(result["report"])

    print("\n" + "=" * 80)
    print("🧐 CRITIC FEEDBACK")
    print("=" * 80)
    print(result["feedback"])