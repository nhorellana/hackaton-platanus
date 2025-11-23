"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  TrendingUp,
  AlertTriangle,
  Scale,
  Users,
  Globe,
  Lightbulb,
  FileText,
} from "lucide-react";

interface ResearchResultsProps {
  result: string; // JSON string from the job result
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function CollapsibleSection({
  title,
  icon,
  children,
  defaultOpen = false,
}: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-(--color-border) rounded-xl overflow-hidden bg-(--color-input-bg) transition-all hover:shadow-md">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-(--color-background) transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="text-(--color-primary)">{icon}</div>
          <h3 className="text-base font-semibold text-(--color-text)">
            {title}
          </h3>
        </div>
        {isOpen ? (
          <ChevronUp size={20} className="text-(--color-text-secondary)" />
        ) : (
          <ChevronDown size={20} className="text-(--color-text-secondary)" />
        )}
      </button>
      {isOpen && (
        <div className="px-6 pb-6 pt-2 border-t border-(--color-border)">
          {children}
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  unit?: string;
  trend?: string;
}

function StatCard({ label, value, unit, trend }: StatCardProps) {
  return (
    <div className="bg-(--color-background) rounded-lg p-3 border border-(--color-border)">
      <p className="text-xs text-(--color-text-secondary) mb-1">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-bold text-(--color-text)">{value}</span>
        {unit && (
          <span className="text-xs text-(--color-text-secondary)">{unit}</span>
        )}
      </div>
      {trend && (
        <p className="text-xs text-(--color-primary) mt-1 flex items-center gap-1">
          <TrendingUp size={12} />
          {trend}
        </p>
      )}
    </div>
  );
}

export default function ResearchResults({ result }: ResearchResultsProps) {
  // Parse the result JSON - handle nested structure from backend
  let findings: any = {};
  let instructions = "";
  let synthesis = "";

  try {
    // Parse the outer result
    const parsedResult = JSON.parse(result);

    // Extract the nested result field (which is also a JSON string)
    const data = parsedResult.result
      ? typeof parsedResult.result === "string"
        ? JSON.parse(parsedResult.result)
        : parsedResult.result
      : parsedResult;

    // Get findings - should be clean JSON objects from backend
    const rawFindings = data.findings || {};

    // Handle both old format (with raw_response) and new format (clean JSON)
    Object.keys(rawFindings).forEach((key) => {
      const agentData = rawFindings[key];

      // If it's the old format with raw_response, try to extract JSON
      if (
        agentData &&
        typeof agentData === "object" &&
        agentData.raw_response
      ) {
        const jsonMatch = agentData.raw_response.match(
          /```json\s*\n([\s\S]*?)\n```/
        );
        if (jsonMatch && jsonMatch[1]) {
          try {
            findings[key] = JSON.parse(jsonMatch[1]);
          } catch (e) {
            console.warn(`Failed to parse JSON for ${key}:`, e);
            findings[key] = {}; // Empty object as fallback
          }
        } else {
          findings[key] = {};
        }
      }
      // New format - should already be clean JSON
      else if (agentData && typeof agentData === "object") {
        findings[key] = agentData;
      } else {
        findings[key] = {};
      }
    });

    instructions = data.instructions || parsedResult.context_summary || "";
    synthesis = data.synthesis || "";

    // Use synthesis as fallback description
    if (!instructions && synthesis) {
      instructions = synthesis.substring(0, 500);
    }

    console.log("Loaded research data:", {
      hasObstacles: !!findings.obstacles,
      hasSolutions: !!findings.solutions,
      hasLegal: !!findings.legal,
      hasCompetitors: !!findings.competitors,
      hasMarket: !!findings.market,
      findingsKeys: Object.keys(findings),
      obstaclesKeys: findings.obstacles ? Object.keys(findings.obstacles) : [],
    });
  } catch (error) {
    console.error("Error parsing research result:", error);
    return (
      <div className="text-red-500 p-4 bg-(--color-background) rounded-lg border border-(--color-border)">
        <p className="font-semibold mb-2">
          Error al cargar los resultados de investigación
        </p>
        <p className="text-sm">{String(error)}</p>
      </div>
    );
  }

  // Extract key metrics from actual data
  const getKeyMetrics = () => {
    const obstacles = findings.obstacles || {};
    const solutions = findings.solutions || {};

    return {
      technicalObstacles: obstacles.technical?.length || 0,
      digitalSolutions: solutions.digital_solutions?.length || 0,
      marketGaps: solutions.gaps?.length || 0,
    };
  };

  const metrics = getKeyMetrics();

  return (
    <div className="space-y-6 mt-6">
      {/* Market Analysis */}
      {findings.market && (
        <CollapsibleSection
          title="Análisis de Mercado"
          icon={<Globe size={20} />}
          defaultOpen={true}
        >
          <div className="space-y-4">
            {/* Market Size */}
            {findings.market.market_size && (
              <div>
                <h4 className="text-sm font-semibold text-(--color-text) mb-3">
                  Tamaño del Mercado
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {findings.market.market_size.tam && (
                    <StatCard
                      label="TAM (Total Addressable Market)"
                      value={findings.market.market_size.tam.value}
                      unit={findings.market.market_size.tam.unit || "USD"}
                      trend={findings.market.market_size.tam.growth_rate}
                    />
                  )}
                  {findings.market.market_size.sam && (
                    <StatCard
                      label="SAM (Serviceable Available Market)"
                      value={findings.market.market_size.sam.value}
                      unit={findings.market.market_size.sam.unit || "USD"}
                    />
                  )}
                  {findings.market.market_size.som && (
                    <StatCard
                      label="SOM (Serviceable Obtainable Market)"
                      value={findings.market.market_size.som.value}
                      unit={findings.market.market_size.som.unit || "USD"}
                    />
                  )}
                </div>
              </div>
            )}

            {/* Critical Market Insights */}
            {findings.market.critical_insights &&
              findings.market.critical_insights.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-(--color-text) mb-2">
                    Insights Clave del Mercado
                  </h4>
                  <div className="space-y-1">
                    {findings.market.critical_insights
                      .slice(0, 5)
                      .map((insight: string, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2 border-l-2 border-(--color-primary)"
                        >
                          <span className="text-(--color-primary) mt-0.5">
                            📊
                          </span>
                          <span>{insight}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

            {/* Market Trends */}
            {findings.market.trends && findings.market.trends.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-(--color-text) mb-2">
                  Tendencias del Mercado
                </h4>
                <div className="space-y-1">
                  {findings.market.trends
                    .slice(0, 5)
                    .map((trend: string, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2"
                      >
                        <span className="text-green-600 mt-0.5">↗</span>
                        <span>{trend}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Geographic Distribution */}
            {findings.market.geographic_distribution && (
              <div className="bg-(--color-background) rounded-lg p-4 border border-(--color-border)">
                <h4 className="text-sm font-semibold text-(--color-text) mb-2">
                  Distribución Geográfica
                </h4>
                <div className="space-y-2">
                  {Object.entries(findings.market.geographic_distribution)
                    .slice(0, 5)
                    .map(([region, data]: [string, any], idx: number) => {
                      const percentage =
                        typeof data === "number" ? data : data.percentage || 0;
                      return (
                        <div
                          key={idx}
                          className="flex justify-between items-center"
                        >
                          <span className="text-sm text-(--color-text-secondary)">
                            {region}
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-24 bg-(--color-border) rounded-full overflow-hidden">
                              <div
                                className="h-full bg-(--color-primary)"
                                style={{ width: `${percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-(--color-text) w-10">
                              {percentage}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* Obstacles */}
      {findings.obstacles && (
        <CollapsibleSection
          title="Obstáculos y Desafíos"
          icon={<AlertTriangle size={20} />}
        >
          <div className="space-y-3">
            {/* Critical Insights */}
            {findings.obstacles.critical_insights &&
              findings.obstacles.critical_insights.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Insights Críticos
                  </h5>
                  {findings.obstacles.critical_insights.map(
                    (insight: string, idx: number) => (
                      <div
                        key={idx}
                        className="border-l-4 border-red-600 bg-(--color-background) p-3 rounded-lg mb-2"
                      >
                        <div className="flex items-start gap-2">
                          <AlertTriangle
                            size={16}
                            className="text-red-600 mt-0.5 flex-shrink-0"
                          />
                          <p className="text-xs text-(--color-text-secondary)">
                            {insight}
                          </p>
                        </div>
                      </div>
                    )
                  )}
                </div>
              )}

            {/* Technical Obstacles */}
            {findings.obstacles.technical &&
              findings.obstacles.technical.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Obstáculos Técnicos
                  </h5>
                  <div className="space-y-1">
                    {findings.obstacles.technical
                      .slice(0, 5)
                      .map((obstacle: string, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2"
                        >
                          <span className="text-(--color-primary) mt-0.5">
                            •
                          </span>
                          <span>{obstacle}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

            {/* Regulatory Obstacles */}
            {findings.obstacles.regulatory &&
              findings.obstacles.regulatory.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Obstáculos Regulatorios
                  </h5>
                  <div className="space-y-1">
                    {findings.obstacles.regulatory
                      .slice(0, 5)
                      .map((obstacle: string, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2"
                        >
                          <span className="text-orange-500 mt-0.5">•</span>
                          <span>{obstacle}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

            {/* Market Obstacles */}
            {findings.obstacles.market &&
              findings.obstacles.market.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Obstáculos de Mercado
                  </h5>
                  <div className="space-y-1">
                    {findings.obstacles.market
                      .slice(0, 5)
                      .map((obstacle: string, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2"
                        >
                          <span className="text-yellow-600 mt-0.5">•</span>
                          <span>{obstacle}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
          </div>
        </CollapsibleSection>
      )}

      {/* Competitors */}
      {findings.competitors && (
        <CollapsibleSection
          title="Panorama Competitivo"
          icon={<Users size={20} />}
        >
          <div className="space-y-3">
            {/* Direct Competitors */}
            {findings.competitors.direct_competitors &&
              findings.competitors.direct_competitors.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Competidores Directos
                  </h5>
                  {findings.competitors.direct_competitors
                    .slice(0, 5)
                    .map((competitor: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-(--color-background) rounded-lg p-3 border border-(--color-border) hover:border-(--color-primary) transition-colors mb-2"
                      >
                        <div className="flex items-start justify-between mb-1">
                          <div>
                            <h6 className="font-semibold text-(--color-text) text-sm">
                              {competitor.name}
                            </h6>
                            {competitor.market_position && (
                              <p className="text-xs text-(--color-text-secondary)">
                                {competitor.market_position}
                              </p>
                            )}
                          </div>
                          {competitor.url && (
                            <a
                              href={competitor.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-(--color-primary) hover:text-(--color-primary-hover) transition-colors"
                            >
                              <ExternalLink size={14} />
                            </a>
                          )}
                        </div>
                        {competitor.description && (
                          <p className="text-xs text-(--color-text-secondary) mb-2">
                            {competitor.description}
                          </p>
                        )}
                        {competitor.key_strengths && (
                          <p className="text-xs text-green-600 mb-1">
                            ✓ {competitor.key_strengths}
                          </p>
                        )}
                        {competitor.weaknesses && (
                          <p className="text-xs text-orange-500">
                            ⚠ {competitor.weaknesses}
                          </p>
                        )}
                      </div>
                    ))}
                </div>
              )}

            {/* Indirect Competitors */}
            {findings.competitors.indirect_competitors &&
              findings.competitors.indirect_competitors.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Competidores Indirectos
                  </h5>
                  {findings.competitors.indirect_competitors
                    .slice(0, 3)
                    .map((competitor: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-(--color-background) rounded-lg p-2 border border-(--color-border) mb-2"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h6 className="font-semibold text-(--color-text) text-xs">
                              {competitor.name || competitor}
                            </h6>
                            {competitor.description && (
                              <p className="text-xs text-(--color-text-secondary) mt-1">
                                {competitor.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
          </div>
        </CollapsibleSection>
      )}

      {/* Legal */}
      {findings.legal && (
        <CollapsibleSection
          title="Marco Legal y Regulatorio"
          icon={<Scale size={20} />}
        >
          <div className="space-y-3">
            {/* Industry Regulations */}
            {findings.legal.industry_regulations &&
              findings.legal.industry_regulations.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Regulaciones de la Industria
                  </h5>
                  {findings.legal.industry_regulations.map(
                    (regulation: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-(--color-background) rounded-lg p-3 border border-(--color-border) mb-2"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h6 className="font-semibold text-(--color-text) text-sm">
                              {regulation.regulation || regulation.name}
                            </h6>
                            {regulation.jurisdiction && (
                              <p className="text-xs text-(--color-text-secondary)">
                                📍 {regulation.jurisdiction}
                              </p>
                            )}
                          </div>
                          {regulation.complexity && (
                            <span
                              className={`px-2.5 py-1 text-xs rounded-lg font-semibold flex-shrink-0 ml-2 ${
                                regulation.complexity.toLowerCase() === "high"
                                  ? "bg-red-600 text-white"
                                  : regulation.complexity.toLowerCase() ===
                                    "medium"
                                  ? "bg-orange-600 text-white"
                                  : "bg-green-600 text-white"
                              }`}
                            >
                              {regulation.complexity}
                            </span>
                          )}
                        </div>
                        {regulation.requirements && (
                          <p className="text-xs text-(--color-text-secondary) mb-2">
                            {regulation.requirements}
                          </p>
                        )}
                        {regulation.timeline && (
                          <p className="text-xs text-blue-500">
                            ⏱️ {regulation.timeline}
                          </p>
                        )}
                      </div>
                    )
                  )}
                </div>
              )}

            {/* Financial Regulations */}
            {findings.legal.financial_regs &&
              findings.legal.financial_regs.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Regulaciones Financieras
                  </h5>
                  {findings.legal.financial_regs.map(
                    (regulation: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-(--color-background) rounded-lg p-3 border border-(--color-border) mb-2"
                      >
                        <h6 className="font-semibold text-(--color-text) text-sm mb-1">
                          {regulation.regulation}
                        </h6>
                        {regulation.jurisdiction && (
                          <p className="text-xs text-(--color-text-secondary) mb-1">
                            📍 {regulation.jurisdiction}
                          </p>
                        )}
                        {regulation.applies_if && (
                          <p className="text-xs text-(--color-text-secondary) italic">
                            Aplica si: {regulation.applies_if}
                          </p>
                        )}
                        {regulation.requirements && (
                          <p className="text-xs text-(--color-text-secondary) mt-2">
                            {regulation.requirements}
                          </p>
                        )}
                      </div>
                    )
                  )}
                </div>
              )}

            {/* Regional Variations */}
            {findings.legal.regional_variations &&
              findings.legal.regional_variations.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Variaciones Regionales
                  </h5>
                  <div className="space-y-2">
                    {findings.legal.regional_variations.map(
                      (region: any, idx: number) => (
                        <div
                          key={idx}
                          className="bg-(--color-background) rounded-lg p-3 border-l-4 border-(--color-primary)"
                        >
                          <h6 className="font-semibold text-(--color-text) text-sm mb-1">
                            {region.region}
                          </h6>
                          <p className="text-xs text-(--color-text-secondary)">
                            {region.key_difference ||
                              region.specific_requirements}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

            {/* Data Protection (if exists) */}
            {findings.legal.data_protection &&
              findings.legal.data_protection.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Protección de Datos
                  </h5>
                  {findings.legal.data_protection.map(
                    (law: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-(--color-background) rounded-lg p-3 border border-(--color-border) mb-2"
                      >
                        <h6 className="font-semibold text-(--color-text) text-sm">
                          {law.law || law.name}
                        </h6>
                        {law.jurisdiction && (
                          <p className="text-xs text-(--color-text-secondary)">
                            {law.jurisdiction}
                          </p>
                        )}
                        {law.key_requirements && (
                          <p className="text-xs text-(--color-text-secondary) mt-2">
                            {law.key_requirements}
                          </p>
                        )}
                        {law.penalties && (
                          <p className="text-xs text-red-500 font-medium mt-2">
                            ⚠️ {law.penalties}
                          </p>
                        )}
                      </div>
                    )
                  )}
                </div>
              )}
          </div>
        </CollapsibleSection>
      )}

      {/* Solutions */}
      {findings.solutions && (
        <CollapsibleSection
          title="Soluciones y Alternativas"
          icon={<FileText size={20} />}
        >
          <div className="space-y-4">
            {/* Digital Solutions */}
            {findings.solutions.digital_solutions &&
              findings.solutions.digital_solutions.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Soluciones Digitales (
                    {findings.solutions.digital_solutions.length})
                  </h5>
                  <div className="space-y-2">
                    {findings.solutions.digital_solutions
                      .slice(0, 5)
                      .map((solution: any, idx: number) => (
                        <div
                          key={idx}
                          className="bg-(--color-background) rounded-lg p-3 border border-(--color-border) hover:border-(--color-primary) transition-colors"
                        >
                          <div className="flex items-start justify-between mb-1">
                            <h6 className="text-sm font-semibold text-(--color-text)">
                              {solution.name}
                            </h6>
                            {solution.url && (
                              <a
                                href={solution.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-(--color-primary) hover:text-(--color-primary-hover) transition-colors"
                              >
                                <ExternalLink size={14} />
                              </a>
                            )}
                          </div>
                          <p className="text-xs text-(--color-text-secondary) mb-2">
                            {solution.description}
                          </p>
                          {solution.strengths && (
                            <p className="text-xs text-green-600 mb-1">
                              ✓ {solution.strengths}
                            </p>
                          )}
                          {solution.weaknesses && (
                            <p className="text-xs text-orange-500">
                              ⚠ {solution.weaknesses}
                            </p>
                          )}
                        </div>
                      ))}
                    {findings.solutions.digital_solutions.length > 5 && (
                      <p className="text-xs text-(--color-text-secondary) italic text-center">
                        +{findings.solutions.digital_solutions.length - 5}{" "}
                        soluciones más
                      </p>
                    )}
                  </div>
                </div>
              )}

            {/* Workarounds */}
            {findings.solutions.workarounds &&
              findings.solutions.workarounds.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Workarounds Comunes
                  </h5>
                  <div className="space-y-1">
                    {findings.solutions.workarounds
                      .slice(0, 5)
                      .map((workaround: string, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2"
                        >
                          <span className="text-(--color-primary) mt-0.5">
                            →
                          </span>
                          <span>{workaround}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

            {/* Market Gaps */}
            {findings.solutions.gaps && findings.solutions.gaps.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                  Brechas de Mercado ({findings.solutions.gaps.length})
                </h5>
                <div className="space-y-1">
                  {findings.solutions.gaps
                    .slice(0, 5)
                    .map((gap: string, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2 border-l-2 border-(--color-primary)"
                      >
                        <span className="text-(--color-primary) mt-0.5">
                          💡
                        </span>
                        <span>{gap}</span>
                      </div>
                    ))}
                  {findings.solutions.gaps.length > 5 && (
                    <p className="text-xs text-(--color-text-secondary) italic text-center mt-2">
                      +{findings.solutions.gaps.length - 5} brechas más
                      identificadas
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}
    </div>
  );
}
