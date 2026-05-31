import logging
import asyncio
from agents import Runner, trace, gen_trace_id
from ai_agents.search_agent import search_agent
from ai_agents.planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from ai_agents.writer_agent import writer_agent, ReportData
from ai_agents.email_agent import email_agent

logger = logging.getLogger(__name__)


class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            logger.info("Starting research...")
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report


    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        logger.info("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        plan = result.final_output_as(WebSearchPlan)
        logger.info(f"Planned {len(plan.searches)} searches:")
        for i, item in enumerate(plan.searches, 1):
            logger.info(f"  [{i}] Query: {item.query}")
            logger.info(f"       Reason: {item.reason}")
        return plan

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        logger.info(f"Starting {len(search_plan.searches)} searches in parallel...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            logger.info(f"Searching... {num_completed}/{len(tasks)} completed")
        logger.info(f"All searches done. {len(results)} results collected.")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        logger.info(f"🔍 Searching: '{item.query}'")
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            output = str(result.final_output)
            logger.info(f"✅ Search result for '{item.query}' ({len(output)} chars):")
            logger.info(f"\n--- SEARCH RESULT: {item.query} ---\n{output}\n--- END ---\n")
            return output
        except Exception as e:
            logger.error(f"❌ Search failed for '{item.query}': {e}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        logger.info(f"Writing report from {len(search_results)} search results...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )
        report = result.final_output_as(ReportData)
        logger.info("✅ Report written")
        logger.info(f"   Summary: {report.short_summary}")
        logger.info(f"   Follow-up questions: {report.follow_up_questions}")
        return report

    async def send_email(self, report: ReportData) -> None:
        logger.info("Sending email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        logger.info("✅ Email agent finished")
        return report