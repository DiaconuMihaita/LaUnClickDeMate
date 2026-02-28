// Statul aplicației (frontend)
let localChapters = [];
let lastChapterId = null;
let visitedChapters = [];
let sessionScore = { correct: 0, total: 0 };
let currentUser = JSON.parse(localStorage.getItem('mateai_user')) || null;
let authMode = 'login'; // login sau register
let ttsEnabled = localStorage.getItem('mateai_tts_enabled') !== 'false';

// --- PERSISTENT PROGRESS (LocalStorage - Fallback) ---
let userProgress = JSON.parse(localStorage.getItem('mateai_progress')) || {
    chaptersExplored: [],
    exercisesCorrect: 0,
    badges: [],
    lastChallengeDate: null,
    dailyLog: [],
    chapterScores: {}
};

function saveProgress() {
    localStorage.setItem('mateai_progress', JSON.stringify(userProgress));
}

// --- DAILY PROGRESS LOGGING ---
function logDailyProgress(isCorrect, chapterId) {
    const today = new Date().toISOString().slice(0, 10);
    if (!userProgress.dailyLog) userProgress.dailyLog = [];
    let entry = userProgress.dailyLog.find(e => e.date === today);
    if (!entry) {
        entry = { date: today, correct: 0, total: 0 };
        userProgress.dailyLog.push(entry);
    }
    entry.total++;
    if (isCorrect) entry.correct++;

    // Track per-chapter scores for adaptive difficulty
    if (chapterId) {
        if (!userProgress.chapterScores) userProgress.chapterScores = {};
        if (!userProgress.chapterScores[chapterId]) {
            userProgress.chapterScores[chapterId] = { correct: 0, total: 0 };
        }
        userProgress.chapterScores[chapterId].total++;
        if (isCorrect) userProgress.chapterScores[chapterId].correct++;
    }
    saveProgress();
}

// --- CONFETTI ANIMATION ---
function launchConfetti() {
    if (typeof confetti === 'function') {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        });
    }
}

// F1 — Starea quiz activ
let quizState = { active: false, exercise: '', correctAnswer: '', chapterId: '' };
let currentDailyChallenge = null;

