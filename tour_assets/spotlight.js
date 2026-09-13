// Phase 1: only geometry is read from the dashboard, never financial text/inputs.
export default function render(component) {
    const { parentElement, data, setStateValue, setTriggerValue } = component;
    const steps = data.steps;
    let index = data.step;
    let disposed = false;
    let frame = 0;
    let observedTarget = null;
    let shouldScroll = true;
    const priorFocus = document.activeElement;
    const dialog = document.createElement("dialog");
    dialog.className = "tour-overlay";
    dialog.setAttribute("aria-label", "Product Guide prototype");
    dialog.dataset.missing = "true";
    // Static owned HTML, never interpolated user data.
    dialog.innerHTML = `<div class="tour-spotlight" aria-hidden="true"></div>
      <section class="tour-card" aria-live="polite">
        <div class="tour-top"><span class="tour-count"></span><button data-action="close">Close</button></div>
        <h2></h2><p class="tour-copy"></p><p class="tour-warning" hidden></p>
        <div class="tour-actions"><button data-action="back">Back</button>
          <button data-action="skip">Skip</button><button class="primary" data-action="next">Next</button></div>
      </section>`;
    const card = dialog.querySelector(".tour-card");
    const spotlight = dialog.querySelector(".tour-spotlight");
    const warning = dialog.querySelector(".tour-warning");
    const next = dialog.querySelector('[data-action="next"]');
    const back = dialog.querySelector('[data-action="back"]');
    const close = dialog.querySelector('[data-action="close"]');
    const abort = new AbortController();
    const options = { signal: abort.signal };
    const viewport = window.visualViewport;
    const resize = new ResizeObserver(schedule);
    const mutations = new MutationObserver(schedule);

    function cleanup() {
        if (disposed) return;
        disposed = true;
        abort.abort();
        cancelAnimationFrame(frame);
        resize.disconnect();
        mutations.disconnect();
        if (dialog.open) dialog.close();
        dialog.remove();
        if (priorFocus?.isConnected) priorFocus.focus({ preventScroll: true });
    }

    function finish(reason) {
        // Restore the interface before notifying Python, even if communication fails.
        cleanup();
        setTriggerValue("finished", reason);
    }

    function schedule() {
        if (!disposed && !frame) frame = requestAnimationFrame(() => {
            frame = 0;
            try { position(); } catch { finish("error"); }
        });
    }

    function position() {
        const width = viewport?.width || window.innerWidth;
        const height = viewport?.height || window.innerHeight;
        const left = viewport?.offsetLeft || 0;
        const top = viewport?.offsetTop || 0;
        const gap = 12;
        card.style.width = `${Math.min(360, width - gap * 2)}px`;
        card.style.maxHeight = `${height - gap * 2}px`;
        const target = document.querySelector(`.st-key-${steps[index].target}`);
        if (target !== observedTarget) {
            if (observedTarget) resize.unobserve(observedTarget);
            observedTarget = target;
            if (target) resize.observe(target);
            shouldScroll = true;
        }
        const rect = target?.getBoundingClientRect();
        if (!rect || rect.width === 0 || rect.height === 0) {
            dialog.dataset.missing = "true";
            warning.hidden = false;
            warning.textContent = "This section isn't available right now. You can continue or close the tour.";
            card.style.left = `${left + (width - card.offsetWidth) / 2}px`;
            card.style.top = `${top + Math.max(gap, (height - card.offsetHeight) / 2)}px`;
            return;
        }
        if (shouldScroll) {
            shouldScroll = false;
            target.scrollIntoView({ behavior: "instant", block: "center", inline: "nearest" });
            schedule();
            return;
        }
        warning.hidden = true;
        // Prefer beside the target; on narrow screens put the card below it.
        const cardWidth = card.offsetWidth;
        let x = rect.right + gap;
        let y = Math.max(top + gap, rect.top);
        if (x + cardWidth > left + width - gap) {
            x = Math.max(left + gap, Math.min(rect.left, left + width - cardWidth - gap));
            y = rect.bottom + gap;
            if (y + card.offsetHeight > top + height - gap) {
                // Scroll only the target's nearest scrollable ancestor. No DOM reparenting.
                const desiredTop = top + gap + 48;
                let scroller = target.parentElement;
                while (scroller && !(scroller.scrollHeight > scroller.clientHeight &&
                    /auto|scroll/.test(getComputedStyle(scroller).overflowY))) scroller = scroller.parentElement;
                const delta = rect.top - desiredTop;
                if (scroller && Math.abs(delta) > 2) {
                    const before = scroller.scrollTop;
                    scroller.scrollTop += delta;
                    if (Math.abs(scroller.scrollTop - before) > 1) { schedule(); return; }
                }
                y = top + height - card.offsetHeight - gap;
            }
        }
        y = Math.max(top + gap, Math.min(y, top + height - card.offsetHeight - gap));
        card.style.left = `${x}px`;
        card.style.top = `${y}px`;
        const overlap = x < rect.right && x + cardWidth > rect.left &&
            y < rect.bottom && y + card.offsetHeight > rect.top;
        // Do not pretend an obscured target has been successfully highlighted.
        dialog.dataset.missing = String(overlap);
        if (overlap) {
            warning.hidden = false;
            warning.textContent = "This section doesn't fit beside the guide at this screen size. Rotate your device, or continue or close the tour.";
        }
        spotlight.style.left = `${Math.max(left, rect.left - 4)}px`;
        spotlight.style.top = `${Math.max(top, rect.top - 4)}px`;
        spotlight.style.width = `${Math.min(rect.width + 8, width)}px`;
        spotlight.style.height = `${Math.min(rect.height + 8, height)}px`;
    }

    function showStep() {
        dialog.querySelector(".tour-count").textContent = `${index + 1} of ${steps.length}`;
        dialog.querySelector("h2").textContent = steps[index].title;
        dialog.querySelector(".tour-copy").textContent = steps[index].copy;
        back.disabled = index === 0;
        next.textContent = index === steps.length - 1 ? "Finish" : "Next";
        shouldScroll = true;
        schedule();
    }

    try {
        parentElement.append(dialog);
        // Native modal top layer makes the underlying app inert (pointer and keyboard).
        dialog.showModal();
        close.focus({ preventScroll: true });
        dialog.addEventListener("cancel", event => { event.preventDefault(); finish("escape"); }, options);
        dialog.addEventListener("close", () => finish("close"), options);
        dialog.addEventListener("click", event => {
            const action = event.target.closest("button")?.dataset.action;
            if (action === "close" || action === "skip") return finish(action);
            if (action === "next" && index === steps.length - 1) return finish("finish");
            if (action === "next" || (action === "back" && index > 0)) {
                index += action === "next" ? 1 : -1;
                showStep();
                setStateValue("step", index);
            }
        }, options);
        // Keep touch/wheel gestures on the guide, not on underlying financial forms.
        dialog.addEventListener("wheel", event => {
            if (!card.contains(event.target)) event.preventDefault();
        }, { ...options, passive: false });
        dialog.addEventListener("touchmove", event => {
            if (!card.contains(event.target)) event.preventDefault();
        }, { ...options, passive: false });
        document.addEventListener("scroll", schedule, { ...options, capture: true });
        window.addEventListener("resize", schedule, options);
        viewport?.addEventListener("resize", schedule, options);
        viewport?.addEventListener("scroll", schedule, options);
        window.addEventListener("pagehide", cleanup, options);
        // The owned overlay is in shadow DOM; its layout changes don't loop this observer.
        mutations.observe(document.body, { childList: true, subtree: true });
        resize.observe(card);
        showStep();
    } catch {
        finish("error");
    }
    return cleanup;
}
