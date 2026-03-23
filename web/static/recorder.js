let mediaRecorder;
let chunks = [];
let recordingBlob = null;

function setStatus(text) {
  const el = document.getElementById("status");
  if (el) el.textContent = text;
}

async function startRecording() {
  chunks = [];
  recordingBlob = null;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Recording not supported in this browser.");
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    // Prefer webm on most browsers
    recordingBlob = new Blob(chunks, { type: "audio/webm" });

    const audio = document.getElementById("playback");
    audio.src = URL.createObjectURL(recordingBlob);
    audio.style.display = "block";

    setStatus("Recording ready. You can upload it.");
  };

  mediaRecorder.start();
  setStatus("Recording...");
  toggleButtons(true);
}

function stopRecording() {
  if (!mediaRecorder) return;

  mediaRecorder.stop();
  setStatus("Stopping...");
  toggleButtons(false);
}

function toggleButtons(isRecording) {
  document.getElementById("startBtn").disabled = isRecording;
  document.getElementById("stopBtn").disabled = !isRecording;
  document.getElementById("uploadBtn").disabled = isRecording; // allow upload after stop
}

async function uploadRecording() {
  if (!recordingBlob) {
    alert("No recording to upload yet.");
    return;
  }

  const title = (document.getElementById("title").value || "").trim();
  const fd = new FormData();
  fd.append("title", title);
  fd.append("audio", recordingBlob, "recording.webm");

  setStatus("Uploading...");

  const res = await fetch("/record/upload", { method: "POST", body: fd });
  if (!res.ok) {
    setStatus("Upload failed.");
    alert("Upload failed. Check server logs.");
    return;
  }

  const data = await res.json();
  setStatus("Uploaded! Saved as: " + data.filename);

  // Go to recordings list
  window.location.href = "/recordings";
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("startBtn").addEventListener("click", startRecording);
  document.getElementById("stopBtn").addEventListener("click", stopRecording);
  document.getElementById("uploadBtn").addEventListener("click", uploadRecording);

  toggleButtons(false);
  document.getElementById("uploadBtn").disabled = true;
  setStatus("Ready.");
});