// --- FUNDAL INTERACTIV (Math Neural Background) ---
function initBackground() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let width, height;
    let particles = [];
    const symbols = ['+', '-', '×', '÷', '=', '√', 'π', '∑', '∞', 'x', 'y', 'z', 'Δ', '∫', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '±', '≠', '≤', '≥', '^', '√', 'α', 'β', 'γ', 'θ'];
    const equations = [
        'a²+b²=c²', 'E=mc²', 'x+y=z', '2+2=4', 'πr²', 'A=bh/2', 'x=(-b±√D)/2a',
        'sin²θ+cos²θ=1', 'F=ma', 'V=IR', 'd=vt', 'P=IV', 'log(ab)=log a+log b'
    ];
    const colors = ['#4F6AF5', '#7C3AED', '#FF9F43', '#A855F7', '#34C759', '#6366F1'];

    const mouse = { x: -2000, y: -2000 };

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }

    class Particle {
        constructor(isEquation = false) {
            this.isEquation = isEquation;
            this.reset();
        }

        reset() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.text = this.isEquation
                ? equations[Math.floor(Math.random() * equations.length)]
                : symbols[Math.floor(Math.random() * symbols.length)];

            this.size = this.isEquation ? (Math.random() * 8 + 12) : (Math.random() * 12 + 10);
            this.speedX = (Math.random() - 0.5) * 0.35;
            this.speedY = (Math.random() - 0.5) * 0.35;
            this.opacity = Math.random() * 0.4 + 0.05; // Slightly more variation
            this.baseOpacity = this.opacity;
            this.color = colors[Math.floor(Math.random() * colors.length)];
            this.angle = Math.random() * Math.PI * 2;
            this.spin = (Math.random() - 0.5) * 0.005;
            this.glow = Math.random() > 0.7;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.angle += this.spin;

            // Smooth interaction with mouse
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 250) {
                const force = (250 - dist) / 250;
                this.x += dx * force * 0.02;
                this.y += dy * force * 0.02;
                this.opacity = Math.min(0.7, this.baseOpacity + force * 0.5);
            } else {
                this.opacity = this.baseOpacity;
            }

            // Wrap around Screen
            if (this.x < -100) this.x = width + 100;
            if (this.x > width + 100) this.x = -100;
            if (this.y < -100) this.y = height + 100;
            if (this.y > height + 100) this.y = -100;
        }

        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.angle);

            if (this.glow) {
                ctx.shadowBlur = 12;
                ctx.shadowColor = this.color;
            }

            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.opacity;
            ctx.font = `${this.isEquation ? 'bold ' : ''}${this.size}px "Fredoka One", cursive`;
            ctx.fillText(this.text, 0, 0);
            ctx.restore();
        }
    }

    function drawLines() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 140) { // Slightly tighter lines for the denser background
                    const opacity = (140 - dist) / 140 * 0.12;
                    ctx.beginPath();
                    ctx.strokeStyle = p1.color;
                    ctx.globalAlpha = opacity;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
    }

    function init() {
        resize();
        particles = [];
        // More symbols (Density boost)
        for (let i = 0; i < 110; i++) {
            particles.push(new Particle(false));
        }
        // Rare equations (Density boost)
        for (let i = 0; i < 15; i++) {
            particles.push(new Particle(true));
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        drawLines();
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    init();
    animate();
}

// ---------------------------------------------------------
// --- 🌟 PREMIUM FEATURES (Ultimate Evolution) ---
// ---------------------------------------------------------

// 1. PROVOCAREA ZILEI (Daily Challenge)
async function fetchDailyChallenge() {
    const today = new Date().toDateString();
    const card = document.getElementById('daily-challenge-card');

    // Dacă utilizatorul a rezolvat deja azi, arătăm feedback direct
    if (userProgress.lastChallengeDate === today) {
        card.classList.remove('hidden');
        document.getElementById('challenge-question').innerHTML = "🌟 Ai rezolvat deja provocarea de azi! Revino mâine pentru una nouă.";
        document.querySelector('#daily-challenge-card .input-group').style.display = 'none';
        return;
    }

    try {
        const response = await fetch('/api/daily-challenge');
        currentDailyChallenge = await response.json();

        document.getElementById('challenge-question').innerText = currentDailyChallenge.question;
        card.classList.remove('hidden');
        document.querySelector('#daily-challenge-card .input-group').style.display = 'flex';
        document.getElementById('challenge-feedback').innerText = '';
    } catch (e) {
        console.error("Eroare la încărcarea provocării:", e);
    }
}

document.getElementById('btn-challenge-submit').addEventListener('click', () => {
    const userInput = document.getElementById('challenge-answer').value.trim();
    const feedback = document.getElementById('challenge-feedback');

    if (userInput === currentDailyChallenge.answer) {
        feedback.innerHTML = "🎉 Corect! Ai câștigat 10 puncte de experiență!";
        feedback.style.color = "var(--accent-green)";
        userProgress.lastChallengeDate = new Date().toDateString();
        userProgress.exercisesCorrect += 1;
        checkBadges();
        saveProgress();
        launchConfetti();
        setTimeout(() => fetchDailyChallenge(), 2000);
    } else {
        feedback.innerHTML = `❌ Mai încearcă! Indiciu: ${currentDailyChallenge.hint}`;
        feedback.style.color = "#FF4757";
    }
});

// 2. VOX MATEAI (Voice Assistant)
function initVoiceAssistant() {
    const micBtn = document.getElementById('btn-chat-mic');
    const input = document.getElementById('chat-input');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        micBtn.style.display = 'none';
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'ro-RO';
    recognition.interimResults = false;

    micBtn.addEventListener('click', () => {
        micBtn.innerText = 'Listening...';
        micBtn.style.background = 'var(--primary-500)';
        recognition.start();
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        micBtn.innerText = '🎤';
        micBtn.style.background = 'var(--bg-glass-heavy)';
        sendMessage(); // Trimite automat mesajul vocal
    };

    recognition.onerror = () => {
        micBtn.innerText = '🎤';
        micBtn.style.background = 'var(--bg-glass-heavy)';
    };
}

// Funcție pentru TTS (Text-to-Speech)
function speak(text) {
    if (!ttsEnabled || !('speechSynthesis' in window)) return;

    const cleanText = (text || '').replace(/<[^>]*>/g, '').trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'ro-RO';

    const voices = speechSynthesis.getVoices();
    const roVoice = voices.find(v => (v.lang || '').toLowerCase().startsWith('ro'));
    if (roVoice) utterance.voice = roVoice;

    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
}

function initTtsControls() {
    const toggleBtn = document.getElementById('btn-tts-toggle');
    const stopBtn = document.getElementById('btn-tts-stop');
    if (!toggleBtn || !stopBtn) return;

    const refreshToggleLabel = () => {
        toggleBtn.textContent = ttsEnabled ? '🔊 ON' : '🔇 OFF';
    };

    refreshToggleLabel();

    toggleBtn.addEventListener('click', () => {
        ttsEnabled = !ttsEnabled;
        localStorage.setItem('mateai_tts_enabled', String(ttsEnabled));
        if (!ttsEnabled && 'speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        refreshToggleLabel();
    });

    stopBtn.addEventListener('click', () => {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
    });
}

// 3. GAMIFICATION & DASHBOARD
function checkBadges() {
    const badges = [
        { id: 'first_step', name: '👣 Primul Pas', criteria: userProgress.chaptersExplored.length >= 1 },
        { id: 'explorer', name: '🧭 Explorator', criteria: userProgress.chaptersExplored.length >= 5 },
        { id: 'master', name: '🎓 Maestrul Cifrelor', criteria: userProgress.chaptersExplored.length >= 22 },
        { id: 'smart', name: '🧠 Micul Geniu', criteria: userProgress.exercisesCorrect >= 10 }
    ];

    badges.forEach(b => {
        if (b.criteria && !userProgress.badges.includes(b.name)) {
            userProgress.badges.push(b.name);
            alert(`🏆 Nouă insignă câștigată: ${b.name}!`);
        }
    });
}

function renderProfile() {
    document.getElementById('stat-chapters').innerText = `${userProgress.chaptersExplored.length}/22`;
    document.getElementById('stat-exercises').innerText = userProgress.exercisesCorrect;

    const badgeList = document.getElementById('badge-list');
    badgeList.innerHTML = userProgress.badges.length > 0
        ? userProgress.badges.map(b => `<div class="badge" style="background: var(--grad-primary); padding: 8px 15px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;">${b}</div>`).join('')
        : "<p style='color: var(--text-500); font-size: 0.9rem;'>Nu ai încă insigne. Începe să înveți!</p>";

    renderProgressChart();
}

// --- PROGRESS CHART (Chart.js) ---
let progressChartInstance = null;

async function renderProgressChart() {
    const ctx = document.getElementById('progress-chart');
    if (!ctx) return;

    let labels = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică'];
    let data = [0, 0, 0, 0, 0, 0, 0];

    // Dacă utilizatorul e logat, luăm datele de pe server
    if (currentUser && currentUser.token) {
        try {
            const res = await fetch('/api/stats/daily', {
                headers: { 'Authorization': currentUser.token }
            });
            const resData = await res.json();
            if (resData.success && resData.activity.length > 0) {
                // Mapăm ultimele 7 zile
                labels = resData.activity.map(a => a.date.split('-').slice(1).reverse().join('.'));
                data = resData.activity.map(a => a.count);
            }
        } catch (e) {
            console.error("Eroare chart:", e);
        }
    }

    if (progressChartInstance) progressChartInstance.destroy();

    progressChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Exerciții rezolvate',
                data: data,
                borderColor: '#6366F1',
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#6366F1',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

// 4. LABORATOR GEOMETRIE (Geometry Lab)
var geoLab = {
    canvas: null,
    ctx: null,
    shape: 'manual',
    isDrawing: false,
    color: '#6366F1',
    initialized: false,
    points: [], // For recognition

    init() {
        if (this.initialized) return;
        this.canvas = document.getElementById('geo-canvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.dragDrawing(e));
        this.canvas.addEventListener('mouseup', () => this.stopDrawing());
        this.canvas.addEventListener('mouseleave', () => this.stopDrawing());

        this.initialized = true;
        this.draw();
    },

    startDrawing(e) {
        if (this.shape !== 'manual') return;
        this.isDrawing = true;
        this.points = [];
        this.ctx.beginPath();
        this.ctx.moveTo(e.offsetX, e.offsetY);
        this.points.push({ x: e.offsetX, y: e.offsetY });
    },

    dragDrawing(e) {
        if (!this.isDrawing || this.shape !== 'manual') return;
        this.ctx.lineTo(e.offsetX, e.offsetY);
        this.ctx.strokeStyle = this.color;
        this.ctx.lineWidth = 4;
        this.ctx.stroke();
        this.points.push({ x: e.offsetX, y: e.offsetY });
    },

    stopDrawing() {
        this.isDrawing = false;
    },

    setShape(s) {
        this.shape = s;
        // Toggle input groups
        document.getElementById('group-rect').classList.toggle('hidden', s !== 'rect');
        document.getElementById('group-side').classList.toggle('hidden', s === 'rect' || s === 'manual');

        if (s !== 'manual') {
            this.draw();
        }
    },

    updateFromInputs() {
        if (this.shape !== 'manual') {
            this.draw();
        }
    },

    clear() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.shape = 'manual';
        this.points = [];
        document.getElementById('geo-stats').innerHTML = '📐 Planșă curățată. Poți desena liber!';
    },

    recognizeShape() {
        if (this.points.length < 15) {
            alert("🪄 Desenează o formă mai clară!");
            return;
        }

        // --- CALIBRATION: Point Resampling ---
        const filtered = [this.points[0]];
        for (let i = 1; i < this.points.length; i++) {
            const p1 = filtered[filtered.length - 1];
            const p2 = this.points[i];
            const dist = Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2);
            if (dist > 4) filtered.push(p2);
        }
        this.points = filtered;

        // Calculate bounding box
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        this.points.forEach(p => {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.y > maxY) maxY = p.y;
        });

        const width = maxX - minX;
        const height = maxY - minY;
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        // --- CALIBRATION: Refined Heuristics ---
        const radius = (width + height) / 4;
        let distVar = 0;
        this.points.forEach(p => {
            const d = Math.sqrt((p.x - centerX) ** 2 + (p.y - centerY) ** 2);
            distVar += Math.abs(d - radius);
        });
        const circularity = distVar / this.points.length;

        // Threshold 0.12 is much stricter - prevents squares (var ~0.16) from being circles (var ~0.05)
        if (circularity < radius * 0.12) {
            this.shape = 'circle';
            document.getElementById('input-l').value = Math.round(radius);
        } else {
            const aspect = width / height;
            // Square logic: 0.8 to 1.25 is a reasonable hand-drawn square
            if (aspect > 0.8 && aspect < 1.25) {
                this.shape = 'square';
                document.getElementById('input-l').value = Math.round((width + height) / 2);
            } else {
                this.shape = 'rect';
                document.getElementById('input-w').value = Math.round(width);
                document.getElementById('input-h').value = Math.round(height);
            }
        }

        this.setShape(this.shape);
        this.draw();

        // --- CALIBRATION: Precision Feedback ---
        this.ctx.save();
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([8, 4]);

        // Draw the precise detection box
        this.ctx.beginPath();
        this.ctx.strokeRect(minX, minY, width, height);

        // Add "magic sparkles" at the corners for better alignment feel
        const corners = [[minX, minY], [maxX, minY], [minX, maxY], [maxX, maxY]];
        corners.forEach(c => {
            this.ctx.fillStyle = '#6EE7B7'; // Mint sparkle
            this.ctx.beginPath();
            this.ctx.arc(c[0], c[1], 4, 0, Math.PI * 2);
            this.ctx.fill();
        });

        this.ctx.restore();

        // Feedback persists for 700ms to be noticeable
        setTimeout(() => this.draw(), 700);
    },

    draw() {
        if (!this.ctx || this.shape === 'manual') return;
        const ctx = this.ctx;
        const w_canvas = this.canvas.width;
        const h_canvas = this.canvas.height;
        ctx.clearRect(0, 0, w_canvas, h_canvas);

        ctx.strokeStyle = this.color;
        ctx.lineWidth = 5;
        ctx.fillStyle = 'rgba(99, 102, 241, 0.2)';

        ctx.beginPath();
        let area = 0, perim = 0, formula = "";

        if (this.shape === 'square') {
            const s = parseInt(document.getElementById('input-l').value) || 100;
            ctx.rect(w_canvas / 2 - s / 2, h_canvas / 2 - s / 2, s, s);
            area = s * s;
            perim = 4 * s;
            formula = `A = l² = ${s}² = ${area} | P = 4l = 4·${s} = ${perim}`;
        } else if (this.shape === 'rect') {
            const w = parseInt(document.getElementById('input-w').value) || 150;
            const h = parseInt(document.getElementById('input-h').value) || 80;
            ctx.rect(w_canvas / 2 - w / 2, h_canvas / 2 - h / 2, w, h);
            area = w * h;
            perim = 2 * (w + h);
            formula = `A = L·l = ${w}·${h} = ${area} | P = 2(L+l) = 2(${w}+${h}) = ${perim}`;
        } else if (this.shape === 'circle') {
            const r = parseInt(document.getElementById('input-l').value) || 60;
            ctx.arc(w_canvas / 2, h_canvas / 2, r, 0, Math.PI * 2);
            area = Math.round(Math.PI * r * r);
            perim = Math.round(2 * Math.PI * r);
            formula = `A = πr² ≈ 3.14·${r}² = ${area} | P = 2πr ≈ 2·3.14·${r} = ${perim}`;
        }

        ctx.fill();
        ctx.stroke();

        document.getElementById('geo-stats').innerHTML = `
            <div style="font-size: 1.1rem; color: var(--accent-orange); margin-bottom: 5px;">📐 Formă: ${this.shape.toUpperCase()}</div>
            <div style="font-family: 'Courier New', monospace; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 5px;">${formula}</div>
        `;
    }
};

// Gestionare Vizualizare
function changeView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(viewId);
    if (target) {
        target.classList.remove('hidden');
        window.scrollTo(0, 0);
    }

    if (viewId === 'profil') renderProfile();
    if (viewId === 'clasa') updateClassroomUI();
    if (viewId === 'login') updateAuthUI();

    // Update nav active state
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('data-section') === viewId) {
            link.style.color = 'var(--primary-400)';
            link.style.borderBottom = '2px solid var(--primary-400)';
        } else {
            link.style.color = '';
            link.style.borderBottom = '';
        }
    });

    if (viewId === 'lectii') renderChapters();
    if (viewId === 'laborator') geoLab.init();
    if (viewId === 'home') fetchDailyChallenge();
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        changeView(link.getAttribute('data-section'));
    });
});

