export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  database: {
    status: string;
    dialect: string;
  };
  timestamp: string;
}

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  badge_number?: string;
  department?: string;
  role: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface CaseItem {
  id: number;
  case_id: string;
  case_number: string;
  title: string;
  description?: string;
  crime_type: string;
  status: "OPEN" | "UNDER_INVESTIGATION" | "PENDING_REVIEW" | "CLOSED";
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  police_station?: string;
  district?: string;
  state?: string;
  location?: string;
  incident_date?: string;
  created_by?: string;
  created_by_id?: number;
  assigned_officer_id?: number;
  created_at: string;
  updated_at: string;
  source_record_key?: string;
  fir_year?: number;
  fir_month?: number;
  fir_day?: number;
  fir_type?: string;
  fir_stage?: string;
  complaint_mode?: string;
  crime_head?: string;
  latitude?: number;
  longitude?: number;
  offence_duration?: string;
  act_section?: string;
  distance_from_ps?: string;
  beat_name?: string;
  village_area_name?: string;
  male?: number;
  female?: number;
  boy?: number;
  girl?: number;
  age_0?: number;
  victim_count?: number;
  accused_count?: number;
  arrested_male?: number;
  arrested_female?: number;
  arrested_count?: number;
  accused_chargesheeted_count?: number;
  conviction_count?: number;
  unit_id?: string;
  registration_method?: "MANUAL" | "AI_ASSISTED";
  source_document_reference?: string;
  extraction_metadata?: Record<string, unknown>;
}

export interface CaseCreatePayload {
  case_number: string;
  title: string;
  description?: string;
  crime_type: string;
  status?: string;
  priority?: string;
  police_station?: string;
  district?: string;
  state?: string;
  location?: string;
  incident_date?: string;
  act_section?: string;
  registration_method?: "MANUAL" | "AI_ASSISTED";
}

export interface AiCaseExtraction {
  filename: string;
  fields: Record<string, any>;
  entities: ExtractedEntityItem[];
  metadata: Record<string, unknown>;
}

export interface CaseUpdatePayload {
  title?: string;
  description?: string;
  crime_type?: string;
  status?: string;
  priority?: string;
  location?: string;
  police_station?: string;
}

export interface DashboardStats {
  metrics: {
    total_cases: number;
    active_investigations: number;
    documents_processed: number;
    evidence_items: number;
    potential_correlations: number;
  };
  cases_by_status: { name: string; count: number }[];
  cases_by_crime_type: { name: string; count: number }[];
  cases_by_language: { name: string; count: number }[];
  recent_audit_events: any[];
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

// Token storage helpers
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("evidential_token");
}

export function setStoredToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("evidential_token", token);
  }
}

export function removeStoredToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("evidential_token");
  }
}

export function getAuthHeaders(): HeadersInit {
  const token = getStoredToken();
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail || "Authentication failed");
  }
  const data: AuthResponse = await res.json();
  setStoredToken(data.access_token);
  return data;
}

export async function getCurrentUser(): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Unauthorized");
  return res.json();
}

export async function getCases(params?: {
  search?: string; status?: string; crime_type?: string; district?: string;
  police_station?: string; crime_head?: string; fir_year?: number; fir_stage?: string;
  skip?: number; limit?: number;
}): Promise<CaseItem[]> {
  const query = new URLSearchParams();
  if (params?.search) query.append("search", params.search);
  if (params?.status) query.append("status", params.status);
  if (params?.crime_type) query.append("crime_type", params.crime_type);
  if (params?.district) query.append("district", params.district);
  if (params?.police_station) query.append("police_station", params.police_station);
  if (params?.crime_head) query.append("crime_head", params.crime_head);
  if (params?.fir_year) query.append("fir_year", String(params.fir_year));
  if (params?.fir_stage) query.append("fir_stage", params.fir_stage);
  if (params?.skip !== undefined) query.append("skip", String(params.skip));
  if (params?.limit !== undefined) query.append("limit", String(params.limit));

  const res = await fetch(`${API_BASE_URL}/cases?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch cases" }));
    throw new Error(error.detail || "Failed to load cases");
  }
  return res.json();
}

export async function getCaseDetail(caseId: string | number): Promise<CaseItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Case not found" }));
    throw new Error(error.detail || "Failed to load case");
  }
  return res.json();
}

export async function createCase(payload: CaseCreatePayload): Promise<CaseItem> {
  const res = await fetch(`${API_BASE_URL}/cases`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to create case" }));
    throw new Error(error.detail || "Failed to create case");
  }
  return res.json();
}

export async function extractAiCaseIntake(file: File): Promise<AiCaseExtraction> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/cases/ai-assisted/extract`, {
    method: "POST",
    headers: { Accept: "application/json", ...(getStoredToken() ? { Authorization: `Bearer ${getStoredToken()}` } : {}) },
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "AI extraction failed" }));
    throw new Error(error.detail || "AI extraction failed");
  }
  return res.json();
}

