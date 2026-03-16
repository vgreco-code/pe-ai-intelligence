import { Lightbulb, Rocket, Clock, TrendingUp } from 'lucide-react'
import type { PortfolioCompany } from '../App'

// ── AI Use Case Engine ──────────────────────────────────────────────────────
// Generates company-specific, vertical-aware AI use case recommendations
// based on the company's vertical, dimension scores, and tier.

interface UseCase {
  title: string
  description: string
  impact: 'High' | 'Medium' | 'Low'
  timeframe: string
  category: string
  requiredScore?: string  // which dimension enables this
}

// Vertical-specific use case libraries
const VERTICAL_USE_CASES: Record<string, UseCase[]> = {
  'Financial Services': [
    { title: 'AI-Powered Fraud Detection', description: 'Deploy real-time transaction monitoring with anomaly detection models to identify fraudulent patterns across payment flows and account activity.', impact: 'High', timeframe: '3-6 months', category: 'Risk & Compliance' },
    { title: 'Predictive Credit Risk Scoring', description: 'Build ML models that assess creditworthiness using alternative data signals beyond traditional FICO — behavioral patterns, cash flow trends, and market indicators.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Intelligent Document Processing', description: 'Automate extraction and classification of financial documents (statements, invoices, tax forms) using OCR + NLP pipelines to reduce manual data entry by 80%+.', impact: 'Medium', timeframe: '2-4 months', category: 'Operations' },
    { title: 'Conversational AI for Client Services', description: 'Deploy LLM-powered assistants for common client inquiries — account status, transaction disputes, product recommendations — reducing support ticket volume by 40%.', impact: 'Medium', timeframe: '3-5 months', category: 'Customer Experience' },
    { title: 'Automated Regulatory Reporting', description: 'Use AI to auto-generate compliance reports (SOX, AML, KYC) from transaction data, reducing reporting cycle from weeks to hours.', impact: 'High', timeframe: '6-12 months', category: 'Risk & Compliance' },
    { title: 'Portfolio Optimization Engine', description: 'ML-driven asset allocation and rebalancing recommendations based on market signals, risk tolerance, and macroeconomic indicators.', impact: 'High', timeframe: '9-12 months', category: 'Core Product' },
  ],
  'Healthcare/Life Sciences': [
    { title: 'Clinical Decision Support', description: 'AI models that surface relevant clinical guidelines, drug interactions, and treatment recommendations at the point of care — integrated directly into EHR workflows.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Predictive Patient Risk Stratification', description: 'Identify high-risk patients for readmission, chronic disease progression, or adverse events using longitudinal health data and ML risk models.', impact: 'High', timeframe: '6-12 months', category: 'Core Product' },
    { title: 'Medical Coding Automation', description: 'NLP-powered extraction of diagnosis and procedure codes from clinical notes, reducing coding backlogs and improving revenue cycle accuracy.', impact: 'Medium', timeframe: '3-6 months', category: 'Operations' },
    { title: 'AI-Driven Population Health Analytics', description: 'Aggregate and analyze patient population data to identify disease trends, care gaps, and intervention opportunities across provider networks.', impact: 'High', timeframe: '6-9 months', category: 'Analytics' },
    { title: 'Intelligent Prior Authorization', description: 'Automate prior authorization workflows using NLP to match clinical documentation against payer criteria, reducing denial rates and processing time.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
    { title: 'HIPAA-Compliant AI Assistant', description: 'Deploy an LLM-based assistant for clinicians that can summarize patient histories, draft referral letters, and answer clinical questions within a compliant framework.', impact: 'Medium', timeframe: '3-6 months', category: 'Customer Experience' },
  ],
  'Enterprise Software': [
    { title: 'AI Copilot for End Users', description: 'Embed an LLM-powered assistant directly into the product UI that helps users navigate features, build reports, and automate repetitive workflows using natural language.', impact: 'High', timeframe: '3-6 months', category: 'Core Product' },
    { title: 'Predictive Churn Prevention', description: 'ML models that analyze product usage patterns, support ticket sentiment, and engagement metrics to identify at-risk accounts 60-90 days before churn.', impact: 'High', timeframe: '4-6 months', category: 'Revenue' },
    { title: 'Intelligent Search & Discovery', description: 'Replace keyword search with semantic search powered by embeddings — users find what they need in natural language, improving activation and feature adoption.', impact: 'Medium', timeframe: '2-4 months', category: 'Core Product' },
    { title: 'Automated Data Quality Monitoring', description: 'Deploy anomaly detection on incoming data feeds to flag quality issues, duplicates, and schema drift in real time before they impact downstream analytics.', impact: 'Medium', timeframe: '3-5 months', category: 'Data Infrastructure' },
    { title: 'AI-Generated Insights & Reporting', description: 'Auto-generate executive summaries, trend analyses, and anomaly alerts from platform data — delivering proactive intelligence instead of passive dashboards.', impact: 'High', timeframe: '4-8 months', category: 'Core Product' },
    { title: 'Smart Workflow Automation', description: 'Use AI to learn common user workflows and suggest (or auto-execute) routine sequences — approvals, data entry, status updates — reducing manual clicks by 60%.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
  ],
  'E-commerce/Retail': [
    { title: 'AI-Powered Product Recommendations', description: 'Deploy collaborative filtering and deep learning models to personalize product recommendations in real time, increasing average order value by 15-25%.', impact: 'High', timeframe: '3-6 months', category: 'Revenue' },
    { title: 'Dynamic Pricing Engine', description: 'ML models that optimize pricing based on demand signals, competitor pricing, inventory levels, and customer segments — maximizing margin per transaction.', impact: 'High', timeframe: '6-9 months', category: 'Revenue' },
    { title: 'Visual Search & Discovery', description: 'Enable customers to search by image — snap a photo and find matching or similar products using computer vision and embedding similarity.', impact: 'Medium', timeframe: '4-6 months', category: 'Core Product' },
    { title: 'Demand Forecasting & Inventory Optimization', description: 'Predict demand at the SKU level using time-series models, reducing stockouts by 30% and overstock carrying costs by 20%.', impact: 'High', timeframe: '4-8 months', category: 'Operations' },
    { title: 'AI Customer Service Agent', description: 'LLM-powered chatbot that handles order inquiries, returns, and product questions — resolving 60% of tickets without human intervention.', impact: 'Medium', timeframe: '2-4 months', category: 'Customer Experience' },
    { title: 'Automated Content Generation', description: 'Generate product descriptions, marketing copy, and SEO metadata at scale using fine-tuned language models — reducing content creation costs by 70%.', impact: 'Medium', timeframe: '2-3 months', category: 'Operations' },
  ],
}

// Fallback for unknown verticals
const GENERIC_USE_CASES: UseCase[] = [
  { title: 'AI-Powered Process Automation', description: 'Identify and automate high-volume, rule-based workflows using AI agents — reducing manual effort and error rates across operations.', impact: 'High', timeframe: '3-6 months', category: 'Operations' },
  { title: 'Intelligent Document Processing', description: 'Deploy NLP pipelines to extract, classify, and route unstructured documents — contracts, emails, forms — into structured data feeds.', impact: 'Medium', timeframe: '2-4 months', category: 'Operations' },
  { title: 'Predictive Analytics Dashboard', description: 'Build ML-powered forecasting models for key business metrics — revenue, demand, resource utilization — surfaced through executive dashboards.', impact: 'High', timeframe: '4-8 months', category: 'Analytics' },
  { title: 'LLM-Powered Customer Assistant', description: 'Deploy a conversational AI agent that handles FAQs, troubleshooting, and product guidance — reducing support costs by 40%.', impact: 'Medium', timeframe: '2-4 months', category: 'Customer Experience' },
  { title: 'AI Copilot for Internal Teams', description: 'Embed an AI assistant into internal tools that helps employees search knowledge bases, generate reports, and automate routine tasks.', impact: 'Medium', timeframe: '3-5 months', category: 'Core Product' },
  { title: 'Anomaly Detection & Monitoring', description: 'Deploy real-time anomaly detection on operational metrics to catch issues early — system performance, data quality, security events.', impact: 'Medium', timeframe: '3-6 months', category: 'Data Infrastructure' },
]

function selectUseCases(company: PortfolioCompany): UseCase[] {
  const ps = company.pillar_scores
  const verticalKey = Object.keys(VERTICAL_USE_CASES).find(v =>
    company.vertical.toLowerCase().includes(v.toLowerCase()) ||
    v.toLowerCase().includes(company.vertical.toLowerCase())
  )
  const pool = verticalKey ? VERTICAL_USE_CASES[verticalKey] : GENERIC_USE_CASES

  // Score each use case by relevance to this company's profile
  const scored = pool.map(uc => {
    let relevance = 0

    // High-impact cases get a boost
    if (uc.impact === 'High') relevance += 2

    // If the company has strong data foundations, prioritize data-heavy use cases
    const dataAvg = ((ps.data_quality || 0) + (ps.data_integration || 0) + (ps.analytics_maturity || 0)) / 3
    if (dataAvg >= 2.5 && (uc.category === 'Analytics' || uc.category === 'Core Product')) relevance += 2

    // If weak on data, prioritize operations/quick-wins
    if (dataAvg < 2.5 && (uc.category === 'Operations' || uc.category === 'Customer Experience')) relevance += 2

    // If strong AI capabilities, go for advanced use cases
    if ((ps.ai_product_features || 0) >= 3.0 && uc.category === 'Core Product') relevance += 1
    if ((ps.ai_engineering || 0) >= 2.5 && uc.impact === 'High') relevance += 1

    // If strong revenue upside potential
    if ((ps.revenue_ai_upside || 0) >= 3.0 && uc.category === 'Revenue') relevance += 2

    // Quick wins for emerging/limited companies
    if (company.tier === 'AI-Emerging' || company.tier === 'AI-Limited') {
      if (uc.timeframe.includes('2-') || uc.timeframe.includes('3-')) relevance += 1
    }

    return { ...uc, relevance }
  })

  // Sort by relevance, take top 4
  scored.sort((a, b) => b.relevance - a.relevance)
  return scored.slice(0, 4)
}

const IMPACT_COLORS: Record<string, string> = {
  High: '#02C39A',
  Medium: '#F5A623',
  Low: '#94a3b8',
}

const CATEGORY_ICONS: Record<string, string> = {
  'Core Product': '🎯',
  'Revenue': '💰',
  'Operations': '⚙️',
  'Analytics': '📊',
  'Customer Experience': '💬',
  'Risk & Compliance': '🛡️',
  'Data Infrastructure': '🗄️',
}

interface Props {
  company: PortfolioCompany
}

export default function AIUseCases({ company }: Props) {
  const useCases = selectUseCases(company)

  return (
    <div className="glass-card rounded-xl border border-cyan-500/20 p-6">
      <h2 className="text-lg font-bold text-[var(--text-primary)] mb-2 flex items-center gap-2">
        <Rocket className="w-5 h-5 text-cyan-400" />
        AI Use Case Recommendations
      </h2>
      <p className="text-xs text-[var(--text-muted)] mb-5">
        Tailored to {company.name}'s {company.vertical} vertical and current AI maturity profile
      </p>

      <div className="grid grid-cols-2 gap-4">
        {useCases.map((uc, i) => (
          <div
            key={i}
            className="relative bg-slate-800/40 rounded-xl p-5 border border-slate-700/40 hover:border-cyan-500/30 transition-all group"
          >
            {/* Priority number */}
            <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-cyan-500/10 flex items-center justify-center">
              <span className="text-xs font-bold text-cyan-400">{i + 1}</span>
            </div>

            {/* Category badge */}
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm">{CATEGORY_ICONS[uc.category] || '🔹'}</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                {uc.category}
              </span>
            </div>

            {/* Title */}
            <h3 className="text-sm font-bold text-[var(--text-primary)] mb-2 pr-8 leading-snug">
              {uc.title}
            </h3>

            {/* Description */}
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-4">
              {uc.description}
            </p>

            {/* Meta row */}
            <div className="flex items-center gap-3 text-[10px]">
              <div className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" style={{ color: IMPACT_COLORS[uc.impact] }} />
                <span className="font-semibold" style={{ color: IMPACT_COLORS[uc.impact] }}>
                  {uc.impact} Impact
                </span>
              </div>
              <div className="flex items-center gap-1 text-[var(--text-muted)]">
                <Clock className="w-3 h-3" />
                <span>{uc.timeframe}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Investment summary */}
      <div className="mt-5 bg-cyan-500/5 rounded-lg p-4 border border-cyan-500/10">
        <div className="flex items-start gap-3">
          <Lightbulb className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
            <span className="font-semibold text-cyan-400">Investment Priority: </span>
            {company.tier === 'AI-Ready' || company.tier === 'AI-Buildable'
              ? `${company.name} has the infrastructure to pursue advanced AI use cases immediately. Focus on high-impact, revenue-generating capabilities first — the data and engineering foundations are already in place.`
              : `${company.name} should start with quick-win operational AI — document processing, automated workflows, and customer-facing assistants — while building the data infrastructure needed for more advanced ML use cases.`
            }
          </div>
        </div>
      </div>
    </div>
  )
}
