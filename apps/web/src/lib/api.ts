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