export async function registerAiAssistedCase(
  file: File, payload: CaseCreatePayload, extractionMetadata: Record<string, unknown>
): Promise<CaseItem> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("case_data", JSON.stringify({ ...payload, registration_method: "AI_ASSISTED" }));
  formData.append("extraction_metadata", JSON.stringify(extractionMetadata));
  const res = await fetch(`${API_BASE_URL}/cases/ai-assisted/register`, {
    method: "POST",
    headers: { Accept: "application/json", ...(getStoredToken() ? { Authorization: `Bearer ${getStoredToken()}` } : {}) },
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Case registration failed" }));
    throw new Error(error.detail || "Case registration failed");
  }
  return res.json();
}

export async function updateCase(caseId: string | number, payload: CaseUpdatePayload): Promise<CaseItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to update case" }));
    throw new Error(error.detail || "Failed to update case");
  }
  return res.json();
}

export interface DocumentVersionItem {
  id: number;
  document_id: number;
  version_number: number;
  file_path: string;
  file_size_bytes?: number;
  sha256_hash: string;
  uploaded_by_id?: number;
  created_at: string;
}

export interface ExtractedEntityItem {
  id: number;
  case_id: number;
  document_id?: number;
  entity_type: string;
  entity_value: string;
  normalized_value?: string;
  confidence: number;
  context_snippet?: string;
}

export interface DocumentTranslationItem {
  id: number;
  document_id: number;
  source_language: string;
  target_language: string;
  translated_text: string;
  translator_model?: string;
  created_at: string;
}

export interface DocumentItem {
  id: number;
  case_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size_bytes?: number;
  mime_type?: string;
  sha256_hash: string;
  uploaded_by_id?: number;
  processing_status: "PENDING" | "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";
  error_message?: string;
  detected_language?: string;
  language_confidence?: number;
  original_text?: string;
  ocr_confidence?: number;
  ocr_engine?: string;
  created_at: string;
  updated_at: string;
  versions?: DocumentVersionItem[];
  translations?: DocumentTranslationItem[];
  entities?: ExtractedEntityItem[];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE_URL}/dashboard/stats`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load dashboard statistics");
  return res.json();
}

export async function getCaseDocuments(caseId: string | number): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/documents`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch documents" }));
    throw new Error(error.detail || "Failed to load documents");
  }
  return res.json();
}

export function uploadCaseDocument(
  caseId: string | number,
  file: File,
  onProgress?: (percent: number) => void
): Promise<DocumentItem> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);

    xhr.open("POST", `${API_BASE_URL}/cases/${caseId}/documents/upload`);

    const token = getStoredToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }
    xhr.setRequestHeader("Accept", "application/json");

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          resolve(data);
        } catch {
          reject(new Error("Failed to parse server response"));
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          reject(new Error(errorData.detail || "File upload failed"));
        } catch {
          reject(new Error(`Upload failed with HTTP ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network error during document upload"));
    };

    xhr.send(formData);
  });
}

export async function downloadDocumentFile(documentId: number, originalFilename: string) {
  const token = getStoredToken();
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new Error("Failed to download document");
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = originalFilename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function processCaseDocument(documentId: number): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/process`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Document processing failed" }));
    throw new Error(error.detail || "Failed to process document through AI pipeline");
  }
  return res.json();
}

export type SearchResultType = "CASE" | "DOCUMENT" | "ENTITY";

export interface SearchResultItem {
  result_type: SearchResultType;
  case_id: number;
  case_number: string;
  case_title: string;
  document_id?: number | null;
  document_filename?: string | null;
  entity_type?: string | null;
  entity_value?: string | null;
  match_field: string;
  match_snippet: string;
  score: number;
}

export interface SearchResponse {
  total: number;
  query?: string | null;
  filters_applied: Record<string, any>;
  search_mode: string;
  results: SearchResultItem[];
}

export interface SearchFilters {
  q?: string;
  case_number?: string;
  entity_type?: string;
  entity_value?: string;
  crime_type?: string;
  location?: string;
  skip?: number;
  limit?: number;
}

export async function searchInvestigation(params: SearchFilters): Promise<SearchResponse> {
  const url = new URL(`${API_BASE_URL}/search`);
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && String(val).trim() !== "") {
      url.searchParams.append(key, String(val).trim());
    }
  });

  const res = await fetch(url.toString(), {
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Investigation search failed" }));
    throw new Error(error.detail || "Search request failed");
  }
  return res.json();
}