// --- API FETCH ---
async function loadChapters() {
    try {
        const res = await fetch('/api/chapters');
        localChapters = await res.json();
        renderChapters();
    } catch (e) {
        console.error("Eroare la încărcarea capitolelor:", e);
    }
}

function renderChapters() {
    const list = document.getElementById('chapter-list');
    if (!list) return;
    list.innerHTML = '';
    localChapters.forEach(ch => {
        const card = document.createElement('div');
        card.className = 'chapter-card';
        card.innerHTML = `
            <div style="font-size: 2rem;">${ch.icon}</div>
            <h3>${ch.title}</h3>
        `;
        card.onclick = () => showChapterDetail(ch.id);
        list.appendChild(card);
    });
}

function showChapterDetail(chId) {
    const ch = localChapters.find(c => c.id === chId);
    if (!ch) return;

    changeView('chapter-detail');
    const container = document.getElementById('detail-content');

    const lessonsHtml = "<ul>" + ch.lessons.map(l => `<li>${l}</li>`).join('') + "</ul>";
    const examplesHtml = "<ul>" + ch.examples.map(ex => `<li><em>${ex}</em></li>`).join('') + "</ul>";

    let exercisesHtml = "";
    if (ch.exercises && ch.exercises.length > 0) {
        exercisesHtml = `
            <div class="lesson-node">
                <h4>Exerciții Propuse</h4>
                <ul>${ch.exercises.map(ex => `<li>${typeof ex === 'object' ? ex.question : ex}</li>`).join('')}</ul>
            </div>
        `;
    }

    let dictHtml = "";
    if (ch.dictionary) {
        const terms = Object.entries(ch.dictionary).map(([term, def]) => `<li><strong>${term}:</strong> ${def}</li>`).join('');
        dictHtml = `
            <div class="lesson-node">
                <h4>Dicționar de Termeni</h4>
                <ul>${terms}</ul>
            </div>
        `;
    }

    let funHtml = "";
    if (ch.fun_facts && ch.fun_facts.length > 0) {
        funHtml = `
            <div class="lesson-node">
                <h4>Știai că?</h4>
                <ul>${ch.fun_facts.map(f => `<li>${f}</li>`).join('')}</ul>
            </div>
        `;
    }

    container.innerHTML = `
        <h2>${ch.icon} ${ch.title}</h2>
        <div class="lesson-node">
            <h4>Curriculă Capitol</h4>
            ${lessonsHtml}
        </div>
        <div class="lesson-node">
            <h4>Exemple Relevante</h4>
            ${examplesHtml}
        </div>
        ${dictHtml}
        ${exercisesHtml}
        ${funHtml}
    `;
}

