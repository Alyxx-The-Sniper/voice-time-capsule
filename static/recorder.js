
// Recording variables
let mediaRecorder, audioChunks = [], recordedBlob = null,
    audioContext, analyser, meterInterval,
    isRecording = false, isPaused = false, isSubmitting = false;

const MIN_SEC = 60;

const toggleBtn   = document.getElementById("toggleBtn"),
      stopBtn     = document.getElementById("stopBtn"),
      submitBtn   = document.getElementById("submitBtn"),
      status      = document.getElementById("status"),
      meterFill   = document.getElementById("meter-fill"),
      progressBar = document.getElementById("progressBar"),
      loadingStatus = document.getElementById("loadingStatus"),
      emailInput  = document.getElementById("email"),
      dateInput   = document.getElementById("deliveryDate");

function startMeter(stream) {
  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const src = audioContext.createMediaStreamSource(stream);
  analyser = audioContext.createAnalyser();
  src.connect(analyser);
  analyser.fftSize = 256;
  meterInterval = setInterval(() => {
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    const avg = data.reduce((a, b) => a + b, 0) / data.length;
    meterFill.style.width = `${Math.min(avg / 256, 1) * 100}%`;
  }, 100);
}

function stopMeter() {
  clearInterval(meterInterval);
  if (audioContext) audioContext.close();
  meterFill.style.width = "0%";
}

// START/PAUSE/RESUME toggle
toggleBtn.addEventListener("click", async () => {
  if (!isRecording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      mediaRecorder = new MediaRecorder(stream, { mimeType: mime });
      audioChunks = [];
      isRecording = true;
      isPaused = false;
      startMeter(stream);

      mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };
      mediaRecorder.onstop = () => {
        stopBtn.disabled = true;
        stopMeter();
        recordedBlob = new Blob(audioChunks, { type: mime });
        status.innerText = recordedBlob.size
          ? "✅ Recording complete — ready to submit"
          : "❌ Recording failed";
        submitBtn.disabled = !recordedBlob.size;
        isRecording = false;
        toggleBtn.innerText = "Start Recording";
        toggleBtn.classList.replace("bg-red-600", "bg-blue-600");
      };

      mediaRecorder.start();
      status.innerText = "🎙️ Recording…";
      toggleBtn.innerText = "Pause";
      toggleBtn.classList.replace("bg-blue-600", "bg-red-600");
      stopBtn.disabled = false;
      submitBtn.disabled = true;
    } catch (err) {
      console.error(err);
      alert("❌ Could not access microphone.");
    }
  } else {
    // Pause or resume
    if (!isPaused) {
      mediaRecorder.pause();
      stopMeter();
      status.innerText = "⏸️ Paused";
      toggleBtn.innerText = "Resume";
    } else {
      mediaRecorder.resume();
      startMeter(mediaRecorder.stream);
      status.innerText = "▶️ Recording…";
      toggleBtn.innerText = "Pause";
    }
    isPaused = !isPaused;
  }
});

// STOP button
stopBtn.addEventListener("click", () => {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    status.innerText = "⏳ Processing…";
    stopBtn.disabled = true;
  }
});

// SUBMIT button and progress bar/status
const steps = [
  "🚀 Initiating quantum uplink...",
  "🧬 Analyzing temporal voice patterns...",
  "🧠 Synthesizing neural echoes...",
  "🔭 Encoding message for time displacement...",
  "🛰️ Dispatching capsule to the future..."
];

const totalDuration = 12000; // 12 seconds for full "loading"
const stepDuration = totalDuration / steps.length;

let fakeInterval, stepTimeouts = [];

submitBtn.addEventListener("click", () => {
  if (isSubmitting) return;
  isSubmitting = true;

  const email = emailInput.value.trim();
  const date  = dateInput.value;
  if (!email || !date) {
    alert("Please enter email & delivery date.");
    isSubmitting = false;
    return;
  }
  if (!recordedBlob || !recordedBlob.size) {
    alert("No recording to submit.");
    isSubmitting = false;
    return;
  }
  const secs = (recordedBlob.size * 8) / 48000;
  if (secs < MIN_SEC) {
    alert("Recording must be at least 60 seconds.");
    isSubmitting = false;
    return;
  }

  submitBtn.disabled = true;
  emailInput.disabled = true;
  dateInput.disabled = true;

  // --- Animate loading bar and steps (fake until upload finishes) ---
  progressBar.style.width = "0%";
  progressBar.classList.remove("bg-green-500", "bg-red-600");
  progressBar.classList.add("bg-blue-400");
  loadingStatus.innerText = steps[0];
  loadingStatus.className = "text-sm text-blue-100 mb-2";

  // Fake progress bar animation
  let startTime = Date.now();
  fakeInterval = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const percent = Math.min(100, (elapsed / totalDuration) * 100);
    progressBar.style.width = percent + "%";
    if (percent >= 100) clearInterval(fakeInterval);
  }, 30);

// Cycle through steps in sync with progress bar
stepTimeouts.forEach(clearTimeout);
stepTimeouts = [];
steps.forEach((step, idx) => {
  stepTimeouts.push(setTimeout(() => {
    loadingStatus.innerText = steps[idx];
    loadingStatus.className = "text-sm font-bold text-blue-100 text-center mb-2";  // <--- add this line
  }, idx * stepDuration));
});

  // Do the upload for real in parallel
  const fd = new FormData();
  fd.append("email", email);
  fd.append("deliveryDate", date);
  fd.append("audio", recordedBlob, "voice.webm");

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/submit", true);

  // When upload finishes, immediately fill the bar & show last step
  xhr.onload = () => {
    isSubmitting = false;
    clearInterval(fakeInterval);
    stepTimeouts.forEach(clearTimeout);
    progressBar.style.width = "100%";
    progressBar.classList.remove("bg-blue-400", "bg-red-600");
    progressBar.classList.add("bg-green-500");
    loadingStatus.innerText = "✅ Submission successful! Check your email. Reloading...";
    loadingStatus.className = "text-xl text-green-500 mb-2";
    setTimeout(() => window.location.reload(), 2500);
  };

  xhr.onerror = () => {
    isSubmitting = false;
    clearInterval(fakeInterval);
    stepTimeouts.forEach(clearTimeout);
    progressBar.style.width = "0%";
    progressBar.classList.remove("bg-blue-400", "bg-green-500");
    progressBar.classList.add("bg-red-600");
    loadingStatus.innerText = "❌ Network error. Please try again.";
    loadingStatus.className = "text-sm text-red-600 mb-2";
    submitBtn.disabled = false;
    emailInput.disabled = false;
    dateInput.disabled = false;
  };

  xhr.send(fd);
});