export interface MatchedEntityItem {
  entity_type: string;
  source_value: string;
  related_value: string;
  similarity: number;
  match_type: string;
}

export interface CorrelationResult {
  source_case: {
    id: number;
    case_number: string;
    title: string;
    crime_type: string;
    status?: string;
    district?: string;
    fir_year?: number;
    crime_head?: string;
  };
  related_case: {
    id: number;
    case_number: string;
    title: string;
    crime_type: string;
    status?: string;
    district?: string;
    fir_year?: number;
    crime_head?: string;
  };
  correlation_score: number;
  matching_entities: MatchedEntityItem[];
  matching_factors: string[];
  factor_scores?: Record<string, number>;
  explanation: string;
}

export interface CorrelationListResponse {
  source_case_id: number;
  total: number;
  correlations: CorrelationResult[];
}

export async function getCaseCorrelations(
  caseId: string | number,
  minThreshold: number = 0.25
): Promise<CorrelationListResponse> {
  const res = await fetch(
    `${API_BASE_URL}/cases/${caseId}/correlations?min_threshold=${minThreshold}`,
    {
      headers: getAuthHeaders(),
    }
  );
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch case correlations" }));
    throw new Error(error.detail || "Failed to retrieve case correlations");
  }
  return res.json();
}

export interface TimelineEventItem {
  id: string;
  event_date: string;
  event_type: string;
  title: string;
  description?: string | null;
  source: string;
  source_type: string;
  source_id?: number | null;
  source_document?: string | null;
  location?: string | null;
  metadata?: Record<string, any> | null;
}

export interface CaseTimelineResponse {
  case_id: number;
  case_number: string;
  case_title: string;
  total_events: number;
  events: TimelineEventItem[];
}

export interface TimelineEventCreatePayload {
  title: string;
  description?: string;
  event_date: string;
  event_type?: string;
  location?: string;
  source_document_id?: number;
}

export async function getCaseTimeline(
  caseId: string | number,
  order: "asc" | "desc" = "asc"
): Promise<CaseTimelineResponse> {
  const res = await fetch(
    `${API_BASE_URL}/cases/${caseId}/timeline?order=${order}`,
    {
      headers: getAuthHeaders(),
    }
  );
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch investigation timeline" }));
    throw new Error(error.detail || "Failed to retrieve case timeline");
  }
  return res.json();
}

export async function createTimelineEvent(
  caseId: string | number,
  payload: TimelineEventCreatePayload
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/timeline/events`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to create timeline event" }));
    throw new Error(error.detail || "Failed to record investigation event");
  }
  return res.json();
}

export interface SourceCitation {
  citation_id: string;
  source_type: string;
  source_title: string;
  document_filename?: string | null;
  snippet?: string | null;
}

export interface CopilotQueryResponse {
  case_id: number;
  case_number: string;
  question: string;
  answer: string;
  citations: SourceCitation[];
  uncertainty_flag: boolean;
  confidence_level: string;
}

export interface CopilotCaseSummaryResponse {
  case_id: number;
  case_number: string;
  case_title: string;
  summary_answer: string;
  citations: SourceCitation[];
  persons_identified: string[];
  evidence_count: number;
  timeline_events_count: number;
}

export async function queryCopilot(
  caseId: number,
  question: string
): Promise<CopilotQueryResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/copilot/query`, {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ case_id: caseId, question }),
    });
  } catch {
    throw new Error("Unable to connect to the AI backend.");
  }
  if (!res.ok) {
    if (res.status === 401) throw new Error("Please sign in to use the AI Copilot.");
    if (res.status === 403) throw new Error("You are not authorized to access this FIR.");
    if (res.status === 404) throw new Error("The selected FIR could not be found.");
    if (res.status >= 500) throw new Error("AI service is temporarily unavailable.");
    const error = await res.json().catch(() => ({ detail: "Copilot query failed" }));
    throw new Error(error.detail || "Unable to process the Copilot request.");
  }
  return res.json();
}