// --- F2: SCOR UI ---
function updateScoreUI() {
    const counter = document.getElementById('score-counter');
    const scoreText = document.getElementById('score-text');
    if (!counter || !scoreText) return;

    if (sessionScore.total === 0) {
        counter.classList.add('hidden');
        return;
    }
    counter.classList.remove('hidden');
    scoreText.textContent = `${sessionScore.correct}/${sessionScore.total} corecte`;

    const ratio = sessionScore.correct / sessionScore.total;
    counter.className = 'score-counter';
    if (ratio >= 0.7) counter.classList.add('score-good');
    else if (ratio >= 0.4) counter.classList.add('score-medium');
    else counter.classList.add('score-bad');
}

// --- CHAT LOGIC ---
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const btnChatSend = document.getElementById('btn-chat-send');
const aiTyping = document.getElementById('ai-typing');

function addMessage(text, sender, extraClass = '') {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message ${extraClass}`;
    msgDiv.innerHTML = text;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
}

// F4 — Buton sugestie capitol următor
function renderSuggestionButton(suggestion) {
    const area = document.getElementById('suggestion-area');
    if (!area || !suggestion) { if (area) area.innerHTML = ''; return; }
    area.innerHTML = `
        <button class="suggestion-btn" onclick="askAboutChapter('${suggestion.id}', '${suggestion.title}')">
            ${suggestion.icon} Continuă cu: ${suggestion.title} →
        </button>
    `;
}

function askAboutChapter(chapterId, chapterTitle) {
    chatInput.value = `explică-mi ${chapterTitle}`;
    document.getElementById('suggestion-area').innerHTML = '';
    handleChat();
}

// F1 — Afișare input răspuns quiz
function renderQuizInput(exercise, correctAnswer, chapterId) {
    quizState = { active: true, exercise, correctAnswer, chapterId };
    const area = document.getElementById('quiz-answer-area');
    if (!area) return;
    area.innerHTML = `
        <div class="quiz-input-box">
            <input type="text" id="quiz-answer-input" placeholder="Scrie răspunsul tău aici..." autocomplete="off">
            <button id="btn-quiz-submit" onclick="submitQuizAnswer()">✔ Verifică</button>
        </div>
    `;
    const inp = document.getElementById('quiz-answer-input');
    if (inp) {
        inp.focus();
        inp.addEventListener('keypress', e => { if (e.key === 'Enter') submitQuizAnswer(); });
    }
}

async function submitQuizAnswer() {
    if (!quizState.active) return;
    const answerInput = document.getElementById('quiz-answer-input');
    if (!answerInput) return;
    const userAnswer = answerInput.value.trim();
    if (!userAnswer) return;

    addMessage(userAnswer, 'user');
    document.getElementById('quiz-answer-area').innerHTML = '';
    quizState.active = false;

    sessionScore.total++;
    updateScoreUI();

    try {
        const res = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userAnswer,
                correctAnswer: quizState.correctAnswer,
                chapterId: quizState.chapterId
            })
        });
        const data = await res.json();

        if (data.isCorrect) { sessionScore.correct++; launchConfetti(); }
        logDailyProgress(data.isCorrect, quizState.chapterId);
        updateScoreUI();

        const cls = data.isCorrect ? 'feedback-correct' : 'feedback-wrong';
        addMessage(data.feedback, 'ai', cls);
    } catch (e) {
        addMessage("Nu am putut verifica răspunsul. Încearcă din nou!", 'ai');
    }
}

async function handleChat() {
    const input = chatInput.value.trim();
    const level = document.querySelector('input[name="level"]:checked')?.value || 'simple';
    if (!input) return;

    // Dacă e activ quiz, nu trimite ca mesaj normal
    if (quizState.active) {
        submitQuizAnswer();
        return;
    }

    addMessage(input, 'user');
    chatInput.value = '';
    document.getElementById('suggestion-area').innerHTML = '';
    document.getElementById('quiz-answer-area').innerHTML = '';

    aiTyping.classList.remove('hidden');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                input,
                level,
                lastChapterId,
                visitedChapters  // F3
            })
        });

        const data = await response.json();
        aiTyping.classList.add('hidden');
        // Afișează mesajul
        addMessage(data.message, 'ai'); // Fixed: changed 'ai-message' to 'ai'
        speak(data.message); // --- VOICE ASSISTANT (TTS) ---

        // Actualizează starea
        if (data.lastChapterId) {
            lastChapterId = data.lastChapterId;
            // F3 — Adaugă la istoricul vizitat (Recap)
            if (!visitedChapters.includes(lastChapterId)) {
                visitedChapters.push(lastChapterId);
            }

            // --- PROGRESS TRACKING ---
            if (!userProgress.chaptersExplored.includes(lastChapterId)) {
                userProgress.chaptersExplored.push(lastChapterId);
                checkBadges();
                saveProgress();
            }
        }

        // F4 — Sugestie capitol următor
        if (data.suggestion) renderSuggestionButton(data.suggestion);

        // F1 — Quiz activ
        if (data.quizMode) renderQuizInput(data.exercise, data.correctAnswer, data.chapterId);

    } catch (e) {
        aiTyping.classList.add('hidden');
        addMessage("Sunt ocupat acum, te rog revino!", 'ai');
    }
}

btnChatSend.addEventListener('click', handleChat);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleChat();
});

// --- MANUAL EXERCISE SOLVER ---
document.getElementById('btn-solve').addEventListener('click', async () => {
    const rawInput = document.getElementById('exercise-input').value;
    const studentAnswer = document.getElementById('student-answer').value.trim();
    const resultBox = document.getElementById('exercise-result');

    if (!rawInput.trim()) return;

    resultBox.classList.remove('hidden');
    resultBox.innerHTML = "Se calculează...";

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: rawInput, level: 'simple' })
        });
        const data = await response.json();

        resultBox.innerHTML = `<h4>Rezultat MateAI:</h4><p>${data.message}</p>`;
        if (studentAnswer) {
            resultBox.innerHTML += `<p style="margin-top:10px; color: #7f8c8d;">Verifică dacă răspunsul tău coincide cu cel al AI-ului!</p>`;
        }
    } catch (e) {
        resultBox.innerHTML = "Eroare la calcul.";
    }
});

// Inițializare
loadChapters();
initBackground();
initVoiceAssistant();
initTtsControls();
fetchDailyChallenge();
fetchAdaptiveSuggestion();

// --- ADAPTIVE DIFFICULTY ---
async function fetchAdaptiveSuggestion() {
    const scores = userProgress.chapterScores || {};
    if (Object.keys(scores).length < 2) return; // Minim 2 capitole testate

    try {
        const res = await fetch('/api/suggest-weak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chapterScores: scores })
        });
        const data = await res.json();
        if (data.suggestion) {
            const banner = document.getElementById('adaptive-banner');
            const text = document.getElementById('adaptive-text');
            if (banner && text) {
                window._adaptiveChapterId = data.suggestion.id;
                text.innerHTML = `${data.suggestion.icon} Ai un scor de doar <strong>${data.suggestion.score}%</strong> la <strong>${data.suggestion.title}</strong>. Exersează pentru a te îmbunătăți!`;
                banner.classList.remove('hidden');
            }
        }
    } catch (e) {
        console.error("Eroare adaptiv:", e);
    }
}

function startAdaptiveQuiz() {
    if (!window._adaptiveChapterId) return;
    changeView('explica');
    const chatInput = document.getElementById('chat-input');
    const ch = localChapters.find(c => c.id === window._adaptiveChapterId);
    if (ch) {
        chatInput.value = `quiz ${ch.title}`;
        handleChat();
    }
}

// --- MOD COMPETIȚIE REFINED (Race Style) ---
let compState = {
    players: ['Jucător 1', 'Jucător 2'],
    scores: [0, 0],
    questions: [],
    currentQ: 0,
    timer: null,
    timeLeft: 30,
    roundActive: false
};

async function startCompetition() {
    const p1 = document.getElementById('player1-name').value.trim() || 'Jucător 1';
    const p2 = document.getElementById('player2-name').value.trim() || 'Jucător 2';
    compState.players = [p1, p2];
    compState.scores = [0, 0];
    compState.currentQ = 0;
    compState.roundActive = true;

    try {
        const res = await fetch('/api/competition');
        const data = await res.json();
        compState.questions = data.questions;
    } catch (e) {
        alert('Eroare la încărcarea întrebărilor!');
        return;
    }

    document.getElementById('comp-setup').classList.add('hidden');
    document.getElementById('comp-results').classList.add('hidden');
    document.getElementById('comp-game').classList.remove('hidden');

    // Update labels for race mode
    document.getElementById('comp-p1-label').textContent = '🔵 ' + p1;
    document.getElementById('comp-p2-label').textContent = '🔴 ' + p2;
    document.getElementById('comp-p1-score').textContent = '0';
    document.getElementById('comp-p2-score').textContent = '0';

    // Show shared race UI
    const compGame = document.getElementById('comp-game');
    compGame.innerHTML = `
        <div id="comp-scoreboard" class="welcome-card" style="padding: 15px; margin-bottom: 15px; display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center;">
                <div style="color: #4ECDC4; font-weight: 700;">🔵 ${p1}</div>
                <div style="font-size: 2rem; font-weight: 800;" id="mp-score-0">0</div>
            </div>
            <div style="font-size: 1.5rem; color: var(--text-500);">VS</div>
            <div style="text-align: center;">
                <div style="color: #FF6B6B; font-weight: 700;">🔴 ${p2}</div>
                <div style="font-size: 2rem; font-weight: 800;" id="mp-score-1">0</div>
            </div>
        </div>
        <div class="welcome-card" style="padding: 25px;">
            <div id="comp-timer" style="font-size: 1.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 10px;">30s</div>
            <h3 id="comp-question" style="color: white; margin-bottom: 15px; font-size: 1.4rem;"></h3>
            
            <div style="display: flex; gap: 20px; justify-content: center; margin-top: 20px;">
                <div style="flex: 1;">
                    <label style="color: #4ECDC4; font-size: 0.8rem;">${p1} (Tastează aici)</label>
                    <input type="text" id="mp-input-0" placeholder="Răspuns..." style="width: 100%;" autocomplete="off">
                </div>
                <div style="flex: 1;">
                    <label style="color: #FF6B6B; font-size: 0.8rem;">${p2} (Tastează aici)</label>
                    <input type="text" id="mp-input-1" placeholder="Răspuns..." style="width: 100%;" autocomplete="off">
                </div>
            </div>
            <p style="font-size: 0.8rem; margin-top: 15px; opacity: 0.7;">Primul care apasă ENTER în box-ul său cu răspunsul corect câștigă runda!</p>
            <div id="comp-feedback" style="margin-top: 15px; font-weight: 700; min-height: 24px;"></div>
        </div>
    `;

    // Add listeners
    document.getElementById('mp-input-0').addEventListener('keypress', (e) => { if (e.key === 'Enter') checkRaceAnswer(0); });
    document.getElementById('mp-input-1').addEventListener('keypress', (e) => { if (e.key === 'Enter') checkRaceAnswer(1); });

    showNextRaceQuestion();
}

function showNextRaceQuestion() {
    if (compState.currentQ >= compState.questions.length) {
        endCompetition();
        return;
    }

    compState.roundActive = true;
    const q = compState.questions[compState.currentQ];
    document.getElementById('comp-question').innerHTML = `Runda ${compState.currentQ + 1}/5:<br><em>${q.question}</em>`;
    document.getElementById('mp-input-0').value = '';
    document.getElementById('mp-input-1').value = '';
    document.getElementById('mp-input-0').disabled = false;
    document.getElementById('mp-input-1').disabled = false;
    document.getElementById('comp-feedback').innerHTML = '';
    document.getElementById('mp-input-0').focus();

    compState.timeLeft = 30;
    if (compState.timer) clearInterval(compState.timer);
    compState.timer = setInterval(() => {
        compState.timeLeft--;
        const timerEl = document.getElementById('comp-timer');
        if (timerEl) {
            timerEl.textContent = compState.timeLeft + 's';
            if (compState.timeLeft <= 5) timerEl.style.color = '#FF4757';
        }
        if (compState.timeLeft <= 0) {
            clearInterval(compState.timer);
            document.getElementById('comp-feedback').innerHTML = "⌛ Timp expirat! Trecem la următoarea.";
            compState.roundActive = false;
            setTimeout(showNextRaceQuestion, 2000);
            compState.currentQ++;
        }
    }, 1000);
}

async function checkRaceAnswer(playerIdx) {
    if (!compState.roundActive) return;

    const input = document.getElementById(`mp-input-${playerIdx}`);
    const userAnswer = input.value.trim();
    if (!userAnswer) return;

    const q = compState.questions[compState.currentQ];

    try {
        const res = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userAnswer, correctAnswer: q.answer, chapterId: q.chapterId })
        });
        const data = await res.json();

        if (data.isCorrect) {
            compState.roundActive = false;
            clearInterval(compState.timer);
            const bonus = Math.max(0, compState.timeLeft);
            const totalPoints = 10 + bonus;
            compState.scores[playerIdx] += totalPoints;

            document.getElementById(`mp-score-${playerIdx}`).textContent = compState.scores[playerIdx];
            document.getElementById('comp-feedback').innerHTML = `🎉 ${compState.players[playerIdx]} a câștigat runda! (+${totalPoints})`;
            document.getElementById('comp-feedback').style.color = playerIdx === 0 ? '#4ECDC4' : '#FF6B6B';

            launchConfetti();

            document.getElementById('mp-input-0').disabled = true;
            document.getElementById('mp-input-1').disabled = true;

            compState.currentQ++;
            setTimeout(showNextRaceQuestion, 2000);
        } else {
            // Hint optional: visual shake or red border
            input.style.border = '2px solid #FF4757';
            setTimeout(() => input.style.border = '', 500);
        }
    } catch (e) { console.error(e); }
}

// --- MULTIPLAYER ONLINE LOGIC ---
let mpRoomCode = null;
let mpPollingInterval = null;

async function createRoom() {
    if (!currentUser) { alert("Trebuie să fii conectat!"); changeView('login'); return; }
    try {
        const res = await fetch('/api/multiplayer/create', {
            method: 'POST',
            headers: { 'Authorization': currentUser.token }
        });
        const data = await res.json();
        if (data.success) {
            mpRoomCode = data.code;
            document.getElementById('mp-lobby').classList.add('hidden');
            document.getElementById('mp-waiting').classList.remove('hidden');
            document.getElementById('mp-room-code-display').textContent = mpRoomCode;
            startPolling();
        }
    } catch (e) { console.error(e); }
}

async function joinRoom() {
    if (!currentUser) { alert("Trebuie să fii conectat!"); changeView('login'); return; }
    const code = document.getElementById('join-room-code').value.trim().toUpperCase();
    if (!code) return;

    try {
        const res = await fetch(`/api/multiplayer/join/${code}`, {
            method: 'POST',
            headers: { 'Authorization': currentUser.token }
        });
        const data = await res.json();
        if (data.success) {
            mpRoomCode = code;
            document.getElementById('mp-lobby').classList.add('hidden');
            document.getElementById('mp-game').classList.remove('hidden');
            startPolling();
        } else {
            alert(data.error || "Cod invalid.");
        }
    } catch (e) { console.error(e); }
}

function startPolling() {
    if (mpPollingInterval) clearInterval(mpPollingInterval);
    mpPollingInterval = setInterval(async () => {
        if (!mpRoomCode) return;
        try {
            const res = await fetch(`/api/multiplayer/status/${mpRoomCode}`);
            const data = await res.json();
            if (data.success) {
                updateMPUI(data);
                if (data.status === 'finished') {
                    stopPolling();
                    showMPResults(data);
                }
            }
        } catch (e) { console.error(e); }
    }, 1500);
}

function stopPolling() {
    if (mpPollingInterval) {
        clearInterval(mpPollingInterval);
        mpPollingInterval = null;
    }
}

function updateMPUI(data) {
    const { status, state, host_name, guest_name, server_time } = data;

    if (status === 'playing') {
        document.getElementById('mp-waiting').classList.add('hidden');
        document.getElementById('mp-game').classList.remove('hidden');

        document.getElementById('mp-host-name').textContent = host_name || "Host";
        document.getElementById('mp-guest-name').textContent = guest_name || "Adversar";
        document.getElementById('mp-host-score').textContent = state.scores[0];
        document.getElementById('mp-guest-score').textContent = state.scores[1];

        const qCount = 10;
        document.getElementById('mp-round-info').textContent = `Runda ${state.currentQ + 1}/${qCount}`;

        const q = state.questions[state.currentQ];
        if (q) {
            document.getElementById('mp-question-text').textContent = q.question;
            if (q.chapterTitle) {
                document.getElementById('mp-round-info').innerHTML = `Runda ${state.currentQ + 1}/${qCount} <span style="opacity:0.6">(${q.chapterTitle})</span>`;
            }
        }

        // Timer Logic
        if (server_time && state.roundStartTime) {
            const elapsed = server_time - state.roundStartTime;
            const remaining = Math.max(0, 20 - Math.floor(elapsed));
            const timerEl = document.getElementById('mp-timer-display');
            if (timerEl) {
                timerEl.textContent = `${remaining}s`;
                timerEl.style.color = remaining <= 5 ? '#FF4757' : '#F59E0B';

                const bar = document.getElementById('mp-timer-bar');
                if (bar) {
                    const pct = (remaining / 20) * 100;
                    bar.style.width = pct + "%";
                    bar.style.background = remaining <= 5 ? '#FF4757' : '#F59E0B';
                }
            }
        }

        const feedback = document.getElementById('mp-feedback-msg');
        feedback.innerHTML = state.lastFeedback || "";
        if (state.lastFeedback && state.lastFeedback.includes("corect")) {
            feedback.style.color = "#4ECDC4";
        } else if (state.lastFeedback && state.lastFeedback.includes("expirat")) {
            feedback.style.color = "#FF4757";
        }
    }
}

async function submitMPAnswer() {
    const input = document.getElementById('mp-answer-input');
    const answer = input.value.trim();
    if (!answer || !mpRoomCode) return;

    try {
        const res = await fetch(`/api/multiplayer/action/${mpRoomCode}`, {
            method: 'POST',
            headers: {
                'Authorization': currentUser.token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ answer })
        });
        const data = await res.json();
        if (data.success) {
            if (data.isCorrect) {
                input.value = '';
                launchConfetti();
            } else if (data.timeout) {
                input.value = '';
            } else {
                input.style.border = '2px solid #FF4757';
                setTimeout(() => input.style.border = '', 500);
            }
        }
    } catch (e) { console.error(e); }
}

function showMPResults(data) {
    document.getElementById('mp-game').classList.add('hidden');
    document.getElementById('mp-results').classList.remove('hidden');

    const { state, host_name, guest_name } = data;
    const s1 = state.scores[0];
    const s2 = state.scores[1];

    let winnerText = "";
    if (s1 > s2) winnerText = `${host_name} a Câștigat!`;
    else if (s2 > s1) winnerText = `${guest_name} a Câștigat!`;
    else winnerText = "Egalitate!";

    document.getElementById('mp-result-title').textContent = winnerText;
    document.getElementById('mp-result-score').textContent = `Scor Final: ${s1} - ${s2} (din 10 runde)`;
    document.getElementById('mp-winner-icon').textContent = s1 === s2 ? "🤝" : "🏆";
}

// Event delegation pentru input enter
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.target.id === 'mp-answer-input') {
        submitMPAnswer();
    }
});

// --- AUTH LOGIC ---
function switchAuth(mode) {
    const card = document.getElementById('auth-card');
    if (!card) return;
    authMode = mode;
    if (mode === 'register') {
        card.classList.add('show-register');
    } else {
        card.classList.remove('show-register');
    }
}

function updateAuthUI() {
    const navAuth = document.getElementById('nav-auth');
    if (!navAuth) return;

    if (currentUser) {
        navAuth.innerHTML = `<a href="#" class="nav-link" onclick="handleLogout()">${currentUser.username} (Logout)</a>`;
        if (!document.getElementById('login').classList.contains('hidden')) {
            changeView('home');
        }
    } else {
        navAuth.innerHTML = `<a href="#" class="nav-link" data-section="login">Conectare</a>`;
        navAuth.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            changeView('login');
        });
        switchAuth('login');
    }
}

async function handleLogin() {
    const userEl = document.getElementById('login-username');
    const passEl = document.getElementById('login-password');
    if (!userEl || !passEl) return;

    const username = userEl.value.trim();
    const password = passEl.value.trim();
    if (!username || !password) {
        alert("Introdu numele și parola!");
        return;
    }

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.success) {
            currentUser = data.user;
            localStorage.setItem('mateai_user', JSON.stringify(currentUser));
            updateAuthUI();
            launchConfetti();
            changeView('home');
        } else {
            alert(data.error || "Eroare la conectare.");
        }
    } catch (e) { alert("Eroare de conexiune."); }
}

async function handleRegister() {
    const userEl = document.getElementById('register-username');
    const passEl = document.getElementById('register-password');
    const roleEl = document.querySelector('input[name="register-role"]:checked');
    if (!userEl || !passEl || !roleEl) return;

    const username = userEl.value.trim();
    const password = passEl.value.trim();
    const role = roleEl.value;

    if (!username || !password) {
        alert("Introdu numele și parola!");
        return;
    }

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });
        const data = await res.json();

        if (data.success) {
            alert("Cont creat cu succes! Acum te poți conecta.");
            launchConfetti();
            userEl.value = '';
            passEl.value = '';
            switchAuth('login');
        } else {
            alert(data.error || "Eroare la înregistrare.");
        }
    } catch (e) { alert("Eroare de conexiune."); }
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('mateai_user');
    location.reload();
}

// --- CLASSROOM LOGIC ---

async function showStudentDetails(userId, username) {
    const view = document.getElementById('student-detail-view');
    const statsArea = document.getElementById('detail-student-stats');
    document.getElementById('detail-student-name').textContent = `Analiză Progres: ${username}`;
    view.classList.remove('hidden');
    statsArea.innerHTML = 'Se încarcă datele...';

    try {
        const res = await fetch(`/api/student/details/${userId}`, {
            headers: { 'Authorization': currentUser.token }
        });
        const data = await res.json();
        if (data.success) {
            if (data.details.length === 0) {
                statsArea.innerHTML = '<p>Elevul nu a început încă nicio lecție.</p>';
                return;
            }

            let html = '<ul style="list-style: none;">';
            data.details.forEach(p => {
                const ratio = p.total > 0 ? (p.correct / p.total) * 100 : 0;
                const statusColor = ratio >= 80 ? '#4ECDC4' : ratio >= 50 ? '#FFD93D' : '#FF6B6B';
                const statusText = ratio >= 80 ? 'Stăpânește' : ratio >= 50 ? 'În lucru' : 'Se poticnește';

                html += `
                    <li style="margin-bottom: 10px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 4px solid ${statusColor};">
                        <strong>${p.chapter_id}</strong>: ${p.correct}/${p.total} corecte (${Math.round(ratio)}%)
                        <br><span style="font-size: 0.8rem; color: ${statusColor};">${statusText}</span>
                    </li>
                `;
            });
            html += '</ul>';
            statsArea.innerHTML = html;
        }
    } catch (e) {
        statsArea.innerHTML = 'Eroare la încărcarea datelor.';
    }
}

function switchClassTab(tabName) {
    document.getElementById('class-tab-ranking').classList.add('hidden');
    document.getElementById('class-tab-homework').classList.add('hidden');
    document.querySelectorAll('.btn-tab').forEach(b => b.classList.remove('active-tab'));

    document.getElementById(`class-tab-${tabName}`).classList.remove('hidden');
    const activeBtn = document.getElementById(`tab-${tabName}`);
    if (activeBtn) activeBtn.classList.add('active-tab');

    if (tabName === 'homework') {
        loadHomework();
    } else {
        if (currentUser && currentUser.class_code) {
            loadRankings(currentUser.class_code);
        }
    }
}

function hideStudentDetails() {
    document.getElementById('student-detail-view').classList.add('hidden');
}

async function updateClassroomUI() {
    if (!currentUser) {
        document.getElementById('class-tab-ranking').classList.remove('hidden');
        document.getElementById('class-tab-homework').classList.add('hidden');
        document.getElementById('class-student-zone').classList.remove('hidden');
        document.getElementById('class-ranking-card').classList.add('hidden');
        return;
    }

    const teacherZone = document.getElementById('class-teacher-zone');
    const studentZone = document.getElementById('class-student-zone');
    const teacherHwZone = document.getElementById('teacher-homework-zone');
    const studentHwZone = document.getElementById('student-homework-zone');

    if (currentUser.role === 'teacher') {
        teacherZone.classList.remove('hidden');
        teacherHwZone.classList.remove('hidden');
        studentZone.classList.add('hidden');
        studentHwZone.classList.add('hidden');

        if (currentUser.class_code) {
            teacherZone.innerHTML = `
                <p>Clasă activă: <strong>${currentUser.class_code}</strong></p>
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <button onclick="location.reload()" style="background: var(--bg-soft); color: white; font-size: 0.8rem;">🔄 Refresh</button>
                    <button onclick="handleLogout()" style="background: rgba(255,71,87,0.2); color: #FF4757; font-size: 0.8rem;">Ieșire Cont</button>
                </div>
            `;
            // Populate chapter select for homework
            const selectHw = document.getElementById('hw-chapter-select');
            if (selectHw && selectHw.innerHTML === '') {
                selectHw.innerHTML = localChapters.map(c => `<option value="${c.id}">${c.title}</option>`).join('');
            }
        } else {
            teacherZone.innerHTML = `
                <p>Nu ai nicio clasă creată încă.</p>
                <div class="input-group" style="margin-top: 10px;">
                    <input type="text" id="new-class-name" placeholder="Numele clasei (ex: 5A)">
                    <button onclick="createClass()">Creează Clasă</button>
                </div>
            `;
        }
    } else {
        teacherZone.classList.add('hidden');
        teacherHwZone.classList.add('hidden');
        studentZone.classList.remove('hidden');
        studentHwZone.classList.remove('hidden');
    }

    if (currentUser.class_code) {
        loadRankings(currentUser.class_code);
    }
}

async function createClass() {
    const nameEl = document.getElementById('new-class-name');
    if (!nameEl) return;
    const name = nameEl.value.trim();
    if (!name) return;

    try {
        const res = await fetch('/api/class/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': currentUser.token
            },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            alert(`Clasă creată! Cod: ${data.code}`);
            currentUser.class_code = data.code;
            localStorage.setItem('mateai_user', JSON.stringify(currentUser));
            updateClassroomUI();
        }
    } catch (e) { console.error(e); }
}

async function joinClass() {
    const codeEl = document.getElementById('join-class-code');
    if (!codeEl) return;
    const code = codeEl.value.trim();
    if (!code) return;

    try {
        const res = await fetch('/api/class/join', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': currentUser.token
            },
            body: JSON.stringify({ code })
        });
        const data = await res.json();
        if (data.success) {
            alert(`Te-ai alăturat clasei ${data.className}!`);
            currentUser.class_code = code.toUpperCase();
            localStorage.setItem('mateai_user', JSON.stringify(currentUser));
            updateClassroomUI();
        } else {
            alert(data.error);
        }
    } catch (e) { console.error(e); }
}

async function loadRankings(code) {
    try {
        const res = await fetch(`/api/class/rankings/${code}`);
        const result = await res.json();
        if (result.success) {
            const data = result.data;
            document.getElementById('ranking-class-name').textContent = data.className;
            document.getElementById('ranking-class-code').textContent = data.code;
            document.getElementById('class-ranking-card').classList.remove('hidden');

            const tbody = document.getElementById('ranking-body');
            tbody.innerHTML = '';
            data.students.forEach((s, idx) => {
                const tr = document.createElement('tr');
                tr.style.background = s.username === currentUser.username.toLowerCase() ? 'rgba(99, 102, 241, 0.2)' : 'transparent';

                let actionBtn = '';
                if (currentUser.role === 'teacher') {
                    actionBtn = `<button onclick="showStudentDetails(${s.id}, '${s.username}')" style="padding: 4px 8px; font-size: 0.7rem;">🔍 Detalii</button>`;
                }

                tr.innerHTML = `
                    <td style="padding: 10px;">${idx + 1}</td>
                    <td style="padding: 10px;"><strong>${s.username}</strong></td>
                    <td style="padding: 10px;">${s.total_answers}</td>
                    <td style="padding: 10px; color: #4ECDC4;">${s.total_correct}</td>
                    <td style="padding: 10px;">${actionBtn}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) { console.error(e); }
}

