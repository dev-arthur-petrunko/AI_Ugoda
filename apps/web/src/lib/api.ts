export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

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
};

export async function getStats() {
  return request<{ documents: number; revisions: number; provisions: number; links: number }>("/api/v1/stats");
}

export async function listDocuments(q = "", limit = 20, offset = 0) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
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
export async function getAnalysis(id: string) {
  return request<any>(`/api/v1/documents/${id}/analysis`);
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
