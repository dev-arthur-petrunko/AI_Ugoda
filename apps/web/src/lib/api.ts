// Same-origin: усі запити йдуть на /api/* і проксіюються Next.js (rewrites у
// next.config.js) на бекенд. Це прибирає CORS, розбіжності localhost/127.0.0.1
// та адресу API, вшиту в збірку, назавжди (аудит v5, §4).
export const API_BASE = "";

// --- JWT: зберігаємо токен у localStorage, підставляємо в Authorization ----
const TOKEN_KEY = "aiugoda_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Мережева помилка або CORS перекладаються українською, щоб UI не показував
  // сирий "Failed to fetch" (аудит v5, S1).
  let res: Response;
  try {
    const token = getToken();
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers || {}),
      },
    });
  } catch {
    throw new Error("Немає зв'язку з сервером. Перевірте, чи запущено API.");
  }
  if (res.status === 401) {
    throw new AuthError("Сесія завершена. Увійдіть знову, будь ласка.");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export class AuthError extends Error {}

export type DocumentItem = {
  id: string;
  source_id: string;
  title: string;
  document_type: string;
  document_number: string | null;
  adoption_date: string | null;
  issuing_authority: string | null;
  current_known_status: string | null;
  source_url: string | null;
  revision_id: string | null;
  revision_date: string | null;
  data_origin?: "official" | "fixture";
};

export async function getStats() {
  return request<{
    documents: number;
    revisions: number;
    provisions: number;
    links: number;
    events?: number;
    documents_official?: number;
    documents_fixture?: number;
    has_official?: boolean;
  }>("/api/v1/stats");
}

export async function listDocuments(
  q = "",
  limit = 20,
  offset = 0,
  adoptionDateFrom = "",
  adoptionDateTo = "",
  includeFixtures = false,
) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (adoptionDateFrom) params.set("adoption_date_from", adoptionDateFrom);
  if (adoptionDateTo) params.set("adoption_date_to", adoptionDateTo);
  if (includeFixtures) params.set("include_fixtures", "true"); // S3.2
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  return request<{ total: number; limit: number; offset: number; items: DocumentItem[] }>(`/api/v1/documents?${params}`);
}

export async function getDocument(id: string) {
  return request<any>(`/api/v1/documents/${id}`);
}

export async function getProvisions(id: string) {
  return request<{ document_id: string; revision_id: string | null; items: any[] }>(`/api/v1/documents/${id}/provisions`);
}

export async function getRevisions(id: string) {
  return request<{ document_id: string; items: any[] }>(`/api/v1/documents/${id}/revisions`);
}

export async function getDocumentAt(id: string, date: string) {
  return request<any>(`/api/v1/documents/${id}/at?date=${date}`);
}

export async function getSuggestions(q: string) {
  return request<{ suggestions: string[] }>(`/api/v1/documents/suggestions?q=${encodeURIComponent(q)}`);
}

export async function searchByProvision(ref: string) {
  return request<{ items: DocumentItem[] }>(`/api/v1/documents/search/by-provision?provision_ref=${encodeURIComponent(ref)}`);
}

export async function getSyncStatus() {
  return request<any>("/api/v1/sync/status");
}

export async function runSync() {
  return request<any>("/api/v1/sync/run", { method: "POST" });
}

export async function getSyncRuns(limit = 5) {
  return request<{ items: any[] }>(`/api/v1/sync/runs?limit=${limit}`);
}
export async function getAnalysis(id: string) {
  return request<any>(`/api/v1/documents/${id}/analysis`);
}

export async function getQuality(id: string) {
  return request<any>(`/api/v1/documents/${id}/quality`);
}

// --- Зміни (§4.3) -----------------------------------------------------------
export type ChangeEvent = {
  id: string;
  event_type: string;
  event_label: string;
  source_provision: string | null;
  source_act_ref: string | null;
  source_event_date: string | null;
  affected_document_id: string;
  affected_title: string;
  source_document_id: string | null;
  source_title: string | null;
  source_url: string | null;
  found_by: string;
};

