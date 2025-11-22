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
    Solutions Agent: Researches existing manual/digital solutions and workarounds.

    Input: {job_id, problem_context, obstacles_findings}
    Output: {manual_solutions, digital_solutions, workarounds, gaps, sources}
    """
    logger.info(f"Solutions Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        instructions = event.get("instructions", event.get("problem_context", ""))
        obstacles_findings = event.get("obstacles_findings", {})

        logger.info(f"Processing Solutions Agent for job {job_id}")

        # Update job status
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "processing_solutions",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Run agent with Claude
        result = run_solutions_analysis(instructions, obstacles_findings)

        # Save findings to DynamoDB
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression=("SET solutions_findings = :findings, " "updated_at = :updated_at"),
            ExpressionAttributeValues={
                ":findings": json.dumps(result),
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Completed Solutions Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "solutions", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Solutions Agent: {str(e)}", exc_info=True)

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
                        ":status": "failed_solutions",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def run_solutions_analysis(problem_context, obstacles_findings):
    """
    Analyze existing solutions using Claude with web search tools.
    """
    system_prompt = """You are an expert analyst researching existing solutions and workarounds for problems. Your research will inform multi-million dollar go/no-go decisions for institutional investors.

CITATION REQUIREMENTS - CRITICAL:
Your findings MUST be backed by credible, verifiable sources with complete citation information. Prioritize:
1. Official product websites and company information
2. Product review sites - G2, Capterra, TrustRadius, Product Hunt
3. Industry analyst reports - Gartner Magic Quadrants, Forrester Wave
4. Major tech publications - TechCrunch, The Information, VentureBeat
5. Company financial data - Crunchbase, PitchBook, company announcements
6. User community discussions - Reddit, Hacker News, industry forums (with verification)

For EVERY solution, workaround, or gap identified, you must provide detailed citations including:
- Full URL (must be accessible)
- Source title
- Publishing organization
- Publication date (if available)
- Specific data point, quote, or review
- Explanation of credibility

AVOID: Unverified claims, anonymous reviews, promotional content without third-party validation.

Your role is to identify:
1. Manual solutions - how people solve this problem manually today
2. Digital solutions - existing software/apps/platforms addressing this
3. Workarounds - creative ways people bypass the problem
4. Gaps - what's missing in current solutions that creates opportunities

For each finding, provide:
- Specific examples with verifiable details
- Evidence-based effectiveness assessment
- Limitations backed by user feedback or reviews
- Direct links to sources

Use web_search and web_fetch extensively to find authoritative information.

Output your findings as a JSON object with this structure:
{
  "manual_solutions": [
    {
      "name": "Solution name or description",
      "description": "How it works",
      "effectiveness": "full|partial|poor - with justification",
      "limitations": "Specific limitations with evidence",
      "adoption_level": "widespread|common|niche|rare",
      "citation_ids": ["cite_1", "cite_2"]
    }
  ],
  "digital_solutions": [
    {
      "name": "Product/Service Name",
      "company": "Company name",
      "url": "Official website",
      "description": "What it does",
      "market_position": "leader|challenger|niche|emerging",
      "strengths": "Key advantages with evidence",
      "weaknesses": "Key limitations with evidence",
      "pricing_model": "free|freemium|subscription|enterprise",
      "user_base": "Approximate size or scale if available",
      "citation_ids": ["cite_1", "cite_2"]
    }
  ],
  "workarounds": [
    {
      "description": "Workaround description",
      "prevalence": "How common this workaround is",
      "limitations": "Why it's suboptimal",
      "citation_ids": ["cite_1"]
    }
  ],
  "gaps": [
    {
      "gap": "What's missing in current solutions",
      "evidence": "Proof this gap exists (user complaints, missing features)",
      "opportunity_size": "potential impact if solved",
      "citation_ids": ["cite_1"]
    }
  ],
  "citations": [
    {
      "id": "cite_1",
      "url": "https://...",
      "title": "Article or Product Page Title",
      "source_organization": "Organization Name",
      "source_type": "product_page|review_site|industry_report|publication|community|financial_data",
      "date_published": "YYYY-MM-DD or null if unavailable",
      "date_accessed": "YYYY-MM-DD",
      "author": "Author Name or null",
      "excerpt": "Relevant quote, data point, or review excerpt",
      "relevance": "How this source supports the finding",
      "credibility_indicators": "Why this source is trustworthy"
    }
  ]
}"""

    obstacles_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{obstacles_context}

Given the identified obstacles, please research existing solutions and workarounds.

RESEARCH REQUIREMENTS:
Use web_search and web_fetch extensively to gather authoritative information:
- Official product websites and documentation
- Verified product review platforms (G2, Capterra, TrustRadius)
- Industry analyst assessments and comparisons
- Tech publication product reviews and coverage
- Company funding and market presence data
- User community discussions (verify claims with multiple sources)

Focus on:
- Specific named products with verifiable details
- Market leaders and their limitations (backed by reviews/reports)
- Manual processes currently in use (with adoption evidence)
- Documented workarounds (from user forums, support docs)
- Identified gaps in existing solutions (backed by user feedback)

CRITICAL: Every solution, product feature, limitation, and gap must be linked to credible citations. If you find product information, cite both the official source AND third-party reviews/assessments. Do not describe solutions without verifiable sources.

Today's date is {datetime.utcnow().strftime("%Y-%m-%d")} - use this for date_accessed in citations."""

    logger.info("Calling Claude API for solutions analysis...")

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
            },
            {
                "name": "web_fetch",
                "description": "Fetch and read the full content of a webpage",
                "input_schema": {
                    "type": "object",
                    "properties": {"url": {"type": "string", "description": "The URL to fetch"}},
                    "required": ["url"],
                },
            },
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
        "manual_solutions": [],
        "digital_solutions": [],
        "workarounds": [],
        "gaps": [],
        "citations": [],
        "raw_response": text_content[:1000],
        "parse_error": "Could not parse structured JSON from response",
    }
