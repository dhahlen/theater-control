import { useState } from "react";
import { runScene } from "../api";
import type { SceneProgress } from "../store";
import type { StepStatus } from "../types";

const STATUS_ICON: Record<StepStatus, string> = {
  pending: "○",
  running: "◌",
  ok: "●",
  sent_unconfirmed: "◍",
  failed: "✕",
};

function Checklist({ progress }: { progress?: SceneProgress }) {
  if (!progress || progress.steps.length === 0) return null;
  return (
    <div className="checklist">
      {progress.steps.map((s) => (
        <div key={s.step} className={`check check-${s.status}`}>
          <span className="check-icon">{STATUS_ICON[s.status]}</span>
          <span className="check-step">{s.step.replace(/_/g, " ")}</span>
          {s.detail && <span className="check-detail">{s.detail}</span>}
        </div>
      ))}
      {progress.overall && (
        <div className={`check-overall overall-${progress.overall}`}>
          {progress.overall}
        </div>
      )}
    </div>
  );
}

export function SceneBar({
  sources,
  defaultSource,
  progress,
  markSceneStarted,
}: {
  sources: string[];
  defaultSource: string;
  progress: Record<string, SceneProgress>;
  markSceneStarted: (scene: string) => void;
}) {
  const [source, setSource] = useState(defaultSource);

  const run = (scene: string, body: Record<string, unknown> = {}) => {
    markSceneStarted(scene);
    runScene(scene, body).catch((e) => console.error(e));
  };

  const onBusy = progress["theater-on"]?.running;
  const offBusy = progress["theater-off"]?.running;

  return (
    <div className="scenebar">
      <div className="scene-primary">
        <button
          className="scene-btn scene-on"
          onClick={() => run("theater-on", { source })}
          disabled={onBusy}
        >
          <span className="scene-title">Theater On</span>
          <span className="scene-sub">{onBusy ? "working…" : `source: ${source}`}</span>
        </button>
        <Checklist progress={progress["theater-on"]} />
      </div>

      <div className="scene-source">
        <span className="scene-source-label">Source</span>
        <div className="source-list">
          {sources.map((s) => (
            <button
              key={s}
              className={`source-chip ${s === source ? "chip-active" : ""}`}
              onClick={() => setSource(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="scene-primary">
        <button
          className="scene-btn scene-off"
          onClick={() => run("theater-off")}
          disabled={offBusy}
        >
          <span className="scene-title">Theater Off</span>
          <span className="scene-sub">{offBusy ? "working…" : "standby"}</span>
        </button>
        <Checklist progress={progress["theater-off"]} />
      </div>
    </div>
  );
}
