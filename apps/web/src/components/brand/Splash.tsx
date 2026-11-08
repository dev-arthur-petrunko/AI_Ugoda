"use client";
import { useEffect, useState } from "react";
import { Logo } from "./Logo";

export function Splash() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    // Автотести (Playwright): сплеш не показуємо — він накладається на
    // скриншоти приймання і перехоплює кліки (navigator.webdriver = true).
    if (navigator.webdriver) return;
    if (sessionStorage.getItem("ugoda-splash")) return;
    sessionStorage.setItem("ugoda-splash", "1");
    setShow(true);
    const t = setTimeout(() => setShow(false), 2300);
    return () => clearTimeout(t);
  }, []);
  if (!show) return null;
  return (
    <div className="splash" onClick={() => setShow(false)} role="presentation">
      <Logo variant="mark" size={160} animated />
      <p>Юридичний інтелект</p>
    </div>
  );
}
