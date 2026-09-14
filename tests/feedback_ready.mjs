// Deterministic visibility/timer tests; no live browser or financial data.
import assert from 'node:assert/strict';
import render from '../tour_assets/feedback_ready.js';

export function runTests() {
    class Events {
        constructor() { this.listeners = []; }
        addEventListener(type, callback, options = {}) { this.listeners.push({ type, callback, options }); }
        dispatchEvent(event) {
            for (const entry of this.listeners) {
                if (entry.type === event.type && !entry.options.signal?.aborted) entry.callback(event);
            }
        }
    }
    class Event { constructor(type) { this.type = type; } }
    class AbortController {
        constructor() { this.signal = { aborted: false }; }
        abort() { this.signal.aborted = true; }
    }
    let now = 0, sequence = 0, targetExists = true, modal = false;
    const intervals = new Map(), results = [];
    const doc = new Events(), win = new Events();
    doc.visibilityState = 'visible';
    const target = {
        rect: { top: 0, left: 10, right: 350, width: 340, height: 900 },
        scrollIntoView() { this.rect.top = 0; },
        getBoundingClientRect() { return this.rect; },
    };
    doc.querySelector = selector => selector === '.st-key-tour_summary' ? (targetExists ? target : null) : modal;
    Object.assign(win, { Event, AbortController, performance: { now: () => now },
        innerHeight: 700, innerWidth: 390,
        setInterval: callback => { intervals.set(++sequence, callback); return sequence; },
        clearInterval: id => intervals.delete(id),
    });
    doc.defaultView = win;
    const mount = () => render({ parentElement: { ownerDocument: doc }, setTriggerValue: (key, value) => results.push([key, value]) });
    const tick = milliseconds => { now += milliseconds; for (const callback of [...intervals.values()]) callback(); };

    mount(); tick(2999); assert.equal(results.length, 0);
    tick(1); assert.deepEqual(results.pop(), ['ready', 'visible']);
    assert.equal(intervals.size, 0);

    // Time hidden or behind another dialog does not count as seeing the dashboard.
    doc.visibilityState = 'hidden'; mount(); tick(4000); assert.equal(results.length, 0);
    doc.visibilityState = 'visible'; tick(0); tick(2999); assert.equal(results.length, 0);
    modal = true; tick(1); modal = false; tick(0); tick(2999); assert.equal(results.length, 0);
    tick(1); assert.deepEqual(results.pop(), ['ready', 'visible']);

    // Moving the summary outside the viewport resets the uninterrupted viewing time.
    mount(); tick(2000); target.rect.top = -1000; tick(1000); target.rect.top = 0; tick(0);
    tick(2999); assert.equal(results.length, 0); tick(1); assert.equal(results.pop()[1], 'visible');

    // A slightly clipped top edge still leaves the summary meaningfully visible.
    mount(); target.rect.top = -10; tick(3000);
    assert.deepEqual(results.pop(), ['ready', 'visible']);

    for (const event of ['pointerdown', 'keydown']) {
        mount(); doc.dispatchEvent(new Event(event)); tick(5000);
        assert.deepEqual(results.pop(), ['ready', 'cancelled']); assert.equal(results.length, 0);
    }
    targetExists = false; mount(); tick(31000);
    assert.deepEqual(results.pop(), ['ready', 'cancelled']); targetExists = true;

    const stale = mount(); tick(1000); const current = mount(); stale();
    assert.equal(intervals.size, 1); tick(2999); assert.equal(results.length, 0);
    current(); tick(5000); assert.equal(results.length, 0); assert.equal(intervals.size, 0);
    mount(); win.dispatchEvent(new Event('pagehide')); assert.equal(intervals.size, 0);
    return 'Passed: visible delay, narrow viewport, hidden tab/modal, scroll reset, interaction cancellation, missing target, rerenders and cleanup';
}
