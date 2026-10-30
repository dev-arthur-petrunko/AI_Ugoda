"use client";

import { useState, useEffect } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { Bookmark, Trash2, ExternalLink } from "lucide-react";
import { listBookmarks, removeBookmark } from "@/lib/api";
import Link from "next/link";

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBookmarks = async () => {
    setLoading(true);
    try {
      const res = await listBookmarks();
      setBookmarks(res.items || []);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Помилка завантаження");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadBookmarks(); }, []);

  const handleDelete = async (id: string) => {
    try {
      await removeBookmark(id);
      await loadBookmarks();
    } catch (err: any) {
      setError(err?.message || "Помилка видалення");
    }
  };

  return (
    <PageShell
      title="Мої закладки"
      subtitle="Збережені акти та положення для швидкого доступу."
    >
      <div className="space-y-4">
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {loading ? (
          <p className="text-text-secondary">Завантаження...</p>
        ) : bookmarks.length === 0 ? (
          <div className="glass card text-center py-8">
            <Bookmark className="h-8 w-8 mx-auto mb-2 text-text-secondary" />
            <p className="text-text-secondary">Закладок поки немає</p>
            <p className="text-sm text-text-secondary mt-1">
              Додайте закладку на акт або статтю, щоб швидко повернутися до неї.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {bookmarks.map((b) => (
              <div key={b.id} className="glass card flex justify-between items-center">
                <div>
                  <p className="font-medium">
                    {b.provision_identifier ? `${b.provision_identifier} — ` : ""}
                    <Link href={`/uk/legislation/${b.document_id}`} className="text-gold hover:underline">
                      Документ {b.document_id.slice(0, 8)}...
                    </Link>
                  </p>
                  {b.note && <p className="text-sm text-text-secondary mt-1">{b.note}</p>}
                  <p className="text-xs text-text-secondary mt-1">
                    Додано {new Date(b.created_at).toLocaleDateString("uk-UA")}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Link href={`/uk/legislation/${b.document_id}`} className="btn s flex items-center gap-1">
                    <ExternalLink className="h-4 w-4" />
                  </Link>
                  <button
                    className="btn s flex items-center gap-1"
                    onClick={() => handleDelete(b.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}