export async function listEvents(limit = 50, offset = 0, documentId?: string) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (documentId) params.set("document_id", documentId);
  return request<{ total: number; limit: number; offset: number; items: ChangeEvent[] }>(
    `/api/v1/events?${params}`,
  );
}

// Bookmarks
export async function listBookmarks(limit = 50, offset = 0) {
  return request<{ total: number; limit: number; offset: number; items: any[] }>(`/api/v1/bookmarks?limit=${limit}&offset=${offset}`);
}
export async function addBookmark(documentId: string, provisionIdentifier?: string, note?: string) {
  const params = new URLSearchParams({ document_id: documentId });
  if (provisionIdentifier) params.set("provision_identifier", provisionIdentifier);
  if (note) params.set("note", note);
  return request<any>(`/api/v1/bookmarks?${params}`, { method: "POST" });
}
export async function removeBookmark(bookmarkId: string) {
  return request<any>(`/api/v1/bookmarks/${bookmarkId}`, { method: "DELETE" });
}

// Monitoring
export async function listMonitoringRules(limit = 50, offset = 0) {
  return request<{ total: number; limit: number; offset: number; items: any[] }>(`/api/v1/monitoring?limit=${limit}&offset=${offset}`);
}
export async function createMonitoringRule(ruleType: string, ruleConfig?: any, deliveryPrefs?: any, enabled = true) {
  const params = new URLSearchParams({ rule_type: ruleType, enabled: String(enabled) });
  if (ruleConfig) params.set("rule_configuration", JSON.stringify(ruleConfig));
  if (deliveryPrefs) params.set("delivery_preferences", JSON.stringify(deliveryPrefs));
  return request<any>(`/api/v1/monitoring?${params}`, { method: "POST" });
}
export async function deleteMonitoringRule(ruleId: string) {
  return request<any>(`/api/v1/monitoring/${ruleId}`, { method: "DELETE" });
}

// Contracts
export async function listContracts(limit = 50, offset = 0) {
  return request<{ total: number; limit: number; offset: number; items: any[] }>(`/api/v1/contracts?limit=${limit}&offset=${offset}`);
}
export async function getContract(contractId: string) {
  return request<any>(`/api/v1/contracts/${contractId}`);
}
export async function deleteContract(contractId: string) {
  return request<any>(`/api/v1/contracts/${contractId}`, { method: "DELETE" });
}

// Conflicts
export async function getConflicts() {
  return request<{ items: any[]; total: number }>("/api/v1/conflicts/");
}

export async function getConflict(conflictId: string) {
  return request<any>(`/api/v1/conflicts/${conflictId}`);
}

/** §6: рішення експерта — «Підтверджено» | «Відхилено» (потрібні права адміна). */
export async function reviewConflict(conflictId: string, review_status: "Підтверджено" | "Відхилено") {
  return request<any>(`/api/v1/conflicts/${conflictId}`, {
    method: "PATCH",
    body: JSON.stringify({ review_status }),
  });
}

// AI assistant
export async function askAI(question: string, documentId?: string) {
  const params = new URLSearchParams({ question });
  if (documentId) params.set("document_id", documentId);
  return request<any>(`/api/v1/ai/ask?${params}`, { method: "POST" });
}

// Graph (зв'язки акта)
export async function getGraph(documentId: string, depth = 2) {
  return request<{ document_id: string; depth: number; nodes: any[]; edges: any[] }>(
    `/api/v1/graph/${documentId}?depth=${depth}`,
  );
}

// --- Auth ------------------------------------------------------------------
/** Вхід: OAuth2 password flow → { access_token, token_type }. Токен кладемо в localStorage. */
export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  const data = await request<{ access_token: string; token_type: string }>("/api/v1/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  setToken(data.access_token);
  return data;
}

export async function register(email: string, password: string) {
  return request<any>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout() {
  setToken(null);
}

export async function refreshAccessToken() {
  const token = getToken();
  if (!token) throw new AuthError("Немає токена");
  const data = await request<{ access_token: string }>("/api/v1/auth/refresh", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  setToken(data.access_token);
  return data;
}
