import { Lightbulb, Rocket, Clock, TrendingUp } from 'lucide-react'
import type { PortfolioCompany } from '../App'

interface UseCase {
  title: string
  description: string
  impact: 'High' | 'Medium' | 'Low'
  timeframe: string
  category: string
}

// ── Company-Specific AI Use Cases ─────────────────────────────────────────
// Tailored recommendations based on each company's actual product, vertical,
// data assets, and current AI maturity. Researched against primary sources.

const COMPANY_USE_CASES: Record<string, UseCase[]> = {
  "Dash": [
    { title: 'Intelligent Invoice Data Extraction', description: 'Upgrade AP Robot\'s OCR-based capture with ML-powered intelligent document processing — handling non-standard invoice layouts, handwritten POs, and multi-page documents without manual template configuration.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'AP Fraud & Anomaly Detection', description: 'Deploy ML models on 25 years of invoice processing data to detect duplicate payments, vendor fraud patterns, and anomalous amounts before approval — a natural extension of AP Robot\'s 3-way matching.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'AI-Powered Document Search & Retrieval', description: 'Add semantic search to DDX document management — users describe what they need in natural language instead of searching by metadata tags. Leverages the document archive built over 20+ years of customer data.', impact: 'Medium', timeframe: '3-6 months', category: 'Core Product' },
    { title: 'Predictive Cash Flow from AP Data', description: 'Use invoice and payment history data to build ML models predicting cash flow timing, vendor payment optimization, and early payment discount opportunities for manufacturing clients.', impact: 'Medium', timeframe: '9-12 months', category: 'Revenue' },
  ],
  "Track Star": [
    { title: 'AI-Powered Driver Behavior Scoring', description: 'Build on existing video telematics to create real-time driver safety scores using computer vision — harsh braking, distracted driving, following distance — with fleet-wide benchmarking and risk prediction.', impact: 'High', timeframe: '4-6 months', category: 'Core Product' },
    { title: 'Predictive Maintenance from GPS + ThingTech IoT', description: 'Combine Track Star\'s GPS telemetry with ThingTech\'s IoT sensor data to predict vehicle maintenance needs — engine hours, mileage patterns, sensor anomalies — reducing fleet downtime by 25-30%.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'AI Route Optimization for Municipal Fleets', description: 'Deploy ML-based route optimization using historical GPS data and real-time traffic — purpose-built for government fleet patterns (police patrols, utility crews, school bus routes).', impact: 'Medium', timeframe: '6-9 months', category: 'Revenue' },
    { title: 'Esri ArcGIS AI Analytics Layer', description: 'Build an AI analytics overlay on the rebuilt Esri ArcGIS platform — geospatial anomaly detection, automated dispatch recommendations, and predictive asset positioning.', impact: 'Medium', timeframe: '9-12 months', category: 'Core Product' },
  ],
  "NexTalk": [
    { title: 'Real-Time ASR Accuracy Enhancement', description: 'Fine-tune SpeechPath ASR models on domain-specific vocabularies (medical, legal, financial) to improve word error rates for specialized professional conversations.', impact: 'High', timeframe: '3-6 months', category: 'Core Product' },
    { title: 'AI-Powered Caption Quality Scoring', description: 'Deploy ML models that automatically score caption accuracy in real-time, flagging segments where human CA intervention is needed — improving the hybrid ASR+human workflow efficiency.', impact: 'High', timeframe: '4-6 months', category: 'Operations' },
    { title: 'Multilingual Expansion via Transfer Learning', description: 'Extend SpeechPath beyond English using transfer learning from the existing ASR model — Spanish, French Canadian — expanding the 50M addressable market significantly.', impact: 'High', timeframe: '9-12 months', category: 'Revenue' },
    { title: 'Sentiment & Intent Analysis for Accessibility', description: 'Layer sentiment detection and speaker intent classification on top of captioning — enabling deaf/HoH users to perceive tone, urgency, and emotion that text alone doesn\'t convey.', impact: 'Medium', timeframe: '6-9 months', category: 'Core Product' },
  ],
  "SMRTR": [
    { title: 'AI Invoice Anomaly Detection', description: 'Deploy ML on SMRTR\'s AP automation data to flag anomalous invoices — duplicate payments, unusual amounts, vendor fraud patterns — before approval. High-value for food & beverage distributors processing thousands of invoices monthly.', impact: 'High', timeframe: '3-6 months', category: 'Core Product' },
    { title: 'Intelligent Document Classification', description: 'Use NLP to automatically classify, extract, and route incoming documents (BOLs, COAs, invoices, compliance certs) — replacing manual sorting and reducing processing time by 60%.', impact: 'High', timeframe: '3-5 months', category: 'Operations' },
    { title: 'FSMA 204 Compliance AI', description: 'Build AI-powered traceability features for the 2028 FSMA 204 deadline — automated ingredient tracking, supplier documentation validation, and recall simulation using ML on supply chain data.', impact: 'High', timeframe: '6-12 months', category: 'Revenue' },
    { title: 'Predictive Backhaul Optimization', description: 'ML models that analyze historical delivery patterns, equipment availability, and route data to optimize backhaul scheduling — reducing empty miles and equipment idle time.', impact: 'Medium', timeframe: '6-9 months', category: 'Operations' },
  ],
  "Champ": [
    { title: 'AI-Driven Population Health Risk Stratification', description: 'Build ML models on Nightingale Notes\' longitudinal public health data to identify at-risk populations for disease outbreaks, chronic conditions, and social determinants of health.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Clinical Decision Support for Community Health', description: 'Embed AI-powered clinical recommendations into the Nightingale Notes workflow — treatment protocols, immunization scheduling, and care gap alerts based on Omaha System taxonomy data.', impact: 'High', timeframe: '9-12 months', category: 'Core Product' },
    { title: 'Automated Public Health Reporting', description: 'NLP-powered extraction and formatting of required public health reports from EHR data — reducing the reporting burden on community health nurses by 50%.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
    { title: 'AI-Powered Social Determinants Screening', description: 'Deploy NLP on clinical notes to automatically identify social determinants of health (housing, food security, transportation) and trigger appropriate referral workflows.', impact: 'Medium', timeframe: '6-9 months', category: 'Core Product' },
  ],
  "AutoTime": [
    { title: 'Predictive Labor Compliance Alerts', description: 'ML models that analyze time entry patterns across defense contracts to predict DCAA audit findings before they happen — flagging misallocations, threshold violations, and unusual patterns.', impact: 'High', timeframe: '4-6 months', category: 'Core Product' },
    { title: 'AI-Powered Contract Labor Forecasting', description: 'Predict labor needs per contract using historical patterns, project milestones, and seasonal trends — helping defense primes optimize workforce planning and reduce bench time.', impact: 'High', timeframe: '6-9 months', category: 'Revenue' },
    { title: 'Intelligent Time Entry Assistant', description: 'LLM-powered assistant that helps employees allocate time correctly across contracts — suggesting charge codes, flagging potential compliance issues, and auto-completing routine entries.', impact: 'Medium', timeframe: '3-5 months', category: 'Core Product' },
    { title: 'Anomaly Detection for Audit Readiness', description: 'Real-time anomaly detection on time entries that identifies patterns DCAA auditors typically flag — worked overnight but clocked standard hours, sudden allocation shifts between contracts.', impact: 'High', timeframe: '4-6 months', category: 'Core Product' },
  ],
  "FMSI": [
    { title: 'AI-Optimized Branch Staffing Models', description: 'Build ML models on FMSI\'s lobby traffic, transaction, and appointment data to predict optimal staffing levels per branch per hour — reducing wait times while minimizing labor costs.', impact: 'High', timeframe: '4-6 months', category: 'Core Product' },
    { title: 'Predictive Member Traffic Patterns', description: 'Time-series forecasting of branch foot traffic and transaction volumes using historical FMSI data, local events, and seasonal patterns — enabling proactive scheduling.', impact: 'High', timeframe: '3-6 months', category: 'Core Product' },
    { title: 'Conversational AI for Member Services', description: 'Extend the Posh partnership by integrating conversational AI deeper into the OneCX platform — appointment booking, queue management, and pre-visit needs assessment via chat/voice.', impact: 'Medium', timeframe: '3-5 months', category: 'Customer Experience' },
    { title: 'Branch Performance Benchmarking AI', description: 'ML-powered comparison of branch operations across FMSI\'s 140+ customers — identify top performers, surface best practices, and flag underperforming locations with specific improvement recommendations.', impact: 'Medium', timeframe: '6-9 months', category: 'Analytics' },
  ],
  "Thought Foundry": [
    { title: 'AI Content Recommendation Engine', description: 'Build recommendation models on content entitlement data — suggest relevant content packages, predict viewing patterns, and optimize digital content distribution for entertainment clients.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Automated Rights & Entitlements Matching', description: 'NLP-powered matching of content rights agreements to distribution rules — reducing manual rights management overhead and preventing unauthorized distribution.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
    { title: 'Content Performance Prediction', description: 'ML models that predict content performance based on metadata, release timing, and historical patterns — helping entertainment companies optimize their content investment decisions.', impact: 'Medium', timeframe: '6-9 months', category: 'Analytics' },
    { title: 'Intelligent Content Metadata Extraction', description: 'Deploy NLP/computer vision to auto-generate content metadata from raw assets — genre classification, mood tagging, content descriptions — at scale.', impact: 'Medium', timeframe: '3-5 months', category: 'Operations' },
  ],
  "Primate": [
    { title: 'ML-Powered Grid Anomaly Detection', description: 'Upgrade GridGuardian\'s rule-based anomaly detection to ML models trained on historical SCADA/EMS patterns — detecting subtle precursor signals that rules miss, with 30-60 minute advance warning.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Predictive Outage Duration Estimation', description: 'ML models that predict outage duration and restoration time based on fault type, weather, crew availability, and historical recovery patterns — improving NERC reporting accuracy.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'AI-Driven NERC Compliance Automation', description: 'Automate NERC reporting by using NLP to extract reportable events from GridGuardian data streams and auto-generate compliance documentation — replacing manual audit prep.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
    { title: 'Digital Twin for Grid Operations', description: 'Build a digital twin using GridGuardian\'s real-time data feeds to simulate grid scenarios — contingency planning, capacity analysis, and stress testing for utility operators.', impact: 'High', timeframe: '12-18 months', category: 'Core Product' },
  ],
  "ViaPeople": [
    { title: 'Enhanced AI Performance Summaries', description: 'Upgrade AI Instant Insights from basic LLM summaries to structured multi-rater analysis — identifying patterns across feedback sources, development themes, and behavioral trends over time.', impact: 'High', timeframe: '3-5 months', category: 'Core Product' },
    { title: 'Predictive Retention & Flight Risk Scoring', description: 'Build ML models on performance review data, 360 feedback patterns, and engagement signals to predict employee flight risk — enabling proactive retention interventions.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'AI Bias Detection in Reviews', description: 'Deploy NLP models to detect bias patterns in performance reviews — gender, racial, seniority — and surface them to HR leaders with specific examples and recommendations.', impact: 'Medium', timeframe: '4-6 months', category: 'Core Product' },
    { title: 'Succession Planning Intelligence', description: 'ML-powered identification of high-potential employees for leadership succession using 9-box data, performance trajectories, and skill gap analysis.', impact: 'Medium', timeframe: '6-9 months', category: 'Analytics' },
  ],
  "ThingTech": [
    { title: 'IoT Predictive Maintenance Models', description: 'Build ML models on ThingTech\'s IoT sensor data (manageIT) to predict asset failures before they occur — vibration patterns, temperature anomalies, usage cycles — with specific maintenance recommendations.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'AI-Optimized Fleet Routing (routeIT)', description: 'Enhance routeIT\'s scheduling with ML-based route optimization using historical patterns, real-time conditions, and vehicle/driver constraints — reducing fuel costs and improving on-time rates.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Anomaly Detection for Government Asset Compliance', description: 'Deploy anomaly detection on transit agency asset condition data (FTA TAM compliance) to automatically flag assets approaching condition thresholds before mandatory reporting periods.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
    { title: 'Salesforce Einstein Integration', description: 'Leverage Salesforce platform\'s Einstein AI capabilities to add predictive analytics to the AppExchange-based products — asset lifecycle prediction, demand forecasting, and smart alerts.', impact: 'Medium', timeframe: '3-5 months', category: 'Core Product' },
  ],
  "Cairn Applications": [
    { title: 'ML-Based Route Optimization', description: 'Upgrade Box Tracker\'s route management from deterministic algorithms to ML-based optimization — learning from historical patterns, seasonal demand, and real-time conditions to minimize fuel costs and maximize dumpster utilization.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Predictive Container Demand', description: 'Build demand forecasting models using Cairn\'s data on 65,000+ dumpsters across 350+ customers — predict when and where containers will be needed, reducing empty runs and improving asset utilization.', impact: 'High', timeframe: '6-9 months', category: 'Revenue' },
    { title: 'AI-Powered Weight Estimation (Scale House)', description: 'Deploy computer vision and ML on Scale House data to estimate container weights before weighing — flagging discrepancies, detecting overloaded containers, and automating billing adjustments.', impact: 'Medium', timeframe: '4-6 months', category: 'Operations' },
    { title: 'Automated Billing Reconciliation', description: 'NLP + rules engine to automatically match hauling records against customer contracts, identifying billing discrepancies and revenue leakage across the ~$150M in annual commerce.', impact: 'Medium', timeframe: '3-5 months', category: 'Operations' },
  ],
  "Spokane": [
    { title: 'AI Yield Prediction from Historical Data', description: 'Leverage 37 years of citrus packing data to build ML yield prediction models — forecast crop volumes by variety, grade, and region weeks before harvest, helping growers optimize pricing and logistics.', impact: 'High', timeframe: '9-12 months', category: 'Core Product' },
    { title: 'Computer Vision for Pack Quality Grading', description: 'Deploy CV models at packing houses for automated fruit quality grading — size, color, blemish detection — replacing manual inspection and improving consistency across facilities.', impact: 'High', timeframe: '12-18 months', category: 'Revenue' },
    { title: 'Predictive Traceability (FSMA Compliance)', description: 'Build AI-powered traceability on top of PackPoint that predicts recall risk based on supplier patterns, lot anomalies, and processing conditions — ahead of FSMA requirements.', impact: 'Medium', timeframe: '9-12 months', category: 'Core Product' },
    { title: 'Platform Modernization Strategy', description: 'NOTE: All AI use cases require platform modernization from AS/400/RPG to a modern cloud architecture first. Recommended approach: API wrapper around existing DB2 data, new AI services deployed alongside legacy system during gradual migration.', impact: 'High', timeframe: '18-24 months', category: 'Data Infrastructure' },
  ],
  "TrackIt Transit": [
    { title: 'AI-Powered Safety Risk Prediction', description: 'Build ML models on TrackIt\'s PTASP compliance data (attendance, incidents, claims, vehicle inspections) to predict safety risks before incidents occur — enabling proactive intervention.', impact: 'High', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Automated Incident Classification', description: 'Deploy NLP to automatically classify and route incident reports — severity assessment, root cause categorization, and escalation recommendations — reducing manual triage time by 70%.', impact: 'Medium', timeframe: '3-5 months', category: 'Operations' },
    { title: 'Predictive Vehicle Maintenance from Inspection Data', description: 'ML models trained on TrackIt\'s vehicle inspection history to predict maintenance needs and flag vehicles at risk of failure before the next inspection cycle.', impact: 'Medium', timeframe: '6-9 months', category: 'Core Product' },
    { title: 'Compliance Readiness Scoring', description: 'AI-driven scoring of transit agency PTASP compliance readiness using assessment data from 100+ agencies — benchmarking, gap identification, and prioritized remediation recommendations.', impact: 'Medium', timeframe: '4-6 months', category: 'Analytics' },
  ],
}

// Fallback for any company not in the map
const GENERIC_USE_CASES: UseCase[] = [
  { title: 'AI-Powered Process Automation', description: 'Identify and automate high-volume, rule-based workflows using AI agents — reducing manual effort and error rates across operations.', impact: 'High', timeframe: '3-6 months', category: 'Operations' },
  { title: 'Intelligent Document Processing', description: 'Deploy NLP pipelines to extract, classify, and route unstructured documents into structured data feeds.', impact: 'Medium', timeframe: '2-4 months', category: 'Operations' },
  { title: 'Predictive Analytics Dashboard', description: 'Build ML-powered forecasting models for key business metrics surfaced through executive dashboards.', impact: 'High', timeframe: '4-8 months', category: 'Analytics' },
  { title: 'LLM-Powered Customer Assistant', description: 'Deploy a conversational AI agent that handles FAQs, troubleshooting, and product guidance.', impact: 'Medium', timeframe: '2-4 months', category: 'Customer Experience' },
]

function selectUseCases(company: PortfolioCompany): UseCase[] {
  return COMPANY_USE_CASES[company.name] || GENERIC_USE_CASES
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

  // Calculate quick-win count and max impact
  const quickWins = useCases.filter(uc =>
    uc.timeframe.includes('3-') || uc.timeframe.includes('2-') || uc.timeframe.includes('4-')
  ).length
  const highImpact = useCases.filter(uc => uc.impact === 'High').length

  return (
    <div className="glass-card rounded-xl border border-cyan-500/20 p-6">
      <div className="flex items-start justify-between mb-2">
        <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Rocket className="w-5 h-5 text-cyan-400" />
          AI Use Case Roadmap
        </h2>
        <div className="flex gap-2">
          <span className="text-[10px] font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400">
            {highImpact} High Impact
          </span>
          <span className="text-[10px] font-semibold px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400">
            {quickWins} Quick Wins
          </span>
        </div>
      </div>
      <p className="text-xs text-[var(--text-muted)] mb-5">
        Company-specific AI initiatives for {company.name} based on current product capabilities, data assets, and market position
      </p>

      <div className="grid grid-cols-2 gap-4">
        {useCases.map((uc, i) => (
          <div
            key={i}
            className="relative bg-slate-800/40 rounded-xl p-5 border border-slate-700/40 hover:border-cyan-500/30 transition-all group"
          >
            <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-cyan-500/10 flex items-center justify-center">
              <span className="text-xs font-bold text-cyan-400">{i + 1}</span>
            </div>

            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm">{CATEGORY_ICONS[uc.category] || '🔹'}</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                {uc.category}
              </span>
            </div>

            <h3 className="text-sm font-bold text-[var(--text-primary)] mb-2 pr-8 leading-snug">
              {uc.title}
            </h3>

            <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-4">
              {uc.description}
            </p>

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

      <div className="mt-5 bg-cyan-500/5 rounded-lg p-4 border border-cyan-500/10">
        <div className="flex items-start gap-3">
          <Lightbulb className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
            <span className="font-semibold text-cyan-400">CAIO Recommendation: </span>
            {company.wave === 1
              ? `${company.name} is a Wave 1 priority — AI-ready for immediate investment. Start with the highest-impact use case (#1) and build toward a compound AI advantage that strengthens the competitive moat.`
              : company.wave === 2
              ? `${company.name} is Wave 2 — invest in data infrastructure and talent first (Q1-Q2), then deploy AI features (Q3-Q4). Focus on quick-win operational AI while building the foundation for core product enhancements.`
              : `${company.name} is Wave 3 — requires groundwork before AI is feasible. Prioritize platform modernization and data quality improvements. AI use cases are 12-24 month horizon after foundational investments.`
            }
          </div>
        </div>
      </div>
    </div>
  )
}
