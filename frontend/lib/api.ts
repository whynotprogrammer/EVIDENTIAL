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

function getAuthHeaders(): HeadersInit {
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
