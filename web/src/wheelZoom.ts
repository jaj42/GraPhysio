/**
 * uPlot plugin: translate raw mouse/wheel gestures into *view requests*.
 *
 *   plain drag  -> pan (x; also y when already box/wheel-zoomed)
 *   shift-drag  -> box-zoom (x AND y)
 *   wheel       -> 2D zoom around the cursor (x AND y)
 *   double-click-> reset to the full curve (auto-fit y)
 *
 * The plugin does NOT touch uPlot scales itself. It computes the intended bounds
 * and hands them to the `ViewController` (in Chart.tsx), which is the single place
 * that mutates scales and triggers the decimation refetch. This keeps every
 * gesture going through one code path instead of each re-implementing scale +
 * fetch + y-autofit logic (which is what made pan/zoom/dblclick diverge).
 *
 * uPlot's own drag-zoom is disabled by the Chart (`cursor.drag` off) so it can't
 * fight this plugin over the same mousedown. X is clamped to the full bounds; the
 * y-autofit policy (keep vs. refit on pan/wheel) is decided by the controller from
 * the current view mode, not toggled here.
 */
import type uPlot from 'uplot';

/** What the plugin asks the chart to do. The chart owns scales + fetching. */
export interface ViewController {
  /** Drag-pan: x to [x0,x1]; y to [y0,y1] *only if* already in manual-y mode
   *  (in auto-y mode y stays owned by the auto-fit and the y delta is ignored). */
  pan(x0: number, x1: number, y0: number, y1: number): void;
  /** 2D zoom (wheel or box-drag): set x AND an explicit y-range -> manual-y mode. */
  zoomXY(x0: number, x1: number, y0: number, y1: number): void;
  /** Reset to the full curve with auto-fit y. */
  reset(): void;
}

interface WheelZoomOpts {
  /** Full x bounds (epoch-seconds): the limits panning/zooming clamp to. */
  xMin: number;
  xMax: number;
  /** Zoom step per wheel notch (<1 == zoom in on scroll-up). */
  factor?: number;
  /** The chart-side view controller every gesture routes through. */
  controller: ViewController;
}

const MIN_DRAG_PX = 5; // shorter shift-drags are treated as a click, not a zoom

export function wheelZoomPlugin({ xMin, xMax, factor = 0.9, controller }: WheelZoomOpts): uPlot.Plugin {
  const xRange = xMax - xMin;

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
            startBoxZoom(u, offsetX(e.clientX), offsetY(e.clientY), offsetX, offsetY, clampX, controller);
          } else {
            startPan(u, e.clientX, e.clientY, clampX, controller);
          }
        });

        over.addEventListener(
          'wheel',
          (e: WheelEvent) => {
            e.preventDefault();
            const zoomIn = e.deltaY < 0;

            // x: keep the value under the cursor fixed, scale the range by `factor`.
            const cursorX = offsetX(e.clientX);
            const leftPct = cursorX / over.clientWidth;
            const valX = u.posToVal(cursorX, 'x');
            const xRangeNow = u.scales.x.max! - u.scales.x.min!;
            const nXRange = zoomIn ? xRangeNow * factor : xRangeNow / factor;
            const [nxMin, nxMax] = clampX(nXRange, valX - leftPct * nXRange, valX + (1 - leftPct) * nXRange);

            // y: same, but y pixels grow downward so the cursor's fraction is from
            // the top, and the top pixel maps to the max value.
            const cursorY = offsetY(e.clientY);
            const topPct = cursorY / over.clientHeight;
            const valY = u.posToVal(cursorY, 'y');
            const yRangeNow = u.scales.y.max! - u.scales.y.min!;
            const nYRange = zoomIn ? yRangeNow * factor : yRangeNow / factor;
            const nyMax = valY + topPct * nYRange;
            const nyMin = valY - (1 - topPct) * nYRange;

            controller.zoomXY(nxMin, nxMax, nyMin, nyMax);
          },
          { passive: false },
        );

        over.addEventListener('dblclick', (e: MouseEvent) => {
          e.preventDefault();
          controller.reset();
        });
      },
    },
  };
}

type ClampX = (nRange: number, nMin: number, nMax: number) => [number, number];

function startPan(u: uPlot, clientX0: number, clientY0: number, clampX: ClampX, controller: ViewController) {
  const xMin0 = u.scales.x.min!;
  const xMax0 = u.scales.x.max!;
  const yMin0 = u.scales.y.min!;
  const yMax0 = u.scales.y.max!;
  const xPerPx = u.posToVal(1, 'x') - u.posToVal(0, 'x');
  const yPerPx = u.posToVal(1, 'y') - u.posToVal(0, 'y'); // negative: y pixels grow downward

  const onMove = (ev: MouseEvent) => {
    const dx = (ev.clientX - clientX0) * xPerPx;
    const dy = (ev.clientY - clientY0) * yPerPx;
    const [nxMin, nxMax] = clampX(xMax0 - xMin0, xMin0 - dx, xMax0 - dx);
    // Hand over both axes; the controller applies y only in manual mode.
    controller.pan(nxMin, nxMax, yMin0 - dy, yMax0 - dy);
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
  controller: ViewController,
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

    const [nMin, nMax] = clampX(x1 - x0, x0, x1);
    controller.zoomXY(nMin, nMax, yBot, yTop);
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}
