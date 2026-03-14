"""Research agent for comprehensive company analysis across 8 pillars"""
import json
from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent


PILLAR_DESCRIPTIONS = {
    "data_quality": "Data Quality & Availability - How mature are the company's data assets and infrastructure? What data collection and storage capabilities exist?",
    "workflow_digitization": "Workflow Digitization - To what extent are key business processes digitized? What is the automation maturity level?",
    "infrastructure": "Infrastructure Readiness - Does the company have modern, scalable cloud infrastructure? Are systems AI-ready?",
    "competitive_position": "Competitive Position - What is the company's market position and AI differentiation potential?",
    "revenue_upside": "Revenue Upside - What are the opportunities for new revenue streams through AI products/features?",
    "margin_upside": "Margin Upside - How much cost reduction and efficiency improvement is possible through AI/automation?",
    "org_readiness": "Org Readiness - Does the team have the capabilities and culture to adopt AI solutions?",
    "risk_compliance": "Risk & Compliance - What are the regulatory, data privacy, and governance considerations?",
}


class ResearchAgent(BaseAgent):
    """
    Research agent that evaluates a single company across all 8 AI readiness pillars.
    Uses Claude + MCP tools to gather intelligence and produce structured scores.
    """

    async def run(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research a company across all 8 pillars.

        Args:
            company: Company data dictionary with name, website, vertical, etc.

        Returns:
            Structured research result with pillar scores
        """
        company_name = company.get("name", "Unknown Company")

        # Build research context
        research_context = f"""
You are an expert AI readiness analyst. Evaluate {company_name} across the 8-pillar AI readiness framework.

Company Info:
- Name: {company_name}
- Vertical: {company.get('vertical', 'Unknown')}
- Website: {company.get('website', 'N/A')}
- Employees: {company.get('employee_count', 'Unknown')}
- GitHub: {company.get('github_org', 'N/A')}

For each pillar, provide:
1. Score (0-5 scale)
2. Confidence (0-1 scale)
3. Key evidence points
4. Research sources

Focus on factual, evidence-based analysis.
"""

        # Use Claude to analyze each pillar
        client = self.get_claude_client()
        if not client:
            return self._mock_research(company_name)

        pillar_results = {}

        for pillar_key, pillar_desc in PILLAR_DESCRIPTIONS.items():
            prompt = f"""{research_context}

PILLAR: {pillar_desc}

Based on your knowledge and research capabilities, evaluate this pillar for {company_name}.

Respond with JSON:
{{
    "score": <0-5>,
    "confidence": <0-1>,
    "evidence": ["point1", "point2", "point3"],
    "reasoning": "explanation"
}}
"""

            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Parse response
                text = response.content[0].text
                result = self._parse_pillar_response(text)
                pillar_results[pillar_key] = result

            except Exception as e:
                print(f"Error evaluating pillar {pillar_key}: {e}")
                pillar_results[pillar_key] = {
                    "score": 3.0,
                    "confidence": 0.5,
                    "evidence": ["Mock data - evaluation error"],
                    "sources": [],
                }

        # Compile results
        return {
            "company_id": company.get("id", ""),
            "company_name": company_name,
            "pillars": pillar_results,
            "research_summary": f"Comprehensive AI readiness analysis of {company_name}",
            "timestamp": "2024-01-15T12:00:00Z",
        }

    @staticmethod
    def _parse_pillar_response(text: str) -> Dict[str, Any]:
        """Extract JSON from Claude response"""
        try:
            # Try to extract JSON from response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                data = json.loads(json_str)
                return {
                    "score": min(5.0, max(0.0, data.get("score", 3.0))),
                    "confidence": min(1.0, max(0.0, data.get("confidence", 0.7))),
                    "evidence": data.get("evidence", []),
                    "sources": data.get("sources", []),
                }
        except Exception as e:
            print(f"Error parsing pillar response: {e}")

        # Default response
        return {
            "score": 3.0,
            "confidence": 0.6,
            "evidence": ["Unable to parse response"],
            "sources": [],
        }

    @staticmethod
    def _mock_research(company_name: str) -> Dict[str, Any]:
        """Generate mock research for testing"""
        mock_scores = {
            "data_quality": 3.5,
            "workflow_digitization": 3.4,
            "infrastructure": 3.2,
            "competitive_position": 3.6,
            "revenue_upside": 3.3,
            "margin_upside": 3.1,
            "org_readiness": 3.0,
            "risk_compliance": 3.5,
        }

        return {
            "company_id": "",
            "company_name": company_name,
            "pillars": {
                pillar: {
                    "score": score,
                    "confidence": 0.75,
                    "evidence": [
                        f"Mock evidence for {pillar} - {company_name}",
                        "Based on public information and market research",
                    ],
                    "sources": ["https://example.com", "https://research.com"],
                }
                for pillar, score in mock_scores.items()
            },
            "research_summary": f"Mock research analysis for {company_name}",
            "timestamp": "2024-01-15T12:00:00Z",
        }
