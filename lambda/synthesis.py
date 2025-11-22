import json
import logging
import os
from datetime import datetime

import boto3
from anthropic import Anthropic

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


def handler(event, context):
    """
    Synthesis Lambda: Generates executive summary from all agent findings.

    Input: {
        session_id, job_id, instructions,
        obstacles_findings, solutions_findings, legal_findings,
        competitor_findings, market_findings
    }
    Output: {synthesis with consolidated citations}
    """
    logger.info(f"Synthesis Lambda received event: {json.dumps(event)}")

    try:
        # Parse input
        session_id = event["session_id"]
        job_id = event["job_id"]
        instructions = event["instructions"]
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})
        legal_findings = event.get("legal_findings", {})
        competitor_findings = event.get("competitor_findings", {})
        market_findings = event.get("market_findings", {})

        logger.info(f"Generating synthesis for job {job_id}")

        # Update status
        jobs_table.update_item(
            Key={"session_id": session_id, "id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "synthesizing",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Generate synthesis with citation consolidation
        synthesis = generate_synthesis(
            instructions,
            obstacles_findings,
            solutions_findings,
            legal_findings,
            competitor_findings,
            market_findings
        )

        # Build final result
        final_result = {
            "instructions": instructions,
            "findings": {
                "obstacles": obstacles_findings,
                "solutions": solutions_findings,
                "legal": legal_findings,
                "competitors": competitor_findings,
                "market": market_findings,
            },
            "synthesis": synthesis,
            "completed_at": datetime.utcnow().isoformat(),
        }

        # Update job with final result
        jobs_table.update_item(
            Key={"session_id": session_id, "id": job_id},
            UpdateExpression=(
                "SET #status = :status, "
                "#result = :result, "
                "updated_at = :updated_at, "
                "completed_at = :completed_at"
            ),
            ExpressionAttributeNames={
                "#status": "status",
                "#result": "result"
            },
            ExpressionAttributeValues={
                ":status": "completed",
                ":result": json.dumps(final_result),
                ":updated_at": datetime.utcnow().isoformat(),
                ":completed_at": datetime.utcnow().isoformat()
            },
        )

        logger.info(f"Synthesis completed for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "job_id": job_id,
                "synthesis": synthesis,
                "status": "completed"
            })
        }

    except Exception as e:
        logger.error(f"Error in Synthesis Lambda: {str(e)}", exc_info=True)

        if "session_id" in locals() and "job_id" in locals():
            try:
                jobs_table.update_item(
                    Key={"session_id": session_id, "id": job_id},
                    UpdateExpression=(
                        "SET #status = :status, "
                        "error_message = :error, "
                        "updated_at = :updated_at"
                    ),
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "failed",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def generate_synthesis(instructions, obstacles, solutions, legal, competitors, market):
    """
    Generate executive summary synthesizing all research findings with proper citation attribution.
    """
    # Extract and consolidate citations from all agents
    all_citations = []
    citation_map = {}  # Maps original cite_id to new cite_id

    def extract_and_renumber_citations(findings, prefix):
        """Extract citations from findings and renumber them with a prefix."""
        citations = findings.get("citations", [])
        for i, citation in enumerate(citations):
            original_id = citation.get("id", f"{prefix}_{i}")
            new_id = f"{prefix}_{i+1}"
            citation_copy = citation.copy()
            citation_copy["id"] = new_id
            all_citations.append(citation_copy)
            citation_map[original_id] = new_id

    # Extract citations from each agent
    extract_and_renumber_citations(obstacles, "obs")
    extract_and_renumber_citations(solutions, "sol")
    extract_and_renumber_citations(legal, "leg")
    extract_and_renumber_citations(competitors, "comp")
    extract_and_renumber_citations(market, "mkt")

    logger.info(f"Consolidated {len(all_citations)} citations from all agents")

    system_prompt = """You are an executive business analyst creating a comprehensive market research report for institutional investors making multi-million dollar go/no-go decisions.

CRITICAL - CITATION REQUIREMENTS:
This report will be used to justify major investment decisions. Every claim, data point, and conclusion MUST be properly attributed to sources using citation references.

Your role is to synthesize findings from 5 research agents into a clear, actionable executive summary.

The summary should include these sections:
1. **Executive Summary** (200 words) - Key takeaways and recommendation
2. **Problem Statement** (150 words) - Clear articulation of the opportunity
3. **Key Obstacles & Challenges** - Critical barriers with severity assessment (cite sources)
4. **Existing Solutions Analysis** - Current market offerings and their gaps (cite sources)
5. **Legal & Regulatory Landscape** - Compliance requirements and complexity (cite official sources)
6. **Competitive Dynamics** - Market structure, key players, barriers to entry (cite sources)
7. **Market Opportunity** - TAM/SAM/SOM with growth projections (cite research sources)
8. **Strategic Recommendations** - Actionable next steps with risk assessment

CITATION USAGE:
- Reference citations inline using [cite_id] format (e.g., "The market is valued at $2.5B [mkt_1]")
- Use citations for ALL quantitative claims (market sizes, growth rates, pricing)
- Use citations for ALL qualitative assessments (competitor strengths, regulatory requirements)
- Multiple citations can support one claim [cite_1, cite_2]
- Every major finding should trace back to at least one source

WRITING STYLE:
- Professional, analytical tone appropriate for institutional investors
- Use specific data points, not vague terms ("$2.5B market" not "large market")
- Bullet points for key insights within sections
- Clear risk vs opportunity assessment
- Aim for 1500-2000 words

Focus on actionable intelligence that informs investment decisions."""

    all_findings = f"""
PROBLEM CONTEXT:
{instructions}

OBSTACLES FINDINGS:
{json.dumps(obstacles, indent=2)}

SOLUTIONS FINDINGS:
{json.dumps(solutions, indent=2)}

LEGAL/REGULATORY FINDINGS:
{json.dumps(legal, indent=2)}

COMPETITIVE LANDSCAPE:
{json.dumps(competitors, indent=2)}

MARKET ANALYSIS:
{json.dumps(market, indent=2)}
"""

    user_prompt = f"""Please synthesize the following market research findings into a comprehensive executive summary.

{all_findings}

IMPORTANT:
- Use inline citations [cite_id] throughout your analysis to reference sources
- All citations are provided in the findings above - reference them appropriately
- Ensure every major claim, data point, and conclusion is properly cited
- Create a well-structured report that tells the complete story
- Provide clear, actionable insights with proper source attribution

The citation references will be compiled into a master bibliography that follows your report."""

    logger.info("Generating synthesis with Claude API...")

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=6000,  # Increased for longer, detailed report
        temperature=0.4,  # Slightly higher for better prose
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract text from response
    synthesis_text = ""
    for block in response.content:
        if block.type == "text":
            synthesis_text += block.text

    # Return structured synthesis with citations
    return {
        "executive_summary": synthesis_text,
        "citations": all_citations,
        "citation_count": len(all_citations),
        "research_date": datetime.utcnow().strftime("%Y-%m-%d")
    }
