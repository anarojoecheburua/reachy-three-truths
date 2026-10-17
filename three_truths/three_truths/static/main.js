// Phone remote for the show. It only sends button presses; the robot
// decides what happens (see show.py) and this page just shows its state.

const LABELS = {
    "01_intro": "Intro",
    "02_round1": "Round 1: about me",
    "03_reveal1": "Reveal 1",
    "04_round2": "Round 2: about robots",
    "05_reveal2": "Reveal 2",
    "06_round3": "Round 3: open source",
    "07_reveal3": "Reveal 3",
    "08_goodbye": "Goodbye",
};
const CLIPS = Object.keys(LABELS);
const STATE_TEXT = {
    asleep: "Asleep",
    playing: "Speaking…",
    waiting: "Ready",
    done: "Show finished",
};
const CONFIRM_MS = 2000;

const $ = (id) => document.getElementById(id);
let last = null;

async function send(cmd) {
    if (navigator.vibrate) navigator.vibrate(30);
    try {
        await fetch(`/command/${cmd}`, { method: "POST" });
    } catch (e) {
        setConnected(false);
    }
    refresh();
}

// SKIP and STOP need a second tap within 2 s, so they can't be hit by accident.
function armOrSend(button) {
    if (button.classList.contains("armed")) {
        button.classList.remove("armed");
        button.textContent = button.dataset.label;
        send(button.dataset.cmd);
        return;
    }
    button.dataset.label = button.textContent;
    button.classList.add("armed");
    button.textContent = "TAP AGAIN";
    setTimeout(() => {
        button.classList.remove("armed");
        button.textContent = button.dataset.label;
    }, CONFIRM_MS);
}

document.querySelectorAll("button[data-cmd]").forEach((b) => {
    b.addEventListener("click", () => ("confirm" in b.dataset ? armOrSend(b) : send(b.dataset.cmd)));
});

function setConnected(ok) {
    $("conn").className = ok ? "ok" : "lost";
    if (!ok) $("state").textContent = "No connection";
}

function render(s) {
    const started = s.step >= 0;
    const nextClip = s.state === "done" ? null : CLIPS[s.step + 1];

    $("state").textContent = STATE_TEXT[s.state] ?? s.state;
    $("state").className = `pill ${s.state}`;
    $("progress").textContent = started ? `${s.step + 1} / ${s.total}` : "";
    $("current").textContent = started ? LABELS[s.clip] : "Three Truths and a Lie";
    $("upnext").textContent = nextClip ? `NEXT plays: ${LABELS[nextClip]}` : "";

    // Mirror the robot's rules so Ana can see what will work right now.
    const busy = s.state === "playing" || s.state === "done";
    $("next").disabled = busy || !nextClip;
    document.querySelector('[data-cmd="back"]').disabled = busy || !started;
    document.querySelector('[data-cmd="repeat"]').disabled = busy || !started;
    document.querySelector('[data-cmd="skip_to_goodbye"]').disabled = busy || !started;
    document.querySelector('[data-cmd="stop"]').disabled = s.state === "asleep" || s.state === "done";
}

async function refresh() {
    try {
        const resp = await fetch("/state", { cache: "no-store" });
        last = await resp.json();
        setConnected(true);
        render(last);
    } catch (e) {
        setConnected(false);
    }
}

async function showAddress() {
    try {
        const info = await (await fetch("/info")).json();
        $("address").textContent = info.ip ? `Robot: http://${info.ip}:${info.port}` : "";
    } catch (e) { /* not important */ }
}

showAddress();
refresh();
setInterval(refresh, 500);
