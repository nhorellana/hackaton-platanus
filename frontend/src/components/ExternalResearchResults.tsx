"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  User,
  Briefcase,
  GraduationCap,
  Search,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Mail,
  Linkedin,
  Globe,
} from "lucide-react";

interface ExternalResearchResultsProps {
  result: string; // JSON string from the job result
}

interface Expert {
  name: string;
  title?: string;
  company?: string;
  expertise?: string;
  linkedin_url?: string;
  email?: string;
  phone?: string;
  relevance_score?: number;
  recommended_approach?: string;
  why_relevant?: string;
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

export default function ExternalResearchResults({
  result,
}: ExternalResearchResultsProps) {
  let data: any = {};

  try {
    // Parse the result JSON
    const parsedResult = JSON.parse(result);

    // Extract the nested result if it exists
    data =
      parsedResult.result && typeof parsedResult.result === "string"
        ? JSON.parse(parsedResult.result)
        : parsedResult.result || parsedResult;

    console.log("Loaded external research data:", {
      hasExperts: !!data.found_experts,
      expertCount: data.found_experts?.length || 0,
      hasProfile: !!data.expert_profile_needed,
      hasSearchStrategy: !!data.search_strategy,
    });
  } catch (error) {
    console.error("Error parsing external research result:", error);
    return (
      <div className="text-red-500 p-4 bg-(--color-background) rounded-lg border border-(--color-border)">
        <p className="font-semibold mb-2">
          Error al cargar los resultados de búsqueda externa
        </p>
        <p className="text-sm">{String(error)}</p>
      </div>
    );
  }

  const experts: Expert[] = data.found_experts || [];
  const recommendations = data.recommendations || [];
  const expertProfile = data.expert_profile_needed || "";
  const searchStrategy = data.search_strategy || {};
  const searchSummary = data.search_summary || "";
  const questionsForExperts = data.questions_for_experts || [];

  // Extract metrics from search summary
  const totalExperts = experts.length;
  const recommendedExperts = experts.filter(
    (e) => (e.relevance_score || 0) >= 7
  ).length;

  return (
    <div className="space-y-6 mt-6">
      {/* Expert Profile Needed */}
      {expertProfile && (
        <CollapsibleSection
          title="Perfil del Experto Necesario"
          icon={<GraduationCap size={20} />}
          defaultOpen={true}
        >
          <div className="bg-(--color-background) rounded-lg p-4 border border-(--color-border)">
            <div className="flex items-start gap-3">
              <User
                size={20}
                className="text-(--color-primary) mt-1 flex-shrink-0"
              />
              <p className="text-sm text-(--color-text-secondary) leading-relaxed">
                {expertProfile}
              </p>
            </div>
          </div>
        </CollapsibleSection>
      )}

      {/* Search Strategy */}
      {searchStrategy && Object.keys(searchStrategy).length > 0 && (
        <CollapsibleSection
          title="Estrategia de Búsqueda"
          icon={<Search size={20} />}
        >
          <div className="space-y-3">
            {searchStrategy.professional_keywords &&
              searchStrategy.professional_keywords.filter(
                (k: string) => k && k.trim().length > 0
              ).length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Palabras Clave Profesionales
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {searchStrategy.professional_keywords
                      .filter(
                        (keyword: string) =>
                          keyword && keyword.trim().length > 0
                      )
                      .map((keyword: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-3 py-1.5 bg-(--color-primary) text-white rounded-lg text-xs font-medium shadow-sm"
                        >
                          {keyword}
                        </span>
                      ))}
                  </div>
                </div>
              )}

            {searchStrategy.target_roles &&
              searchStrategy.target_roles.filter(
                (r: string) => r && r.trim().length > 0
              ).length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Roles Objetivo
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {searchStrategy.target_roles
                      .filter((role: string) => role && role.trim().length > 0)
                      .map((role: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium shadow-sm flex items-center gap-1 w-fit"
                        >
                          <Briefcase size={12} />
                          {role}
                        </span>
                      ))}
                  </div>
                </div>
              )}

            {searchStrategy.target_industries &&
              searchStrategy.target_industries.filter(
                (i: string) => i && i.trim().length > 0
              ).length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-(--color-text) mb-2 uppercase tracking-wider">
                    Industrias Objetivo
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {searchStrategy.target_industries
                      .filter(
                        (industry: string) =>
                          industry && industry.trim().length > 0
                      )
                      .map((industry: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium shadow-sm"
                        >
                          {industry}
                        </span>
                      ))}
                  </div>
                </div>
              )}
          </div>
        </CollapsibleSection>
      )}

      {/* Questions for Experts */}
      {questionsForExperts.length > 0 && (
        <CollapsibleSection
          title={`Preguntas Sugeridas para Expertos (${questionsForExperts.length})`}
          icon={<CheckCircle2 size={20} />}
        >
          <div className="space-y-2">
            {questionsForExperts.map((question: string, idx: number) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-(--color-background) rounded-lg border border-(--color-border)"
              >
                <span className="text-(--color-primary) font-bold text-sm flex-shrink-0 mt-0.5">
                  {idx + 1}.
                </span>
                <p className="text-sm text-(--color-text-secondary)">
                  {question}
                </p>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Found Experts */}
      {experts.length > 0 && (
        <CollapsibleSection
          title={`Expertos Identificados (${experts.length})`}
          icon={<User size={20} />}
          defaultOpen={true}
        >
          <div className="space-y-3">
            {experts.map((expert, idx) => (
              <div
                key={idx}
                className="bg-(--color-background) rounded-lg p-4 border border-(--color-border) hover:border-(--color-primary) transition-all"
              >
                {/* Expert Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="text-base font-semibold text-(--color-text) mb-1">
                      {expert.name}
                    </h4>
                    {expert.title && (
                      <p className="text-sm text-(--color-text-secondary) mb-0.5">
                        {expert.title}
                      </p>
                    )}
                    {expert.company && (
                      <p className="text-xs text-(--color-text-secondary) flex items-center gap-1">
                        <Briefcase size={12} />
                        {expert.company}
                      </p>
                    )}
                  </div>
                  {expert.relevance_score && (
                    <div className="flex-shrink-0">
                      <div
                        className={`px-3 py-1 rounded-full text-xs font-bold ${
                          expert.relevance_score >= 8
                            ? "bg-green-500 bg-opacity-20 text-green-500"
                            : expert.relevance_score >= 6
                            ? "bg-blue-500 bg-opacity-20 text-blue-500"
                            : "bg-yellow-500 bg-opacity-20 text-yellow-600"
                        }`}
                      >
                        {expert.relevance_score}/10
                      </div>
                    </div>
                  )}
                </div>

                {/* Expertise */}
                {expert.expertise && (
                  <div className="mb-3 p-3 bg-(--color-input-bg) rounded-lg border-l-4 border-(--color-primary)">
                    <p className="text-xs text-(--color-text-secondary)">
                      {expert.expertise}
                    </p>
                  </div>
                )}

                {/* Why Relevant */}
                {expert.why_relevant && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-(--color-text) mb-1">
                      ¿Por qué es relevante?
                    </p>
                    <p className="text-xs text-(--color-text-secondary)">
                      {expert.why_relevant}
                    </p>
                  </div>
                )}

                {/* Contact Information */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {expert.linkedin_url && (
                    <a
                      href={expert.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 bg-opacity-10 text-blue-600 rounded hover:bg-opacity-20 transition-colors"
                    >
                      <Linkedin size={12} />
                      LinkedIn
                    </a>
                  )}
                  {expert.email && (
                    <a
                      href={`mailto:${expert.email}`}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-(--color-primary) bg-opacity-10 text-(--color-primary) rounded hover:bg-opacity-20 transition-colors"
                    >
                      <Mail size={12} />
                      {expert.email}
                    </a>
                  )}
                  {expert.phone && (
                    <span className="flex items-center gap-1 px-2 py-1 text-xs bg-(--color-text-secondary) bg-opacity-10 text-(--color-text-secondary) rounded">
                      📞 {expert.phone}
                    </span>
                  )}
                </div>

                {/* Recommended Approach */}
                {expert.recommended_approach && (
                  <div className="pt-3 border-t border-(--color-border)">
                    <p className="text-xs font-semibold text-(--color-text) mb-1 flex items-center gap-1">
                      <CheckCircle2
                        size={12}
                        className="text-(--color-primary)"
                      />
                      Enfoque Recomendado
                    </p>
                    <p className="text-xs text-(--color-text-secondary) italic">
                      {expert.recommended_approach}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <CollapsibleSection
          title={`Recomendaciones (${recommendations.length})`}
          icon={<CheckCircle2 size={20} />}
        >
          <div className="space-y-2">
            {recommendations.map((rec: string, idx: number) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-(--color-background) rounded-lg border border-(--color-border)"
              >
                <CheckCircle2
                  size={16}
                  className="text-(--color-primary) mt-0.5 flex-shrink-0"
                />
                <p className="text-sm text-(--color-text-secondary)">{rec}</p>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Next Steps - Show when no experts found */}
      {experts.length === 0 && (
        <div className="bg-(--color-input-bg) rounded-xl p-6 border border-(--color-border)">
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h3 className="text-base font-semibold text-(--color-text) mb-2">
                Próximos Pasos
              </h3>
              <p className="text-sm text-(--color-text-secondary) mb-3">
                Se ha identificado el perfil de experto ideal para tu problema.
                Puedes buscar expertos con estas características en:
              </p>
              <ul className="space-y-2 text-sm text-(--color-text-secondary)">
                <li className="flex items-start gap-2">
                  <Linkedin
                    size={16}
                    className="text-blue-600 mt-0.5 flex-shrink-0"
                  />
                  <span>LinkedIn Professional Network</span>
                </li>
                <li className="flex items-start gap-2">
                  <GraduationCap
                    size={16}
                    className="text-(--color-primary) mt-0.5 flex-shrink-0"
                  />
                  <span>Academic Research Networks</span>
                </li>
                <li className="flex items-start gap-2">
                  <Globe
                    size={16}
                    className="text-green-600 mt-0.5 flex-shrink-0"
                  />
                  <span>Industry Professional Networks</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Generated timestamp */}
      {data.generated_at && (
        <div className="text-center">
          <p className="text-xs text-(--color-text-secondary)">
            Búsqueda realizada el{" "}
            {new Date(data.generated_at).toLocaleString("es-ES", {
              dateStyle: "long",
              timeStyle: "short",
            })}
          </p>
        </div>
      )}
    </div>
  );
}
