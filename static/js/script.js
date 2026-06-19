/* Football Analyzer - Frontend */
(function () {
    "use strict";

    const form = document.getElementById("analyzeForm");
    const input = document.getElementById("matchInput");
    const submitBtn = document.getElementById("submitBtn");
    const statusPill = document.getElementById("statusPill");
    const statusText = document.getElementById("statusText");

    const progressSection = document.getElementById("progressSection");
    const progressTitle = document.getElementById("progressTitle");
    const progressStatus = document.getElementById("progressStatus");
    const progressSteps = document.getElementById("progressSteps");

    const resultSection = document.getElementById("resultSection");
    const resultTitle = document.getElementById("resultTitle");
    const matchMeta = document.getElementById("matchMeta");
    const analysisContent = document.getElementById("analysisContent");
    const contextBlock = document.getElementById("contextBlock");
    const contextContent = document.getElementById("contextContent");
    const scoutBlock = document.getElementById("scoutBlock");
    const scoutContent = document.getElementById("scoutContent");

    const errorSection = document.getElementById("errorSection");
    const errorMessage = document.getElementById("errorMessage");
    const errorDismiss = document.getElementById("errorDismiss");

    const copyBtn = document.getElementById("copyBtn");
    const downloadBtn = document.getElementById("downloadBtn");
    const printBtn = document.getElementById("printBtn");

    let currentMarkdown = "";
    let currentMatch = "";
    let scoutFactsContent = "";

    const md = window.marked || null;

    function escapeHtml(s) {
        return s
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function renderMarkdown(text) {
        if (md && typeof md.parse === "function") {
            return md.parse(text, { breaks: true, gfm: true });
        }
        return renderMarkdownFallback(text);
    }

    function renderMarkdownFallback(text) {
        const lines = text.split("\n");
        const out = [];
        let inTable = false;
        let tableBuf = [];
        let inList = null;
        let inCode = false;
        let codeBuf = [];
        let paraBuf = [];

        function flushPara() {
            if (paraBuf.length) {
                out.push("<p>" + inline(paraBuf.join(" ")) + "</p>");
                paraBuf = [];
            }
        }
        function flushList() {
            if (inList) {
                out.push("</" + inList + ">");
                inList = null;
            }
        }
        function flushTable() {
            if (inTable && tableBuf.length >= 2) {
                const header = tableBuf[0].split("|").map((s) => s.trim()).filter(Boolean);
                const rows = tableBuf.slice(2).map((row) =>
                    row.split("|").map((s) => s.trim())
                );
                let html = "<table><thead><tr>";
                header.forEach((h) => (html += "<th>" + inline(h) + "</th>"));
                html += "</tr></thead><tbody>";
                rows.forEach((r) => {
                    html += "<tr>";
                    r.forEach((c) => {
                        if (c !== undefined) html += "<td>" + inline(c) + "</td>";
                    });
                    html += "</tr>";
                });
                html += "</tbody></table>";
                out.push(html);
            } else if (inTable) {
                tableBuf.forEach((l) => paraBuf.push(l));
            }
            inTable = false;
            tableBuf = [];
        }

        function inline(s) {
            let r = escapeHtml(s);
            r = r.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
            r = r.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>");
            r = r.replace(/`([^`]+)`/g, "<code>$1</code>");
            r = r.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
            return r;
        }

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (inCode) {
                if (/^```/.test(line.trim())) {
                    out.push("<pre><code>" + escapeHtml(codeBuf.join("\n")) + "</code></pre>");
                    codeBuf = [];
                    inCode = false;
                } else {
                    codeBuf.push(line);
                }
                continue;
            }
            if (/^```/.test(line.trim())) {
                flushPara();
                flushList();
                flushTable();
                inCode = true;
                continue;
            }
            if (/^\s*$/.test(line)) {
                flushPara();
                flushList();
                flushTable();
                continue;
            }
            const h = line.match(/^(#{1,6})\s+(.*)$/);
            if (h) {
                flushPara();
                flushList();
                flushTable();
                const lvl = h[1].length;
                out.push("<h" + lvl + ">" + inline(h[2]) + "</h" + lvl + ">");
                continue;
            }
            if (/^---+$/.test(line.trim())) {
                flushPara();
                flushList();
                flushTable();
                out.push("<hr>");
                continue;
            }
            if (/^>\s?/.test(line)) {
                flushPara();
                flushList();
                flushTable();
                out.push("<blockquote>" + inline(line.replace(/^>\s?/, "")) + "</blockquote>");
                continue;
            }
            if (/^[-*]\s+/.test(line)) {
                flushPara();
                flushTable();
                if (inList !== "ul") {
                    flushList();
                    out.push("<ul>");
                    inList = "ul";
                }
                out.push("<li>" + inline(line.replace(/^[-*]\s+/, "")) + "</li>");
                continue;
            }
            if (/^\d+\.\s+/.test(line)) {
                flushPara();
                flushTable();
                if (inList !== "ol") {
                    flushList();
                    out.push("<ol>");
                    inList = "ol";
                }
                out.push("<li>" + inline(line.replace(/^\d+\.\s+/, "")) + "</li>");
                continue;
            }
            if (/^\s*\|.*\|\s*$/.test(line)) {
                flushPara();
                flushList();
                if (!inTable) {
                    flushList();
                    inTable = true;
                }
                tableBuf.push(line);
                continue;
            } else if (inTable) {
                flushTable();
            }
            paraBuf.push(line);
        }
        flushPara();
        flushList();
        flushTable();
        if (inCode) out.push("<pre><code>" + escapeHtml(codeBuf.join("\n")) + "</code></pre>");
        return out.join("\n");
    }

    function setStatus(text, kind) {
        statusText.textContent = text;
        statusPill.className = "status-pill" + (kind ? " " + kind : "");
    }

    function addStep(text, status) {
        const step = document.createElement("div");
        step.className = "progress-step " + (status || "");
        step.textContent = text;
        progressSteps.appendChild(step);
        step.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function resetUI() {
        progressSection.hidden = false;
        resultSection.hidden = true;
        errorSection.hidden = true;
        progressSteps.innerHTML = "";
        analysisContent.innerHTML = "";
        currentMarkdown = "";
        matchMeta.innerHTML = "";
        contextBlock.hidden = true;
        contextContent.textContent = "";
        if (scoutBlock) scoutBlock.hidden = true;
        if (scoutContent) scoutContent.textContent = "";
        scoutFactsContent = "";
    }

    function showError(msg) {
        errorSection.hidden = false;
        errorMessage.textContent = msg;
        setStatus("Erreur", "error");
        progressSection.hidden = true;
        submitBtn.disabled = false;
        submitBtn.querySelector(".btn-text").textContent = "Lancer l'analyse complète";
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const match = input.value.trim();
        if (!match) return;
        currentMatch = match;

        submitBtn.disabled = true;
        submitBtn.querySelector(".btn-text").textContent = "Analyse en cours...";
        setStatus("Recherche en cours...", "busy");
        resetUI();

        progressTitle.textContent = "🔎 Analyse de " + match;
        progressStatus.textContent = "Initialisation de la recherche web...";

        try {
            const resp = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ match }),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ error: "Erreur " + resp.status }));
                showError(err.error || "Erreur inconnue");
                return;
            }
            if (!resp.body || !resp.body.getReader) {
                showError("Streaming non supporté par ce navigateur.");
                return;
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            let analysisBuffer = "";

            analysisContent.classList.add("streaming-cursor");

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                let idx;
                while ((idx = buffer.indexOf("\n\n")) !== -1) {
                    const rawEvent = buffer.slice(0, idx);
                    buffer = buffer.slice(idx + 2);
                    handleSSE(rawEvent);
                }
            }

            function handleSSE(raw) {
                const lines = raw.split("\n");
                let event = "message";
                const dataLines = [];
                for (const l of lines) {
                    if (l.startsWith("event: ")) event = l.slice(7).trim();
                    else if (l.startsWith("data: ")) dataLines.push(l.slice(6));
                }
                const data = dataLines.join("\n");
                if (!data) return;

                if (event === "status") {
                    progressStatus.textContent = data;
                    setStatus(data.replace(/^[^\w]+/, ""), "busy");
                } else if (event === "context") {
                    contextContent.textContent = data;
                    contextBlock.hidden = false;
                    addStep("Contexte collecté", "done");
                } else if (event === "scout_start") {
                    addStep("🕵️ Pass 1: Scout - extraction des faits clés", "active");
                } else if (event === "scout_done") {
                    addStep("✅ Pass 1: Scout terminé", "done");
                    scoutFactsContent = data;
                    if (scoutBlock) scoutBlock.hidden = false;
                    if (scoutContent) scoutContent.textContent = data;
                } else if (event === "expert_start") {
                    addStep("🧠 Pass 2: Expert - analyse probabiliste", "active");
                } else if (event === "token") {
                    if (!analysisBuffer && data.trim().length > 0) {
                        addStep("Réception de l'analyse", "active");
                    }
                    analysisBuffer += data;
                    analysisContent.innerHTML = renderMarkdown(analysisBuffer);
                    analysisContent.scrollIntoView({ behavior: "smooth", block: "end" });
                } else if (event === "done") {
                    currentMarkdown = data;
                    if (data.length > analysisBuffer.length) {
                        analysisBuffer = data;
                        analysisContent.innerHTML = renderMarkdown(analysisBuffer);
                    }
                    finishAnalysis();
                } else if (event === "error") {
                    showError(data);
                }
            }
        } catch (err) {
            console.error(err);
            showError("Erreur réseau: " + err.message);
        }
    });

    function finishAnalysis() {
        analysisContent.classList.remove("streaming-cursor");
        resultSection.hidden = false;
        resultTitle.textContent = "📊 " + currentMatch;
        matchMeta.innerHTML =
            "<div><strong>Match</strong>: " + escapeHtml(currentMatch) + "</div>" +
            "<div><strong>Généré le</strong>: " + new Date().toLocaleString("fr-FR") + "</div>";
        setStatus("Analyse prête ✅", "");
        submitBtn.disabled = false;
        submitBtn.querySelector(".btn-text").textContent = "Lancer une nouvelle analyse";
        addStep("Analyse terminée ✅", "done");
        progressSection.hidden = true;
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    errorDismiss.addEventListener("click", () => {
        errorSection.hidden = true;
    });

    copyBtn.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(currentMarkdown);
            copyBtn.textContent = "✅ Copié !";
            setTimeout(() => (copyBtn.textContent = "📋 Copier"), 1800);
        } catch (e) {
            alert("Copiez manuellement: \n\n" + currentMarkdown);
        }
    });

    downloadBtn.addEventListener("click", () => {
        const filename = currentMatch.replace(/[^a-z0-9]+/gi, "_") + ".md";
        const blob = new Blob([currentMarkdown], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    });

    printBtn.addEventListener("click", () => window.print());

    document.querySelectorAll(".example-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            input.value = chip.dataset.example;
            input.focus();
        });
    });

    fetch("/api/health")
        .then((r) => r.json())
        .then((d) => {
            if (!d.llm_configured) {
                statusText.textContent = "⚠️ Clé API manquante";
                statusPill.classList.add("error");
            }
        })
        .catch(() => {});
})();
