/**
 * uPlot plugin owning all interaction for the re-fetched viewport.
 *
 *   plain drag  -> pan (x)
 *   shift-drag  -> box-zoom (x AND y, with a live selection rectangle)
 *   wheel       -> zoom around the cursor (x)
 *   double-click-> reset to the full curve
 *
 * uPlot's own drag-zoom is disabled by the Chart (`cursor.drag` off) so it can't
 * fight this plugin over the same mousedown. X clamps to the full bounds passed in;
 * reset goes to the *full curve* (not uPlot's data extent, which here is only the
 * current decimated window). Every gesture ends in `u.setScale(...)`, firing the
 * `setScale` hook the viewport-fetch loop runs on.
 *
 * `onAutoY` reports whether the y-scale should keep auto-fitting to the visible
 * data: pan/wheel/reset want that, but box-zoom sets an explicit y-range that must
 * not be clobbered by the next fetch's auto-fit, so it reports `false`.
 */
import type uPlot from 'uplot';

interface WheelZoomOpts {
  /** Full x bounds (epoch-seconds): the limits panning/zooming clamp to. */
  xMin: number;
  xMax: number;
  /** Zoom step per wheel notch (<1 == zoom in on scroll-up). */
  factor?: number;
  /** Report the desired y-autofit mode (false after a box-zoom). */
  onAutoY?: (auto: boolean) => void;
}

const MIN_DRAG_PX = 5; // shorter shift-drags are treated as a click, not a zoom

export function wheelZoomPlugin({ xMin, xMax, factor = 0.9, onAutoY }: WheelZoomOpts): uPlot.Plugin {
  const xRange = xMax - xMin;
  const setAutoY = (auto: boolean) => onAutoY?.(auto);

  function clampX(nRange: number, nMin: number, nMax: number): [number, number] {
    if (nRange >= xRange) return [xMin, xMax];
    if (nMin < xMin) return [xMin, xMin + nRange];
    if (nMax > xMax) return [xMax - nRange, xMax];
    return [nMin, nMax];
  }

  return {
    hooks: {
      ready: (u: uPlot) => {
        const over = u.over;
        const offsetX = (clientX: number) => clientX - over.getBoundingClientRect().left;
        const offsetY = (clientY: number) => clientY - over.getBoundingClientRect().top;

        over.addEventListener('mousedown', (e: MouseEvent) => {
          if (e.button !== 0) return;
          e.preventDefault();
          if (e.shiftKey) {
            startBoxZoom(u, offsetX(e.clientX), offsetY(e.clientY), offsetX, offsetY, clampX, setAutoY);
          } else {
            startPan(u, e.clientX, clampX, setAutoY);
          }
        });

        over.addEventListener(
          'wheel',
          (e: WheelEvent) => {
            e.preventDefault();
            setAutoY(true);
            const cursorX = offsetX(e.clientX);
            const leftPct = cursorX / over.clientWidth;
            const valAtCursor = u.posToVal(cursorX, 'x');
            const curRange = u.scales.x.max! - u.scales.x.min!;
            const nRange = e.deltaY < 0 ? curRange * factor : curRange / factor;
            const [nMin, nMax] = clampX(nRange, valAtCursor - leftPct * nRange, valAtCursor + (1 - leftPct) * nRange);
            u.setScale('x', { min: nMin, max: nMax });
          },
          { passive: false },
        );

        over.addEventListener('dblclick', (e: MouseEvent) => {
          e.preventDefault();
          setAutoY(true);
          u.setScale('x', { min: xMin, max: xMax });
        });
      },
    },
  };
}

type ClampX = (nRange: number, nMin: number, nMax: number) => [number, number];

function startPan(u: uPlot, clientX0: number, clampX: ClampX, setAutoY: (a: boolean) => void) {
  const min0 = u.scales.x.min!;
  const max0 = u.scales.x.max!;
  const unitsPerPx = u.posToVal(1, 'x') - u.posToVal(0, 'x');

  const onMove = (ev: MouseEvent) => {
    setAutoY(true); // panning re-frames y to whatever scrolls into view
    const shift = (ev.clientX - clientX0) * unitsPerPx;
    const [nMin, nMax] = clampX(max0 - min0, min0 - shift, max0 - shift);
    u.setScale('x', { min: nMin, max: nMax });
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function startBoxZoom(
  u: uPlot,
  startPx: number,
  startPy: number,
  offsetX: (clientX: number) => number,
  offsetY: (clientY: number) => number,
  clampX: ClampX,
  setAutoY: (a: boolean) => void,
) {
  const width = u.over.clientWidth;
  const height = u.over.clientHeight;
  const clamp = (v: number, hi: number) => Math.max(0, Math.min(hi, v));

  const onMove = (ev: MouseEvent) => {
    const curPx = clamp(offsetX(ev.clientX), width);
    const curPy = clamp(offsetY(ev.clientY), height);
    u.setSelect(
      {
        left: Math.min(startPx, curPx),
        width: Math.abs(curPx - startPx),
        top: Math.min(startPy, curPy),
        height: Math.abs(curPy - startPy),
      },
      false,
    );
  };
  const onUp = (ev: MouseEvent) => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    const endPx = clamp(offsetX(ev.clientX), width);
    const endPy = clamp(offsetY(ev.clientY), height);
    u.setSelect({ left: 0, top: 0, width: 0, height: 0 }, false); // clear the rectangle

    // Too small a drag -> treat as a click, not a zoom.
    if (Math.abs(endPx - startPx) < MIN_DRAG_PX || Math.abs(endPy - startPy) < MIN_DRAG_PX) return;

    const x0 = u.posToVal(Math.min(startPx, endPx), 'x');
    const x1 = u.posToVal(Math.max(startPx, endPx), 'x');
    // Pixel y grows downward, so the top pixel is the larger value.
    const yTop = u.posToVal(Math.min(startPy, endPy), 'y');
    const yBot = u.posToVal(Math.max(startPy, endPy), 'y');

    setAutoY(false); // the box defines y explicitly; don't auto-fit over it
    u.setScale('y', { min: yBot, max: yTop });
    const [nMin, nMax] = clampX(x1 - x0, x0, x1);
    u.setScale('x', { min: nMin, max: nMax }); // fires the fetch for the new window
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}
