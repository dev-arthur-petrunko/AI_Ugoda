// Спільна тема сайту (ніч/день): localStorage + клас .theme-light на <html>.
// Вмикається з меню (shell) і слухається сценою (InteractiveScene) через CustomEvent.

export const THEME_EVENT = "ai-ugoda-theme-change";

export type Theme = "dark" | "light";

export function readTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  try {
    return localStorage.getItem("ai-ugoda-theme") === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("theme-light", theme === "light");
  try {
    localStorage.setItem("ai-ugoda-theme", theme);
  } catch {
    /* storage unavailable */
  }
  window.dispatchEvent(new CustomEvent<Theme>(THEME_EVENT, { detail: theme }));
}
