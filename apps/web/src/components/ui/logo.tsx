"use client";

import * as React from "react";

interface LogoProps {
  className?: string;
  size?: number | "hero";
}

export function Logo({ className = "", size = 34 }: LogoProps) {
  const isHero = size === "hero";
  const px = isHero ? 230 : (typeof size === "number" ? size : 34);
  const clamped = Math.min(px, 230);

  return (
    <svg
      viewBox="0 0 120 120"
      width={clamped}
      height={clamped}
      className={className}
      role="img"
      aria-label="AI Ugoda"
      style={{ width: clamped, height: clamped, flexShrink: 0 }}
    >
      <defs>
        <linearGradient id="logo-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8F6F2B" />
          <stop offset=".5" stopColor="#E8C871" />
          <stop offset="1" stopColor="#A67C2E" />
        </linearGradient>
      </defs>
      <path
        className="stand"
        d="M60 28 V100"
        fill="none"
        stroke="url(#logo-gold)"
        strokeWidth="6"
        strokeLinecap="round"
        style={{ strokeDasharray: "1", strokeDashoffset: "1", animation: "logo-draw .7s ease-out forwards" }}
      />
      <g
        className="arm"
        style={{ transformOrigin: "60px 28px", transform: "rotate(0deg)", animation: "logo-swing 2.4s cubic-bezier(.4,0,.2,1) 1.6s forwards" }}
      >
        <path
          className="beam"
          d="M18 28 H102"
          fill="none"
          stroke="url(#logo-gold)"
          strokeWidth="6"
          strokeLinecap="round"
          style={{ strokeDasharray: "1", strokeDashoffset: "1", animation: "logo-draw 1s ease-out .2s forwards" }}
        />
        <line className="strL" x1="18" y1="28" x2="22" y2="50" stroke="url(#logo-gold)" strokeWidth="3" strokeLinecap="round" style={{ strokeDasharray: "1", strokeDashoffset: "1", animation: "logo-draw .6s ease-out .7s forwards" }} />
        <line className="strR" x1="102" y1="28" x2="98" y2="50" stroke="url(#logo-gold)" strokeWidth="3" strokeLinecap="round" style={{ strokeDasharray: "1", strokeDashoffset: "1", animation: "logo-draw .6s ease-out .7s forwards" }} />
        <ellipse className="bowl bowlL" cx="22" cy="56" rx="14" ry="7" fill="none" stroke="url(#logo-gold)" strokeWidth="4" style={{ transformBox: "fill-box", transformOrigin: "center", transform: "scale(0)", animation: "logo-pop .5s ease-out 1.2s forwards" }} />
        <ellipse className="bowl bowlR" cx="98" cy="56" rx="14" ry="7" fill="none" stroke="url(#logo-gold)" strokeWidth="4" style={{ transformBox: "fill-box", transformOrigin: "center", transform: "scale(0)", animation: "logo-pop .5s ease-out 1.25s forwards" }} />
      </g>
      <path
        className="seal"
        d="M60 8 L72 20 L60 32 L48 20 Z"
        fill="url(#logo-gold)"
        style={{ transformBox: "fill-box", transformOrigin: "center", transform: "scale(0) rotate(-90deg)", animation: "logo-stamp .6s cubic-bezier(0.2, 1.4, 0.4, 1) 1.4s forwards" }}
      />
      <style>{`
        @keyframes logo-draw { to { stroke-dashoffset: 0 } }
        @keyframes logo-pop { to { transform: scale(1) } }
        @keyframes logo-stamp { to { transform: scale(1) rotate(0) } }
        @keyframes logo-swing {
          0% { transform: rotate(0deg) }
          12% { transform: rotate(-9deg) }
          30% { transform: rotate(6deg) }
          48% { transform: rotate(-3.2deg) }
          66% { transform: rotate(1.4deg) }
          84% { transform: rotate(-0.5deg) }
          100% { transform: rotate(0deg) }
        }
        @media (prefers-reduced-motion: reduce) {
          .stand, .beam, .strL, .strR, .bowl, .seal, .arm { animation: none !important; stroke-dashoffset: 0; transform: none !important }
        }
      `}</style>
    </svg>
  );
}