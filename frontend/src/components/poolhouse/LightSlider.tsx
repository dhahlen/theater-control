import { useEffect, useRef, useState } from "react";

// Brightness slider that drags smoothly and only sends to the bridge on release,
// so it never floods the backend or fights the 5s status poll. While the user is
// dragging, the poll is ignored; otherwise the slider tracks the live value. The
// track greys out when the zone is off.
export function LightSlider({
  online,
  on,
  bri,
  onCommit,
  showPercent,
}: {
  online: boolean;
  on: boolean;
  bri: number;
  onCommit: (value: number) => void;
  showPercent?: boolean;
}) {
  const [val, setVal] = useState(bri);
  const dragging = useRef(false);
  const latest = useRef(bri);

  useEffect(() => {
    if (!dragging.current) {
      setVal(bri);
      latest.current = bri;
    }
  }, [bri]);

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Number(e.currentTarget.value);
    latest.current = v;
    setVal(v);
  };

  const commit = () => {
    if (!dragging.current) return;
    dragging.current = false;
    onCommit(latest.current);
  };

  const slider = (
    <input
      className={`vol-slider light-slider ${on ? "" : "slider-off"}`}
      type="range"
      min={0}
      max={254}
      value={val}
      disabled={!online}
      onChange={handleInput}
      onPointerDown={() => (dragging.current = true)}
      onPointerUp={commit}
      onPointerCancel={commit}
      onKeyUp={() => onCommit(latest.current)}
    />
  );

  if (!showPercent) return slider;
  return (
    <span className="light-with-pct">
      {slider}
      <span className="light-pct">{Math.round((val / 254) * 100)}%</span>
    </span>
  );
}
