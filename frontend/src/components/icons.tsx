import type { ReactNode } from "react";
import nvidiaLogo from "../assets/sources/nvidia.svg";
import rogLogo from "../assets/sources/rog.svg";
import kaleidescapeLogo from "../assets/sources/kaleidescape.svg";

export function MuteIcon({ muted, size = 22 }: { muted?: boolean; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor" />
      {muted ? (
        <path d="M16 9l5 6M21 9l-5 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      ) : (
        <>
          <path d="M16 8.5a5 5 0 010 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" />
          <path d="M18.5 6a8 8 0 010 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" />
        </>
      )}
    </svg>
  );
}

// Per-source display. A source maps to either a brand logo image or a short
// monogram, plus a role label (Shield, PC, HTPC ...). Drop a logo file in
// assets/sources and reference it here to add or replace a mark.
interface SourceMeta {
  label: string;
  logo?: string;
  mark?: ReactNode;
  color?: string;
}

const SOURCE_META: Record<string, SourceMeta> = {
  shield: { label: "Shield", logo: nvidiaLogo },
  kaleidescape: { label: "Kscape", logo: kaleidescapeLogo },
  gaming_pc: { label: "PC", logo: rogLogo },
  htpc: { label: "HTPC", mark: "HT", color: "#8a94a6" }, // Beelink logo pending
};

export function sourceLabel(name: string): string {
  return SOURCE_META[name]?.label ?? name;
}

export function SourceMark({ name, size = 32 }: { name: string; size?: number }) {
  const meta = SOURCE_META[name];
  if (meta?.logo) {
    return (
      <span className="source-mark source-mark-logo">
        <img src={meta.logo} alt="" />
      </span>
    );
  }
  const text = meta?.mark ?? name.slice(0, 2).toUpperCase();
  const color = meta?.color ?? "var(--accent)";
  return (
    <span
      className="source-mark"
      style={{ width: size, height: size, borderColor: color, color }}
    >
      {text}
    </span>
  );
}