async function assignHomework() {
    const chapterId = document.getElementById('hw-chapter-select').value;
    const desc = document.getElementById('hw-description').value.trim();
    const date = document.getElementById('hw-due-date').value;
    const fileInput = document.getElementById('hw-file');

    if (!chapterId && !desc && (!fileInput || !fileInput.files.length)) {
        alert("Selectează măcar un capitol, o descriere sau încarcă un fișier.");
        return;
    }

    const formData = new FormData();
    formData.append('chapterId', chapterId);
    if (desc) formData.append('description', desc);
    if (date) formData.append('dueDate', date);
    if (fileInput && fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    }

    try {
        const res = await fetch('/api/homework/create', {
            method: 'POST',
            headers: {
                'Authorization': currentUser.token
            },
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            alert("Temă asignată cu succes!");
            document.getElementById('hw-description').value = '';
            document.getElementById('hw-due-date').value = '';
            if (fileInput) fileInput.value = '';
            loadHomework();
        } else {
            alert(data.error || "Eroare la crearea temei.");
        }
    } catch (e) { console.error(e); }
}

async function loadHomework() {
    if (!currentUser || !currentUser.class_code) return;

    try {
        const res = await fetch(`/api/homework/class/${currentUser.class_code}`, {
            headers: { 'Authorization': currentUser.token }
        });
        const data = await res.json();
        if (data.success) {
            const list = currentUser.role === 'teacher' ? 'teacher-homework-list' : 'student-homework-list';
            const container = document.getElementById(list);
            if (!container) return;

            if (data.homework.length === 0) {
                container.innerHTML = '<p style="opacity: 0.5;">Nicio temă activă.</p>';
                return;
            }

            container.innerHTML = data.homework.map(hw => {
                const chapter = localChapters.find(c => c.id === hw.chapter_id);
                const title = chapter ? chapter.title : (hw.chapter_id || 'Temă Generală');
                const descStr = hw.description ? `<div style="font-size: 0.9rem; margin-top: 5px; opacity: 0.9;">${hw.description}</div>` : '';
                const fileStr = hw.file_path ? `<div style="margin-top: 10px;"><a href="${hw.file_path}" target="_blank" style="color: #4ECDC4; text-decoration: none; font-size: 0.9rem;">📎 Vezi Fișier Atașat</a></div>` : '';
                const dueStr = hw.due_date ? `<div style="font-size: 0.8rem; color: #ff6b6b; margin-top: 5px;">Scadentă: ${hw.due_date}</div>` : '';

                let content = `
                    <div style="padding: 15px; background: rgba(255,255,255,0.05); border-radius: 12px; margin-bottom: 10px; border-left: 4px solid var(--primary-400);">
                        <strong>${title}</strong>
                        ${descStr}
                        ${fileStr}
                        <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 5px;">Data: ${new Date(hw.created_at).toLocaleDateString()}</div>
                        ${dueStr}
                `;

                if (currentUser.role === 'teacher') {
                    content += `<button onclick="loadHomeworkCompletions(${hw.id})" style="padding: 5px 10px; font-size: 0.8rem; border-radius: 6px; margin-top: 10px; border: 1px solid var(--primary-400); background: transparent; color: white;">📊 Vezi completări</button>`;
                    content += `<div id="hw-completions-${hw.id}" style="margin-top: 10px;" class="hidden"></div>`;
                } else if (currentUser.role === 'student') {
                    const status = hw.completed_at ? '✅ Trimisă' : '⏳ În așteptare';
                    content += `<div style="font-size: 0.85rem; color: ${hw.completed_at ? '#4ECDC4' : '#feca57'}; margin-top: 10px; font-weight: bold;">Stare: ${status}</div>`;

                    if (!hw.completed_at) {
                        content += `
                            <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px; align-items: flex-start;">
                                <label style="font-size: 0.8rem; color: var(--text-500);">Încarcă rezolvarea (poză / fișier):</label>
                                <input type="file" id="submit-file-${hw.id}" accept="image/*,.pdf,.doc,.docx" style="font-size: 0.8rem;">
                                <button onclick="trimiteRezolvare(${hw.id})" style="padding: 6px 12px; font-size: 0.8rem; margin-top: 5px;">Trimite Rezolvare</button>
                            </div>
                        `;
                    }
                }

                content += `</div>`;
                return content;
            }).join('');
        }
    } catch (e) { console.error(e); }
}

async function trimiteRezolvare(homeworkId) {
    const fileInput = document.getElementById(`submit-file-${homeworkId}`);
    if (!fileInput || !fileInput.files.length) {
        alert("Te rog să încarci un fișier cu rezolvarea!");
        return;
    }

    const formData = new FormData();
    formData.append('homeworkId', homeworkId);
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/api/homework/complete', {
            method: 'POST',
            headers: {
                'Authorization': currentUser.token
            },
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            alert("Rezoluția ta a fost trimisă cu succes!");
            loadHomework();
        } else {
            alert(data.error || "A apărut o eroare la trimitere.");
        }
    } catch (e) { console.error(e); }
}

