// Only visibility and geometry are inspected. No financial text or inputs are read.
export default function render({ parentElement, setTriggerValue }) {
    const doc = parentElement.ownerDocument;
    const win = doc.defaultView;
    const disposeEvent = "finance-feedback-ready-dispose";
    doc.dispatchEvent(new win.Event(disposeEvent));
    const abort = new win.AbortController();
    const options = { signal: abort.signal };
    let since = null;
    let done = false;
    let scrolled = false;
    let interval;
    const started = win.performance.now();
    function cleanup() {
        done = true;
        win.clearInterval(interval);
        abort.abort();
    }
    function finish(reason) {
        if (done) return;
        cleanup();
        setTriggerValue("ready", reason);
    }
    function check() {
        if (done) return;
        const target = doc.querySelector(".st-key-tour_summary");
        if (target && !scrolled) {
            scrolled = true;
            target.scrollIntoView({ behavior: "instant", block: "start" });
        }
        const rect = target?.getBoundingClientRect();
        const viewport = win.visualViewport;
        const top = viewport?.offsetTop || 0;
        const height = viewport?.height || win.innerHeight;
        const width = viewport?.width || win.innerWidth;
        const visibleHeight = rect ? Math.min(rect.top + rect.height, top + height) -
            Math.max(rect.top, top) : 0;
        const visible = doc.visibilityState === "visible" && rect && rect.width > 0 &&
            rect.height > 0 && visibleHeight >= Math.min(rect.height, height) / 2 &&
            rect.left < width && rect.right > 0 && !doc.querySelector('dialog[open]');
        const now = win.performance.now();
        if (!visible) since = null;
        else if (since === null) since = now;
        else if (now - since >= 3000) return finish("visible");
        if (now - started > 30000) finish("cancelled");
    }
    doc.addEventListener(disposeEvent, cleanup, options);
    // If someone begins using the app immediately, don't interrupt their work.
    doc.addEventListener("pointerdown", () => finish("cancelled"), options);
    doc.addEventListener("keydown", () => finish("cancelled"), options);
    win.addEventListener("pagehide", cleanup, options);
    interval = win.setInterval(check, 150);
    check();
    return cleanup;
}
