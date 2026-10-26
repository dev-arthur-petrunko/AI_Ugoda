"use client";
import { useId } from "react";

type Props = { variant?: "mark" | "lockup" | "seal"; size?: number; animated?: boolean; className?: string };

export function Logo({ variant = "mark", size = 34, animated = false, className }: Props) {
  const uid = useId().replace(/:/g, "");
  const g = `g${uid}`;
  const grad = (
    <linearGradient id={g} gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="160" y2="160">
      <stop offset="0" stopColor="#8F6F2B" />
      <stop offset=".5" stopColor="#E8C871" />
      <stop offset="1" stopColor="#A67C2E" />
    </linearGradient>
  );
  const fill = `url(#${g})`;
  const cls = `lg ${animated ? "lg-anim" : ""} ${className ?? ""}`;

  const Mark = ({ px }: { px: number }) => (
    <svg width={px} height={px} viewBox="0 0 160 160" role="img" aria-label="AI Ugoda" className={cls}>
      <defs>{grad}</defs>
      <g fill={fill} stroke={fill} strokeLinecap="round" strokeLinejoin="round">
        <path className="lg-fin" d="M80 5l8 9-8 9-8-9z" stroke="none" />
        <path className="lg-post" pathLength={1} d="M80 23V131" strokeWidth={4} fill="none" />
        <path d="M52 146l9-14h38l9 14z" stroke="none" />
        <g className="lg-sw">
          <path className="lg-bm" pathLength={1} d="M22 40H138" strokeWidth={3.2} fill="none" />
          <path d="M22 40L4 88M22 40L40 88M138 40L120 88M138 40L156 88" strokeWidth={3.2} fill="none" />
          <path className="lg-pan" d="M4 88A18 18 0 0 0 40 88Z" strokeWidth={2} />
          <path className="lg-pan lg-pan-r" d="M120 88A18 18 0 0 0 156 88Z" strokeWidth={2} />
          <circle cx="80" cy="40" r="5.5" stroke="none" />
        </g>
      </g>
    </svg>
  );

  if (variant === "mark") return <Mark px={size} />;

  if (variant === "lockup")
    return (
      <span className="lg-lock" style={{ display: "inline-flex", alignItems: "center", gap: Math.round(size * 0.35) }}>
        <Mark px={size} />
        <span>
          <b style={{ font: `600 ${Math.round(size * 0.68)}px/1 var(--font-display, "Playfair Display"), serif` }}>
            <i style={{ fontStyle: "normal", color: "#E8C871" }}>AI</i>{" "}
            <span style={{ color: "#F3E6BC" }}>Ugoda</span>
          </b>
          {size >= 40 && (
            <small
              style={{
                display: "block",
                font: "500 11px var(--font-ui, Inter), sans-serif",
                letterSpacing: ".14em",
                color: "#B3A28A",
                marginTop: 6,
              }}
            >
              ЮРИДИЧНИЙ ІНТЕЛЕКТ
            </small>
          )}
        </span>
      </span>
    );

  // seal
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" role="img" aria-label="Печатка AI Ugoda" className={`${cls} lg-seal`}>
      <defs>
        {grad}
        <path id={`c${uid}`} d="M100 100m-72 0a72 72 0 1 1 144 0a72 72 0 1 1-144 0" />
      </defs>
      <circle cx="100" cy="100" r="94" fill="none" stroke={fill} strokeWidth="2" />
      <circle cx="100" cy="100" r="88" fill="none" stroke={fill} strokeWidth=".8" />
      <circle cx="100" cy="100" r="56" fill="rgba(15,11,8,.7)" stroke={fill} strokeWidth="1.5" />
      <g className="lg-ring">
        <text fontFamily="Playfair Display, serif" fontSize="14" fontWeight="600" letterSpacing="3.6" fill={fill}>
          <textPath href={`#c${uid}`}>AI UGODA · ЗАКОН · ПРАВО · УГОДА · ЗАКОН ·</textPath>
        </text>
      </g>
      <g transform="translate(40 40) scale(.5)" fill={fill} stroke={fill} strokeLinecap="round" strokeLinejoin="round">
        <path d="M80 5l8 9-8 9-8-9z" stroke="none" />
        <path d="M80 23V131" strokeWidth="4" />
        <path d="M52 146l9-14h38l9 14z" stroke="none" />
        <path d="M22 40H138M22 40L4 88M22 40L40 88M138 40L120 88M138 40L156 88" strokeWidth="3.2" fill="none" />
        <path d="M4 88A18 18 0 0 0 40 88ZM120 88A18 18 0 0 0 156 88Z" strokeWidth="2" />
        <circle cx="80" cy="40" r="5.5" stroke="none" />
      </g>
    </svg>
  );
}
