# Market Research Worker - Complete Flow Documentation

## Table of Contents
1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Complete Flow Diagram](#complete-flow-diagram)
4. [Step-by-Step Execution](#step-by-step-execution)
5. [Agent Details](#agent-details)
6. [Citation System](#citation-system)
7. [Context Accumulation Strategy](#context-accumulation-strategy)
8. [State Management](#state-management)
9. [Error Handling](#error-handling)
10. [Performance Characteristics](#performance-characteristics)
11. [Example Execution](#example-execution)

---

## Overview

The **Market Research Worker** is a sophisticated multi-agent orchestration system that conducts comprehensive market research by coordinating 5 specialized AI agents that run sequentially, each building upon the findings of previous agents.

**Purpose:** Transform a business problem into a comprehensive market research report with obstacles analysis, competitive landscape, legal requirements, and market opportunity quantification.

**Key Design Decision:** Sequential execution (not parallel) to enable context accumulation - later agents benefit from earlier findings.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                     POST /jobs                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator Lambda                    │
│  • Creates 3 jobs (slack, market_research, external)       │
│  • Sends messages to 3 SQS queues                           │
│  • Stores job metadata in DynamoDB                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQS: market_research                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              MARKET RESEARCH ORCHESTRATOR                   │
│              (market_research_worker.py)                    │
│                                                             │
│  Coordinates 5 Sequential Agents:                          │
│                                                             │
│  1. Obstacles Agent      → Identifies challenges           │
│  2. Solutions Agent      → Researches existing solutions   │
│  3. Legal Agent          → Analyzes regulations            │
│  4. Competitor Agent     → Maps competitive landscape      │
│  5. Market Agent         → Quantifies market opportunity   │
│                                                             │
│  Then: Synthesis Agent   → Creates executive summary       │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. USER SUBMITS JOB                                              │
│    POST /jobs { "problem": "..." }                               │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR CREATES JOBS                                     │
│    • job_id_1 (slack) → slack queue                              │
│    • job_id_2 (market_research) → market_research queue          │
│    • job_id_3 (external_research) → external_research queue      │
│    • Stores in DynamoDB: status="pending"                        │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. MARKET RESEARCH WORKER PICKS UP MESSAGE                       │
│    • Reads from SQS: {job_id, instructions}                      │
│    • Updates DynamoDB: status="processing"                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. AGENT 1: OBSTACLES                                            │
│    Input: problem_context                                        │
│    Process:                                                      │
│      • Updates DynamoDB: status="processing_obstacles"           │
│      • Invokes obstacles_agent Lambda                            │
│      • Agent calls Claude + web_search                           │
│      • Agent saves findings to DynamoDB                          │
│    Output: {technical, market, regulatory, user, financial,      │
│             critical_insights, sources}                          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. AGENT 2: SOLUTIONS                                            │
│    Input: problem_context + obstacles_findings                   │
│    Process:                                                      │
│      • Updates DynamoDB: status="processing_solutions"           │
│      • Invokes solutions_agent Lambda                            │
│      • Agent calls Claude + web_search + web_fetch               │
│      • Agent saves findings to DynamoDB                          │
│    Output: {manual_solutions, digital_solutions, workarounds,    │
│             gaps, sources}                                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. AGENT 3: LEGAL                                                │
│    Input: problem_context + obstacles + solutions               │
│    Process:                                                      │
│      • Updates DynamoDB: status="processing_legal"               │
│      • Invokes legal_agent Lambda                                │
│      • Agent calls Claude + web_search                           │
│      • Agent saves findings to DynamoDB                          │
│    Output: {industry_regulations, data_protection,               │
│             financial_regs, regional_variations, sources}        │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 7. AGENT 4: COMPETITOR                                           │
│    Input: problem_context + obstacles + solutions + legal       │
│    Process:                                                      │
│      • Updates DynamoDB: status="processing_competitors"         │
│      • Invokes competitor_agent Lambda                           │
│      • Agent calls Claude + web_search + web_fetch               │
│      • Agent saves findings to DynamoDB                          │
│    Output: {direct_competitors, indirect_competitors,            │
│             market_structure, barriers, white_space, sources}    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 8. AGENT 5: MARKET                                               │
│    Input: problem_context + ALL previous findings               │
│    Process:                                                      │
│      • Updates DynamoDB: status="processing_market"              │
│      • Invokes market_agent Lambda                               │
│      • Agent calls Claude + web_search                           │
│      • Agent saves findings to DynamoDB                          │
│    Output: {market_size, growth_trends, customer_segments,       │
│             pricing_benchmarks, sources}                         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 9. SYNTHESIS GENERATION                                          │
│    Input: All 5 agent findings                                   │
│    Process:                                                      │
│      • Orchestrator calls Claude (no tools)                      │
│      • Creates comprehensive executive summary                   │
│      • Temperature = 0.4 (slightly higher for prose)             │
│    Output: 800-1200 word executive summary (prose)               │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 10. FINAL RESULT STORAGE                                         │
│     • Updates DynamoDB: status="completed"                       │
│     • Stores complete result with all findings + synthesis       │
│     • Sets completed_at timestamp                                │
│     • Returns success to SQS (message deleted)                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Execution

### Phase 1: Job Submission & Queue

**File:** `orchestrator.py`

```python
# 1. User submits job
POST /jobs
{
  "problem": "I want to build a SaaS platform for small businesses"
}

# 2. Orchestrator creates 3 jobs
job_1 = create_job(type="slack", status="pending")
job_2 = create_job(type="market_research", status="pending")
job_3 = create_job(type="external_research", status="pending")

# 3. Sends to SQS queues
sqs.send_message(slack_queue, {job_id: job_1.id, instructions: problem})
sqs.send_message(market_research_queue, {job_id: job_2.id, instructions: problem})
sqs.send_message(external_research_queue, {job_id: job_3.id, instructions: problem})
```

### Phase 2: Market Research Orchestration

**File:** `market_research_worker.py`

```python
# 1. Receive SQS message
message = sqs.receive({job_id, instructions})

# 2. Update status
dynamodb.update(job_id, status="processing")

# 3. Execute agents sequentially
obstacles_findings = invoke_agent("obstacles_agent", {
    job_id: job_id,
    problem_context: instructions
})

solutions_findings = invoke_agent("solutions_agent", {
    job_id: job_id,
    problem_context: instructions,
    obstacles_findings: obstacles_findings
})

legal_findings = invoke_agent("legal_agent", {
    job_id: job_id,
    problem_context: instructions,
    obstacles_findings: obstacles_findings,
    solutions_findings: solutions_findings
})

competitor_findings = invoke_agent("competitor_agent", {
    job_id: job_id,
    problem_context: instructions,
    obstacles_findings: obstacles_findings,
    solutions_findings: solutions_findings,
    legal_findings: legal_findings
})

market_findings = invoke_agent("market_agent", {
    job_id: job_id,
    problem_context: instructions,
    obstacles_findings: obstacles_findings,
    solutions_findings: solutions_findings,
    legal_findings: legal_findings,
    competitor_findings: competitor_findings
})

# 4. Generate synthesis
synthesis = generate_synthesis(
    instructions,
    obstacles_findings,
    solutions_findings,
    legal_findings,
    competitor_findings,
    market_findings
)

# 5. Store final result
final_result = {
    problem_context: instructions,
    findings: {
        obstacles: obstacles_findings,
        solutions: solutions_findings,
        legal: legal_findings,
        competitors: competitor_findings,
        market: market_findings
    },
    synthesis: synthesis,
    completed_at: timestamp
}

dynamodb.update(job_id, status="completed", result=final_result)
```

---

## Agent Details

### 1. Obstacles Agent (`obstacles_agent.py`)

**Purpose:** Identify challenges and barriers to success

**Input:**
- `job_id`: Job identifier
- `problem_context`: The business problem description

**Process:**
1. Updates DynamoDB status to `"processing_obstacles"`
2. Constructs specialized system prompt for obstacle identification
3. Calls Claude Sonnet 4 with:
   - Model: `claude-sonnet-4-20250514`
   - Temperature: `0.3` (for consistency)
   - Max tokens: `4000`
   - Tools: `web_search`
4. Conducts web searches for:
   - Similar solutions that failed
   - Industry challenges
   - Regulatory obstacles
   - User adoption barriers
5. Parses JSON response
6. Saves findings to DynamoDB field: `obstacles_findings`

**Output Schema:**
```json
{
  "technical": ["obstacle 1", "obstacle 2", ...],
  "market": ["obstacle 1", "obstacle 2", ...],
  "regulatory": ["obstacle 1", "obstacle 2", ...],
  "user": ["obstacle 1", "obstacle 2", ...],
  "financial": ["obstacle 1", "obstacle 2", ...],
  "critical_insights": ["insight 1", "insight 2", ...],
  "sources": ["url 1", "url 2", ...]
}
```

**Execution Time:** ~45-90 seconds

---

### 2. Solutions Agent (`solutions_agent.py`)

**Purpose:** Research existing solutions and identify gaps

**Input:**
- `job_id`: Job identifier
- `problem_context`: The business problem
- `obstacles_findings`: Output from Obstacles Agent

**Process:**
1. Updates DynamoDB status to `"processing_solutions"`
2. Constructs prompt with obstacles context
3. Calls Claude Sonnet 4 with:
   - Tools: `web_search`, `web_fetch`
4. Researches:
   - Existing products/services
   - Manual workarounds
   - Digital solutions
   - Gaps in current offerings
5. Uses `web_fetch` to deeply analyze competitor websites
6. Saves findings to DynamoDB field: `solutions_findings`

**Output Schema:**
```json
{
  "manual_solutions": [
    {
      "name": "...",
      "description": "...",
      "effectiveness": "...",
      "limitations": "..."
    }
  ],
  "digital_solutions": [
    {
      "name": "...",
      "url": "...",
      "description": "...",
      "strengths": "...",
      "weaknesses": "..."
    }
  ],
  "workarounds": ["workaround 1", "workaround 2", ...],
  "gaps": ["gap 1", "gap 2", ...],
  "sources": ["url 1", "url 2", ...]
}
```

**Execution Time:** ~60-120 seconds (longer due to web_fetch)

---

### 3. Legal Agent (`legal_agent.py`)

**Purpose:** Analyze legal and regulatory landscape

**Input:**
- `job_id`: Job identifier
- `problem_context`: The business problem
- `obstacles_findings`: Output from Obstacles Agent
- `solutions_findings`: Output from Solutions Agent

**Process:**
1. Updates DynamoDB status to `"processing_legal"`
2. Uses previous findings to understand industry context
3. Calls Claude Sonnet 4 with:
   - Tools: `web_search`
4. Researches:
   - Industry-specific regulations
   - Data protection laws (GDPR, CCPA)
   - Financial regulations
   - Regional compliance requirements
5. Saves findings to DynamoDB field: `legal_findings`

**Output Schema:**
```json
{
  "industry_regulations": [
    {
      "regulation": "...",
      "jurisdiction": "...",
      "requirements": "...",
      "complexity": "high|medium|low"
    }
  ],
  "data_protection": [
    {
      "law": "...",
      "jurisdiction": "...",
      "key_requirements": "...",
      "penalties": "..."
    }
  ],
  "financial_regs": [
    {
      "regulation": "...",
      "applies_if": "...",
      "requirements": "..."
    }
  ],
  "regional_variations": [
    {
      "region": "...",
      "specific_requirements": "...",
      "difficulty": "..."
    }
  ],
  "sources": ["url 1", "url 2", ...]
}
```

**Execution Time:** ~45-90 seconds

---

### 4. Competitor Agent (`competitor_agent.py`)

**Purpose:** Map competitive landscape and identify opportunities

**Input:**
- `job_id`: Job identifier
- `problem_context`: The business problem
- `obstacles_findings`: Output from Obstacles Agent
- `solutions_findings`: Output from Solutions Agent
- `legal_findings`: Output from Legal Agent

**Process:**
1. Updates DynamoDB status to `"processing_competitors"`
2. Uses all previous context to understand market
3. Calls Claude Sonnet 4 with:
   - Tools: `web_search`, `web_fetch`
4. Researches:
   - Direct competitors
   - Indirect competitors and substitutes
   - Market structure
   - Barriers to entry
   - White space opportunities
5. Fetches competitor websites for detailed analysis
6. Saves findings to DynamoDB field: `competitor_findings`

**Output Schema:**
```json
{
  "direct_competitors": [
    {
      "name": "...",
      "url": "...",
      "description": "...",
      "strengths": ["..."],
      "weaknesses": ["..."],
      "market_position": "leader|challenger|niche",
      "funding": "..."
    }
  ],
  "indirect_competitors": [
    {
      "name": "...",
      "type": "substitute|alternative",
      "description": "...",
      "why_competitive": "..."
    }
  ],
  "market_structure": {
    "type": "monopolistic|oligopolistic|fragmented|emerging",
    "description": "...",
    "key_players": ["..."]
  },
  "barriers": [
    {
      "type": "brand|network|technology|regulatory|capital",
      "description": "...",
      "severity": "high|medium|low"
    }
  ],
  "white_space": ["opportunity 1", "opportunity 2", ...],
  "sources": ["url 1", "url 2", ...]
}
```

**Execution Time:** ~60-120 seconds

---

### 5. Market Agent (`market_agent.py`)

**Purpose:** Quantify market size and opportunity

**Input:**
- `job_id`: Job identifier
- `problem_context`: The business problem
- ALL previous findings (obstacles, solutions, legal, competitors)

**Process:**
1. Updates DynamoDB status to `"processing_market"`
2. Uses complete context to understand market dynamics
3. Calls Claude Sonnet 4 with:
   - Tools: `web_search`
4. Researches:
   - TAM/SAM/SOM (market sizing)
   - Growth rates and trends
   - Customer segments
   - Pricing benchmarks
5. Gathers quantitative data with sources
6. Saves findings to DynamoDB field: `market_findings`

**Output Schema:**
```json
{
  "market_size": {
    "tam": {
      "value": "...",
      "unit": "USD|users|...",
      "year": "...",
      "source": "..."
    },
    "sam": {
      "value": "...",
      "unit": "...",
      "year": "...",
      "methodology": "..."
    },
    "som": {
      "value": "...",
      "unit": "...",
      "year": "...",
      "assumptions": "..."
    }
  },
  "growth_trends": {
    "historical_cagr": "...",
    "projected_cagr": "...",
    "time_period": "...",
    "drivers": ["driver 1", "driver 2", ...],
    "headwinds": ["headwind 1", "headwind 2", ...]
  },
  "customer_segments": [
    {
      "segment": "...",
      "size": "...",
      "characteristics": "...",
      "needs": ["..."],
      "buying_behavior": "..."
    }
  ],
  "pricing_benchmarks": {
    "range": "...",
    "average": "...",
    "models": ["subscription", "one-time", "usage-based", ...],
    "examples": [
      {
        "product": "...",
        "price": "...",
        "model": "..."
      }
    ]
  },
  "sources": ["url 1", "url 2", ...]
}
```

**Execution Time:** ~60-90 seconds

---

### 6. Synthesis Agent (within orchestrator)

**Purpose:** Create executive summary of all research

**Input:** All 5 agent findings

**Process:**
1. Orchestrator (not a separate Lambda) calls Claude
2. Builds comprehensive prompt with all findings
3. Calls Claude Sonnet 4 with:
   - Temperature: `0.4` (higher for better prose)
   - Max tokens: `4000`
   - **No tools** (pure synthesis)
4. Generates 800-1200 word executive summary

**Output:** Markdown/prose executive summary covering:
1. Problem statement
2. Key obstacles
3. Existing solutions analysis
4. Legal/regulatory considerations
5. Competitive assessment
6. Market opportunity
7. Strategic recommendations

**Execution Time:** ~30-45 seconds

---

## Citation System

### Overview

All research findings are backed by **comprehensive, verifiable source citations** to provide credibility for multi-million dollar investment decisions. Every claim, data point, and assessment traces back to authoritative sources.

### Why Citations Matter

The market research system is designed to inform **institutional go/no-go decisions** on major projects. To ensure research integrity:

- **Credibility:** Every finding must be verifiable by third parties
- **Accountability:** Sources provide audit trail for due diligence
- **Trust:** Institutional investors require evidence-based analysis
- **Compliance:** Regulatory and financial claims need official sources

### Citation Structure

Each citation includes comprehensive metadata:

```json
{
  "id": "cite_1",
  "url": "https://...",
  "title": "Report/Article/Regulation Title",
  "source_organization": "Publishing Organization",
  "source_type": "government|academic|industry_report|major_publication|...",
  "date_published": "YYYY-MM-DD",
  "date_accessed": "YYYY-MM-DD",
  "author": "Author Name or null",
  "excerpt": "Relevant quote or data point",
  "relevance": "How this supports the finding",
  "credibility_indicators": "Why this source is trustworthy"
}
```

### Source Prioritization by Agent

#### Obstacles Agent
**Prioritizes:**
1. Government sources (.gov) - regulatory data, statistics
2. Academic research (.edu) - peer-reviewed studies
3. Industry reports - Gartner, McKinsey, Forrester, IDC
4. Major publications - WSJ, NYT, Bloomberg, Reuters
5. Company financial filings - 10-K, annual reports

**Avoids:** Blog posts, social media, Wikipedia, promotional content

#### Solutions Agent
**Prioritizes:**
1. Official product websites and documentation
2. Product review sites - G2, Capterra, TrustRadius
3. Industry analyst reports - Gartner Magic Quadrants, Forrester Wave
4. Major tech publications - TechCrunch, The Information
5. Company financial data - Crunchbase, PitchBook

**Avoids:** Unverified claims, promotional content without validation

#### Legal Agent
**Prioritizes:**
1. Government regulatory websites (.gov domains)
2. Official legal databases - regulations.gov, EUR-Lex
3. Regulatory body publications - SEC, FTC, FDA, FCC
4. Major law firm compliance guides
5. Official legal texts with section numbers

**Avoids:** Unofficial interpretations, outdated information, secondary sources without primary citation

#### Competitor Agent
**Prioritizes:**
1. Company financial data - Crunchbase, PitchBook, SEC filings
2. Industry analyst reports - Gartner, Forrester, IDC
3. Major business publications - Bloomberg, WSJ, Forbes
4. Market research firms - Statista, eMarketer, CB Insights
5. Company official websites and investor relations

**Avoids:** Speculation, outdated information, unverified claims

#### Market Agent
**Prioritizes:**
1. Market research firms - Gartner, Forrester, IDC, Statista
2. Industry associations - official trade statistics
3. Government data - Census Bureau, BLS, industry regulators
4. Financial research - Goldman Sachs, Morgan Stanley, McKinsey
5. Public company data - SEC filings, earnings transcripts

**Avoids:** Unsubstantiated estimates, outdated reports (>2 years), marketing materials

### Citation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Agent Execution                                             │
│ 1. Receives research task                                   │
│ 2. Conducts web_search/web_fetch                           │
│ 3. For EACH finding, creates citation object               │
│ 4. Links findings to citation_ids                          │
│ 5. Returns {findings with citation_ids, citations array}   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Synthesis Generation                                        │
│ 1. Collects all citations from 5 agents                    │
│ 2. Renumbers with prefixes (obs_, sol_, leg_, comp_, mkt_) │
│ 3. Creates master citations list                           │
│ 4. Claude writes synthesis using [cite_id] references      │
│ 5. Returns {executive_summary with inline citations,       │
│             citations array, metadata}                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Final Report Structure                                      │
│ {                                                           │
│   "instructions": "...",                                    │
│   "findings": {                                             │
│     "obstacles": {...with citations array},                │
│     "solutions": {...with citations array},                │
│     "legal": {...with citations array},                    │
│     "competitors": {...with citations array},              │
│     "market": {...with citations array}                    │
│   },                                                        │
│   "synthesis": {                                            │
│     "executive_summary": "...text with [cite_id]...",      │
│     "citations": [...master list...],                      │
│     "citation_count": 47,                                  │
│     "research_date": "2024-01-15"                          │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Citation Requirements

#### Every Finding Must Include:

**Quantitative Claims:**
- ✅ "Market valued at $2.5B in 2024 [mkt_1]"
- ❌ "Large market opportunity"

**Qualitative Assessments:**
- ✅ "Competitor X holds 34% market share [comp_3, comp_4]"
- ❌ "Competitor X is the market leader"

**Regulatory Requirements:**
- ✅ "GDPR Article 6 requires explicit consent [leg_2]"
- ❌ "GDPR requires consent"

**Product Information:**
- ✅ "Product Y raised $50M Series B in Dec 2023 [sol_5]"
- ❌ "Product Y is well-funded"

#### Multiple Citations:

Findings can reference multiple sources for validation:
```
"The SaaS market is projected to grow at 18% CAGR from 2024-2028
[mkt_1, mkt_2], driven primarily by cloud migration [mkt_3] and
remote work adoption [mkt_4]."
```

### Example Citation Output

```json
{
  "id": "mkt_1",
  "url": "https://www.gartner.com/en/newsroom/press-releases/2024-01-15-gartner-forecasts-worldwide-saas-revenue",
  "title": "Gartner Forecasts Worldwide SaaS Revenue to Reach $195 Billion in 2024",
  "source_organization": "Gartner, Inc.",
  "source_type": "market_research",
  "date_published": "2024-01-15",
  "date_accessed": "2024-01-20",
  "author": "Gartner Research",
  "excerpt": "The worldwide SaaS market is forecast to grow 18% in 2024 to reach $195 billion, up from $165 billion in 2023",
  "relevance": "Provides official market size and growth rate projection for SaaS market",
  "credibility_indicators": "Gartner is a leading IT research and advisory firm, widely cited in industry analyses. This is an official press release with specific quantified projections."
}
```

### Quality Assurance

#### Agent Prompts Enforce:
- Every claim must link to at least one citation
- Quantitative data requires primary source citation
- Multiple sources preferred for key claims
- Date recency checked (prefer <2 year old data)
- Official sources prioritized over secondary

#### Synthesis Validation:
- All citation IDs in text must exist in citations array
- Master citations list consolidates all agent citations
- No duplicate citations (unique by URL + title)
- Citation density: ~1 citation per 50-100 words of analysis

### Benefits

1. **Due Diligence Ready:** Every claim can be independently verified
2. **Regulatory Compliance:** Legal citations include official regulation codes
3. **Financial Validation:** Market sizes and growth rates have research backing
4. **Competitive Intelligence:** Competitor data sourced from financial filings
5. **Audit Trail:** Complete provenance of all research findings
6. **Credibility:** Institutional-grade research suitable for board presentations

---

## Context Accumulation Strategy

The sequential design enables each agent to build upon previous findings:

```
Agent 1: Obstacles
Context: problem_context
↓
Agent 2: Solutions
Context: problem_context + obstacles
         (knows what obstacles to address)
↓
Agent 3: Legal
Context: problem_context + obstacles + solutions
         (understands industry from previous agents)
↓
Agent 4: Competitors
Context: problem_context + obstacles + solutions + legal
         (knows what solutions exist and regulations)
↓
Agent 5: Market
Context: problem_context + ALL previous findings
         (full context for accurate market sizing)
↓
Synthesis
Context: ALL findings
         (creates coherent narrative)
```

**Benefits:**
- Solutions agent can reference specific obstacles
- Legal agent understands which regulations apply based on solutions
- Competitor agent knows what to look for based on obstacles/solutions
- Market agent has full picture for accurate sizing
- Synthesis creates cohesive story

**Trade-offs:**
- Slower execution (5-7 min vs 2-3 min parallel)
- Higher token usage (passing context)
- Single point of failure (sequential dependency)

---

## State Management

### DynamoDB Storage Strategy

**Jobs Table:**
```
Partition Key: id (job_id)

Fields:
- id: Job UUID
- status: Current status
- type: "market_research"
- instructions: Original problem
- created_at: Timestamp
- updated_at: Timestamp
- started_at: When orchestrator began
- completed_at: When finished
- obstacles_findings: JSON string (Agent 1)
- solutions_findings: JSON string (Agent 2)
- legal_findings: JSON string (Agent 3)
- competitor_findings: JSON string (Agent 4)
- market_findings: JSON string (Agent 5)
- result: Final result with synthesis (JSON string)
- error_message: Error details if failed
```

### Status Progression:

```
pending
  ↓
processing (orchestrator starts)
  ↓
processing_obstacles (Agent 1)
  ↓
processing_solutions (Agent 2)
  ↓
processing_legal (Agent 3)
  ↓
processing_competitors (Agent 4)
  ↓
processing_market (Agent 5)
  ↓
completed (or failed)
```

### State Persistence Points:

Each agent saves findings immediately after completion:
- **Enables progress tracking** - Frontend can poll and see which agents completed
- **Enables resume capability** - Could restart from last successful agent
- **Enables debugging** - Can inspect what each agent produced

---

## Error Handling

### Failure Modes & Recovery:

**1. Agent Lambda Failure:**
```python
try:
    result = invoke_agent(agent_name, payload)
except Exception as e:
    # Orchestrator catches error
    dynamodb.update(job_id, status="failed", error_message=str(e))
    # SQS message fails, will retry based on queue config
```

**2. JSON Parse Failure:**
```python
# Each agent has fallback parsing
try:
    return json.loads(response)
except JSONDecodeError:
    # Try markdown code block extraction
    # Try regex matching
    # Fall back to raw text
    return {"raw_response": text, "parse_error": "..."}
```

**3. Claude API Error:**
```python
# Boto3 automatic retries with exponential backoff
# If all retries fail, agent returns error
# Orchestrator marks job as failed
```

**4. DynamoDB Error:**
```python
# Boto3 automatic retries
# If save fails, agent still returns result
# Orchestrator attempts to save final result
```

### Partial Success Handling:

If Agent 3 fails:
- Agents 1 & 2 findings are already saved in DynamoDB
- Job status shows "failed_legal"
- Frontend can still see partial findings
- Could manually retry from Agent 3 in future enhancement

---

## Performance Characteristics

### Timing Breakdown:

```
Total Execution Time: 5-7 minutes

Breakdown:
- Queue pickup: ~1-2 seconds
- Obstacles Agent: 45-90 seconds
- Solutions Agent: 60-120 seconds (web_fetch is slower)
- Legal Agent: 45-90 seconds
- Competitor Agent: 60-120 seconds (web_fetch)
- Market Agent: 60-90 seconds
- Synthesis: 30-45 seconds
- DynamoDB updates: <1 second total
```

### Resource Usage:

**Per Agent:**
- Input tokens: 2,000-4,000
- Output tokens: 800-1,500
- Memory: 1GB
- Timeout: 15 minutes (typically uses 1-2 minutes)

**Full Research Run:**
- Total input tokens: 15,000-25,000
- Total output tokens: 6,000-10,000
- Cost: ~$0.08-$0.15 per research job
- Memory peak: ~1GB
- Network calls: 15-25 (web searches + fetches)

### Scalability:

**Concurrent Jobs:**
- Queue: Can handle many messages
- Orchestrator: 1 job at a time per worker instance
- Agents: Independent Lambdas, can run different jobs simultaneously
- Bottleneck: Claude API rate limits (50 req/min Tier 1)

**Horizontal Scaling:**
- Multiple market_research_worker instances can process different jobs
- Each orchestrator instance is stateless
- State is in DynamoDB (supports high concurrency)

---

## Example Execution

### Input:
```json
{
  "problem": "I want to build a SaaS platform that helps small restaurants manage their online orders from multiple delivery platforms (UberEats, DoorDash, etc.) in one dashboard."
}
```

### Agent 1 - Obstacles:
```json
{
  "technical": [
    "API integration complexity with multiple delivery platforms",
    "Real-time order synchronization challenges",
    "Different data formats from each platform"
  ],
  "market": [
    "Restaurants already locked into platform-specific tablets",
    "Low switching costs for existing solutions",
    "Market dominated by established POS providers"
  ],
  "regulatory": [
    "Food safety tracking requirements",
    "Payment processing compliance (PCI-DSS)",
    "Local health department integrations"
  ],
  "user": [
    "Restaurant staff resistant to new technology",
    "Limited time for training during busy hours",
    "Need for 24/7 reliability"
  ],
  "financial": [
    "Small restaurants have limited budgets ($50-200/mo)",
    "Requires significant upfront development investment",
    "Chicken-and-egg: need scale for platform partnerships"
  ],
  "critical_insights": [
    "Major pain point is managing 3-5 separate tablets during rush hours",
    "Existing solutions (ChowNow, Toast) are expensive ($300+/mo)"
  ],
  "sources": [...]
}
```

### Agent 2 - Solutions:
```json
{
  "digital_solutions": [
    {
      "name": "Toast",
      "url": "https://pos.toasttab.com",
      "description": "All-in-one POS with delivery aggregation",
      "strengths": ["Established brand", "Full POS integration"],
      "weaknesses": ["Expensive ($300+/mo)", "Heavy, requires hardware"]
    },
    {
      "name": "ChowNow",
      "url": "https://chownow.com",
      "description": "Direct ordering for restaurants",
      "strengths": ["Commission-free ordering"],
      "weaknesses": ["Doesn't integrate 3rd party platforms"]
    }
  ],
  "manual_solutions": [
    {
      "name": "Multiple tablets",
      "description": "Restaurant keeps separate tablet for each platform",
      "effectiveness": "Poor - error-prone, time consuming",
      "limitations": "Staff confusion, duplicate orders, missed orders"
    }
  ],
  "gaps": [
    "No affordable solution under $100/mo",
    "No solution focuses solely on aggregation without POS",
    "Limited analytics across platforms"
  ],
  "sources": [...]
}
```

### Agent 3 - Legal:
```json
{
  "industry_regulations": [
    {
      "regulation": "FDA Food Safety Modernization Act (FSMA)",
      "jurisdiction": "United States",
      "requirements": "Food tracking and traceability",
      "complexity": "medium"
    }
  ],
  "data_protection": [
    {
      "law": "GDPR",
      "jurisdiction": "EU",
      "key_requirements": "Customer data consent, right to deletion",
      "penalties": "Up to €20M or 4% of revenue"
    },
    {
      "law": "CCPA",
      "jurisdiction": "California",
      "key_requirements": "Privacy policy, data disclosure",
      "penalties": "$2,500-$7,500 per violation"
    }
  ],
  "financial_regs": [
    {
      "regulation": "PCI-DSS",
      "applies_if": "Processing credit cards",
      "requirements": "Secure payment processing, regular audits"
    }
  ],
  "sources": [...]
}
```

### Agent 4 - Competitors:
```json
{
  "direct_competitors": [
    {
      "name": "Ordermark",
      "url": "https://ordermark.com",
      "description": "Delivery aggregation platform",
      "market_position": "challenger",
      "strengths": ["Focused on aggregation", "Simple setup"],
      "weaknesses": ["Limited to 6 platforms", "$300/mo price point"],
      "funding": "$120M raised"
    }
  ],
  "market_structure": {
    "type": "fragmented",
    "description": "Mix of POS providers adding aggregation and aggregation specialists",
    "key_players": ["Toast", "Square", "Ordermark", "ChowNow"]
  },
  "barriers": [
    {
      "type": "network",
      "description": "API partnerships with delivery platforms",
      "severity": "high"
    },
    {
      "type": "technology",
      "description": "Real-time order management",
      "severity": "medium"
    }
  ],
  "white_space": [
    "Affordable option for single-location restaurants",
    "Mobile-first solution (no hardware)",
    "Analytics and insights focus"
  ],
  "sources": [...]
}
```

### Agent 5 - Market:
```json
{
  "market_size": {
    "tam": {
      "value": "800,000",
      "unit": "restaurants in US",
      "year": "2024",
      "source": "National Restaurant Association"
    },
    "sam": {
      "value": "200,000",
      "unit": "restaurants using 2+ delivery platforms",
      "methodology": "25% of restaurants * multiple platforms"
    },
    "som": {
      "value": "10,000",
      "unit": "restaurants in year 1",
      "assumptions": "5% market penetration in target segment"
    }
  },
  "growth_trends": {
    "historical_cagr": "15%",
    "projected_cagr": "12%",
    "time_period": "2020-2027",
    "drivers": [
      "Continued growth in food delivery",
      "Ghost kitchen proliferation",
      "Multi-platform ordering becoming standard"
    ]
  },
  "customer_segments": [
    {
      "segment": "Single-location restaurants",
      "size": "600,000 in US",
      "characteristics": "1-2 employees, $200-500K revenue",
      "needs": ["Simplicity", "Affordability", "Reliability"]
    }
  ],
  "pricing_benchmarks": {
    "average": "$250/month",
    "range": "$100-400/month",
    "models": ["subscription", "per-location"],
    "examples": [
      {"product": "Toast", "price": "$300/mo", "model": "subscription"},
      {"product": "Ordermark", "price": "$300/mo", "model": "per-location"}
    ]
  },
  "sources": [...]
}
```

### Final Synthesis:
```markdown
# Executive Summary: Restaurant Delivery Aggregation Platform

## Problem Statement
Small restaurants struggle to manage orders from multiple delivery platforms...

## Key Obstacles
The primary challenges include technical complexity of API integrations...

## Competitive Landscape
The market is currently fragmented between full POS providers...

## Market Opportunity
With 200,000 restaurants using multiple delivery platforms and an average...

## Strategic Recommendations
1. Focus on affordable pricing ($99/mo) to target underserved segment
2. Mobile-first approach to avoid hardware costs
3. Partner with one major platform first, expand incrementally
...
```

---

## Conclusion

The Market Research Worker represents a sophisticated approach to AI-powered market research, leveraging:

1. **Sequential Agent Design** - Each agent builds upon previous findings
2. **Specialized Expertise** - Each agent has focused research scope
3. **Real-time Web Research** - Claude's tools gather current information
4. **State Persistence** - Progress tracking and resume capability
5. **Comprehensive Output** - Structured data + executive synthesis

This architecture balances thoroughness with maintainability, enabling high-quality market research at scale.

---

**Last Updated:** 2025-11-22
**Version:** 1.0
