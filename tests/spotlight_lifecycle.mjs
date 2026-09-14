// Offline lifecycle regression test, not a browser positioning/accessibility test.
import assert from "node:assert/strict";
import render from "../tour_assets/spotlight.js";

export function runTests() {
    class Event {
        constructor(type) { this.type = type; }
        preventDefault() {}
    }
    class EventTarget {
        constructor() { this.listeners = []; }
        addEventListener(type, callback, options = {}) { this.listeners.push({ type, callback, options }); }
        dispatchEvent(event) {
            event.target = this;
            for (const listener of [...this.listeners]) {
                if (listener.type === event.type && !listener.options.signal?.aborted) listener.callback(event);
            }
        }
    }
    class AbortController {
        constructor() { this.signal = { aborted: false }; }
        abort() { this.signal.aborted = true; }
    }
    const observers = [];
    const frames = new Map();
    let sequence = 0;
    class Observer {
        constructor() { this.disconnected = false; observers.push(this); }
        observe() {}
        unobserve() {}
        disconnect() { this.disconnected = true; }
    }
    class Element extends EventTarget {
        constructor() {
            super(); this.style = {}; this.dataset = {}; this.childrenBySelector = new Map();
            this.open = false; this.removed = false; this.isConnected = true;
            this.offsetWidth = 360; this.offsetHeight = 260;
        }
        setAttribute() {}
        querySelector(selector) {
            if (!this.childrenBySelector.has(selector)) this.childrenBySelector.set(selector, new Element());
            return this.childrenBySelector.get(selector);
        }
        showModal() { this.open = true; }
        close() { this.open = false; }
        remove() { this.removed = true; this.isConnected = false; }
        focus() {}
        contains() { return false; }
        closest() { return { dataset: { action: this.action } }; }
    }
    const doc = new EventTarget();
    doc.body = new Element(); doc.activeElement = new Element();
    doc.createElement = () => new Element();
    doc.querySelector = () => null;
    doc.defaultView = Object.assign(new EventTarget(), {
        AbortController, Event, ResizeObserver: Observer, MutationObserver: Observer,
        innerWidth: 1000, innerHeight: 800,
        requestAnimationFrame: callback => { frames.set(++sequence, callback); return sequence; },
        cancelAnimationFrame: key => frames.delete(key),
        getComputedStyle: () => ({ fontFamily: 'App font' }),
    });
    const dialogs = [], triggers = [], states = [];
    const steps = [0, 1, 2, 3].map(i => ({ target: `target_${i}`, title: `Step ${i}`, copy: 'Static copy' }));
    const labels = { title: 'Trumpa apžvalga', close: 'Uždaryti', back: 'Atgal', skip: 'Praleisti',
        next: 'Toliau', finish: 'Baigti', count: '{current} iš {total}', missing: 'Skiltis nepasiekiama.', small: 'Nepakanka vietos.',
        dashboard: 'Eiti į mano finansinį vaizdą', feedback: 'Palikti trumpą atsiliepimą' };
    function mount(step, offerFeedback = true) {
        return render({
            parentElement: { ownerDocument: doc, append: dialog => dialogs.push(dialog) },
            data: { steps, step, labels, language: 'lt', offer_feedback: offerFeedback },
            setStateValue: (key, value) => states.push([key, value]),
            setTriggerValue: (key, value) => triggers.push([key, value]),
        });
    }
    function click(action) {
        const dialog = dialogs.at(-1); dialog.action = action;
        dialog.dispatchEvent(new Event('click'));
    }
    const open = () => dialogs.filter(dialog => dialog.open && !dialog.removed);
    const firstCleanup = mount(3);
    click('back');
    assert.deepEqual(states.at(-1), ['step', 2]);
    mount(2); // Framework rerender WITHOUT old unmount cleanup: original bug.
    assert.equal(open().length, 1);
    assert.equal(dialogs[0].removed, true);
    assert.ok(observers.slice(0, 2).every(observer => observer.disconnected));
    firstCleanup(); // Delayed old cleanup must not remove the new instance.
    assert.equal(open().length, 1);
    for (const step of [1, 0, 1, 2, 3, 2, 1]) {
        mount(step);
        assert.equal(open().length, 1);
    }
    for (const action of ['close', 'skip']) {
        mount(1); click(action);
        assert.equal(open().length, 0);
        assert.deepEqual(triggers.at(-1), ['finished', action]);
    }
    mount(1);
    dialogs.at(-1).dispatchEvent(new Event('cancel', { cancelable: true }));
    assert.deepEqual(triggers.at(-1), ['finished', 'escape']);
    assert.equal(open().length, 0);
    mount(3); click('next');
    assert.deepEqual(triggers.at(-1), ['finished', 'finish']);
    mount(3);
    assert.equal(dialogs.at(-1).querySelector('[data-action="feedback"]').hidden, false);
    click('feedback');
    assert.deepEqual(triggers.at(-1), ['finished', 'feedback']);
    assert.equal(open().length, 0);
    mount(3, false);
    assert.equal(dialogs.at(-1).querySelector('[data-action="feedback"]').hidden, true);
    const beforeHiddenClick = triggers.length;
    click('feedback');
    assert.equal(triggers.length, beforeHiddenClick);
    const unmount = mount(0);
    for (const [key, callback] of [...frames]) { frames.delete(key); callback(); }
    assert.equal(dialogs.at(-1).dataset.missing, 'true');
    assert.equal(dialogs.at(-1).querySelector('.tour-warning').textContent, labels.missing);
    assert.equal(dialogs.at(-1).querySelector('.tour-count').textContent, '1 iš 4');
    click('en');
    assert.deepEqual(triggers.at(-1), ['language', 'en']);
    assert.deepEqual(states.at(-1), ['step', 0]);
    const before = triggers.length;
    unmount(); unmount();
    assert.equal(open().length, 0);
    assert.equal(triggers.length, before);
    assert.ok(observers.every(observer => observer.disconnected));
    assert.equal(frames.size, 0);
    return 'Passed: rerenders, Back, cleanup, Close/Skip/Escape/Finish, feedback handoff/suppression, language state, missing target, unmount';
}
