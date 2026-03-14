"""Research orchestrator for running agents in parallel"""
import asyncio
from typing import Callable, List, Dict, Any, Optional
from agents.research.research_agent import ResearchAgent


class ResearchOrchestrator:
    """Orchestrates research agents for multiple companies"""

    def __init__(self, max_parallel: int = 5):
        """
        Initialize orchestrator.

        Args:
            max_parallel: Maximum number of parallel agents
        """
        self.max_parallel = max_parallel

    async def run_research(
        self,
        companies: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run research agents for multiple companies in parallel.

        Args:
            companies: List of company data dictionaries
            progress_callback: Optional callback for progress updates (completed, total, message)

        Returns:
            List of research results
        """
        results = []
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def research_company(company: Dict[str, Any]) -> Dict[str, Any]:
            """Research a single company with semaphore for concurrency control"""
            async with semaphore:
                try:
                    agent = ResearchAgent()
                    result = await agent.run(company)

                    if progress_callback:
                        progress_callback(
                            len(results) + 1,
                            len(companies),
                            f"Completed research for {company.get('name', 'Unknown')}",
                        )

                    return result
                except Exception as e:
                    print(f"Error researching {company.get('name')}: {e}")
                    return None

        # Run all research tasks concurrently
        tasks = [research_company(company) for company in companies]
        batch_results = await asyncio.gather(*tasks)

        # Filter out None results
        results = [r for r in batch_results if r is not None]

        return results
