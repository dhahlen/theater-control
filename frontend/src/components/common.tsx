import type { ReactNode } from "react";
import type { DeviceState, Reachability } from "../types";

export function Panel(props: {
  title: string;
  device?: DeviceState;
  children: ReactNode;
  className?: string;
}) {
  const reach = props.device?.reachable ?? "unknown";
  return (
    <section className={`panel ${props.className ?? ""}`}>
      <header className="panel-head">
        <h2>{props.title}</h2>
        {props.device && <Dot reach={reach} />}
      </header>
      <div className="panel-body">{props.children}</div>
    </section>
  );
}

export function Dot({ reach }: { reach: Reachability }) {
  return <span className={`dot dot-${reach}`} title={reach} />;
}

export function Btn(props: {
  onClick: () => void;
  children: ReactNode;
  active?: boolean;
  wide?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      className={`btn ${props.active ? "btn-active" : ""} ${props.wide ? "btn-wide" : ""}`}
      onClick={props.onClick}
      disabled={props.disabled}
    >
      {props.children}
    </button>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value ?? "—"}</span>
    </div>
  );
}
