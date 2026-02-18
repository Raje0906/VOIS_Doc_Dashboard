// Dashboard State
let currentTab = 'patients';
let currentPrescriptionAnalysis = '';
let currentPatientName = '';

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    switchTab('patients');
});

// Tab Switching
function switchTab(tabId) {
    // Update UI
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    document.querySelector(`button[data-tab="${tabId}"]`).classList.add('active');

    currentTab = tabId;

    // Load Data
    if (tabId === 'patients') loadPatients();
    if (tabId === 'calendar') {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('manage-date').value = today;
        loaddocSlots();
    }
}

// --- Patient Logic ---
function loadPatients() {
    const list = document.getElementById('patient-list-container');
    list.innerHTML = '<div class="loading">Loading records...</div>';

    fetch('/api/patients')
        .then(res => res.json())
        .then(data => {
            list.innerHTML = '';
            data.forEach(patient => {
                const card = document.createElement('div');
                card.className = 'patient-card';
                card.innerHTML = `
                    <h3>${patient.name}</h3>
                    <p>ID: ${patient.id} | Age: ${patient.age}</p>
                    <p>Last Visit: ${patient.last_visit}</p>
                `;
                card.onclick = () => showPatientDetails(patient.id);
                list.appendChild(card);
            });
        })
        .catch(err => {
            list.innerHTML = '<div class="error">Failed to load patients.</div>';
            console.error(err);
        });
}

function showPatientDetails(id) {
    fetch(`/api/patients/${id}/history`)
        .then(res => res.json())
        .then(patient => {
            document.getElementById('modal-patient-name').innerText = patient.name;
            document.getElementById('modal-patient-age').innerText = patient.age;
            document.getElementById('modal-patient-visit').innerText = patient.last_visit;
            document.getElementById('modal-patient-history').innerText = patient.history;

            document.getElementById('patient-modal').style.display = 'block';
        });
}

function closeModal() {
    document.getElementById('patient-modal').style.display = 'none';
}

// --- AI Chat Logic ---
function handleEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

function sendMessage() {
    const input = document.getElementById('chat-input-box');
    const history = document.getElementById('chat-history');
    const msg = input.value.trim();

    if (!msg) return;

    // Add User Message
    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerText = msg;
    history.appendChild(userDiv);

    input.value = '';
    history.scrollTop = history.scrollHeight;

    // Loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai';
    loadingDiv.innerText = 'Thinking...';
    history.appendChild(loadingDiv);

    fetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    })
        .then(res => res.json())
        .then(data => {
            history.removeChild(loadingDiv);
            const aiDiv = document.createElement('div');
            aiDiv.className = 'message ai';
            aiDiv.innerText = data.response;
            history.appendChild(aiDiv);
            history.scrollTop = history.scrollHeight;
        })
        .catch(err => {
            loadingDiv.innerText = 'Error: Could not reach AI agent.';
            console.error(err);
        });
}

// --- Prescription Review Logic ---
function analyzePrescription() {
    const text = document.getElementById('rx-text').value;
    const resultBox = document.getElementById('rx-analysis-result');
    const btn = document.getElementById('download-pdf-btn');

    if (!text.trim()) return alert("Please enter prescription details.");

    resultBox.innerText = "Analyzing interactions and safety protocols...";
    btn.disabled = true;

    fetch('/api/prescription/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prescription_text: text })
    })
        .then(res => res.json())
        .then(data => {
            currentPrescriptionAnalysis = data.analysis;
            resultBox.innerText = data.analysis;
            btn.disabled = false;
        })
        .catch(err => {
            resultBox.innerText = "Analysis failed.";
            console.error(err);
        });
}

// Global variables
let currentMedicineRec = '';

function getMedicineRecommendations() {
    const condition = document.getElementById('med-condition').value;
    const resultBox = document.getElementById('med-recommendations');
    const btn = document.getElementById('download-med-pdf-btn');

    if (!condition.trim()) return alert("Enter a condition.");

    resultBox.innerText = "Consulting AI...";
    if (btn) btn.disabled = true;

    fetch('/api/medicine/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ condition: condition })
    })
        .then(res => res.json())
        .then(data => {
            currentMedicineRec = data.recommendations;
            resultBox.innerText = data.recommendations;
            if (btn) btn.disabled = false;
        })
        .catch(err => {
            resultBox.innerText = "Failed to get recommendations.";
            console.error(err);
        });
}

function downloadMedicinePDF() {
    const condition = document.getElementById('med-condition').value;

    if (!currentMedicineRec) return alert("No recommendation to download.");

    fetch('/api/medicine/generate_pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            condition: condition,
            recommendation: currentMedicineRec
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.pdf_url) {
                window.open(data.pdf_url, '_blank');
            } else {
                alert("Failed to generate PDF");
            }
        });
}

