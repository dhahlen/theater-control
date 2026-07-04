import { Btn } from "../common";
import { sourceLabel } from "../icons";
import { ASPECTS, ENERGY, LG_INPUTS, PICTURE_MODES, SOUND_OUT, type PoolHouseState } from "./state";

function ModeRow({
  label,
  options,
  value,
  onSelect,
}: {
  label: string;
  options: string[];
  value: string;
  onSelect: (v: string) => void;
}) {
  return (
    <div className="opt-block">
      <div className="subhead">{label}</div>
      <div className="mode-grid">
        {options.map((o) => (
          <button
            key={o}
            className={`btn mode-btn ${value === o ? "btn-active" : ""}`}
            onClick={() => onSelect(o)}
          >
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}

export function DisplayTab({ s }: { s: PoolHouseState }) {
  return (
    <div className="devview">
      <div className="devview-head">
        <h1>LG G5 84&quot;</h1>
        <span className={`pill ${s.power ? "pill-on" : "pill-off"}`}>{s.power ? "on" : "standby"}</span>
      </div>

      <section className="card">
        <div className="info-grid">
          <div><span className="muted">Input</span><strong>{s.lgInput}</strong></div>
          <div><span className="muted">Source</span><strong>{sourceLabel(s.source)}</strong></div>
          <div><span className="muted">Picture</span><strong>{s.picture}</strong></div>
          <div><span className="muted">Aspect</span><strong>{s.aspect}</strong></div>
        </div>
        <div className="subhead">Power</div>
        <div className="row btn-row">
          <Btn active={s.power} onClick={() => s.setPower(true)}>On</Btn>
          <Btn active={!s.power} onClick={() => s.setPower(false)}>Off</Btn>
        </div>
      </section>

      <section className="card">
        <ModeRow label="Input" options={LG_INPUTS} value={s.lgInput} onSelect={s.setLgInput} />
        <ModeRow label="Picture mode" options={PICTURE_MODES} value={s.picture} onSelect={s.setPicture} />
      </section>

      <section className="card">
        <ModeRow label="Aspect ratio" options={ASPECTS} value={s.aspect} onSelect={s.setAspect} />
        <ModeRow label="Energy saving" options={ENERGY} value={s.energy} onSelect={s.setEnergy} />
        <ModeRow label="Sound output" options={SOUND_OUT} value={s.soundOut} onSelect={s.setSoundOut} />
      </section>
    </div>
  );
}
