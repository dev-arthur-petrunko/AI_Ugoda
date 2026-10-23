"use client";

import * as React from "react";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 120 120"
      className={className}
      role="img"
      aria-label="AI Ugoda"
      style={{ width: "auto", height: "auto" }}
    >
      <defs>
        <linearGradient id="logo-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8F6F2B" />
          <stop offset=".5" stopColor="#E8C871" />
          <stop offset="1" stopColor="#A67C2E" />
        </linearGradient>
      </defs>
      <path
        className="u"
        d="M30 22 V62 a30 30 0 0 0 60 0 V22"
        fill="none"
        stroke="url(#logo-gold)"
        strokeWidth="6"
        strokeLinecap="round"
        style={{
          strokeDasharray: "1",
          strokeDashoffset: "1",
          animation: "logo-draw 1.2s ease-out forwards",
        }}
      />
      <circle
        className="dot d1"
        cx="30"
        cy="22"
        r="5"
        fill="url(#logo-gold)"
        style={{
          transformBox: "fill-box",
          transformOrigin: "center",
          transform: "scale(0)",
          animation: "logo-pop 0.5s ease-out 1.0s forwards",
        }}
      />
      <circle
        className="dot d2"
        cx="90"
        cy="22"
        r="5"
        fill="url(#logo-gold)"
        style={{
          transformBox: "fill-box",
          transformOrigin: "center",
          transform: "scale(0)",
          animation: "logo-pop 0.5s ease-out 1.15s forwards",
        }}
      />
      <path
        className="seal"
        d="M60 84 l8 8 -8 8 -8 -8z"
        fill="url(#logo-gold)"
        style={{
          transformBox: "fill-box",
          transformOrigin: "center",
          transform: "scale(0) rotate(-90deg)",
          animation: "logo-stamp 0.6s cubic-bezier(0.2, 1.4, 0.4, 1) 1.4s forwards",
        }}
      />
      <style>{`
        @keyframes logo-draw { to { stroke-dashoffset: 0 } }
        @keyframes logo-pop { to { transform: scale(1) } }
        @keyframes logo-stamp { to { transform: scale(1) rotate(0) } }
        @media (prefers-reduced-motion: reduce) {
          .u, .dot, .seal { animation: none !important; stroke-dashoffset: 0; transform: none !important }
        }
      `}</style>
    </svg>
  );
}