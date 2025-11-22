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
    Competitor Agent: Analyzes competitive landscape.

    Input: {job_id, problem_context, obstacles_findings, solutions_findings, legal_findings}
    Output: {direct_competitors, indirect_competitors, market_structure, barriers, white_space, sources}
    """
    logger.info(f"Competitor Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        instructions = event.get("instructions", event.get("problem_context", ""))
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})
        legal_findings = event.get("legal_findings", {})

        logger.info(f"Processing Competitor Agent for job {job_id}")

        # Update job status
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "processing_competitors",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Run agent with Claude
        result = run_competitor_analysis(
            instructions, obstacles_findings, solutions_findings, legal_findings
        )

        # Save findings to DynamoDB
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression=("SET competitor_findings = :findings, " "updated_at = :updated_at"),
            ExpressionAttributeValues={
                ":findings": json.dumps(result),
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Completed Competitor Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "competitor", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Competitor Agent: {str(e)}", exc_info=True)

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
                        ":status": "failed_competitors",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def run_competitor_analysis(
    problem_context, obstacles_findings, solutions_findings, legal_findings
):
    """
    Analyze competitive landscape using Claude with web search.
    """
    system_prompt = """You are an expert competitive intelligence analyst specializing in market analysis. Your research will inform multi-million dollar go/no-go decisions for institutional investors.

CITATION REQUIREMENTS - CRITICAL:
Your findings MUST be backed by credible, verifiable sources with complete citation information. Prioritize:
1. Company financial data - Crunchbase, PitchBook, SEC filings, company investor relations
2. Industry analyst reports - Gartner, Forrester, IDC market analyses
3. Major business publications - Bloomberg, WSJ, Financial Times, Forbes
4. Market research firms - Statista, eMarketer, CB Insights
5. Company websites - official product pages, about pages, pricing
6. Tech news - TechCrunch, The Information, VentureBeat (for recent developments)

For EVERY competitor, market assessment, or barrier identified, you must provide detailed citations including:
- Full URL to verifiable source
- Source title and publication
- Organization publishing the data
- Publication/update date
- Specific data point, quote, or metric
- Explanation of how this validates the finding

AVOID: Speculation without evidence, outdated information, unverified claims, anonymous sources.

Your role is to identify:
1. Direct competitors - companies/products solving the exact same problem
2. Indirect competitors - alternative solutions or substitute products
3. Market structure - monopolistic, oligopolistic, fragmented, or emerging
4. Entry barriers - what makes it hard for new entrants to compete
5. White space opportunities - underserved segments or gaps

For each finding, provide:
- Verifiable company/product names with official sources
- Evidence-based market positioning
- Documented strengths and weaknesses (from reviews, reports)
- Verified funding/revenue data with dates
- Recent developments with news citations

Use web_search and web_fetch extensively to find authoritative information.