// Previously unused download logic (removed)


// --- Calendar Management Logic ---
function loaddocSlots() {
    const date = document.getElementById('manage-date').value;
    const containerMorning = document.getElementById('slots-morning');
    const containerEvening = document.getElementById('slots-evening');

    if (!date) return;

    if (containerMorning) containerMorning.innerHTML = 'Loading...';
    if (containerEvening) containerEvening.innerHTML = 'Loading...';

    fetch(`/api/calendar/manage/status?date=${date}`)
        .then(res => res.json())
        .then(statusMap => {
            if (containerMorning) containerMorning.innerHTML = '';
            if (containerEvening) containerEvening.innerHTML = '';

            if (statusMap.error) {
                if (containerMorning) containerMorning.innerHTML = `<p class="error">${statusMap.error}</p>`;
                return;
            }

            // sort keys to ensure order
            const sortedTimes = Object.keys(statusMap).sort();

            sortedTimes.forEach(time => {
                const slotData = statusMap[time]; // { status, details }
                const status = slotData.status; // 'available', 'booked', 'blocked'
                const details = slotData.details;

                const card = document.createElement('div');
                card.className = `slot-card ${status}`;

                let actionBtn = '';
                let detailsHtml = '';

                if (status === 'available') {
                    actionBtn = `<button onclick="toggleSlot('${date}', '${time}', 'block')">Mark Unavailable</button>`;
                } else if (status === 'blocked') {
                    actionBtn = `<button onclick="toggleSlot('${date}', '${time}', 'unblock')">Mark Available</button>`;
                } else if (status === 'booked') {
                    // Show patient name if available, else just 'Booked'
                    const patientName = details || 'Unknown Patient';
                    detailsHtml = `<div class="patient-name">${patientName}</div>`;
                    actionBtn = `<span>Booked</span>`;
                }

                card.innerHTML = `
                    <div class="slot-time">${time}</div>
                    ${detailsHtml}
                    <div class="slot-status">${status.toUpperCase()}</div>
                    <div class="slot-action">${actionBtn}</div>
                `;

                // Determine Morning vs Evening
                const hour = parseInt(time.split(':')[0]);
                if (containerMorning && containerEvening) {
                    if (hour < 14) {
                        containerMorning.appendChild(card);
                    } else {
                        containerEvening.appendChild(card);
                    }
                }
            });

            if (containerMorning && containerMorning.children.length === 0) containerMorning.innerHTML = '<p>No morning slots.</p>';
            if (containerEvening && containerEvening.children.length === 0) containerEvening.innerHTML = '<p>No evening slots.</p>';
        })
        .catch(err => {
            console.error(err);
            if (containerMorning) containerMorning.innerHTML = '<p>Error loading slots.</p>';
        });
}

function toggleSlot(date, time, action) {
    fetch('/api/calendar/manage/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, time, action })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                loaddocSlots(); // Refresh UI
            } else {
                alert("Failed: " + data.message);
            }
        });
}


function fetchSlots() {
    const date = document.getElementById('booking-date').value;
    const select = document.getElementById('booking-slot');

    if (!date) {
        select.innerHTML = '<option value="">Select a date first</option>';
        return;
    }

    select.innerHTML = '<option>Loading...</option>';
    select.disabled = true;

    fetch(`/api/calendar/slots?date=${date}`)
        .then(res => res.json())
        .then(slots => {
            select.innerHTML = '';
            if (slots.length === 0) {
                select.innerHTML = '<option value="">No slots available</option>';
            } else {
                slots.forEach(slot => {
                    const opt = document.createElement('option');
                    opt.value = slot;
                    opt.innerText = slot;
                    select.appendChild(opt);
                });
            }
            select.disabled = false;
        })
        .catch(err => {
            console.error(err);
            select.innerHTML = '<option>Error loading slots</option>';
        });
}

function bookSlot() {
    const date = document.getElementById('booking-date').value;
    const slot = document.getElementById('booking-slot').value;

    if (!date || !slot) return alert("Select a date and time slot.");

    // Combine date and time
    const start_time = `${date}T${slot}:00`;

    fetch('/api/calendar/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            start_time: start_time,
            summary: "Patient Consultation (Booked via Dashboard)"
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Appointment Booked!');
                fetchEvents();
                // Clear selection
                document.getElementById('booking-slot').value = '';
                fetchSlots(); // Refresh slots to remove the booked one (if we had real-time refresh)
            } else {
                alert('Booking failed: ' + data.message);
            }
        });
}

// Close modal when clicking outside
window.onclick = function (event) {
    if (event.target == document.getElementById('patient-modal')) {
        closeModal();
    }
}