export async function getCaseCopilotSummary(
  caseId: string | number
): Promise<CopilotCaseSummaryResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/cases/${caseId}/copilot/summary`, {
      headers: getAuthHeaders(),
    });
  } catch {
    throw new Error("Unable to connect to the AI backend.");
  }
  if (!res.ok) {
    if (res.status === 401) throw new Error("Please sign in to use the AI Copilot.");
    if (res.status === 403) throw new Error("You are not authorized to access this FIR.");
    if (res.status === 404) throw new Error("The selected FIR could not be found.");
    if (res.status >= 500) throw new Error("AI service is temporarily unavailable.");
    const error = await res.json().catch(() => ({ detail: "Unable to load Copilot summary" }));
    throw new Error(error.detail || "Unable to load Copilot summary.");
  }
  return res.json();
}

// Digital Chain of Custody Types & Endpoints

export type CustodyStatus =
  | "COLLECTED"
  | "SEALED"
  | "TRANSFERRED"
  | "RECEIVED"
  | "EXAMINED"
  | "REPORT_GENERATED"
  | "RETURNED"
  | "COURT_SUBMITTED";

export interface CustodyEventItem {
  id: number;
  evidence_id: number;
  case_id: number;
  action: string;
  previous_status?: string;
  new_status: string;
  actor_id?: number;
  actor_name: string;
  timestamp: string;
  location?: string;
  from_custodian?: string;
  to_custodian?: string;
  reason?: string;
  notes?: string;
  evidence_hash: string;
  digital_signature?: string;
  device_info?: string;
  created_at: string;
}

export interface EvidenceItem {
  id: number;
  case_id: number;
  evidence_number: string;
  title: string;
  description?: string;
  evidence_type: string;
  file_path?: string;
  file_size_bytes?: number;
  mime_type?: string;
  sha256_hash: string;
  status: CustodyStatus;
  current_custodian?: string;
  collected_by?: string;
  collection_location?: string;
  collection_date?: string;
  notes?: string;
  forensic_report_path?: string;
  forensic_report_hash?: string;
  is_tampered: boolean;
  verification_status: string;
  last_verified_at?: string;
  uploaded_by_id?: number;
  created_at: string;
  updated_at: string;
  custody_events: CustodyEventItem[];
}

export interface CustodyChainResponse {
  evidence_id: number;
  evidence_number: string;
  case_id: number;
  current_status: CustodyStatus;
  current_custodian?: string;
  total_events: number;
  events: CustodyEventItem[];
}

export interface IntegrityVerificationResult {
  evidence_id: number;
  evidence_number: string;
  stored_sha256: string;
  current_sha256: string;
  status: string;
  is_valid: boolean;
  verified_at: string;
  verified_by: string;
  message: string;
}

export async function getCaseEvidence(caseId: string | number): Promise<EvidenceItem[]> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to load case evidence" }));
    throw new Error(error.detail || "Failed to load case evidence");
  }
  return res.json();
}

export async function addCaseEvidence(caseId: string | number, formData: FormData): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to add evidence" }));
    throw new Error(error.detail || "Failed to add evidence");
  }
  return res.json();
}

export async function getEvidenceDetail(
  caseId: string | number,
  evidenceId: number
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch evidence details" }));
    throw new Error(error.detail || "Failed to fetch evidence details");
  }
  return res.json();
}

export async function getCustodyChain(
  caseId: string | number,
  evidenceId: number
): Promise<CustodyChainResponse> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/custody-chain`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch chain of custody" }));
    throw new Error(error.detail || "Failed to fetch chain of custody");
  }
  return res.json();
}

