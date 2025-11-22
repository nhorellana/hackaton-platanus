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
    Market Agent: Analyzes market size, growth, and dynamics.

    Input: {job_id, problem_context, + all previous findings}
    Output: {market_size, growth_trends, customer_segments, pricing_benchmarks, sources}
    """
    logger.info(f"Market Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        instructions = event.get("instructions", event.get("problem_context", ""))
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})
        legal_findings = event.get("legal_findings", {})
        competitor_findings = event.get("competitor_findings", {})

        logger.info(f"Processing Market Agent for job {job_id}")

        # Update job status
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "processing_market",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Run agent with Claude
        result = run_market_analysis(
            instructions,
            obstacles_findings,
            solutions_findings,
            legal_findings,
            competitor_findings,
        )

        # Save findings to DynamoDB
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression=("SET market_findings = :findings, " "updated_at = :updated_at"),
            ExpressionAttributeValues={
                ":findings": json.dumps(result),
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Completed Market Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "market", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Market Agent: {str(e)}", exc_info=True)

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
                        ":status": "failed_market",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def run_market_analysis(
    problem_context, obstacles_findings, solutions_findings, legal_findings, competitor_findings
):
    """
    Analyze market dynamics using Claude with web search.
    """
    system_prompt = """You are an expert market analyst specializing in market sizing, trends, and customer analysis. Your research will inform multi-million dollar go/no-go decisions for institutional investors.

CITATION REQUIREMENTS - CRITICAL:
Your findings MUST be backed by credible, verifiable market data sources with complete citation information. Prioritize:
1. Market research firms - Gartner, Forrester, IDC, Statista, eMarketer, Grand View Research
2. Industry associations - official trade association reports and statistics
3. Government data - Census Bureau, Bureau of Labor Statistics, industry regulators
4. Financial research - Goldman Sachs, Morgan Stanley, McKinsey sector reports
5. Public company data - SEC filings, earnings calls, investor presentations
6. Academic research - university studies, peer-reviewed market analyses

For EVERY market metric, growth rate, segment size, or pricing data point, you must provide detailed citations including:
- Full URL to verifiable source
- Report title and publication
- Publishing organization
- Publication/report date
- Specific figure, metric, or data point
- Methodology or basis for the figure
- Geographic scope and time period

AVOID: Unsubstantiated estimates, blog posts, marketing materials without data, outdated reports (>2 years old unless historical context).

Your role is to research and quantify:
1. Market size - TAM, SAM, SOM with clear methodology
2. Growth trends - historical rates, projections with evidence
3. Customer segments - quantified segments with characteristics
4. Pricing benchmarks - verified pricing with sources

For each finding, provide:
- Specific quantified metrics (no vague terms like "large" or "growing rapidly")
- Clear geographic scope (Global, US, EU, etc.)
- Time period and date of data
- Calculation methodology where relevant
- Source credibility assessment

Use web_search extensively to find authoritative market data.

