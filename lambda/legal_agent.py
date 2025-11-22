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
    Legal Agent: Analyzes legal and regulatory requirements.

    Input: {job_id, problem_context, obstacles_findings, solutions_findings}
    Output: {industry_regulations, data_protection, financial_regs, regional_variations, sources}
    """
    logger.info(f"Legal Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        instructions = event.get("instructions", event.get("problem_context", ""))
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})

        logger.info(f"Processing Legal Agent for job {job_id}")

        # Update job status
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "processing_legal",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Run agent with Claude
        result = run_legal_analysis(instructions, obstacles_findings, solutions_findings)

        # Save findings to DynamoDB
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression=("SET legal_findings = :findings, " "updated_at = :updated_at"),
            ExpressionAttributeValues={
                ":findings": json.dumps(result),
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Completed Legal Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "legal", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Legal Agent: {str(e)}", exc_info=True)

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
                        ":status": "failed_legal",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def run_legal_analysis(problem_context, obstacles_findings, solutions_findings):
    """
    Analyze legal and regulatory requirements using Claude with web search.
    """
    system_prompt = """You are an expert legal and regulatory analyst specializing in compliance requirements for new businesses and products. Your research will inform multi-million dollar go/no-go decisions for institutional investors.

CITATION REQUIREMENTS - CRITICAL:
Your findings MUST be backed by authoritative legal and regulatory sources with complete citation information. Prioritize:
1. Government regulatory websites (.gov domains) - official regulations, guidance documents
2. Official legal databases - regulations.gov, EUR-Lex, official gazettes
3. Regulatory body publications - SEC, FTC, FDA, FCC, state agencies
4. Legal analysis from major law firms - compliance guides, legal updates
5. Industry compliance resources - official industry association guidance
6. Official legal texts - statutes, codes, directives with section numbers

For EVERY regulatory requirement, you must provide detailed citations including:
- Full URL to official source
- Official name of regulation/law with section numbers
- Regulatory authority/issuing body
- Date of enactment/most recent update
- Specific compliance requirement text or excerpt
- Jurisdiction and applicability
- Explanation of relevance

AVOID: Unofficial interpretations, blog posts, outdated information, secondary sources without primary citation.

Your role is to identify:
1. Industry-specific regulations - sector-specific laws and compliance requirements
2. Data protection - GDPR, CCPA, data privacy laws
3. Financial regulations - payment processing, money transmission, securities laws
4. Regional variations - how regulations differ by country/state
5. Licensing and certification requirements

For each regulatory category, provide:
- Specific regulations with official names and codes
- Exact jurisdictions and applicability criteria
- Detailed compliance requirements with legal citations
- Specific penalties for non-compliance (with legal basis)
- Implementation timeline and complexity assessment
- Links to official regulatory guidance

Use web_search to find authoritative sources.

Output your findings as a JSON object with this structure:
{
  "industry_regulations": [
    {
      "regulation_name": "Official regulation name with code/section",
      "regulatory_body": "Issuing authority",
      "jurisdiction": "Specific jurisdiction(s)",
      "requirements": "Detailed compliance requirements",
      "applicability": "When/how this applies",
      "complexity": "high|medium|low",
      "implementation_timeline": "Estimated time to comply",
      "citation_ids": ["cite_1", "cite_2"]
    }
  ],
  "data_protection": [
    {
      "law_name": "Official law name (e.g., GDPR Article 6)",
      "jurisdiction": "Geographic scope",
      "key_requirements": "Specific obligations",
      "applicability_threshold": "When this applies",
      "penalties": "Specific penalty amounts/structure",
      "compliance_steps": "Key actions required",
      "citation_ids": ["cite_1"]
    }
  ],
  "financial_regs": [
    {
      "regulation_name": "Official name with code",
      "regulatory_body": "Governing authority",
      "applies_if": "Triggering conditions",
      "requirements": "Specific obligations",
      "licensing_needed": "Required licenses/registrations",
      "citation_ids": ["cite_1"]
    }
  ],
  "regional_variations": [
    {
      "region": "Specific jurisdiction",
      "unique_requirements": "Requirements specific to this region",
      "differences_from_baseline": "How this differs",
      "difficulty": "high|medium|low",
      "citation_ids": ["cite_1"]
    }
  ],
  "licensing_requirements": [
    {
      "license_type": "Type of license/certification",
      "issuing_authority": "Who grants this",
      "requirements": "How to obtain",
      "timeline": "Processing time",
      "cost_range": "Estimated costs",
      "renewal": "Renewal requirements",
      "citation_ids": ["cite_1"]
    }
  ],
  "citations": [
    {
      "id": "cite_1",
      "url": "https://...",
      "title": "Regulation/Law Name and Section",
      "source_organization": "Regulatory Body",
      "source_type": "government|legal_database|regulatory_body|law_firm|industry_association",
      "regulation_code": "Official code/section number",
      "date_enacted": "YYYY-MM-DD",
      "date_last_updated": "YYYY-MM-DD",
      "date_accessed": "YYYY-MM-DD",
      "excerpt": "Relevant legal text or compliance requirement",
      "jurisdiction": "Applicable jurisdiction(s)",
      "relevance": "How this citation supports the finding",
      "credibility_indicators": "Official status, authority basis"
    }
  ]
}"""

    previous_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}

PREVIOUS FINDINGS - SOLUTIONS:
{json.dumps(solutions_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{previous_context}

Given the problem and previous research, please analyze the legal and regulatory landscape.

RESEARCH REQUIREMENTS:
Use web_search to find authoritative legal and regulatory sources:
- Official government regulatory websites and databases
- Specific statutes, regulations, and legal codes (with section numbers)
- Regulatory body guidance documents and official interpretations
- Major law firm compliance analyses (to supplement official sources)
- Industry association compliance resources
- Recent regulatory changes and enforcement actions

Focus on:
- Exact regulatory requirements with official citations
- Specific jurisdictions and applicability criteria
- Concrete compliance steps with legal basis
- Documented penalties with legal references
- Timeline and cost estimates for compliance
- Regional regulatory variations

CRITICAL: Every regulatory requirement, penalty, and compliance obligation must be linked to an official legal source. Cite both the primary legal text AND any official guidance documents. Include regulation codes, section numbers, and dates. Do not describe legal requirements without official citations.

Today's date is {datetime.utcnow().strftime("%Y-%m-%d")} - use this for date_accessed in citations."""

    logger.info("Calling Claude API for legal analysis...")

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
        "industry_regulations": [],
        "data_protection": [],
        "financial_regs": [],
        "regional_variations": [],
        "licensing_requirements": [],
        "citations": [],
        "raw_response": text_content[:1000],
        "parse_error": "Could not parse structured JSON from response",
    }
