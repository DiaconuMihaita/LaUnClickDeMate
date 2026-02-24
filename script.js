// Statul aplicației (frontend)
let localChapters = [];
let lastChapterId = null;
let visitedChapters = [];
let sessionScore = { correct: 0, total: 0 };

// --- PERSISTENT PROGRESS (LocalStorage) ---
let userProgress = JSON.parse(localStorage.getItem('mateai_progress')) || {
    chaptersExplored: [],
    exercisesCorrect: 0,
    badges: [],
    lastChallengeDate: null
};

function saveProgress() {
    localStorage.setItem('mateai_progress', JSON.stringify(userProgress));
}

// F1/F6 — Starea quiz/test activ
let quizState = { active: false, exercise: '', correctAnswer: '', chapterId: '' };
let testState = { active: false, questions: [], current: 0, correct: 0 };
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
    const utterance = new SpeechSynthesisUtterance(text.replace(/<[^>]*>/g, '')); // Scoatem HTML-ul
    utterance.lang = 'ro-RO';
    speechSynthesis.speak(utterance);
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
    if (target) target.classList.remove('hidden');

    // Update nav active state
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('data-section') === viewId) {
            link.setAttribute('data-active', 'true');
        } else {
            link.removeAttribute('data-active');
        }
    });

    if (viewId === 'lectii') renderChapters();
    if (viewId === 'profil') renderProfile();
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

        if (data.isCorrect) sessionScore.correct++;
        updateScoreUI();

        const cls = data.isCorrect ? 'feedback-correct' : 'feedback-wrong';
        addMessage(data.feedback, 'ai', cls);
    } catch (e) {
        addMessage("Nu am putut verifica răspunsul. Încearcă din nou!", 'ai');
    }
}

// F6 — Mod Test: avansare la întrebarea următoare
function renderTestQuestion(questions, currentIdx) {
    testState = { active: true, questions, current: currentIdx, correct: testState.correct };
    const area = document.getElementById('quiz-answer-area');
    if (!area) return;

    if (currentIdx >= questions.length) {
        // Test finalizat - calculăm nota
        testState.active = false;
        const nota = Math.round((testState.correct / questions.length) * 9) + 1;
        const emoji = nota >= 9 ? "🏆" : nota >= 7 ? "😊" : nota >= 5 ? "📚" : "💪";
        area.innerHTML = '';
        addMessage(
            `${emoji} <strong>Test finalizat!</strong><br><br>Ai răspuns corect la <strong>${testState.correct}/${questions.length}</strong> întrebări.<br>Nota estimată: <strong>${nota}/10</strong><br><br>${nota >= 7 ? 'Felicitări, ai înțeles bine materia!' : 'Continuă să studiezi, poți mai mult!'}`,
            'ai', nota >= 7 ? 'feedback-correct' : 'feedback-wrong'
        );
        testState.correct = 0;
        return;
    }

    const q = questions[currentIdx];
    // Afișează întrebarea curentă ca mesaj AI
    addMessage(
        `<strong>Întrebarea ${currentIdx + 1}/${questions.length}</strong> — ${q.chapterTitle}:<br><em>${q.question}</em>`,
        'ai'
    );
    area.innerHTML = `
        <div class="quiz-input-box test-box">
            <span class="test-progress-label">Întrebarea ${currentIdx + 1}/${questions.length}</span>
            <div class="test-progress-bar"><div class="test-progress-fill" style="width:${((currentIdx) / questions.length) * 100}%"></div></div>
            <input type="text" id="quiz-answer-input" placeholder="Răspunsul tău..." autocomplete="off">
            <button onclick="submitTestAnswer()">✔ Răspunde</button>
        </div>
    `;
    const inp = document.getElementById('quiz-answer-input');
    if (inp) {
        inp.focus();
        inp.addEventListener('keypress', e => { if (e.key === 'Enter') submitTestAnswer(); });
    }
}

async function submitTestAnswer() {
    if (!testState.active) return;
    const answerInput = document.getElementById('quiz-answer-input');
    if (!answerInput) return;
    const userAnswer = answerInput.value.trim();
    if (!userAnswer) return;

    const q = testState.questions[testState.current];
    addMessage(userAnswer, 'user');

    try {
        const res = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userAnswer, correctAnswer: q.answer, chapterId: q.chapterId })
        });
        const data = await res.json();
        if (data.isCorrect) testState.correct++;
        const cls = data.isCorrect ? 'feedback-correct' : 'feedback-wrong';
        addMessage(data.feedback, 'ai', cls);
    } catch (e) {
        addMessage("Eroare la verificare.", 'ai');
    }

    testState.current++;
    setTimeout(() => renderTestQuestion(testState.questions, testState.current), 800);
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

        // F6 — Mod test
        if (data.testMode) {
            testState.correct = 0;
            testState.questions = data.testQuestions;
            testState.current = 0;
            renderTestQuestion(data.testQuestions, 0); // pornește de la prima întrebare
        }

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
fetchDailyChallenge();
