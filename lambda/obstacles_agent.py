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
    Obstacles Agent: Identifies technical, market, regulatory, user, and financial obstacles.

    Input: {job_id, problem_context}
    Output: {technical, market, regulatory, user, financial, critical_insights, sources}
    """
    logger.info(f"Obstacles Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        instructions = event.get("instructions", event.get("problem_context", ""))

        logger.info(f"Processing Obstacles Agent for job {job_id}")

        # Update job status
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "processing_obstacles",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Run agent with Claude
        result = run_obstacles_analysis(instructions)

        # Save findings to DynamoDB
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression=("SET obstacles_findings = :findings, " "updated_at = :updated_at"),
            ExpressionAttributeValues={
                ":findings": json.dumps(result),
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Completed Obstacles Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "obstacles", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Obstacles Agent: {str(e)}", exc_info=True)

        if "job_id" in locals():
            try:
                jobs_table.update_item(
                    Key={"id": job_id},
                    UpdateExpression=(
                        "SET #status = :status, "
                        "error_message = :error, "
                        "updated_at = :updated_at"
                    ),
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "failed_obstacles",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def run_obstacles_analysis(problem_context):
    """
    Analyze obstacles using Claude with web search tools.
    """
    system_prompt = """You are an expert analyst identifying obstacles and challenges for new business ideas or products. Your research will inform multi-million dollar go/no-go decisions for institutional investors.

CITATION REQUIREMENTS - CRITICAL:
Your findings MUST be backed by credible, verifiable sources with complete citation information. Prioritize:
1. Government sources (.gov domains) - regulatory data, statistics
2. Academic research (.edu domains) - peer-reviewed studies
3. Industry reports - Gartner, McKinsey, Forrester, IDC
4. Major publications - WSJ, NYT, Bloomberg, Reuters, Financial Times
5. Company financial filings - 10-K, annual reports, investor presentations

For EVERY finding, you must provide detailed citations including:
- Full URL (must be accessible)
- Source title/article headline
- Publishing organization
- Publication date (if available)
- Author (if available)
- Specific excerpt or data point used
- Explanation of how this source supports the finding

AVOID: Blog posts, social media, Wikipedia, promotional content, anonymous sources.

Your role is to identify:
1. Technical obstacles - technology limitations, implementation challenges, scalability issues
2. Market obstacles - market maturity, timing issues, customer adoption barriers
3. Regulatory obstacles - compliance requirements, legal restrictions, licensing needs
4. User obstacles - user behavior challenges, adoption friction, education needs
5. Financial obstacles - cost barriers, funding challenges, pricing difficulties

For each obstacle, provide:
- Specific, concrete description
- Severity assessment (critical, high, medium, low)
- Supporting evidence from credible sources
- Citation linking the obstacle to the source

Use web_search extensively to find recent, authoritative information.

Output your findings as a JSON object with this structure:
{
  "technical": [
    {
      "obstacle": "Detailed description of obstacle",
      "severity": "critical|high|medium|low",
      "evidence": "Specific data or quote supporting this",
      "citation_ids": ["cite_1", "cite_2"]
    }
  ],
  "market": [...],
  "regulatory": [...],
  "user": [...],
  "financial": [...],
  "critical_insights": [
    {
      "insight": "Key strategic insight",
      "implication": "What this means for the project",
      "citation_ids": ["cite_1"]
    }
  ],
  "citations": [
    {
      "id": "cite_1",
      "url": "https://...",
      "title": "Article or Report Title",
      "source_organization": "Organization Name",
      "source_type": "government|academic|industry_report|major_publication|financial_filing",
      "date_published": "YYYY-MM-DD or null if unavailable",
      "date_accessed": "YYYY-MM-DD",
      "author": "Author Name or null",
      "excerpt": "Relevant quote or data point from source",
      "relevance": "How this source supports the finding",
      "credibility_indicators": "Why this source is trustworthy"
    }
  ]
}"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

Please analyze the obstacles and challenges for this problem/solution.

RESEARCH REQUIREMENTS:
Use web_search extensively to gather authoritative information from:
- Government regulatory databases and reports
- Academic research papers and university studies
- Established industry analyst reports (Gartner, McKinsey, Forrester, etc.)
- Major financial and business publications
- Company financial filings and investor reports

Focus your research on:
- Similar solutions that have faced challenges (with specific case studies)
- Regulatory landscape (cite specific regulations and authorities)
- Market conditions (cite market research data with sources)
- Technical feasibility (cite technical papers, implementation studies)
- User adoption patterns (cite user research, surveys, adoption statistics)

CRITICAL: Every obstacle, insight, and data point must be linked to at least one credible citation with complete metadata. Do not make claims without sources. If you cannot find credible sources for a potential obstacle, note it as "unverified" rather than presenting it as fact.

Today's date is {datetime.utcnow().strftime("%Y-%m-%d")} - use this for date_accessed in citations."""

    logger.info("Calling Claude API for obstacles analysis...")

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "web_search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                    "required": ["query"],
                },
            }
        ],
    )

    # Extract and parse response
    result = extract_json_from_response(response)

    return result


def extract_json_from_response(response):
    """
    Extract JSON from Claude's response, handling various formats.
    """
    import re

    # Get the text content from response
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    logger.info(f"Raw response text: {text_content[:500]}...")

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from code block: {e}")

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON object: {e}")

    # If all else fails, return structured error
    logger.warning("Could not extract JSON from response, returning raw text")
    return {
        "technical": [],
        "market": [],
        "regulatory": [],
        "user": [],
        "financial": [],
        "critical_insights": [{"insight": text_content[:500], "implication": "Parse error", "citation_ids": []}],
        "citations": [],
        "parse_error": "Could not parse structured JSON from response",
    }