export async function sealEvidence(
  caseId: string | number,
  evidenceId: number,
  payload: { reason?: string; notes?: string } = {}
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/seal`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to seal evidence" }));
    throw new Error(error.detail || "Failed to seal evidence");
  }
  return res.json();
}

export async function transferEvidence(
  caseId: string | number,
  evidenceId: number,
  payload: { to_custodian: string; location?: string; reason?: string; notes?: string }
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/transfer`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to transfer evidence" }));
    throw new Error(error.detail || "Failed to transfer evidence");
  }
  return res.json();
}

export async function receiveEvidence(
  caseId: string | number,
  evidenceId: number,
  payload: { received_by?: string; location?: string; condition_notes?: string } = {}
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/receive`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to receive evidence" }));
    throw new Error(error.detail || "Failed to receive evidence");
  }
  return res.json();
}

export async function startExamination(
  caseId: string | number,
  evidenceId: number,
  payload: { examiner?: string; purpose?: string; notes?: string } = {}
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/start-examination`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to start examination" }));
    throw new Error(error.detail || "Failed to start examination");
  }
  return res.json();
}

export async function completeExamination(
  caseId: string | number,
  evidenceId: number,
  payload: { examiner?: string; result_notes?: string } = {}
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/complete-examination`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to complete examination" }));
    throw new Error(error.detail || "Failed to complete examination");
  }
  return res.json();
}

export async function attachForensicReport(
  caseId: string | number,
  evidenceId: number,
  formData: FormData
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/report`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to attach forensic report" }));
    throw new Error(error.detail || "Failed to attach forensic report");
  }
  return res.json();
}

export async function returnEvidence(
  caseId: string | number,
  evidenceId: number,
  payload: { to_custodian: string; location?: string; reason?: string; notes?: string }
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/return`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to return evidence" }));
    throw new Error(error.detail || "Failed to return evidence");
  }
  return res.json();
}

export async function submitToCourt(
  caseId: string | number,
  evidenceId: number,
  payload: { court_name: string; submission_notes?: string; notes?: string }
): Promise<EvidenceItem> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/submit-court`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to submit evidence to court" }));
    throw new Error(error.detail || "Failed to submit evidence to court");
  }
  return res.json();
}

