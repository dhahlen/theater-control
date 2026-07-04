import nvidiaLogo from "../assets/sources/nvidia.svg";
import rogLogo from "../assets/sources/rog.svg";
import kaleidescapeLogo from "../assets/sources/kaleidescape.png";

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

// Per-source display. A source shows a brand logo (logo-only, no text) or, when
// no logo fits, a short text label. Drop a logo file in assets/sources and map
// it here to add or replace a source mark.
interface SourceMeta {
  logo?: string;
  text?: string;
  label: string; // used for aria/title and as a fallback
}

const SOURCE_META: Record<string, SourceMeta> = {
  shield: { logo: nvidiaLogo, label: "Shield" },
  kaleidescape: { logo: kaleidescapeLogo, label: "KScape" },
  gaming_pc: { logo: rogLogo, label: "Game PC" },
  htpc: { text: "HTPC", label: "HTPC" },
};

export function sourceLabel(name: string): string {
  return SOURCE_META[name]?.label ?? name;
}

export function SourceMark({ name }: { name: string }) {
  const meta = SOURCE_META[name];
  if (meta?.logo) {
    return (
      <span className="source-mark source-mark-logo" title={meta.label}>
        <img src={meta.logo} alt={meta.label} />
      </span>
    );
  }
  return <span className="source-mark source-mark-text">{meta?.text ?? name.toUpperCase()}</span>;
}