Output your findings as a JSON object with this structure:
{
  "direct_competitors": [
    {
      "name": "Company/Product Name",
      "company_legal_name": "Official legal entity name",
      "url": "Official website",
      "founded": "Year founded",
      "headquarters": "Location",
      "description": "What they do",
      "value_proposition": "Their key differentiation",
      "strengths": [
        {"strength": "Specific advantage", "evidence": "Supporting data", "citation_ids": ["cite_1"]}
      ],
      "weaknesses": [
        {"weakness": "Specific limitation", "evidence": "Supporting data", "citation_ids": ["cite_1"]}
      ],
      "market_position": "leader|challenger|niche|emerging",
      "funding": {
        "total_raised": "Amount in USD",
        "last_round": "Series X, $Y, Date",
        "investors": ["Investor names"],
        "citation_ids": ["cite_1"]
      },
      "revenue": {
        "amount": "Reported revenue if available",
        "year": "Fiscal year",
        "growth_rate": "YoY growth if available",
        "citation_ids": ["cite_1"]
      },
      "customer_base": "Known customer count or scale",
      "recent_developments": [
        {"development": "What happened", "date": "When", "citation_ids": ["cite_1"]}
      ],
      "citation_ids": ["cite_1", "cite_2"]
    }
  ],
  "indirect_competitors": [
    {
      "name": "Company/Product Name",
      "type": "substitute|alternative|adjacent",
      "description": "What they do",
      "why_competitive": "How they compete indirectly",
      "market_overlap": "Degree of overlap",
      "citation_ids": ["cite_1"]
    }
  ],
  "market_structure": {
    "type": "monopolistic|oligopolistic|fragmented|emerging",
    "description": "Market dynamics explanation",
    "concentration": "Market share distribution",
    "key_players": [
      {"name": "Player name", "estimated_share": "Market share if available", "citation_ids": ["cite_1"]}
    ],
    "trends": ["Key market trends with evidence"],
    "citation_ids": ["cite_1"]
  },
  "barriers": [
    {
      "type": "brand|network_effect|technology|regulatory|capital|distribution|data",
      "description": "Specific barrier description",
      "severity": "high|medium|low",
      "evidence": "Why this is a barrier",
      "affected_entrants": "Who this impacts",
      "citation_ids": ["cite_1"]
    }
  ],
  "white_space": [
    {
      "opportunity": "Underserved segment or gap",
      "description": "What's missing",
      "evidence": "Proof this gap exists",
      "potential_size": "Estimated opportunity if quantifiable",
      "citation_ids": ["cite_1"]
    }
  ],
  "competitive_intensity": {
    "level": "high|medium|low",
    "factors": ["Key factors driving competition"],
    "citation_ids": ["cite_1"]
  },
  "citations": [
    {
      "id": "cite_1",
      "url": "https://...",
      "title": "Article/Report/Page Title",
      "source_organization": "Publishing Organization",
      "source_type": "financial_data|analyst_report|news|company_website|market_research",
      "date_published": "YYYY-MM-DD or null",
      "date_accessed": "YYYY-MM-DD",
      "author": "Author Name or null",
      "excerpt": "Relevant data point, quote, or metric",
      "relevance": "How this supports the finding",
      "credibility_indicators": "Why this source is trustworthy"
    }
  ]
}"""

    previous_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}

PREVIOUS FINDINGS - SOLUTIONS:
{json.dumps(solutions_findings, indent=2)}

PREVIOUS FINDINGS - LEGAL:
{json.dumps(legal_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{previous_context}

Given the problem and previous research, please analyze the competitive landscape.

RESEARCH REQUIREMENTS:
Use web_search and web_fetch extensively to gather authoritative competitive intelligence:
- Company financial databases (Crunchbase, PitchBook) for funding and metrics
- Industry analyst reports for market positioning and trends
- Business publications for recent news and developments
- Company websites for product details and official information
- Market research reports for market structure and sizing
- SEC filings and investor relations pages for public companies
- Product review sites for customer feedback and positioning

Focus on:
- Named competitors with verified company details
- Quantified market shares where available (with sources)
- Documented funding rounds with amounts and dates
- Specific product strengths/weaknesses backed by reviews or reports
- Identified entry barriers with evidence
- White space opportunities with market data support

CRITICAL: Every competitor, market metric, funding figure, and competitive assessment must be linked to credible citations. Cite multiple sources for key claims. Include both company official sources AND third-party validation. Do not estimate or speculate without clearly labeling it as such.

Today's date is {datetime.utcnow().strftime("%Y-%m-%d")} - use this for date_accessed in citations."""

    logger.info("Calling Claude API for competitor analysis...")

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
        "direct_competitors": [],
        "indirect_competitors": [],
        "market_structure": {},
        "barriers": [],
        "white_space": [],
        "competitive_intensity": {},
        "citations": [],
        "raw_response": text_content[:1000],
        "parse_error": "Could not parse structured JSON from response",
    }
