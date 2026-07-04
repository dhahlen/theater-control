import type { ReactNode } from "react";

export function MuteIcon({ muted, size = 22 }: { muted?: boolean; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 9v6h4l5 4V5L8 9H4z"
        fill="currentColor"
      />
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

// Per-source display: a short brand mark plus a label. Brand marks are simple
// monograms (drop official logo SVG/PNG in here to replace them).
interface SourceMeta {
  label: string;
  mark: ReactNode;
  color: string;
}

const SOURCE_META: Record<string, SourceMeta> = {
  shield: { label: "Shield", mark: "NV", color: "#76b900" },
  kaleidescape: { label: "Kaleidescape", mark: "K", color: "#c0392b" },
  gaming_pc: { label: "PC", mark: "PC", color: "#5b7cff" },
  htpc: { label: "HTPC", mark: "HT", color: "#8a94a6" },
};

export function sourceLabel(name: string): string {
  return SOURCE_META[name]?.label ?? name;
}

export function SourceMark({ name, size = 34 }: { name: string; size?: number }) {
  const meta = SOURCE_META[name];
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
