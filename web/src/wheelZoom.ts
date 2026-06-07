/**
 * uPlot plugin: wheel-to-zoom and drag-to-pan on the x axis.
 *
 * uPlot ships drag-select zoom and double-click reset, but no wheel zoom or pan.
 * The viewport-fetch loop needs continuous range changes to exercise it, so we
 * add the canonical wheel-zoom plugin (adapted from the uPlot demos): the wheel
 * zooms around the cursor, and a plain drag pans. Both end by calling
 * `u.setScale('x', ...)`, which fires the `setScale` hook the Chart listens on.
 */
import type uPlot from 'uplot';

export function wheelZoomPlugin(opts: { factor?: number } = {}): uPlot.Plugin {
  const factor = opts.factor ?? 0.9;

  let xMin = 0;
  let xMax = 1;
  let xRange = 1;

  function clamp(nRange: number, nMin: number, nMax: number, fRange: number, fMin: number, fMax: number) {
    if (nRange > fRange) {
      nMin = fMin;
      nMax = fMax;
    } else if (nMin < fMin) {
      nMin = fMin;
      nMax = fMin + nRange;
    } else if (nMax > fMax) {
      nMax = fMax;
      nMin = fMax - nRange;
    }
    return [nMin, nMax];
  }

  return {
    hooks: {
      ready: (u: uPlot) => {
        xMin = u.scales.x.min!;
        xMax = u.scales.x.max!;
        xRange = xMax - xMin;

        const over = u.over;
        const rect = () => over.getBoundingClientRect();

        // Drag to pan.
        over.addEventListener('mousedown', (e: MouseEvent) => {
          if (e.button !== 0 || e.shiftKey) return; // shift-drag stays uPlot zoom-select
          e.preventDefault();
          const left0 = e.clientX;
          const scXMin0 = u.scales.x.min!;
          const scXMax0 = u.scales.x.max!;
          const xUnitsPerPx = u.posToVal(1, 'x') - u.posToVal(0, 'x');

          const onMove = (ev: MouseEvent) => {
            const dx = ev.clientX - left0;
            const shift = dx * xUnitsPerPx;
            const [nMin, nMax] = clamp(
              scXMax0 - scXMin0,
              scXMin0 - shift,
              scXMax0 - shift,
              xRange,
              xMin,
              xMax,
            );
            u.setScale('x', { min: nMin, max: nMax });
          };
          const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
          };
          document.addEventListener('mousemove', onMove);
          document.addEventListener('mouseup', onUp);
        });

        // Wheel to zoom around the cursor.
        over.addEventListener(
          'wheel',
          (e: WheelEvent) => {
            e.preventDefault();
            const { left: rLeft, width } = rect();
            const cursorX = e.clientX - rLeft;
            const leftPct = cursorX / width;

            const scXMin = u.scales.x.min!;
            const scXMax = u.scales.x.max!;
            const curRange = scXMax - scXMin;
            const valAtCursor = u.posToVal(cursorX, 'x');

            const nRange = e.deltaY < 0 ? curRange * factor : curRange / factor;
            let nMin = valAtCursor - leftPct * nRange;
            let nMax = nMin + nRange;
            [nMin, nMax] = clamp(nRange, nMin, nMax, xRange, xMin, xMax);
            u.setScale('x', { min: nMin, max: nMax });
          },
          { passive: false },
        );
      },
    },
  };
}