async function loadHomeworkCompletions(hwId) {
    const container = document.getElementById(`hw-completions-${hwId}`);
    if (!container) return;

    // Toggle
    if (!container.classList.contains('hidden')) {
        container.classList.add('hidden');
        return;
    }

    container.innerHTML = '<em>Se încarcă...</em>';
    container.classList.remove('hidden');

    try {
        const res = await fetch(`/api/homework/${hwId}/completions`, {
            headers: { 'Authorization': currentUser.token }
        });
        const data = await res.json();
        if (data.success) {
            if (data.completions.length === 0) {
                container.innerHTML = '<span style="opacity:0.5; font-size: 0.8rem;">Niciun elev în clasă.</span>';
                return;
            }

            let html = '<div style="background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px; margin-top: 5px;">';
            data.completions.forEach(c => {
                const badge = c.completed_at ? '<span style="color:#4ECDC4;">✅</span>' : '❌';
                const fileLink = c.file_path ? `<a href="${c.file_path}" target="_blank" style="color: #feca57; font-size: 0.8rem; margin-left: 10px; text-decoration: underline;">[Vezi Rezolvare]</a>` : '';
                html += `<div style="font-size: 0.85rem; padding: 4px 0;">
                    ${badge} <strong>${c.username}</strong>
                    ${c.completed_at ? `<span style="font-size:0.75rem; opacity:0.7; margin-left:5px;">(${new Date(c.completed_at).toLocaleDateString()})</span>` : ''}
                    ${fileLink}
                </div>`;
            });
            html += '</div>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<span style="color:red; font-size: 0.8rem;">Eroare la încărcare.</span>';
        }
    } catch (e) {
        container.innerHTML = '<span style="color:red; font-size: 0.8rem;">Eroare.</span>';
        console.error(e);
    }
}

// --- SYNC PROGRESS WITH SERVER ---
async function syncProgressWithServer(isCorrect, chapterId) {
    if (!currentUser || !currentUser.token) return;

    try {
        await fetch('/api/progress/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': currentUser.token
            },
            body: JSON.stringify({ isCorrect, chapterId })
        });
    } catch (e) { console.error("Sync error:", e); }
}

// Override original logging to include server sync
const originalLogDailyProgress = logDailyProgress;
logDailyProgress = function (isCorrect, chapterId) {
    originalLogDailyProgress(isCorrect, chapterId);
    syncProgressWithServer(isCorrect, chapterId);
};

// Auto-login check on boot
if (currentUser) {
    updateAuthUI();
}

// Ensure login and classroom are initialized on load
window.addEventListener('load', () => {
    if (currentUser) {
        updateAuthUI();
        updateClassroomUI();
    }
});
