import logging
import asyncio
from agents import Runner, trace, gen_trace_id
from ai_agents.search_agent import search_agent
from ai_agents.planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from ai_agents.writer_agent import writer_agent, ReportData
from ai_agents.email_agent import email_agent

logger = logging.getLogger(__name__)


class ResearchManager:

    async def run(self, query: str, email: str):
        """
        Run the deep research process.
        Yields structured event dicts with 'type' and 'data' keys for SSE consumption.
        """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            # --- Step 1: Planning ---
            yield {
                "type": "status",
                "data": {
                    "step": "planning",
                    "message": "Planning research searches...",
                    "progress": 10,
                    "trace_id": trace_id,
                }
            }

            search_plan = await self.plan_searches(query)

            yield {
                "type": "search_plan",
                "data": {
                    "step": "planned",
                    "message": f"Planned {len(search_plan.searches)} searches",
                    "progress": 20,
                    "searches": [
                        {"query": item.query, "reason": item.reason}
                        for item in search_plan.searches
                    ],
                }
            }

            # --- Step 2: Searching ---
            yield {
                "type": "status",
                "data": {
                    "step": "searching",
                    "message": "Searching the web...",
                    "progress": 30,
                }
            }

            search_results = await self.perform_searches(search_plan)

            yield {
                "type": "status",
                "data": {
                    "step": "searches_complete",
                    "message": f"Completed {len(search_results)} searches",
                    "progress": 60,
                }
            }

            # --- Step 3: Writing Report ---
            yield {
                "type": "status",
                "data": {
                    "step": "writing",
                    "message": "Writing research report...",
                    "progress": 70,
                }
            }

            report = await self.write_report(query, search_results)

            yield {
                "type": "status",
                "data": {
                    "step": "sending_email",
                    "message": "Sending report via email...",
                    "progress": 85,
                }
            }

            # --- Step 4: Sending Email ---
            await self.send_email(report, email)

            yield {
                "type": "status",
                "data": {
                    "step": "email_sent",
                    "message": "Email sent successfully",
                    "progress": 95,
                }
            }

            # --- Step 5: Final Report ---
            yield {
                "type": "report",
                "data": {
                    "summary": report.short_summary,
                    "markdown_report": report.markdown_report,
                    "follow_up_questions": report.follow_up_questions,
                }
            }

            yield {
                "type": "done",
                "data": {
                    "message": "Research complete",
                    "progress": 100,
                }
            }

    async def plan_searches(self, query: str) -> WebSearchPlan:
        logger.info("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        plan = result.final_output_as(WebSearchPlan)
        logger.info(f"Planned {len(plan.searches)} searches")
        return plan

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        logger.info(f"Starting {len(search_plan.searches)} searches in parallel...")
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        logger.info(f"All searches done. {len(results)} results collected.")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        logger.info(f"🔍 Searching: '{item.query}'")
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            output = str(result.final_output)
            logger.info(f"✅ Search result for '{item.query}' ({len(output)} chars)")
            return output
        except Exception as e:
            logger.error(f"❌ Search failed for '{item.query}': {e}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        logger.info(f"Writing report from {len(search_results)} search results...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )
        report = result.final_output_as(ReportData)
        logger.info("✅ Report written")
        return report

    async def send_email(self, report: ReportData, email: str) -> None:
        logger.info(f"Sending email to {email}...")
        result = await Runner.run(
            email_agent,
            f"Send to: {email}\n\nReport:\n{report.markdown_report}",
        )
        logger.info("✅ Email agent finished")
        return report
