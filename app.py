<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Organizational Maturity Assessment | AHI Pro</title>

    <link href="https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        :root {
            --primary: #159591;
            --bg: #f4f7f9;
            --text: #333333;
            --header-bg: #000000;
            --card: #ffffff;
            --border: #e0e0e0;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* --- AHI PRO CONSULTANT MODE (AHI2026) --- */
        body.consultant-mode {
            --primary: #ff003c;
            --bg: #0a0a0a;
            --text: #ffffff;
            --header-bg: #1a1a1a;
            --card: #121212;
            --border: #444444;
        }

        body {
            font-family: 'Arimo', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
            transition: var(--transition);
        }

        .container {
            max-width: 1050px;
            margin: 0 auto;
            background: var(--card);
            padding: 40px;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: var(--transition);
            border: 1px solid var(--border);
        }

        header {
            border-bottom: 4px solid var(--header-bg);
            margin-bottom: 40px;
            padding-bottom: 20px;
        }

        h1 {
            color: var(--header-bg);
            font-size: 2.2em;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: bold;
            transition: var(--transition);
        }

        body.consultant-mode h1 {
            color: var(--primary);
            text-shadow: 0 0 15px rgba(255, 0, 60, 0.7);
        }

        h2 {
            color: #ffffff;
            background: var(--header-bg);
            padding: 12px 20px;
            font-size: 1.1em;
            margin-top: 40px;
            margin-bottom: 12px;
            text-transform: uppercase;
            font-weight: bold;
            transition: var(--transition);
        }

        body.consultant-mode h2 {
            background: var(--primary);
            box-shadow: 0 0 10px rgba(255, 0, 60, 0.3);
        }

        /* Setup Section */
        .setup-section {
            background: rgba(0,0,0,0.02);
            padding: 25px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 12px;
        }

        body.consultant-mode .setup-section {
            background: rgba(255, 255, 255, 0.03);
        }

        .input-group {
            margin-bottom: 16px;
        }

        .input-group label {
            font-weight: bold;
            display: block;
            margin-bottom: 10px;
            font-size: 0.95em;
            color: var(--text);
        }

        .name-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            background: var(--card);
            color: var(--text);
            font-size: 16px;
            box-sizing: border-box;
            font-family: 'Arimo', sans-serif;
            border-radius: 4px;
        }

        .section-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 12px;
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            background: var(--card);
            padding: 10px 15px;
            border: 1px solid var(--border);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.88em;
            height: 64px;
            box-sizing: border-box;
            color: var(--text);
            transition: var(--transition);
        }

        .checkbox-item input {
            margin-right: 12px;
            accent-color: var(--primary);
            width: 18px;
            height: 18px;
            flex-shrink: 0;
        }

        /* Assessment Question Layout */
        .q-wrapper {
            display: none;
            margin-bottom: 35px;
            padding: 25px 0;
            border-bottom: 1px solid var(--border);
            color: var(--text);
        }

        .q-label {
            display: block;
            font-weight: 700;
            margin-bottom: 15px;
            font-size: 1.05em;
            color: var(--text);
        }

        .likert-scale {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
        }

        .likert-option {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            cursor: pointer;
        }

        .likert-option input {
            margin-bottom: 10px;
            accent-color: var(--primary);
            width: 20px;
            height: 20px;
        }

        .likert-option span {
            font-size: 0.72em;
            color: #666;
            line-height: 1.3;
        }

        body.consultant-mode .likert-option span {
            color: #bbbbbb;
        }

        textarea {
            width: 100%;
            min-height: 100px;
            padding: 12px;
            font-family: 'Arimo', sans-serif;
            border: 1px solid var(--border);
            border-radius: 4px;
            background: rgba(0,0,0,0.03);
            color: var(--text);
            box-sizing: border-box;
        }

        /* --- NEW: Tagged Justification Box (per category) --- */
        .justify-box {
            border: 1px solid var(--border);
            background: rgba(0,0,0,0.02);
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 10px;
        }

        body.consultant-mode .justify-box {
            background: rgba(255,255,255,0.03);
        }

        .justify-title {
            font-weight: 700;
            margin-bottom: 10px;
            color: var(--text);
        }

        .justify-row {
            display: grid;
            grid-template-columns: 90px 1fr;
            gap: 10px;
            align-items: start;
            margin-bottom: 10px;
        }

        .justify-row label {
            font-weight: 700;
            font-size: 0.9em;
            padding-top: 8px;
        }

        .justify-tag {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid var(--border);
            border-radius: 4px;
            background: var(--card);
            color: var(--text);
            font-family: 'Arimo', sans-serif;
        }

        .justify-text {
            min-height: 80px;
        }

        .justify-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin-bottom: 8px;
        }

        .btn-ghost, .btn-small {
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text);
            cursor: pointer;
            border-radius: 4px;
            font-family: 'Arimo', sans-serif;
            font-weight: 700;
        }

        .btn-ghost {
            padding: 8px 12px;
        }

        .btn-small {
            padding: 8px 12px;
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }

        .btn-ghost[disabled] {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .justify-list {
            margin-top: 8px;
        }

        .justify-item {
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px;
            margin-top: 8px;
            background: rgba(0,0,0,0.015);
        }

        body.consultant-mode .justify-item {
            background: rgba(255,255,255,0.02);
        }

        .justify-meta {
            font-size: 0.82em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 6px;
        }

        .justify-body {
            font-size: 0.92em;
            line-height: 1.4;
            color: var(--text);
            white-space: pre-wrap;
        }

        /* Report View */
        #report-container {
            display: none;
            margin-top: 50px;
        }

        #report-container p,
        #report-container h1,
        #report-container h3,
        #report-container h4,
        #report-container strong,
        #report-container span,
        #report-container li {
            color: var(--text);
        }

        .chart-box {
            background: var(--card);
            margin: 30px 0;
            height: 450px;
            transition: var(--transition);
        }

        .score-matrix {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }

        .matrix-item {
            padding: 20px;
            background: rgba(0,0,0,0.03);
            border-top: 4px solid var(--primary);
            text-align: center;
            border-radius: 4px;
        }

        body.consultant-mode .matrix-item {
            background: rgba(255, 255, 255, 0.05);
        }

        .matrix-score {
            font-size: 2.2em;
            font-weight: 800;
            color: var(--primary);
        }

        .matrix-label {
            font-size: 0.75em;
            font-weight: bold;
            text-transform: uppercase;
            color: #777;
            transition: var(--transition);
        }

        body.consultant-mode .matrix-label {
            color: #bbbbbb;
        }

        .ai-analyst-box {
            border-left: 6px solid var(--primary);
            background: rgba(21, 149, 145, 0.05);
            padding: 30px;
            margin-top: 40px;
        }

        body.consultant-mode .ai-analyst-box {
            background: rgba(255, 0, 60, 0.08);
        }

        .consultant-note {
            background: rgba(0,0,0,0.02);
            border: 1px solid var(--border);
            padding: 20px;
            margin-top: 15px;
            border-radius: 8px;
            color: var(--text);
        }

        .btn-submit {
            background: var(--primary);
            color: white;
            padding: 20px;
            border: none;
            font-size: 1.05em;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-top: 18px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: var(--transition);
            border-radius: 4px;
        }

        /* Consultant Dashboard */
        .portal-zone {
            margin-top: 80px;
            padding: 30px;
            border-top: 1px dashed var(--border);
            text-align: center;
        }

        #portal-controls {
            display: none;
            margin-top: 20px;
        }

        .btn-admin, .btn-portal-trigger {
            background: #333;
            color: white;
            border: none;
            padding: 12px 24px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            margin: 5px;
            font-family: Arial;
        }

        body.consultant-mode .btn-admin,
        body.consultant-mode .btn-portal-trigger {
            background: var(--primary);
        }

        @media (max-width: 760px) {
            .likert-scale {
                grid-template-columns: repeat(2, 1fr);
            }
            .justify-row {
                grid-template-columns: 1fr;
            }
            .justify-row label {
                padding-top: 0;
            }
        }

        @media print {
            .setup-section,
            .btn-submit,
            form,
            .portal-zone {
                display: none !important;
            }
            #report-container {
                display: block !important;
                border: none;
            }
        }

        /* --- Confidence & Evidence Badges --- */
        .badge {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 3px;
            font-size: 0.72em;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            vertical-align: middle;
            margin-left: 8px;
        }
        .badge-conf-high { background: #d4edda; color: #155724; }
        .badge-conf-med  { background: #fff3cd; color: #856404; }
        .badge-conf-low  { background: #f8d7da; color: #721c24; }
        body.consultant-mode .badge-conf-high { background: #0d3b1e; color: #4ade80; }
        body.consultant-mode .badge-conf-med  { background: #3b2c00; color: #fbbf24; }
        body.consultant-mode .badge-conf-low  { background: #3b0d11; color: #ff6b6b; }

        .badge-ev-strong   { background: #cce5ff; color: #004085; }
        .badge-ev-moderate { background: #e2e3e5; color: #383d41; }
        .badge-ev-weak     { background: #ffeeba; color: #856404; }
        .badge-ev-none     { background: #f5c6cb; color: #721c24; }
        body.consultant-mode .badge-ev-strong   { background: #001f3f; color: #60a5fa; }
        body.consultant-mode .badge-ev-moderate { background: #1a1a1a; color: #9ca3af; }
        body.consultant-mode .badge-ev-weak     { background: #2d2000; color: #fbbf24; }
        body.consultant-mode .badge-ev-none     { background: #1f0008; color: #f87171; }

        /* --- Loading Overlay --- */
        #loading-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.6);
            z-index: 9999;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-family: 'Arimo', sans-serif;
        }
        #loading-overlay.active { display: flex; }

        .loading-spinner {
            width: 48px;
            height: 48px;
            border: 5px solid rgba(255,255,255,0.2);
            border-top-color: #159591;
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
            margin-bottom: 24px;
        }
        body.consultant-mode .loading-spinner { border-top-color: #ff003c; }

        @keyframes spin { to { transform: rotate(360deg); } }

        .loading-text {
            font-size: 1.1em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-align: center;
        }
        .loading-sub {
            font-size: 0.85em;
            color: rgba(255,255,255,0.6);
            margin-top: 8px;
        }

        /* --- Phase 1 Results Panel --- */
        .p1-dim-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 14px;
            margin-top: 14px;
        }
        .p1-dim-card {
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px;
            background: rgba(0,0,0,0.02);
        }
        body.consultant-mode .p1-dim-card { background: rgba(255,255,255,0.03); }

        .p1-dim-title {
            font-weight: 800;
            font-size: 0.95em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }
        .p1-dim-score {
            font-size: 1.6em;
            font-weight: 800;
            color: var(--primary);
            line-height: 1;
        }
        .p1-dim-flag {
            font-size: 0.8em;
            color: #c0392b;
            margin-top: 6px;
        }
        body.consultant-mode .p1-dim-flag { color: #ff6b6b; }

        .p1-verify-panel {
            border: 2px solid #c0392b;
            border-radius: 6px;
            padding: 16px;
            margin-top: 16px;
            background: rgba(192, 57, 43, 0.04);
        }
        body.consultant-mode .p1-verify-panel {
            border-color: #ff003c;
            background: rgba(255, 0, 60, 0.08);
        }
        .p1-verify-title {
            font-weight: 800;
            color: #c0392b;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        body.consultant-mode .p1-verify-title { color: #ff6b6b; }

        .p1-hybrid-panel {
            border-left: 4px solid var(--primary);
            padding: 16px;
            margin-top: 16px;
            background: rgba(21,149,145,0.04);
            border-radius: 0 6px 6px 0;
        }
        body.consultant-mode .p1-hybrid-panel {
            background: rgba(255,0,60,0.06);
            border-left-color: var(--primary);
        }
        .p1-gap-item {
            font-size: 0.88em;
            padding: 6px 0;
            border-bottom: 1px solid var(--border);
        }
        .p1-gap-item:last-child { border-bottom: none; }

        .btn-copy-json {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 16px;
            font-family: 'Arimo', sans-serif;
            font-weight: 700;
            font-size: 0.88em;
            cursor: pointer;
            border-radius: 4px;
            margin-top: 12px;
        }
        .btn-copy-json:hover { background: var(--primary); color: #fff; border-color: var(--primary); }

        /* --- Follow-up Interview Panel --- */
        .btn-followup {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 12px 24px;
            font-family: 'Arimo', sans-serif;
            font-weight: 700;
            font-size: 0.92em;
            cursor: pointer;
            border-radius: 4px;
            margin-top: 20px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .btn-followup:hover { opacity: 0.85; }
        .btn-followup .fq-count {
            background: rgba(255,255,255,0.25);
            border-radius: 12px;
            padding: 2px 9px;
            font-size: 0.88em;
        }

        #followup-interview-panel {
            margin-top: 32px;
            border: 2px solid var(--primary);
            border-radius: 8px;
            overflow: hidden;
            background: var(--card);
        }
        .interview-header {
            background: var(--primary);
            color: #fff;
            padding: 14px 20px;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .interview-header h3 {
            margin: 0;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 800;
            white-space: nowrap;
        }
        .interview-progress-bar-wrap {
            flex: 1;
            background: rgba(255,255,255,0.25);
            border-radius: 10px;
            height: 7px;
            overflow: hidden;
        }
        .interview-progress-bar-fill {
            height: 100%;
            background: #fff;
            border-radius: 10px;
            transition: width 0.4s ease;
        }
        .interview-progress-label {
            font-size: 0.8em;
            opacity: 0.85;
            white-space: nowrap;
        }
        .interview-context-bar {
            background: rgba(192,57,43,0.06);
            border-bottom: 1px solid rgba(192,57,43,0.2);
            padding: 10px 20px;
            font-size: 0.82em;
            color: #c0392b;
        }
        body.consultant-mode .interview-context-bar { color: #ff6b6b; background: rgba(255,0,60,0.06); }

        .interview-chat {
            padding: 20px;
            min-height: 180px;
            max-height: 400px;
            overflow-y: auto;
            background: var(--card);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .msg-bubble {
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.9em;
            line-height: 1.55;
        }
        .msg-bubble.assistant {
            align-self: flex-start;
            background: rgba(21,149,145,0.09);
            border: 1px solid rgba(21,149,145,0.2);
            color: var(--text);
        }
        body.consultant-mode .msg-bubble.assistant {
            background: rgba(255,0,60,0.07);
            border-color: rgba(255,0,60,0.2);
        }
        .msg-bubble.user {
            align-self: flex-end;
            background: var(--primary);
            color: #fff;
        }
        .interview-input-area {
            border-top: 1px solid var(--border);
            padding: 14px 20px;
            background: var(--card);
        }
        .interview-input-row {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        #interview-input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 4px;
            font-family: 'Arimo', sans-serif;
            font-size: 0.9em;
            resize: vertical;
            min-height: 58px;
            max-height: 140px;
            background: var(--card);
            color: var(--text);
        }
        .interview-btn-col { display: flex; flex-direction: column; gap: 7px; }
        .btn-iv-send {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 10px 20px;
            font-family: 'Arimo', sans-serif;
            font-weight: 700;
            cursor: pointer;
            border-radius: 4px;
            font-size: 0.88em;
        }
        .btn-iv-skip {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 16px;
            font-family: 'Arimo', sans-serif;
            cursor: pointer;
            border-radius: 4px;
            font-size: 0.82em;
        }
        .interview-complete-box {
            padding: 20px;
            text-align: center;
            background: rgba(21,149,145,0.05);
            border-top: 1px solid var(--border);
        }
    </style>
</head>
<body>

<!-- Loading Overlay -->
<div id="loading-overlay">
    <div class="loading-spinner"></div>
    <div class="loading-text">Consultant Agent is Reviewing Evidence...</div>
    <div class="loading-sub">Parsing justifications &amp; running statistical benchmarking</div>
</div>

<div class="container">
    <header>
        <h1 id="main-title">AI Organizational Maturity Assessment</h1>
    </header>

    <!-- Setup -->
    <div class="setup-section">
        <div class="input-group">
            <label>Respondent Name</label>
            <input type="text" id="userName" class="name-input" placeholder="Full name" />
        </div>

        <div class="input-group">
            <label>Organization Name</label>
            <input type="text" id="orgName" class="name-input" placeholder="Enter company name" />
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
            <div class="input-group">
                <label>Role <span style="font-weight:400; font-size:0.85em;">(used for peer benchmarking)</span></label>
                <select id="respondentRole" class="name-input">
                    <option value="">— Select role —</option>
                    <option value="Senior Leadership">Senior Leadership</option>
                    <option value="Tech Lead">Tech Lead</option>
                    <option value="Data Lead">Data Lead</option>
                    <option value="Operations">Operations</option>
                    <option value="HR">HR</option>
                    <option value="Finance">Finance</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div class="input-group">
                <label>Organization Unit <span style="font-weight:400; font-size:0.85em;">(optional)</span></label>
                <input type="text" id="orgUnit" class="name-input" placeholder="e.g. Enterprise Data Platform" />
            </div>
        </div>

        <div class="input-group">
            <label>Select Relevant Sections</label>
            <div class="section-selector">
                <label class="checkbox-item"><input type="checkbox" name="userSection" value="leadership" onchange="filterQuestions()" /> Senior Leadership</label>
                <label class="checkbox-item"><input type="checkbox" name="userSection" value="tech" onchange="filterQuestions()" /> Technology</label>
                <label class="checkbox-item"><input type="checkbox" name="userSection" value="data" onchange="filterQuestions()" /> Data</label>
                <label class="checkbox-item"><input type="checkbox" name="userSection" value="hr" onchange="filterQuestions()" /> HR / Culture / Workforce</label>
            </div>
        </div>

        <!-- DEMO BUTTON — remove before client delivery -->
        <div style="margin-top:16px; display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
            <button type="button" onclick="loadDemoData()" style="background:#6c757d; color:#fff; border:none; padding:9px 18px; border-radius:4px; cursor:pointer; font-size:0.88em; font-family:inherit; letter-spacing:0.3px;">
                &#9654; Load Demo (Max / Cmax)
            </button>
            <span style="font-size:0.78em; color:#999;">Original audio not available (NDA) — text justifications included.</span>
        </div>
    </div>

    <form id="assessmentForm">
        <!-- =========================================================
             1) LEADERSHIP
        ========================================================== -->
        <div class="cat-header-div" id="head-leadership" style="display:none;">
            <h2>1. Leadership, Strategy & Risk</h2>

            <!-- NEW: Tagged justifications for this category -->
            <div class="justify-box" data-cat="Leadership & Vision">
                <div class="justify-title">Add justification (tagged)</div>

                <div class="justify-row">
                    <label>Tag</label>
                    <select class="justify-tag"></select>
                </div>

                <div class="justify-row">
                    <label>Text</label>
                    <textarea class="justify-text" placeholder="Add context, examples, metrics, owners, constraints..."></textarea>
                </div>

                <div class="justify-controls">
                    <button type="button" class="btn-ghost" data-action="start">Record</button>
                    <button type="button" class="btn-ghost" data-action="stop" disabled>Stop</button>
                    <audio class="justify-audio" controls style="display:none;"></audio>
                    <button type="button" class="btn-small" data-action="add">Add note</button>
                </div>

                <div class="justify-list"></div>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership" data-id="L1" data-cat="Leadership & Vision" data-label="Strategic AI Vision">
            <label class="q-label">Strategic Vision: Our organization has a clear and compelling AI vision and roadmap in place.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="L1" value="1" /><span>Strongly Disagree</span></label>
                <label class="likert-option"><input type="radio" name="L1" value="2" /><span>Disagree</span></label>
                <label class="likert-option"><input type="radio" name="L1" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="L1" value="4" /><span>Agree</span></label>
                <label class="likert-option"><input type="radio" name="L1" value="5" /><span>Strongly Agree</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership" data-id="L2" data-cat="Leadership & Vision" data-label="Corporate Strategy Alignment">
            <label class="q-label">Alignment: AI objectives are explicitly aligned with our primary corporate strategy.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="L2" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="L2" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="L2" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="L2" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="L2" value="5" /><span>5</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership" data-id="L3" data-cat="Leadership & Vision" data-label="AI Enterprise Metrics">
            <label class="q-label">Metrics: How mature are the KPIs used to track AI investment value and business ROI?</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="L3" value="1" /><span>Not Ready</span></label>
                <label class="likert-option"><input type="radio" name="L3" value="2" /><span>Exploring</span></label>
                <label class="likert-option"><input type="radio" name="L3" value="3" /><span>Established</span></label>
                <label class="likert-option"><input type="radio" name="L3" value="4" /><span>Integrated</span></label>
                <label class="likert-option"><input type="radio" name="L3" value="5" /><span>Optimized</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership" data-id="L_Risk" data-cat="Leadership & Vision" data-label="AI Risk Appetite">
            <label class="q-label">Risk Appetite: What level of AI risk is leadership willing to accept for competitive gain?</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="L_Risk" value="1" /><span>Conservative</span></label>
                <label class="likert-option"><input type="radio" name="L_Risk" value="2" /><span>Cautious</span></label>
                <label class="likert-option"><input type="radio" name="L_Risk" value="3" /><span>Balanced</span></label>
                <label class="likert-option"><input type="radio" name="L_Risk" value="4" /><span>Proactive</span></label>
                <label class="likert-option"><input type="radio" name="L_Risk" value="5" /><span>Innovation First</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech" data-id="Q_Decision" data-cat="Leadership & Vision" data-label="AI Decision Ownership">
            <label class="q-label">Qualitative: Who holds final accountability for AI investment and deployment decisions?</label>
            <textarea name="Q_Decision" placeholder="e.g. CTO, CFO, BU Leads..." data-insight="Centralized accountability is the strongest predictor of AI project speed and sustainability."></textarea>
        </div>

        <!-- =========================================================
             2) WAYS OF WORKING
        ========================================================== -->
        <div class="cat-header-div" id="head-ways" style="display:none;">
            <h2>2. Operational Ways of Working</h2>

            <div class="justify-box" data-cat="Ways of Working">
                <div class="justify-title">Add justification (tagged)</div>

                <div class="justify-row">
                    <label>Tag</label>
                    <select class="justify-tag"></select>
                </div>

                <div class="justify-row">
                    <label>Text</label>
                    <textarea class="justify-text" placeholder="Add examples of workflows, handoffs, decisions, blockers..."></textarea>
                </div>

                <div class="justify-controls">
                    <button type="button" class="btn-ghost" data-action="start">Record</button>
                    <button type="button" class="btn-ghost" data-action="stop" disabled>Stop</button>
                    <audio class="justify-audio" controls style="display:none;"></audio>
                    <button type="button" class="btn-small" data-action="add">Add note</button>
                </div>

                <div class="justify-list"></div>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech,data" data-id="W1" data-cat="Ways of Working" data-label="Technology Designed for Business">
            <label class="q-label">Collaboration: There is a strong, collaborative connection between business and technical teams.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="W1" value="1" /><span>Strongly Disagree</span></label>
                <label class="likert-option"><input type="radio" name="W1" value="2" /><span>Disagree</span></label>
                <label class="likert-option"><input type="radio" name="W1" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="W1" value="4" /><span>Agree</span></label>
                <label class="likert-option"><input type="radio" name="W1" value="5" /><span>Strongly Agree</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech" data-id="W_Conflict" data-cat="Ways of Working" data-label="Conflict Resolution">
            <label class="q-label">Conflict Resolution: How effective is the process for resolving disagreements on AI direction?</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="W_Conflict" value="1" /><span>None</span></label>
                <label class="likert-option"><input type="radio" name="W_Conflict" value="2" /><span>Rarely</span></label>
                <label class="likert-option"><input type="radio" name="W_Conflict" value="3" /><span>Sometimes</span></label>
                <label class="likert-option"><input type="radio" name="W_Conflict" value="4" /><span>Mostly</span></label>
                <label class="likert-option"><input type="radio" name="W_Conflict" value="5" /><span>Optimized</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech" data-id="W3" data-cat="Ways of Working" data-label="Utilize AI-Driven Insights">
            <label class="q-label">Insights: How deeply are AI-driven insights integrated into daily decision-making?</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="W3" value="1" /><span>No Usage</span></label>
                <label class="likert-option"><input type="radio" name="W3" value="2" /><span>Manual</span></label>
                <label class="likert-option"><input type="radio" name="W3" value="3" /><span>Partial</span></label>
                <label class="likert-option"><input type="radio" name="W3" value="4" /><span>Integrated</span></label>
                <label class="likert-option"><input type="radio" name="W3" value="5" /><span>Automated</span></label>
            </div>
        </div>

        <!-- =========================================================
             3) CULTURE / WORKFORCE
        ========================================================== -->
        <div class="cat-header-div" id="head-hr" style="display:none;">
            <h2>3. Culture & Change Readiness</h2>

            <div class="justify-box" data-cat="Culture & Workforce">
                <div class="justify-title">Add justification (tagged)</div>

                <div class="justify-row">
                    <label>Tag</label>
                    <select class="justify-tag"></select>
                </div>

                <div class="justify-row">
                    <label>Text</label>
                    <textarea class="justify-text" placeholder="Add context on readiness, trust, resistance, change fatigue..."></textarea>
                </div>

                <div class="justify-controls">
                    <button type="button" class="btn-ghost" data-action="start">Record</button>
                    <button type="button" class="btn-ghost" data-action="stop" disabled>Stop</button>
                    <audio class="justify-audio" controls style="display:none;"></audio>
                    <button type="button" class="btn-small" data-action="add">Add note</button>
                </div>

                <div class="justify-list"></div>
            </div>
        </div>

        <div class="q-wrapper" data-sections="hr" data-id="C1" data-cat="Culture & Workforce" data-label="Organization Aligns to Business Priorities">
            <label class="q-label">Alignment: The organization aligns quickly to business transformation and AI priorities.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="C1" value="1" /><span>Strongly Disagree</span></label>
                <label class="likert-option"><input type="radio" name="C1" value="2" /><span>Disagree</span></label>
                <label class="likert-option"><input type="radio" name="C1" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="C1" value="4" /><span>Agree</span></label>
                <label class="likert-option"><input type="radio" name="C1" value="5" /><span>Strongly Agree</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="hr" data-id="C3" data-cat="Culture & Workforce" data-label="Employees Willingness to Embrace AI">
            <label class="q-label">Willingness: Employees are willing and excited to embrace AI tools in their daily work.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="C3" value="1" /><span>Strongly Disagree</span></label>
                <label class="likert-option"><input type="radio" name="C3" value="2" /><span>Disagree</span></label>
                <label class="likert-option"><input type="radio" name="C3" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="C3" value="4" /><span>Agree</span></label>
                <label class="likert-option"><input type="radio" name="C3" value="5" /><span>Strongly Agree</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="hr" data-id="C_Fatigue" data-cat="Culture & Workforce" data-label="Transformation Legacy">
            <label class="q-label">Legacy: How well has the organization historically managed large-scale technological shifts?</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="C_Fatigue" value="1" /><span>Very Poorly</span></label>
                <label class="likert-option"><input type="radio" name="C_Fatigue" value="2" /><span>Struggled</span></label>
                <label class="likert-option"><input type="radio" name="C_Fatigue" value="3" /><span>Average</span></label>
                <label class="likert-option"><input type="radio" name="C_Fatigue" value="4" /><span>Well</span></label>
                <label class="likert-option"><input type="radio" name="C_Fatigue" value="5" /><span>Excellent</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="hr,leadership" data-id="Q_Concerns" data-cat="Culture & Workforce" data-label="Employee Concerns">
            <label class="q-label">Qualitative: What are the primary concerns regarding AI adoption today?</label>
            <textarea name="Q_Concerns" placeholder="e.g. job security, skill gaps..." data-insight="Addressing psychological safety is essential for reducing long-term adoption resistance."></textarea>
        </div>

        <!-- =========================================================
             4) GOVERNANCE
        ========================================================== -->
        <div class="cat-header-div" id="head-gov" style="display:none;">
            <h2>4. Governance Readiness</h2>

            <div class="justify-box" data-cat="Governance Readiness">
                <div class="justify-title">Add justification (tagged)</div>

                <div class="justify-row">
                    <label>Tag</label>
                    <select class="justify-tag"></select>
                </div>

                <div class="justify-row">
                    <label>Text</label>
                    <textarea class="justify-text" placeholder="Reference policies, committees, reviews, compliance, incidents..."></textarea>
                </div>

                <div class="justify-controls">
                    <button type="button" class="btn-ghost" data-action="start">Record</button>
                    <button type="button" class="btn-ghost" data-action="stop" disabled>Stop</button>
                    <audio class="justify-audio" controls style="display:none;"></audio>
                    <button type="button" class="btn-small" data-action="add">Add note</button>
                </div>

                <div class="justify-list"></div>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech" data-id="G1" data-cat="Governance Readiness" data-label="Solid Governance Structure">
            <label class="q-label">Policy: We have a robust AI governance and ethics framework currently active.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="G1" value="1" /><span>Strongly Disagree</span></label>
                <label class="likert-option"><input type="radio" name="G1" value="2" /><span>Disagree</span></label>
                <label class="likert-option"><input type="radio" name="G1" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="G1" value="4" /><span>Agree</span></label>
                <label class="likert-option"><input type="radio" name="G1" value="5" /><span>Strongly Agree</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech" data-id="G4" data-cat="Governance Readiness" data-label="Effective Risk Mitigation">
            <label class="q-label">Risk Detection: Our processes identify bias, privacy, and security risks in AI models.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="G4" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="G4" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="G4" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="G4" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="G4" value="5" /><span>5</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech" data-id="G_Shadow" data-cat="Governance Readiness" data-label="Shadow AI Confidence">
            <label class="q-label">Shadow AI: Confidence that AI usage is restricted to approved platforms.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="G_Shadow" value="1" /><span>None</span></label>
                <label class="likert-option"><input type="radio" name="G_Shadow" value="2" /><span>Low</span></label>
                <label class="likert-option"><input type="radio" name="G_Shadow" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="G_Shadow" value="4" /><span>Confident</span></label>
                <label class="likert-option"><input type="radio" name="G_Shadow" value="5" /><span>Full</span></label>
            </div>
        </div>

        <!-- =========================================================
             5) TECHNOLOGY
        ========================================================== -->
        <div class="cat-header-div" id="head-tech" style="display:none;">
            <h2>5. Technology Readiness</h2>

            <div class="justify-box" data-cat="Technology Readiness">
                <div class="justify-title">Add justification (tagged)</div>

                <div class="justify-row">
                    <label>Tag</label>
                    <select class="justify-tag"></select>
                </div>

                <div class="justify-row">
                    <label>Text</label>
                    <textarea class="justify-text" placeholder="Reference cloud stack, MLOps, monitoring, security architecture..."></textarea>
                </div>

                <div class="justify-controls">
                    <button type="button" class="btn-ghost" data-action="start">Record</button>
                    <button type="button" class="btn-ghost" data-action="stop" disabled>Stop</button>
                    <audio class="justify-audio" controls style="display:none;"></audio>
                    <button type="button" class="btn-small" data-action="add">Add note</button>
                </div>

                <div class="justify-list"></div>
            </div>
        </div>

        <div class="q-wrapper" data-sections="tech" data-id="T1" data-cat="Technology Readiness" data-label="Modern Cloud Infrastructure">
            <label class="q-label">Cloud: Readiness to support high-performance AI model deployment.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="T1" value="1" /><span>Not Ready</span></label>
                <label class="likert-option"><input type="radio" name="T1" value="2" /><span>Initial</span></label>
                <label class="likert-option"><input type="radio" name="T1" value="3" /><span>Established</span></label>
                <label class="likert-option"><input type="radio" name="T1" value="4" /><span>Scaleable</span></label>
                <label class="likert-option"><input type="radio" name="T1" value="5" /><span>Optimized</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="tech" data-id="T2" data-cat="Technology Readiness" data-label="Core Systems AI Ready">
            <label class="q-label">Backbone: ERP/CRM readiness to serve as an enterprise AI foundation.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="T2" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="T2" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="T2" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="T2" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="T2" value="5" /><span>5</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="tech" data-id="T4" data-cat="Technology Readiness" data-label="ML Ops Maturity">
            <label class="q-label">ML Ops: Maturity of AI platform monitoring and automated deployment.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="T4" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="T4" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="T4" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="T4" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="T4" value="5" /><span>5</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="tech" data-id="T5" data-cat="Technology Readiness" data-label="Security Architecture">
            <label class="q-label">Security: Enterprise architecture supports modern zero-trust AI security needs.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="T5" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="T5" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="T5" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="T5" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="T5" value="5" /><span>5</span></label>
            </div>
        </div>

        <!-- =========================================================
             6) DATA
        ========================================================== -->
        <div class="cat-header-div" id="head-data" style="display:none;">
            <h2>6. Data Assets & Quality</h2>

            <div class="justify-box" data-cat="Data Readiness">
                <div class="justify-title">Add justification (tagged)</div>

                <div class="justify-row">
                    <label>Tag</label>
                    <select class="justify-tag"></select>
                </div>

                <div class="justify-row">
                    <label>Text</label>
                    <textarea class="justify-text" placeholder="Reference data owners, dictionaries, pipelines, quality checks..."></textarea>
                </div>

                <div class="justify-controls">
                    <button type="button" class="btn-ghost" data-action="start">Record</button>
                    <button type="button" class="btn-ghost" data-action="stop" disabled>Stop</button>
                    <audio class="justify-audio" controls style="display:none;"></audio>
                    <button type="button" class="btn-small" data-action="add">Add note</button>
                </div>

                <div class="justify-list"></div>
            </div>
        </div>

        <div class="q-wrapper" data-sections="data,tech" data-id="D1" data-cat="Data Readiness" data-label="Data structured & clean">
            <label class="q-label">Health: Data is structured and clean across primary business domains.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="D1" value="1" /><span>Strongly Disagree</span></label>
                <label class="likert-option"><input type="radio" name="D1" value="2" /><span>Disagree</span></label>
                <label class="likert-option"><input type="radio" name="D1" value="3" /><span>Neutral</span></label>
                <label class="likert-option"><input type="radio" name="D1" value="4" /><span>Agree</span></label>
                <label class="likert-option"><input type="radio" name="D1" value="5" /><span>Strongly Agree</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="data,tech" data-id="D2" data-cat="Data Readiness" data-label="Data integrated for AI">
            <label class="q-label">Accessibility: Cross-functional data is formatted and available for model training.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="D2" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="D2" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="D2" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="D2" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="D2" value="5" /><span>5</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="data,tech" data-id="D3" data-cat="Data Readiness" data-label="Data Dictionary and Ownership">
            <label class="q-label">Governance: We have clear data dictionaries and assigned domain ownership.</label>
            <div class="likert-scale">
                <label class="likert-option"><input type="radio" name="D3" value="1" /><span>1</span></label>
                <label class="likert-option"><input type="radio" name="D3" value="2" /><span>2</span></label>
                <label class="likert-option"><input type="radio" name="D3" value="3" /><span>3</span></label>
                <label class="likert-option"><input type="radio" name="D3" value="4" /><span>4</span></label>
                <label class="likert-option"><input type="radio" name="D3" value="5" /><span>5</span></label>
            </div>
        </div>

        <div class="q-wrapper" data-sections="leadership,tech,data,hr" data-id="Q_Vision" data-cat="Data Readiness" data-label="Future-State Vision">
            <label class="q-label">Qualitative: What is the desired day-to-day impact of AI on the organization in two years?</label>
            <textarea name="Q_Vision" placeholder="Describe the future state..." data-insight="A concrete 2-year vision aligns Roadmap activities toward unified business goals."></textarea>
        </div>

        <!-- Existing local report -->
        <button type="button" class="btn-submit" onclick="generateReport()">Analyze Maturity</button>

        <!-- NEW: Phase 1 backend analysis button -->
        <button type="button" class="btn-submit" onclick="runPhase1AgentAnalysis()" style="background:#222;">
            Analyze with AI (Phase 1)
        </button>
    </form>

    <!-- =========================
         Report Container
    ========================== -->
    <div id="report-container">
        <div class="report-card">
            <h1 id="report-title">Diagnostic Maturity Report</h1>
            <p><strong>Prepared for:</strong> <span id="display-name"></span></p>

            <div class="chart-box">
                <canvas id="spiderChart"></canvas>
            </div>

            <div class="score-matrix" id="score-matrix"></div>

            <div class="ai-analyst-box" id="ai-output">
                <h3 id="analyst-header">Strategic Analyst Conclusion</h3>
                <div id="ai-insight-text"></div>
            </div>

            <h3 style="margin-top:40px;">Qualitative Response Briefing</h3>
            <div id="qualitative-results"></div>

            <!-- Phase 1 agent results from backend -->
            <h3 style="margin-top:40px;">Phase 1 Agent Analysis</h3>
            <div id="phase1-agent-results" class="consultant-note">
                Run "Analyze with AI (Phase 1)" to get the full diagnostic report.
            </div>

            <button class="btn-submit" onclick="alert('Secure Link Initialized: Data bundle ready for SharePoint Vault archiving. (Pending Authentication)')" style="margin-top:40px; background-color: #444;">
                Send Report to AHI
            </button>
        </div>
    </div>

    <!-- Follow-up Interview Panel (shown after Phase 1 analysis when flags exist) -->
    <div id="followup-interview-panel" style="display:none;">
        <div class="interview-header">
            <h3>Follow-up Interview</h3>
            <div class="interview-progress-bar-wrap">
                <div class="interview-progress-bar-fill" id="interview-progress-fill" style="width:0%"></div>
            </div>
            <div class="interview-progress-label" id="interview-progress-label">0 of 0</div>
        </div>
        <div class="interview-context-bar" id="interview-context-bar" style="display:none;"></div>
        <div class="interview-chat" id="interview-chat"></div>
        <div class="interview-input-area" id="interview-input-area">
            <div class="interview-input-row">
                <textarea id="interview-input"
                    placeholder="Type your response... (Shift+Enter for new line, Enter to send)"
                    onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendInterviewResponse();}"></textarea>
                <div class="interview-btn-col">
                    <button class="btn-iv-send" onclick="sendInterviewResponse()">Send</button>
                    <button class="btn-iv-skip" onclick="skipInterviewQuestion()">Skip</button>
                </div>
            </div>
        </div>
        <div class="interview-complete-box" id="interview-complete-box" style="display:none;">
            <p style="font-weight:700; margin-bottom:6px;">Interview Complete</p>
            <p style="font-size:0.88em; color:#888; margin-bottom:12px;">All flagged areas have been addressed. The session data is ready for your consultant.</p>
            <button class="btn-copy-json" onclick="copyInterviewPayload()">Copy Session Payload</button>
        </div>
    </div>

    <!-- Admin / consultant mode -->
    <div class="portal-zone">
        <button class="btn-portal-trigger" id="portal-trigger" onclick="unlockConsultantMode()">Unlock AHI Consultant Dashboard</button>
        <div id="portal-controls">
            <p style="font-weight:bold; text-transform:uppercase;">Admin Access Active: Pro Functions Unlocked</p>
            <button class="btn-admin" onclick="downloadCSV()">Export Strategic CSV</button>
            <button class="btn-admin" onclick="copyLLMPrompt()">Copy for AI Analysis</button>
            <button class="btn-admin" onclick="location.reload()">Reset App</button>
        </div>
    </div>
</div>

<script>
/* =========================================================
   CONFIG
========================================================= */
const CONFIG = {
    categories: ["Leadership & Vision", "Ways of Working", "Culture & Workforce", "Governance Readiness", "Technology Readiness", "Data Readiness"],
    stages: [
        { name: "Nascent", min: 0.0, max: 2.19, blurb: "Foundational stage. AI interest is isolated. You lack the consistent data readiness and ownership needed to scale." },
        { name: "Exploring", min: 2.2, max: 3.19, blurb: "Initial practices are emerging. Scale requires tighter alignment across business and tech units." },
        { name: "Established", min: 3.2, max: 4.19, blurb: "Standardized stage. You have clear capability. Focus on scaling your operating model and tracking ROI." },
        { name: "Leading", min: 4.2, max: 5.0, blurb: "Advanced stage. AI is a core strategic lever. Predictive decisioning and automated governance are primary goals." }
    ],
    PHASE1_API_BASE: "http://127.0.0.1:8001"  // local FastAPI backend
};

let myChart = null;

/* =========================================================
   NEW: Tagged Justification Storage + Voice State
========================================================= */
const JUSTIFICATIONS = []; // {cat, tagId, tagLabel, text, audioUrl, ts}
const REC = {};           // recorder state by category

function getVisibleQuestionElements() {
    return Array.from(document.querySelectorAll('.q-wrapper')).filter(q => q.style.display === 'block');
}

/* =========================================================
   NEW: Justification Dropdowns + UI
========================================================= */
function refreshJustificationDropdowns() {
    document.querySelectorAll('.justify-box').forEach(box => {
        const cat = box.dataset.cat;
        const sel = box.querySelector('.justify-tag');
        if (!sel) return;

        const previous = sel.value || "GENERAL";
        sel.innerHTML = "";

        const generalOption = document.createElement('option');
        generalOption.value = "GENERAL";
        generalOption.textContent = "General note (not tied to a specific question)";
        sel.appendChild(generalOption);

        const visibleQs = getVisibleQuestionElements().filter(q => q.dataset.cat === cat);

        visibleQs.forEach(q => {
            const opt = document.createElement('option');
            opt.value = q.dataset.id;
            opt.textContent = `${q.dataset.id} - ${q.dataset.label || q.dataset.id}`;
            sel.appendChild(opt);
        });

        const stillExists = Array.from(sel.options).some(o => o.value === previous);
        sel.value = stillExists ? previous : "GENERAL";
    });
}

function initJustificationUI() {
    document.querySelectorAll('.justify-box').forEach(box => {
        const cat = box.dataset.cat;

        const btnStart = box.querySelector('[data-action="start"]');
        const btnStop = box.querySelector('[data-action="stop"]');
        const btnAdd = box.querySelector('[data-action="add"]');
        const audioEl = box.querySelector('.justify-audio');

        if (!REC[cat]) {
            REC[cat] = { recorder: null, stream: null, chunks: [], audioUrl: null };
        }

        if (audioEl) {
            audioEl.style.display = 'none';
        }

        btnStart?.addEventListener('click', () => startRecording(cat, box));
        btnStop?.addEventListener('click', () => stopRecording(cat, box));
        btnAdd?.addEventListener('click', () => addJustification(cat, box));
    });

    refreshJustificationDropdowns();
}

async function startRecording(cat, box) {
    const btnStart = box.querySelector('[data-action="start"]');
    const btnStop = box.querySelector('[data-action="stop"]');
    const audioEl = box.querySelector('.justify-audio');

    // Clear previous unsaved clip for this category
    if (REC[cat]?.audioUrl) {
        try { URL.revokeObjectURL(REC[cat].audioUrl); } catch (e) {}
        REC[cat].audioUrl = null;
    }
    if (audioEl) {
        audioEl.src = "";
        audioEl.style.display = "none";
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);

        REC[cat].stream = stream;
        REC[cat].recorder = recorder;
        REC[cat].chunks = [];

        recorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) REC[cat].chunks.push(e.data);
        };

        recorder.onstop = () => {
            const blob = new Blob(REC[cat].chunks, { type: "audio/webm" });
            const url = URL.createObjectURL(blob);
            REC[cat].audioUrl = url;

            if (audioEl) {
                audioEl.src = url;
                audioEl.style.display = "block";
            }

            if (REC[cat].stream) {
                REC[cat].stream.getTracks().forEach(t => t.stop());
                REC[cat].stream = null;
            }
        };

        recorder.start();

        if (btnStart) btnStart.disabled = true;
        if (btnStop) btnStop.disabled = false;

        // Safety auto-stop after 60s
        setTimeout(() => {
            if (REC[cat]?.recorder && REC[cat].recorder.state === "recording") {
                stopRecording(cat, box);
            }
        }, 60000);

    } catch (err) {
        alert("Microphone permission denied or unavailable. Voice recording requires HTTPS on Squarespace (local testing may vary by browser).");
    }
}

function stopRecording(cat, box) {
    const btnStart = box.querySelector('[data-action="start"]');
    const btnStop = box.querySelector('[data-action="stop"]');

    const recorder = REC[cat]?.recorder;
    if (recorder && recorder.state === "recording") recorder.stop();

    if (btnStart) btnStart.disabled = false;
    if (btnStop) btnStop.disabled = true;
}

async function addJustification(cat, box) {
    const tagSel = box.querySelector('.justify-tag');
    const textEl = box.querySelector('.justify-text');
    const btnAdd = box.querySelector('[data-action="add"]');

    const tagId    = tagSel ? tagSel.value : "GENERAL";
    const tagLabel = tagSel ? (tagSel.options[tagSel.selectedIndex]?.textContent || tagId) : tagId;
    let   text     = textEl ? textEl.value.trim() : "";
    const audioUrl = REC[cat]?.audioUrl || null;
    const audioBlob = REC[cat]?.chunks?.length
        ? new Blob(REC[cat].chunks, { type: "audio/webm" })
        : null;

    if (!text && !audioUrl) {
        alert("Add text or record voice before saving the note.");
        return;
    }

    // Auto-transcribe audio if text box is empty and audio exists
    if (!text && audioBlob) {
        if (btnAdd) { btnAdd.textContent = "Transcribing..."; btnAdd.disabled = true; }
        try {
            const formData = new FormData();
            formData.append("audio", audioBlob, "note.webm");
            const res = await fetch(`${CONFIG.PHASE1_API_BASE}/api/transcribe-note`, {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                if (data.transcript) {
                    text = data.transcript;
                    if (textEl) textEl.value = text; // show transcript in text box
                } else if (!data.whisper_available) {
                    text = "(voice note — install openai-whisper for auto-transcription)";
                }
            }
        } catch (e) {
            // Transcription unavailable — save audio-only note
            text = "";
        } finally {
            if (btnAdd) { btnAdd.textContent = "Add note"; btnAdd.disabled = false; }
        }
    }

    JUSTIFICATIONS.push({
        cat,
        tagId,
        tagLabel,
        text,
        audioUrl,
        transcribed: !!(text && audioBlob),
        ts: new Date().toISOString()
    });

    // Clear text box only; keep recorded audio visible until next recording
    if (textEl) textEl.value = "";

    renderJustificationList(cat);
}

function renderJustificationList(cat) {
    const box = Array.from(document.querySelectorAll('.justify-box')).find(b => b.dataset.cat === cat);
    if (!box) return;

    const list = box.querySelector('.justify-list');
    if (!list) return;

    const items = JUSTIFICATIONS.filter(j => j.cat === cat);
    if (!items.length) {
        list.innerHTML = "";
        return;
    }

    list.innerHTML = items.slice().reverse().map(j => {
        const safeText = (j.text || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        const time = new Date(j.ts).toLocaleString();
        const audioHTML = j.audioUrl ? `<div style="margin-top:8px;"><audio controls src="${j.audioUrl}" style="width:100%;"></audio></div>` : "";
        const audioTag = j.audioUrl
            ? (j.transcribed ? `<span style="color:var(--primary);font-weight:700;"> | AUDIO + TRANSCRIBED</span>` : ` | AUDIO`)
            : "";
        return `
            <div class="justify-item">
                <div class="justify-meta">${j.tagLabel}${audioTag} | ${time}</div>
                ${safeText ? `<div class="justify-body">${safeText}</div>` : `<div class="justify-body"><em>(Voice note — no transcript)</em></div>`}
                ${audioHTML}
            </div>
        `;
    }).join("");
}

/* Helpers used in report / export */
function renderJustificationsForReport(visibleCatsSet) {
    const items = JUSTIFICATIONS.filter(j => !visibleCatsSet || visibleCatsSet.has(j.cat));
    if (!items.length) return "";

    return items.map(j => {
        const safeText = (j.text || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        const audioHTML = j.audioUrl ? `<div style="margin-top:8px;"><audio controls src="${j.audioUrl}" style="width:100%;"></audio></div>` : "";
        return `
            <div class="consultant-note">
                <p><strong>${j.cat}</strong> - <span style="color:var(--primary); font-weight:800;">${j.tagLabel}</span></p>
                ${safeText ? `<p><em>"${safeText}"</em></p>` : `<p><em>(Voice note attached)</em></p>`}
                ${audioHTML}
            </div>
        `;
    }).join("");
}

function getTaggedJustificationsForQuestion(cat, qid) {
    const matches = JUSTIFICATIONS.filter(j => j.cat === cat && j.tagId === qid);
    const text = matches.map(m => m.text).filter(Boolean).join(" | ");
    const audio = matches.some(m => !!m.audioUrl);
    return { text, audio };
}

/* =========================================================
   Core UI Behavior
========================================================= */
function filterQuestions() {
    const selected = Array.from(document.querySelectorAll('input[name="userSection"]:checked')).map(cb => cb.value);
    const questions = document.querySelectorAll('.q-wrapper');

    const heads = {
        leadership: document.getElementById('head-leadership'),
        data: document.getElementById('head-data'),
        hr: document.getElementById('head-hr'),
        ways: document.getElementById('head-ways'),
        gov: document.getElementById('head-gov'),
        tech: document.getElementById('head-tech')
    };

    questions.forEach(q => q.style.display = 'none');
    Object.values(heads).forEach(h => { if (h) h.style.display = 'none'; });

    if (selected.length === 0) {
        refreshJustificationDropdowns(); // IMPORTANT: still refresh tags when clearing
        return;
    }

    questions.forEach(q => {
        const qSections = q.dataset.sections.split(',');
        if (selected.some(s => qSections.includes(s))) {
            q.style.display = 'block';

            if (q.dataset.cat.includes('Leadership')) heads.leadership.style.display = 'block';
            if (q.dataset.cat.includes('Data')) heads.data.style.display = 'block';
            if (q.dataset.cat.includes('Culture')) heads.hr.style.display = 'block';
            if (q.dataset.cat.includes('Ways')) heads.ways.style.display = 'block';
            if (q.dataset.cat.includes('Governance')) heads.gov.style.display = 'block';
            if (q.dataset.cat.includes('Technology')) heads.tech.style.display = 'block';
        }
    });

    // IMPORTANT: this belongs inside filterQuestions (not outside)
    refreshJustificationDropdowns();
}

function unlockConsultantMode() {
    const pw = prompt("Enter AHI Access Key:");
    if (pw === "AHI2026") {
        document.body.classList.add("consultant-mode");
        document.getElementById("portal-controls").style.display = "block";
        document.getElementById("portal-trigger").style.display = "none";
        document.getElementById("main-title").innerText = "AHI PRO STRATEGIC CONSOLE";

        if (myChart) generateReport();
    } else {
        alert("Denied.");
    }
}

/* =========================================================
   Existing local report (enhanced to include tagged notes)
========================================================= */
function generateReport() {
    const nameInput = document.getElementById("userName").value.trim() || "Strategic Partner";
    const questions = getVisibleQuestionElements();

    const scoreBuckets = {};
    CONFIG.categories.forEach(cat => scoreBuckets[cat] = { sum: 0, count: 0 });

    let qualHTML = "";
    let matrixHTML = "";

    questions.forEach(q => {
        const cat = q.dataset.cat;
        const radio = q.querySelector('input[type="radio"]:checked');
        const textarea = q.querySelector('textarea');

        if (radio) {
            scoreBuckets[cat].sum += parseInt(radio.value);
            scoreBuckets[cat].count++;
        }

        if (textarea && textarea.value.trim() !== "") {
            qualHTML += `
                <div class="consultant-note">
                    <p><strong>${q.querySelector('label').innerText}</strong></p>
                    <p><em>"${textarea.value.replace(/</g, "&lt;").replace(/>/g, "&gt;")}"</em></p>
                    <p style="font-size:0.8em; color:var(--primary); font-weight:bold;">STRATEGIC CONTEXT: ${textarea.dataset.insight || "N/A"}</p>
                </div>
            `;
        }
    });

    const dataValues = CONFIG.categories.map(cat => {
        const val = scoreBuckets[cat].count > 0 ? (scoreBuckets[cat].sum / scoreBuckets[cat].count) : 0;
        matrixHTML += `
            <div class="matrix-item">
                <div class="matrix-score">${val > 0 ? val.toFixed(1) : "—"}</div>
                <div class="matrix-label">${cat}</div>
            </div>
        `;
        return val;
    });

    const activeScores = dataValues.filter(v => v > 0);
    const composite = activeScores.length > 0 ? activeScores.reduce((a, b) => a + b, 0) / activeScores.length : 0;
    const stage = CONFIG.stages.find(s => composite >= s.min && composite <= s.max) || CONFIG.stages[0];

    document.getElementById("display-name").innerText = nameInput;
    document.getElementById("score-matrix").innerHTML = matrixHTML;

    const visibleCats = new Set(questions.map(q => q.dataset.cat));

    let combinedQual = "";
    combinedQual += qualHTML ? `<h4>Typed responses</h4>${qualHTML}` : `<p>No typed question feedback provided.</p>`;

    const justHTML = renderJustificationsForReport(visibleCats);
    combinedQual += justHTML ? `<h4 style="margin-top:25px;">Tagged justifications</h4>${justHTML}` : `<p style="margin-top:10px;">No tagged justifications provided.</p>`;

    document.getElementById("qualitative-results").innerHTML = combinedQual;

    document.getElementById("report-container").style.display = "block";
    document.getElementById("ai-insight-text").innerHTML = `
        <h3>Composite Maturity Index: ${composite.toFixed(1)} | Stage: ${stage.name}</h3>
        <p>${stage.blurb}</p>
    `;

    renderChart(CONFIG.categories, dataValues);
    document.getElementById("report-container").scrollIntoView({ behavior: "smooth" });
}

function renderChart(labels, data) {
    const ctx = document.getElementById('spiderChart').getContext('2d');
    const isPro = document.body.classList.contains("consultant-mode");

    const theme = {
        primary: isPro ? "#ff003c" : "#159591",
        point: isPro ? "#ffffff" : "#000000",
        label: isPro ? "#ffffff" : "#666666",
        grid: isPro ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.1)"
    };

    if (myChart) myChart.destroy();

    myChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: isPro ? 'rgba(255, 0, 60, 0.2)' : 'rgba(21, 149, 145, 0.1)',
                borderColor: theme.primary,
                borderWidth: 4,
                pointBackgroundColor: theme.point,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    suggestedMin: 0,
                    suggestedMax: 5,
                    ticks: { display: false, stepSize: 1 },
                    grid: { color: theme.grid },
                    angleLines: { color: theme.grid },
                    pointLabels: {
                        color: theme.label,
                        font: { size: 12, weight: 'bold', family: 'Arimo' }
                    }
                }
            }
        }
    });
}

/* =========================================================
   Export / Copy Utilities (enhanced with tagged justifications)
========================================================= */
function copyLLMPrompt() {
    const questions = getVisibleQuestionElements();
    let text = "AHI PRO STRATEGIC DATA BUNDLE:\n\n";

    questions.forEach(q => {
        const radio = q.querySelector('input[type="radio"]:checked');
        const textarea = q.querySelector('textarea');

        if (radio) text += `ID: ${q.dataset.id} | Q: ${q.querySelector('label').innerText} | SCORE: ${radio.value}/5\n`;
        if (textarea && textarea.value.trim() !== "") text += `FEEDBACK: ${textarea.value.trim()}\n`;
    });

    text += `\nTAGGED JUSTIFICATIONS:\n`;
    if (JUSTIFICATIONS.length === 0) {
        text += "None\n";
    } else {
        JUSTIFICATIONS.forEach(j => {
            text += `CAT: ${j.cat} | TAG: ${j.tagLabel} | TEXT: ${j.text ? j.text : "(voice only)"} | AUDIO: ${j.audioUrl ? "YES" : "NO"}\n`;
        });
    }

    navigator.clipboard.writeText(text).then(() => alert("Data bundle copied for AI Analysis."));
}

function downloadCSV() {
    const name = document.getElementById("userName").value || "Respondent";
    const org = document.getElementById("orgName").value || "Unknown";
    const questions = getVisibleQuestionElements();

    // Keep scored questions before qualitative-only rows
    questions.sort((a, b) => (a.querySelector('input[type="radio"]') ? 0 : 1) - (b.querySelector('input[type="radio"]') ? 0 : 1));

    let csv = "ID,Category,Label,HTML Question,Weight,Stage 1,Stage 2,Stage 3,Stage 4,Stage 5,Average Score,Average Dev,Qualitative Response,Tagged Justifications Text,Tagged Justifications Audio\n";
    const esc = (s) => `"${String(s ?? "").replace(/"/g, '""')}"`;

    questions.forEach(q => {
        const tagged = getTaggedJustificationsForQuestion(q.dataset.cat, q.dataset.id);
        const radio = q.querySelector('input[type="radio"]:checked');
        const text = q.querySelector('textarea');

        const scoreVal = radio ? radio.value : "";
        const noteVal = text ? text.value : "";

        csv += `${esc(q.dataset.id)},${esc(q.dataset.cat)},${esc(q.dataset.label)},${esc(q.querySelector('label').innerText)},,,, ,,,${esc(scoreVal)},,${esc(noteVal)},${esc(tagged.text)},${esc(tagged.audio ? "YES" : "NO")}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', `AHI_PRO_EXPORT_${org}_${name.replace(/ /g, "_")}.csv`);
    a.click();
}

/* =========================================================
   NEW: Phase 1 Backend Payload + Render
========================================================= */
function collectPhase1Payload() {
    const respondentName   = document.getElementById("userName").value.trim() || "Strategic Partner";
    const organizationName = document.getElementById("orgName").value.trim() || "Unknown";
    const respondentRole   = (document.getElementById("respondentRole")?.value) || null;
    const orgUnit          = (document.getElementById("orgUnit")?.value.trim()) || null;
    const selectedSections = Array.from(document.querySelectorAll('input[name="userSection"]:checked')).map(cb => cb.value);
    const visibleQuestions = getVisibleQuestionElements();

    const questions = visibleQuestions.map(q => {
        const radio    = q.querySelector('input[type="radio"]:checked');
        const textarea = q.querySelector('textarea');
        return {
            question_id:    q.dataset.id,
            category:       q.dataset.cat,
            label:          q.dataset.label || q.dataset.id,
            prompt:         q.querySelector('label') ? q.querySelector('label').innerText : q.dataset.id,
            score:          radio ? parseInt(radio.value) : null,
            typed_response: textarea ? (textarea.value.trim() || null) : null
        };
    });

    const justifications = JUSTIFICATIONS.map(j => ({
        category:  j.cat,
        tag_id:    j.tagId,
        tag_label: j.tagLabel,
        text:      j.text || null,
        has_audio: !!j.audioUrl
    }));

    return {
        payload_version:   "1.0",
        respondent_name:   respondentName,
        organization_name: organizationName,
        respondent_role:   respondentRole || undefined,
        organization_unit: orgUnit || undefined,
        selected_sections: selectedSections,
        questions,
        justifications
    };
}

let _lastPhase1JSON = null; // stored for "Copy JSON" button

async function runPhase1AgentAnalysis() {
    // Always generate the local report first so user sees scores immediately
    generateReport();

    const box     = document.getElementById("phase1-agent-results");
    const overlay = document.getElementById("loading-overlay");
    if (!box) return;

    const payload = collectPhase1Payload();

    const scoredQuestions = payload.questions.filter(q => q.score !== null);
    if (scoredQuestions.length === 0) {
        box.innerHTML = "<p><strong>No scored questions found.</strong> Select sections and answer at least one Likert question before running Phase 1 analysis.</p>";
        return;
    }

    // Show loading overlay
    if (overlay) overlay.classList.add("active");

    try {
        const res = await fetch(`${CONFIG.PHASE1_API_BASE}/api/analyze-assessment`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt || `HTTP ${res.status}`);
        }

        const data = await res.json();
        _lastPhase1JSON = data;
        renderPhase1AgentResults(data);
        document.getElementById("report-container").scrollIntoView({ behavior: "smooth" });

    } catch (err) {
        console.error(err);
        box.innerHTML = `
            <p><strong>Could not reach Phase 1 backend.</strong></p>
            <p>Ensure FastAPI is running: <code>uvicorn main:app --port 8001 --reload</code></p>
            <p>Target: <code>${CONFIG.PHASE1_API_BASE}</code></p>
            <p style="font-size:0.9em; color:#c0392b;">${String(err.message || err)}</p>
        `;
    } finally {
        if (overlay) overlay.classList.remove("active");
    }
}

function copyPhase1JSON() {
    if (!_lastPhase1JSON) {
        alert("No Phase 1 result to copy yet. Run the analysis first.");
        return;
    }
    navigator.clipboard.writeText(JSON.stringify(_lastPhase1JSON, null, 2))
        .then(() => alert("Backend JSON copied to clipboard."))
        .catch(() => alert("Copy failed — see browser console for raw JSON."));
}

/* --- Badge helpers --- */
function confBadge(label) {
    const cls = { High: "badge-conf-high", Med: "badge-conf-med", Low: "badge-conf-low" }[label] || "badge-conf-low";
    return `<span class="badge ${cls}">Confidence: ${label}</span>`;
}
function evBadge(label) {
    const cls = {
        Strong: "badge-ev-strong", Moderate: "badge-ev-moderate",
        Weak: "badge-ev-weak", None: "badge-ev-none"
    }[label] || "badge-ev-none";
    return `<span class="badge ${cls}">Evidence: ${label}</span>`;
}

function renderPhase1AgentResults(data) {
    const box = document.getElementById("phase1-agent-results");
    if (!box) return;

    const overall     = data.overall     || {};
    const dimensions  = data.dimensions  || [];
    const perQuestion = data.per_question || [];
    const blockers    = data.top_blockers || [];
    const quickWins   = data.quick_wins  || [];
    const nextActions = data.next_best_actions || [];
    const hybrid      = data.hybrid_analyst || null;

    /* Dimension cards */
    const dimCards = dimensions.map(d => {
        const flagHTML = d.summary_flags && d.summary_flags.length
            ? d.summary_flags.map(f => `<div class="p1-dim-flag">&#9888; ${f}</div>`).join("")
            : "";
        const scoreDisp = (d.avg_score !== null && d.avg_score !== undefined) ? d.avg_score.toFixed(1) : "—";
        return `<div class="p1-dim-card">
            <div class="p1-dim-title">${d.category} ${confBadge(d.confidence_label)}</div>
            <div class="p1-dim-score">${scoreDisp}<span style="font-size:0.45em;font-weight:400;color:#888;">/5</span></div>
            <div style="font-size:0.8em;color:#888;margin-top:4px;">${d.question_count} question(s)</div>
            ${flagHTML}
        </div>`;
    }).join("");

    /* Verify panel */
    const flaggedQs = perQuestion.filter(q =>
        q.confidence_label === "Low" || (q.red_flags && q.red_flags.length > 0)
    );
    const verifyHTML = flaggedQs.length
        ? `<div class="p1-verify-panel"><div class="p1-verify-title">&#9888; Verification Required &mdash; ${flaggedQs.length} Item(s)</div>
            ${flaggedQs.map(q => `<div style="margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid rgba(192,57,43,0.2);">
                <strong>${q.question_id} &mdash; ${q.label}</strong> ${confBadge(q.confidence_label)} ${evBadge(q.evidence_strength_label)}<br>
                <span style="font-size:0.85em;">Score: ${q.self_score || "—"}/5 | Stage: ${q.inferred_stage}</span>
                ${q.red_flags && q.red_flags.length ? `<div style="margin-top:6px;font-size:0.82em;color:#c0392b;">${q.red_flags.map(f => `<div>&#9679; ${f}</div>`).join("")}</div>` : ""}
                ${q.recommended_followups && q.recommended_followups.length ? `<div style="margin-top:8px;font-size:0.82em;background:rgba(0,0,0,0.03);padding:8px;border-radius:4px;"><strong>Consultant Probe:</strong>${q.recommended_followups.map(p => `<div style="margin-top:4px;">&#8227; ${p}</div>`).join("")}</div>` : ""}
            </div>`).join("")}</div>`
        : `<div style="color:green;font-weight:bold;margin-top:10px;">&#10003; No critical verification flags.</div>`;

    /* Hybrid analyst block */
    let hybridHTML = "";
    if (hybrid) {
        const gapsHTML = hybrid.perception_gaps && hybrid.perception_gaps.length
            ? hybrid.perception_gaps.map(g => `<div class="p1-gap-item">&#9632; ${g}</div>`).join("")
            : `<div style="font-size:0.85em;color:#888;">No significant perception gaps detected.</div>`;
        const outlierHTML = hybrid.outlier_flags && hybrid.outlier_flags.length
            ? hybrid.outlier_flags.map(f => `<div style="margin-top:6px;font-size:0.85em;color:#c0392b;">&#9888; ${f}</div>`).join("")
            : `<div style="font-size:0.85em;color:#888;">No outlier behavior detected.</div>`;
        const zVal = (hybrid.respondent_zscore !== null && hybrid.respondent_zscore !== undefined)
            ? `<p style="font-size:0.85em;"><strong>Z-Score vs ${hybrid.role_compared_to || "Benchmark"}:</strong> ${hybrid.respondent_zscore >= 0 ? "+" : ""}${hybrid.respondent_zscore.toFixed(2)}</p>` : "";
        hybridHTML = `<div class="p1-hybrid-panel">
            <h4 style="margin:0 0 10px 0;">Hybrid Analyst &mdash; Peer Benchmarking</h4>
            <p style="font-size:0.85em;">${hybrid.benchmark_note || ""}</p>
            ${zVal}
            ${hybrid.zscore_interpretation ? `<p style="font-size:0.85em;font-style:italic;">${hybrid.zscore_interpretation}</p>` : ""}
            <div style="margin-top:12px;"><strong style="font-size:0.85em;text-transform:uppercase;letter-spacing:0.5px;">Perception Gaps</strong>${gapsHTML}</div>
            <div style="margin-top:12px;"><strong style="font-size:0.85em;text-transform:uppercase;letter-spacing:0.5px;">Outlier Analysis</strong>${outlierHTML}</div>
        </div>`;
    }

    const followupBadge = overall.needs_human_followup
        ? `<span class="badge badge-conf-low">Human Follow-Up Required</span>`
        : `<span class="badge badge-conf-high">Automated Review Complete</span>`;

    /* Assemble the full panel — no more placeholder, this is it */
    const dimHTML = ""; /* kept to avoid reference error below — not used */

    box.innerHTML = `<div>
        <div style="display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:16px;">
            <span style="font-size:1.4em;font-weight:800;">Composite: ${overall.composite_score ?? "—"}</span>
            <span style="font-weight:700;color:#888;">${overall.maturity_stage || ""}</span>
            ${followupBadge}
        </div>
        <p style="font-size:0.88em;color:#888;margin-bottom:20px;">${overall.assessment_quality_note || ""}</p>

        <h4 style="margin:0 0 4px 0;text-transform:uppercase;font-size:0.82em;letter-spacing:0.5px;">Dimension Summaries</h4>
        <div class="p1-dim-grid">${dimCards || "<p>No scored dimensions.</p>"}</div>

        <h4 style="margin:24px 0 4px 0;text-transform:uppercase;font-size:0.82em;letter-spacing:0.5px;">Evidence Verification</h4>
        ${verifyHTML}

        ${blockers.length ? `<h4 style="margin:24px 0 8px 0;text-transform:uppercase;font-size:0.82em;letter-spacing:0.5px;color:#c0392b;">Top Blockers</h4>
        ${blockers.map(b => `<div class="consultant-note" style="margin-bottom:8px;border-left:3px solid #c0392b;">${b}</div>`).join("")}` : ""}

        ${quickWins.length ? `<h4 style="margin:24px 0 8px 0;text-transform:uppercase;font-size:0.82em;letter-spacing:0.5px;color:#27ae60;">Quick Wins</h4>
        ${quickWins.map(w => `<div class="consultant-note" style="margin-bottom:8px;border-left:3px solid #27ae60;">${w}</div>`).join("")}` : ""}

        ${nextActions.length ? `<h4 style="margin:24px 0 8px 0;text-transform:uppercase;font-size:0.82em;letter-spacing:0.5px;">Next Best Actions</h4>
        <ol style="padding-left:20px;">${nextActions.map(a => `<li style="margin-bottom:10px;font-size:0.9em;">${a}</li>`).join("")}</ol>` : ""}

        ${hybridHTML}
        <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-top:16px;">
            <button class="btn-copy-json" onclick="copyPhase1JSON()">Copy Backend JSON</button>
            ${overall.needs_human_followup ? `<button class="btn-followup" onclick="startFollowupInterview()">Start Follow-up Interview <span class="fq-count" id="fq-count-badge">...</span></button>` : ""}
        </div>
    </div>`;

    /* Store and display followup queue size badge */
    const fqBadge = document.getElementById("fq-count-badge");
    if (fqBadge) {
        const queueItems = data.followup_queue || buildFollowupQueueClient(data);
        window._lastFollowupQueue = queueItems;
        const critCount = queueItems.filter(i => i.priority === "critical").length;
        fqBadge.textContent = `${queueItems.length} item${queueItems.length !== 1 ? "s" : ""}${critCount > 0 ? ` · ${critCount} critical` : ""}`;
    }
}

/* =========================================================
   FOLLOW-UP INTERVIEW ENGINE (Phase 2 Mode B)
========================================================= */
let _interviewSessionId = null;
let _interviewQueue     = [];
let _interviewIdx       = 0;
let _interviewPayload   = null;

function buildFollowupQueueClient(data) {
    /* Client-side queue builder — used if backend doesn't return followup_queue */
    const order = { critical: 0, high: 1, medium: 2 };
    const q = (data.per_question || [])
        .filter(q => q.confidence_label === "Low" || (q.red_flags && q.red_flags.length > 0))
        .filter(q => q.recommended_followups && q.recommended_followups.length > 0)
        .map(q => ({
            question_id: q.question_id,
            category:    q.category,
            label:       q.label,
            priority:    q.red_flags.some(f => f.includes("CRITICAL"))   ? "critical"
                       : q.red_flags.some(f => f.includes("Contradiction")) ? "high" : "medium",
            reason:      q.red_flags || [],
            probe:       q.recommended_followups[0],
            prior_score: q.self_score,
            confidence:  q.confidence,
            supporting_text_excerpt: q.supporting_text_excerpt
        }));
    return q.sort((a, b) => (order[a.priority] || 2) - (order[b.priority] || 2));
}

async function startFollowupInterview() {
    const analysisData = _lastPhase1JSON || {};
    const queue = (analysisData.followup_queue && analysisData.followup_queue.length > 0)
        ? analysisData.followup_queue
        : buildFollowupQueueClient(analysisData);

    if (!queue || queue.length === 0) {
        alert("No flagged items to follow up on.");
        return;
    }

    _interviewQueue     = queue;
    _interviewIdx       = 0;
    _interviewSessionId = null;
    _interviewPayload   = null;

    /* Show panel, reset state */
    const panel = document.getElementById("followup-interview-panel");
    panel.style.display = "block";
    document.getElementById("interview-chat").innerHTML = "";
    document.getElementById("interview-complete-box").style.display = "none";
    document.getElementById("interview-input-area").style.display = "block";
    panel.scrollIntoView({ behavior: "smooth" });

    /* Build probe overrides from queue */
    const probeOverrides = {};
    queue.forEach(item => { probeOverrides[item.question_id] = item.probe; });

    /* Collect form state for session context */
    const form = collectPhase1Payload();

    try {
        const res = await fetch(`${CONFIG.PHASE1_API_BASE}/api/v2/session/start`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                mode:              "B",
                respondent_name:   form.respondent_name   || null,
                organization_name: form.organization_name || null,
                respondent_role:   form.respondent_role   || null,
                organization_unit: form.organization_unit || null,
                selected_sections: form.selected_sections || [],
                followup_queue:    queue.map(i => i.question_id),
                probe_overrides:   probeOverrides
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const session = await res.json();
        _interviewSessionId = session.session_id;

        /* Show opening line only (not the first question — we control that below) */
        const opening = (session.opening_text || "").split("\n\n")[0];
        if (opening) renderInterviewMessage("assistant", opening);

    } catch (err) {
        renderInterviewMessage("assistant", "Could not start interview session. Ensure the backend is running at " + CONFIG.PHASE1_API_BASE);
        console.error(err);
        return;
    }

    showCurrentInterviewQuestion();
}

function showCurrentInterviewQuestion() {
    if (_interviewIdx >= _interviewQueue.length) {
        finalizeInterview(null);
        return;
    }
    const item = _interviewQueue[_interviewIdx];
    updateInterviewProgress();
    showInterviewContext(item);
    renderInterviewMessage("assistant", item.probe);
    document.getElementById("interview-input").focus();
}

function showInterviewContext(item) {
    const bar = document.getElementById("interview-context-bar");
    if (!item || !item.reason || item.reason.length === 0) {
        bar.style.display = "none";
        return;
    }
    const priorityLabel = { critical: "CRITICAL", high: "High Priority", medium: "Medium Priority" }[item.priority] || item.priority;
    const priorScore    = item.prior_score != null ? ` | Score: ${item.prior_score}/5` : "";
    bar.style.display   = "block";
    bar.innerHTML = `<strong>[${priorityLabel}]</strong> ${item.label}${priorScore} &mdash; <em>${item.reason[0] || ""}</em>`;
}

function updateInterviewProgress() {
    const total = _interviewQueue.length;
    const done  = _interviewIdx;
    const pct   = total ? Math.round((done / total) * 100) : 0;
    document.getElementById("interview-progress-fill").style.width = pct + "%";
    document.getElementById("interview-progress-label").textContent = `${done} of ${total}`;
}

function renderInterviewMessage(role, text) {
    const chat = document.getElementById("interview-chat");
    const div  = document.createElement("div");
    div.className   = `msg-bubble ${role}`;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function sendInterviewResponse() {
    const input = document.getElementById("interview-input");
    const text  = (input.value || "").trim();
    if (!text) return;

    input.value = "";
    renderInterviewMessage("user", text);

    /* Advance backend session */
    if (_interviewSessionId) {
        try {
            const res = await fetch(`${CONFIG.PHASE1_API_BASE}/api/v2/session/turn`, {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: _interviewSessionId, user_text: text })
            });
            if (res.ok) {
                const turn = await res.json();
                if (turn.is_complete) { finalizeInterview(turn.compiled_payload); return; }
            }
        } catch (e) { /* non-fatal — continue frontend flow */ }
    }

    /* Advance frontend queue */
    _interviewIdx++;
    if (_interviewIdx < _interviewQueue.length) {
        showCurrentInterviewQuestion();
    } else {
        /* Ask backend to close session */
        if (_interviewSessionId) {
            try {
                const res = await fetch(`${CONFIG.PHASE1_API_BASE}/api/v2/session/turn`, {
                    method:  "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: _interviewSessionId, user_text: "done" })
                });
                if (res.ok) { const t = await res.json(); finalizeInterview(t.compiled_payload); return; }
            } catch (e) { /* ignore */ }
        }
        finalizeInterview(null);
    }
}

async function skipInterviewQuestion() {
    renderInterviewMessage("user", "[Skipped]");
    if (_interviewSessionId) {
        try {
            await fetch(`${CONFIG.PHASE1_API_BASE}/api/v2/session/turn`, {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: _interviewSessionId, user_text: "skip" })
            });
        } catch (e) { /* non-fatal */ }
    }
    _interviewIdx++;
    if (_interviewIdx < _interviewQueue.length) {
        showCurrentInterviewQuestion();
    } else {
        finalizeInterview(null);
    }
}

function finalizeInterview(compiledPayload) {
    _interviewPayload = compiledPayload;

    /* Final progress bar = 100% */
    document.getElementById("interview-progress-fill").style.width = "100%";
    document.getElementById("interview-progress-label").textContent = `${_interviewQueue.length} of ${_interviewQueue.length}`;
    document.getElementById("interview-context-bar").style.display = "none";
    document.getElementById("interview-input-area").style.display = "none";
    document.getElementById("interview-complete-box").style.display = "block";

    const n = _interviewQueue.length;
    renderInterviewMessage("assistant",
        `Thank you — all ${n} flagged item${n !== 1 ? "s" : ""} have been addressed. ` +
        "Your consultant will review the full session before finalizing recommendations."
    );
}

function copyInterviewPayload() {
    const data = _interviewPayload || { note: "No compiled session payload available." };
    navigator.clipboard.writeText(JSON.stringify(data, null, 2))
        .then(()  => alert("Session payload copied to clipboard."))
        .catch(()  => alert("Copy failed — see browser console."));
}

/* =========================================================
   Load Demo — Max / Cmax (remove before client delivery)
========================================================= */
function loadDemoData() {
    // Identity
    document.getElementById("userName").value       = "Max";
    document.getElementById("orgName").value        = "Cmax";
    document.getElementById("respondentRole").value = "Tech Lead";
    document.getElementById("orgUnit").value        = "";

    // Sections — check all four
    document.querySelectorAll('input[name="userSection"]').forEach(cb => {
        cb.checked = ["leadership", "tech", "data", "hr"].includes(cb.value);
    });
    filterQuestions();

    // Likert scores from Max / Cmax session
    const scores = {
        L1: 2, L2: 2, L3: 1, L_Risk: 2,
        W1: 4, W_Conflict: 2, W3: 5,
        G1: 3, G4: 3, G_Shadow: 2,
        T1: 4, T2: 3, T4: 4, T5: 5,
        D1: 2, D2: 3, D3: 2
    };
    for (const [name, val] of Object.entries(scores)) {
        const radio = document.querySelector(`input[name="${name}"][value="${val}"]`);
        if (radio) radio.checked = true;
    }

    // Qualitative textarea responses
    const qdEl = document.querySelector('textarea[name="Q_Decision"]');
    if (qdEl) qdEl.value = "do not invest in AI";
    const qcEl = document.querySelector('textarea[name="Q_Concerns"]');
    if (qcEl) qcEl.value = "Money and hiring new employees";
    const qvEl = document.querySelector('textarea[name="Q_Vision"]');
    if (qvEl) qvEl.value = "Agents running day to day work with execs making decisions";

    // Justifications — text only (original audio recordings were ephemeral / NDA)
    JUSTIFICATIONS.length = 0;
    const demoNotes = [
        {
            cat: "Leadership & Vision", tagId: "L1",
            tagLabel: "L1 - Strategic AI Vision",
            text: "No formal AI roadmap exists. Leadership views AI as a risk rather than an opportunity and has not committed to a structured investment or implementation plan."
        },
        {
            cat: "Leadership & Vision", tagId: "L_Risk",
            tagLabel: "L_Risk - AI Risk Appetite",
            text: "Prevailing posture is highly conservative — 'wait until competitors prove it first.' No appetite for experimental AI investments or pilot programs."
        },
        {
            cat: "Ways of Working", tagId: "W_Conflict",
            tagLabel: "W_Conflict - Conflict Resolution",
            text: "Frequent unresolved disputes between business and technical teams on AI deployment priorities, timelines, and budget. No structured escalation or resolution process in place."
        },
        {
            cat: "Governance Readiness", tagId: "G_Shadow",
            tagLabel: "G_Shadow - Shadow AI Confidence",
            text: "Employees are actively using ChatGPT and other unapproved AI tools. IT has no visibility into what data is being shared externally. No audit trail or usage policy enforcement."
        },
        {
            cat: "Data Readiness", tagId: "D1",
            tagLabel: "D1 - Data structured & clean",
            text: "Data is fragmented across multiple legacy systems with no centralized repository. Employees have been entering confidential client data into AI tools without controls or oversight."
        }
    ];
    const affectedCats = new Set();
    for (const note of demoNotes) {
        JUSTIFICATIONS.push({ ...note, audioUrl: null, transcribed: false, ts: new Date().toISOString() });
        affectedCats.add(note.cat);
    }
    for (const cat of affectedCats) {
        renderJustificationList(cat);
    }

    // Scroll to top of form
    document.querySelector(".setup-section").scrollIntoView({ behavior: "smooth" });
}

/* =========================================================
   Init
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
    initJustificationUI();
});
</script>
</body>
</html>