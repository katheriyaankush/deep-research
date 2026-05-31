import logging
from agents import Agent, ModelSettings, function_tool
from core.open_api import model
from ddgs import DDGS

logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)


@function_tool
def web_search(query: str) -> str:
    """
    Search the web for latest information.
    Returns titles, snippets and URLs.
    """
    logger.info(f"🌐 web_search called with query: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            logger.warning(f"⚠️ No results found for: '{query}'")
            return "No search results found."
        formatted_results = []
        for idx, r in enumerate(results, start=1):
            formatted_results.append(
                f"""
Result {idx}
Title: {r.get("title")}
Snippet: {r.get("body")}
URL: {r.get("href")}
"""
            )
        logger.info(f"✅ web_search returned {len(results)} results for '{query}'")
        return "\n".join(formatted_results)
    except Exception as e:
        logger.error(f"❌ web_search error for '{query}': {e}")
        return f"Search error: {str(e)}"


search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[web_search],
    model=model,
    model_settings=ModelSettings(tool_choice="required"),
)