Output your findings as a JSON object with this structure:
{
  "market_size": {
    "tam": {
      "value": "Specific number",
      "unit": "USD|units|users",
      "year": "YYYY",
      "geography": "Geographic scope",
      "methodology": "How this was calculated",
      "growth_rate": "CAGR % if available",
      "citation_ids": ["cite_1"]
    },
    "sam": {
      "value": "Specific number",
      "unit": "USD|units|users",
      "year": "YYYY",
      "geography": "Geographic scope",
      "methodology": "How this narrows from TAM",
      "citation_ids": ["cite_1"]
    },
    "som": {
      "value": "Specific number",
      "unit": "USD|units|users",
      "year": "YYYY",
      "geography": "Geographic scope",
      "assumptions": "Realistic capture assumptions",
      "methodology": "How this was calculated",
      "citation_ids": ["cite_1"]
    }
  },
  "growth_trends": {
    "historical": {
      "cagr": "X.X%",
      "time_period": "YYYY-YYYY",
      "key_milestones": ["Milestone with year"],
      "citation_ids": ["cite_1"]
    },
    "projected": {
      "cagr": "X.X%",
      "time_period": "YYYY-YYYY",
      "confidence": "high|medium|low",
      "citation_ids": ["cite_1"]
    },
    "drivers": [
      {"driver": "Growth driver", "impact": "Quantified impact if available", "citation_ids": ["cite_1"]}
    ],
    "headwinds": [
      {"headwind": "Challenge", "impact": "Quantified impact if available", "citation_ids": ["cite_1"]}
    ]
  },
  "customer_segments": [
    {
      "segment_name": "Segment identifier",
      "size": {
        "value": "Specific number",
        "unit": "USD|users|companies",
        "percentage_of_market": "X%",
        "citation_ids": ["cite_1"]
      },
      "characteristics": {
        "demographics": "Key demographic info",
        "firmographics": "Company characteristics if B2B",
        "psychographics": "Behaviors and preferences"
      },
      "needs": ["Specific need 1", "Specific need 2"],
      "buying_behavior": {
        "decision_criteria": ["What drives purchase"],
        "typical_budget": "Budget range if available",
        "purchase_cycle": "Timeframe",
        "decision_makers": "Who buys"
      },
      "willingness_to_pay": {
        "range": "Price range",
        "evidence": "Source of this information",
        "citation_ids": ["cite_1"]
      },
      "citation_ids": ["cite_1"]
    }
  ],
  "pricing_benchmarks": {
    "range": {
      "low": "Minimum price",
      "high": "Maximum price",
      "currency": "USD",
      "unit": "per month|per user|etc."
    },
    "average": {
      "value": "Average price",
      "basis": "How calculated"
    },
    "models": [
      {
        "model_type": "subscription|one-time|usage-based|freemium|tiered",
        "prevalence": "How common",
        "examples": ["Company names using this model"]
      }
    ],
    "examples": [
      {
        "product": "Product name",
        "company": "Company name",
        "price": "Specific price",
        "model": "Pricing model",
        "features": "What's included",
        "citation_ids": ["cite_1"]
      }
    ],
    "citation_ids": ["cite_1"]
  },
  "market_dynamics": {
    "maturity": "emerging|growth|mature|declining",
    "seasonality": "Any seasonal patterns",
    "key_trends": ["Trend 1", "Trend 2"],
    "citation_ids": ["cite_1"]
  },
  "citations": [
    {
      "id": "cite_1",
      "url": "https://...",
      "title": "Report/Article Title",
      "source_organization": "Research Firm/Publisher",
      "source_type": "market_research|government|financial_research|industry_association|academic|company_filing",
      "report_date": "YYYY-MM-DD",
      "date_accessed": "YYYY-MM-DD",
      "author": "Author/Analyst Name or null",
      "excerpt": "Specific data point or quote with numbers",
      "methodology": "How the data was gathered/calculated",
      "sample_size": "If survey/research based",
      "geographic_scope": "Geographic coverage",
      "relevance": "How this supports the finding",
      "credibility_indicators": "Why this source is authoritative"
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

PREVIOUS FINDINGS - COMPETITORS:
{json.dumps(competitor_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{previous_context}

Given the problem and all previous research, please analyze the market dynamics.

RESEARCH REQUIREMENTS:
Use web_search extensively to gather authoritative market data:
- Market research reports (Gartner, Forrester, Statista, IDC, Grand View Research)
- Industry association statistics and reports
- Government economic data and census information
- Financial analyst reports and sector analyses
- Public company filings (10-K, earnings transcripts, investor presentations)
- Academic market research and peer-reviewed studies
- Verified pricing from company websites and review platforms

Focus on:
- Specific market size figures with TAM/SAM/SOM methodology
- Quantified growth rates (historical and projected CAGR) with timeframes
- Customer segment sizes with demographic/firmographic data
- Documented pricing with multiple examples and sources
- Market trends backed by data, not opinions

CRITICAL: Every market figure, growth rate, segment size, and pricing data point must be linked to credible citations. For market sizing, cite the methodology used. For growth projections, cite the basis for the forecast. For segment data, cite the research methodology. Include both primary research sources AND any available validation sources.

Avoid estimates unless clearly labeled. When data is unavailable, state "Data not publicly available" rather than guessing.

Today's date is {datetime.utcnow().strftime("%Y-%m-%d")} - use this for date_accessed in citations. Prioritize recent data (within 2 years) for current market conditions."""

    logger.info("Calling Claude API for market analysis...")

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
        "market_size": {},
        "growth_trends": {},
        "customer_segments": [],
        "pricing_benchmarks": {},
        "market_dynamics": {},
        "citations": [],
        "raw_response": text_content[:1000],
        "parse_error": "Could not parse structured JSON from response",
    }