export async function verifyEvidenceIntegrity(
  caseId: string | number,
  evidenceId: number
): Promise<IntegrityVerificationResult> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/verify`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to verify evidence integrity" }));
    throw new Error(error.detail || "Failed to verify evidence integrity");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Court Evidence Package Types & API
// ---------------------------------------------------------------------------

export interface CourtEvidencePackageData {
  metadata: {
    package_id: string;
    case_id: number;
    case_number: string;
    generated_at: string;
    generated_by: string;
    authority: string;
    system_version: string;
    status: string;
    package_hash: string;
    is_complete: boolean;
    missing_sections: string[];
  };
  case_summary: {
    case_id: number;
    case_number: string;
    title: string;
    crime_type: string;
    priority: string;
    status: string;
    police_station?: string;
    district?: string;
    state?: string;
    location?: string;
    incident_date?: string;
    act_section?: string;
    fir_year?: number;
    crime_head?: string;
    assigned_officer?: string;
    created_at: string;
  };
  fir: {
    available: boolean;
    fir_number?: string;
    fir_year?: number;
    fir_stage?: string;
    police_station?: string;
    district?: string;
    act_section?: string;
    complaint_mode?: string;
    incident_date?: string;
    linked_documents: Array<{
      document_id: number;
      filename: string;
      file_hash: string;
      uploaded_at: string;
    }>;
    empty_message?: string;
  };
  witness_statements: {
    available: boolean;
    count: number;
    statements: Array<{
      witness_name: string;
      role_or_type: string;
      statement_date: string;
      summary: string;
      recorded_by: string;
      document_ref?: string;
      document_hash?: string;
    }>;
    empty_message?: string;
  };
  evidence_register: {
    available: boolean;
    count: number;
    items: Array<{
      evidence_id: number;
      evidence_number: string;
      title: string;
      evidence_type: string;
      original_sha256: string;
      current_sha256: string;
      custody_status: string;
      current_custodian: string;
      storage_location: string;
      verification_status: string;
      is_tampered: boolean;
      collection_date?: string;
      seized_from?: string;
      device_make_model?: string;
      serial_number?: string;
    }>;
    empty_message?: string;
  };
  forensic_reports: {
    available: boolean;
    count: number;
    reports: Array<{
      evidence_id: number;
      evidence_number: string;
      evidence_title: string;
      report_filename: string;
      report_hash: string;
      attached_by: string;
      attached_at: string;
      summary?: string;
    }>;
    empty_message?: string;
  };
  investigation_timeline: {
    available: boolean;
    count: number;
    events: Array<{
      id: number;
      event_date: string;
      event_type: string;
      title: string;
      description: string;
      location?: string;
    }>;
    empty_message?: string;
  };
  chain_of_custody: {
    available: boolean;
    total_events: number;
    items: Array<{
      evidence_id: number;
      evidence_number: string;
      title: string;
      current_status: string;
      current_custodian?: string;
      total_events: number;
      events: Array<{
        action: string;
        who: string;
        when: string;
        where?: string;
        from_custodian?: string;
        to_custodian?: string;
        why?: string;
        evidence_hash: string;
        digital_signature?: string;
        device_info?: string;
      }>;
    }>;
    empty_message?: string;
  };
  integrity_certificates: {
    available: boolean;
    count: number;
    all_valid: boolean;
    certificates: Array<{
      evidence_id: number;
      evidence_number: string;
      title: string;
      original_sha256: string;
      current_sha256: string;
      status: string;
      is_valid: boolean;
      verified_at: string;
      certifying_authority: string;
      integrity_declaration: string;
    }>;
    empty_message?: string;
  };
  digital_signatures: {
    available: boolean;
    total_signatures: number;
    signatures: Array<{
      item_type: string;
      item_identifier: string;
      signer_name: string;
      signer_role: string;
      timestamp: string;
      signature_hash: string;
      algorithm: string;
    }>;
    empty_message?: string;
  };
  audit_certificate: {
    certificate_id: string;
    case_number: string;
    total_audit_events: number;
    chain_of_custody_status: string;
    integrity_declaration: string;
    certified_by: string;
    certified_at: string;
    legal_statute_reference: string;
  };
}

export interface CourtEvidencePackageOut {
  id: number;
  package_id: string;
  case_id: number;
  generated_by_name: string;
  status: string;
  package_hash: string;
  is_complete: boolean;
  created_at: string;
  package_data: CourtEvidencePackageData;
}

export interface CourtPackageReadiness {
  case_id: number;
  case_number: string;
  case_summary_status: string;
  fir_status: string;
  witness_statements_status: string;
  evidence_register_status: string;
  forensic_reports_status: string;
  investigation_timeline_status: string;
  chain_of_custody_status: string;
  integrity_certificates_status: string;
  digital_signatures_status: string;
  audit_certificate_status: string;
  is_package_complete: boolean;
  missing_sections: string[];
  preview: CourtEvidencePackageData;
}

export async function getCourtPackageReadiness(
  caseId: string | number
): Promise<CourtPackageReadiness> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/court-package/readiness`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to evaluate court package readiness" }));
    throw new Error(error.detail || "Failed to evaluate court package readiness");
  }
  return res.json();
}

export async function generateCourtPackage(
  caseId: string | number
): Promise<CourtEvidencePackageOut> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/court-package`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to generate court evidence package" }));
    throw new Error(error.detail || "Failed to generate court evidence package");
  }
  return res.json();
}

export async function getLatestCourtPackage(
  caseId: string | number
): Promise<CourtEvidencePackageOut | null> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/court-package/latest`, {
    headers: getAuthHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch latest court package" }));
    throw new Error(error.detail || "Failed to fetch latest court package");
  }
  return res.json();
}

export async function getCourtPackageById(
  caseId: string | number,
  packageId: string
): Promise<CourtEvidencePackageOut> {
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}/court-package/${packageId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to fetch court package" }));
    throw new Error(error.detail || "Failed to fetch court package");
  }
  return res.json();
}
