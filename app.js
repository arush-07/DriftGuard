// DriftGuard Frontend Core Logic - app.js

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    activeTab: 'overview',
    selectedFinding: null,
    riskFilter: '',
    searchQuery: '',
    isScanning: false,
    scanProgress: 0,
    currentUser: null,
    backendStatus: 'simulated'
  };

  // DOM Elements
  const authContainer = document.getElementById('auth-container');
  const appLayout = document.getElementById('app-layout');
  const loginForm = document.getElementById('login-form');
  const signupForm = document.getElementById('signup-form');
  const toggleSignupLink = document.getElementById('toggle-signup');
  const toggleLoginLink = document.getElementById('toggle-login');
  
  const sidebarMenu = document.getElementById('sidebar-menu');
  const userEmailEl = document.getElementById('user-email');
  const userRoleEl = document.getElementById('user-role');
  const statusDotEl = document.getElementById('status-dot');
  const statusTextEl = document.getElementById('status-text');
  const logoutBtn = document.getElementById('logout-btn');
  
  const viewContainer = document.getElementById('view-content');
  const scanBtn = document.getElementById('scan-btn');
  const scanOverlay = document.getElementById('scan-overlay');
  const scanLogEl = document.getElementById('scan-log');
  const scanProgressFill = document.getElementById('scan-progress-fill');
  const scanPercentEl = document.getElementById('scan-percent');
  
  const roleSwitcherAdmin = document.getElementById('role-btn-admin');
  const roleSwitcherViewer = document.getElementById('role-btn-viewer');

  const findingModal = document.getElementById('finding-modal');
  const modalClose = document.getElementById('modal-close');

  // --- Initializers & Backend Status Checks ---
  async function init() {
    // Check local storage for session
    state.currentUser = window.api.currentUser;
    
    // Listen to connection changes
    window.api.onStatusChange((status) => {
      state.backendStatus = status;
      updateStatusIndicator();
    });

    // Check backend status immediately
    await window.api.checkBackendStatus();
    
    // Periodically poll backend status every 12 seconds
    setInterval(async () => {
      await window.api.checkBackendStatus();
    }, 12000);

    // Initial view router
    if (window.api.token && state.currentUser) {
      showDashboard();
    } else {
      showLogin();
    }
  }

  function updateStatusIndicator() {
    statusDotEl.className = 'status-dot';
    if (state.backendStatus === 'live') {
      statusDotEl.classList.add('active');
      statusTextEl.innerText = 'Connected to Live API';
      statusTextEl.style.color = 'var(--color-success)';
    } else {
      statusDotEl.classList.add('simulated');
      statusTextEl.innerText = 'Offline (Simulated API Mode)';
      statusTextEl.style.color = 'var(--neon-cyan)';
    }
  }

  // --- Authentication UI Flow ---
  function showLogin() {
    authContainer.style.display = 'flex';
    appLayout.style.display = 'none';
    loginForm.style.display = 'block';
    signupForm.style.display = 'none';
  }

  function showDashboard() {
    authContainer.style.display = 'none';
    appLayout.style.display = 'flex';
    
    // Load User UI Info
    userEmailEl.innerText = state.currentUser.email;
    userRoleEl.innerText = state.currentUser.role;
    userRoleEl.className = `user-role-badge role-${state.currentUser.role}`;

    // Manage role quick switcher buttons
    if (state.currentUser.role === 'admin') {
      roleSwitcherAdmin.classList.add('active', 'admin');
      roleSwitcherViewer.classList.remove('active', 'viewer');
      scanBtn.removeAttribute('disabled');
      scanBtn.style.opacity = '1';
    } else {
      roleSwitcherAdmin.classList.remove('active', 'admin');
      roleSwitcherViewer.classList.add('active', 'viewer');
      scanBtn.setAttribute('disabled', 'true');
      scanBtn.style.opacity = '0.5';
    }

    renderSidebar();
    switchTab(state.activeTab);
  }

  // Form Submit Handler
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const pass = document.getElementById('login-password').value;
    const loginError = document.getElementById('login-error');
    const submitBtn = loginForm.querySelector('.btn-primary');

    loginError.innerText = '';
    submitBtn.innerText = 'Authenticating...';
    submitBtn.disabled = true;

    try {
      state.currentUser = await window.api.login(email, pass);
      showDashboard();
    } catch (err) {
      loginError.innerText = err.message;
    } finally {
      submitBtn.innerText = 'Sign In';
      submitBtn.disabled = false;
    }
  });

  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('signup-email').value;
    const pass = document.getElementById('signup-password').value;
    const role = document.getElementById('signup-role').value;
    const signupError = document.getElementById('signup-error');
    const submitBtn = signupForm.querySelector('.btn-primary');

    signupError.innerText = '';
    submitBtn.innerText = 'Creating account...';
    submitBtn.disabled = true;

    try {
      const res = await window.api.signup(email, pass, role);
      // Auto login
      state.currentUser = await window.api.login(email, pass);
      showDashboard();
    } catch (err) {
      signupError.innerText = err.message;
    } finally {
      submitBtn.innerText = 'Create Account';
      submitBtn.disabled = false;
    }
  });

  // Toggle Forms
  toggleSignupLink.addEventListener('click', () => {
    loginForm.style.display = 'none';
    signupForm.style.display = 'block';
  });

  toggleLoginLink.addEventListener('click', () => {
    loginForm.style.display = 'block';
    signupForm.style.display = 'none';
  });

  // Logout Button
  logoutBtn.addEventListener('click', () => {
    window.api.logout();
    state.currentUser = null;
    showLogin();
  });

  // Quick Switch Roles (Demo Tool)
  roleSwitcherAdmin.addEventListener('click', () => {
    if (!state.currentUser) return;
    state.currentUser.role = 'admin';
    localStorage.setItem('dg_user', JSON.stringify(state.currentUser));
    showDashboard();
  });

  roleSwitcherViewer.addEventListener('click', () => {
    if (!state.currentUser) return;
    state.currentUser.role = 'viewer';
    localStorage.setItem('dg_user', JSON.stringify(state.currentUser));
    showDashboard();
  });

  // --- Sidebar Navigation ---
  function renderSidebar() {
    const isViewer = state.currentUser && state.currentUser.role === 'viewer';
    
    let html = `
      <li class="sidebar-item ${state.activeTab === 'overview' ? 'active' : ''}" data-tab="overview">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-layout-dashboard"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="10" rx="1"/><rect width="7" height="5" x="3" y="15" rx="1"/></svg>
        Overview Dashboard
      </li>
      <li class="sidebar-item ${state.activeTab === 'findings' ? 'active' : ''}" data-tab="findings">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-alert"><path d="M20 13c0 5-3.5 7.5-7.66 9.7a1 1 0 0 1-.68 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 .76-.97l8-2a1 1 0 0 1 .48 0l8 2c.57.14.76.64.76.97Z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
        Risk Findings
      </li>
      <li class="sidebar-item ${state.activeTab === 'scores' ? 'active' : ''}" data-tab="scores">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-activity"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        Drift Scores
      </li>
      <li class="sidebar-item ${state.activeTab === 'architecture' ? 'active' : ''}" data-tab="architecture">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-git-branch"><line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
        Architecture Pipeline
      </li>
    `;

    // Only render Audit Log if user is Admin
    if (!isViewer) {
      html += `
        <li class="sidebar-item ${state.activeTab === 'audit' ? 'active' : ''}" data-tab="audit">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-list-todo"><rect x="3" y="5" width="6" height="6" rx="1"/><rect x="3" y="13" width="6" height="6" rx="1"/><path d="M13 8h8"/><path d="M13 16h8"/></svg>
          Audit Activity Logs
        </li>
      `;
    }

    sidebarMenu.innerHTML = html;

    // Attach Click Events to items
    const items = sidebarMenu.querySelectorAll('.sidebar-item');
    items.forEach(item => {
      item.addEventListener('click', () => {
        const tab = item.getAttribute('data-tab');
        switchTab(tab);
      });
    });
  }

  function switchTab(tabId) {
    state.activeTab = tabId;
    renderSidebar();

    // Trigger View Rendering
    switch (tabId) {
      case 'overview':
        renderOverview();
        break;
      case 'findings':
        renderFindings();
        break;
      case 'scores':
        renderScores();
        break;
      case 'architecture':
        renderArchitecture();
        break;
      case 'audit':
        renderAudit();
        break;
    }
  }

  // --- View: Overview Dashboard ---
  async function renderOverview() {
    viewContainer.innerHTML = `<div class="loading-spinner">Loading Dashboard...</div>`;
    
    try {
      const findings = await window.api.getFindings();
      const scores = await window.api.getDriftScores();
      const timeline = await window.api.getTimeline();

      const criticalCount = findings.filter(f => f.risk_tier === 'Critical').length;
      const highCount = findings.filter(f => f.risk_tier === 'High').length;
      const velocityCount = scores.filter(s => s.velocity_flag).length;
      const totalChanges = findings.length;
      
      // Calculate Compliance Rating (simplified logic)
      let compliancePercentage = 100 - (criticalCount * 25 + highCount * 12 + (findings.length - criticalCount - highCount) * 4);
      compliancePercentage = Math.max(10, Math.min(100, compliancePercentage));
      
      let complianceText = 'COMPLIANT';
      let complianceColor = 'text-success';
      if (compliancePercentage < 60) {
        complianceText = 'CRITICAL DRIFT';
        complianceColor = 'text-critical';
      } else if (compliancePercentage < 85) {
        complianceText = 'WARNING';
        complianceColor = 'text-high';
      }

      const totalDriftScore = timeline[timeline.length - 1]?.score || 0;

      let html = `
        <div class="overview-grid">
          <div class="glass-panel stat-card">
            <div class="stat-header">
              <span>Compliance Index</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield"><path d="M20 13c0 5-3.5 7.5-7.66 9.7a1 1 0 0 1-.68 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 .76-.97l8-2a1 1 0 0 1 .48 0l8 2c.57.14.76.64.76.97Z"/></svg>
            </div>
            <div class="stat-value ${complianceColor}">${compliancePercentage}%</div>
            <div class="stat-subtext">Security status: <strong>${complianceText}</strong></div>
          </div>
          
          <div class="glass-panel stat-card">
            <div class="stat-header">
              <span>Drift Score</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-zap"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>
            </div>
            <div class="stat-value text-glow-pink" style="color: var(--neon-pink)">${totalDriftScore}</div>
            <div class="stat-subtext">Cumulative drift metrics</div>
          </div>

          <div class="glass-panel stat-card">
            <div class="stat-header">
              <span>Critical Threats</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-skull"><path d="m12.5 17-.5-1-.5 1h1z"/><path d="M15 22v-2c0-1.38-1.13-2-2.5-2h-1C10.13 18 9 18.62 9 20v2"/><path d="M16 14a2 2 0 1 1-4 0v-2"/><path d="M8 14a2 2 0 1 1-4 0v-2"/><path d="M12 2a8 8 0 0 0-8 8v2h16v-2a8 8 0 0 0-8-8z"/></svg>
            </div>
            <div class="stat-value text-critical">${criticalCount}</div>
            <div class="stat-subtext">Requires immediate rollback</div>
          </div>

          <div class="glass-panel stat-card">
            <div class="stat-header">
              <span>Velocity Alert Files</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flame"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
            </div>
            <div class="stat-value text-high">${velocityCount}</div>
            <div class="stat-subtext">Rapidly degrading configurations</div>
          </div>
        </div>

        <div class="dashboard-split">
          <!-- Timeline SVG Chart -->
          <div class="glass-panel section-card">
            <div class="section-header">
              <h3 class="section-title">Drift Scoring Vector (Timeline)</h3>
              <span style="font-size: 0.8rem; color: var(--text-secondary)">Unit: Compliance Degradation Points</span>
            </div>
            <div style="flex-grow: 1; min-height: 250px; position: relative;" id="timeline-container">
              <!-- Custom SVG graphic inserted here -->
            </div>
          </div>

          <!-- Quick Risk Alerts List -->
          <div class="glass-panel section-card">
            <div class="section-header">
              <h3 class="section-title">Critical & High Incidents</h3>
              <span class="badge badge-critical" style="font-size: 0.65rem">${criticalCount + highCount} Issues</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 12px; overflow-y: auto; max-height: 300px; padding-right: 4px;">
              ${findings.filter(f => f.risk_tier === 'Critical' || f.risk_tier === 'High').map(f => `
                <div style="padding: 12px; background: rgba(0, 0, 0, 0.2); border-radius: 8px; border: 1px solid ${f.risk_tier === 'Critical' ? 'rgba(255, 42, 133, 0.15)' : 'rgba(249, 115, 22, 0.15)'}; cursor: pointer;" class="quick-finding-item" data-id="${f.finding_id}">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span class="badge ${f.risk_tier === 'Critical' ? 'badge-critical' : 'badge-high'}" style="font-size: 0.65rem;">${f.risk_tier}</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">${formatTimestamp(f.timestamp)}</span>
                  </div>
                  <div style="font-weight: 600; font-size: 0.85rem; color: #fff; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${f.file.split('/').pop()}</div>
                  <div style="font-size: 0.8rem; color: var(--text-secondary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; margin-top: 2px;">${f.rule_triggered}</div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;

      viewContainer.innerHTML = html;
      
      // Draw the beautiful interactive SVG Timeline
      drawSVGTimeline(timeline);

      // Attach click events to quick findings list items
      viewContainer.querySelectorAll('.quick-finding-item').forEach(item => {
        item.addEventListener('click', async () => {
          const fid = item.getAttribute('data-id');
          const allFindings = await window.api.getFindings();
          const finding = allFindings.find(f => f.finding_id === fid);
          if (finding) openFindingModal(finding);
        });
      });

    } catch (e) {
      console.error(e);
      viewContainer.innerHTML = `<div style="color: var(--color-critical); padding: 20px;">Error rendering dashboard. API connection failed.</div>`;
    }
  }

  // Draw interactive SVG line chart inside the overview
  function drawSVGTimeline(data) {
    const container = document.getElementById('timeline-container');
    if (!container) return;

    const width = container.clientWidth;
    const height = 240;
    
    if (data.length === 0) {
      container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)">No timeline data</div>`;
      return;
    }

    const paddingX = 50;
    const paddingY = 30;

    const maxScore = Math.max(...data.map(d => d.score)) * 1.15 || 50;
    
    // Scale Helpers
    const getX = (index) => paddingX + (index / (data.length - 1)) * (width - paddingX * 2);
    const getY = (score) => height - paddingY - (score / maxScore) * (height - paddingY * 2);

    // Build the grid lines and axes
    let gridLinesHTML = '';
    const gridCount = 5;
    for (let i = 0; i < gridCount; i++) {
      const yVal = (maxScore / (gridCount - 1)) * i;
      const yCoord = getY(yVal);
      gridLinesHTML += `
        <line x1="${paddingX}" y1="${yCoord}" x2="${width - paddingX}" y2="${yCoord}" class="chart-grid-line" />
        <text x="${paddingX - 10}" y="${yCoord + 4}" fill="var(--text-muted)" font-size="9" text-anchor="end">${Math.round(yVal)}</text>
      `;
    }

    // Build X axis labels
    data.forEach((d, idx) => {
      const xCoord = getX(idx);
      gridLinesHTML += `
        <line x1="${xCoord}" y1="${height - paddingY}" x2="${xCoord}" y2="${height - paddingY + 5}" stroke="rgba(255,255,255,0.08)" />
        <text x="${xCoord}" y="${height - paddingY + 18}" fill="var(--text-secondary)" font-size="9" text-anchor="middle">${d.date.substring(5)}</text>
      `;
    });

    // Build line paths
    let points = '';
    let glowPoints = '';
    data.forEach((d, idx) => {
      const x = getX(idx);
      const y = getY(d.score);
      points += `${idx === 0 ? 'M' : 'L'} ${x} ${y} `;
      glowPoints += `${idx === 0 ? 'M' : 'L'} ${x} ${y} `;
    });

    // Complete gradient path boundary
    const firstX = getX(0);
    const lastX = getX(data.length - 1);
    const yBottom = height - paddingY;
    const gradientPathStr = `${points} L ${lastX} ${yBottom} L ${firstX} ${yBottom} Z`;

    // Interactive nodes/dots HTML
    let dotsHTML = '';
    data.forEach((d, idx) => {
      const x = getX(idx);
      const y = getY(d.score);
      dotsHTML += `
        <circle cx="${x}" cy="${y}" r="4.5" class="chart-dot" data-idx="${idx}" />
      `;
    });

    const svgHTML = `
      <svg width="${width}" height="${height}" style="overflow: visible;">
        <defs>
          <linearGradient id="chart-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--neon-pink)" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="var(--neon-pink)" stop-opacity="0"/>
          </linearGradient>
        </defs>
        ${gridLinesHTML}
        <!-- Glow gradient fill -->
        <path d="${gradientPathStr}" class="svg-chart-glow-area" />
        <!-- Glowing stroke line -->
        <path d="${points}" class="svg-chart-line" />
        <!-- Data dots -->
        ${dotsHTML}
      </svg>
      <div id="chart-tooltip" class="timeline-tooltip"></div>
    `;

    container.innerHTML = svgHTML;

    // Attach Hover event listeners to dots for interactive tooltips!
    const dots = container.querySelectorAll('.chart-dot');
    const tooltip = container.getElementById('chart-tooltip');

    dots.forEach(dot => {
      dot.addEventListener('mouseenter', (e) => {
        const idx = e.target.getAttribute('data-idx');
        const item = data[idx];
        
        tooltip.innerHTML = `
          <div style="font-weight: 700; color:#fff;">Date: ${item.date}</div>
          <div style="margin-top: 4px; display:flex; justify-content:space-between; gap:10px;">
            <span>Drift Score:</span>
            <span style="color:var(--neon-pink); font-weight:700;">${item.score}</span>
          </div>
          <div style="margin-top: 2px; font-size: 0.75rem; color:var(--text-secondary)">Events: ${item.events}</div>
        `;
        tooltip.style.display = 'block';

        const dotRect = e.target.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();

        tooltip.style.left = `${dotRect.left - containerRect.left + 10}px`;
        tooltip.style.top = `${dotRect.top - containerRect.top - 60}px`;
      });

      dot.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
      });
    });
  }

  // --- View: Findings Table ---
  async function renderFindings() {
    viewContainer.innerHTML = `<div class="loading-spinner">Loading Risk Findings...</div>`;

    try {
      const findings = await window.api.getFindings();
      
      let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap:15px;">
          <h3 class="section-title" style="font-size: 1.3rem;">Infrastructure Compliance Logs</h3>
          
          <div style="display: flex; gap:10px;">
            <button class="btn-scan" id="export-btn" style="background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); color:var(--text-primary);">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-download-cloud"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4 4 4-4"/></svg>
              Export Report
            </button>
          </div>
        </div>

        <div class="table-filters">
          <div class="filter-input-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon-svg"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            <input type="text" class="filter-search" id="findings-search" placeholder="Search by file or rule..." value="${state.searchQuery}">
          </div>
          
          <select class="filter-select" id="findings-severity-select">
            <option value="">All Severities</option>
            <option value="Critical" ${state.riskFilter === 'Critical' ? 'selected' : ''}>Critical Only</option>
            <option value="High" ${state.riskFilter === 'High' ? 'selected' : ''}>High Only</option>
            <option value="Medium" ${state.riskFilter === 'Medium' ? 'selected' : ''}>Medium Only</option>
            <option value="Low" ${state.riskFilter === 'Low' ? 'selected' : ''}>Low Only</option>
          </select>
        </div>

        <div class="glass-panel table-wrapper">
          <table class="custom-table" id="findings-table-el">
            <thead>
              <tr>
                <th>Finding ID</th>
                <th>File Path</th>
                <th>Rule Triggered</th>
                <th>Field Target</th>
                <th>Risk Level</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              <!-- Rendered rows -->
            </tbody>
          </table>
        </div>
      `;

      viewContainer.innerHTML = html;

      // Event listeners for filters
      const searchInput = document.getElementById('findings-search');
      const severitySelect = document.getElementById('findings-severity-select');
      const exportBtn = document.getElementById('export-btn');

      searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        filterAndPopulateTable(findings);
      });

      severitySelect.addEventListener('change', (e) => {
        state.riskFilter = e.target.value;
        filterAndPopulateTable(findings);
      });

      exportBtn.addEventListener('click', async () => {
        exportBtn.innerText = 'Generating...';
        exportBtn.disabled = true;
        await window.api.exportReport();
        exportBtn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-download-cloud"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4 4 4-4"/></svg>
          Export Report
        `;
        exportBtn.disabled = false;
        showToast('Report generated and downloaded successfully!');
      });

      // Populate table initially
      filterAndPopulateTable(findings);

    } catch (e) {
      console.error(e);
      viewContainer.innerHTML = `<div style="color: var(--color-critical);">Failed to load findings.</div>`;
    }
  }

  function filterAndPopulateTable(findings) {
    const tableBody = document.querySelector('#findings-table-el tbody');
    if (!tableBody) return;

    let filtered = findings;

    // Filter by risk tier dropdown
    if (state.riskFilter) {
      filtered = filtered.filter(f => f.risk_tier.toLowerCase() === state.riskFilter.toLowerCase());
    }

    // Filter by search query
    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      filtered = filtered.filter(f => 
        f.file.toLowerCase().includes(q) || 
        f.rule_triggered.toLowerCase().includes(q) ||
        f.finding_id.toLowerCase().includes(q)
      );
    }

    if (filtered.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">
            No drift events match the current filter selection.
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = filtered.map(f => `
      <tr class="finding-row" data-id="${f.finding_id}">
        <td style="font-family: monospace; font-weight:700; color: var(--neon-cyan);">${f.finding_id}</td>
        <td style="font-weight: 500; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${f.file}">${f.file}</td>
        <td style="font-size: 0.8rem; color: var(--text-secondary); font-family: monospace;">${f.rule_triggered}</td>
        <td style="color: var(--text-muted); font-size: 0.8rem; font-family: monospace;">${f.field_path}</td>
        <td>
          <span class="badge ${getBadgeClass(f.risk_tier)}">${f.risk_tier}</span>
        </td>
        <td style="color: var(--text-secondary); font-size: 0.8rem;">${formatTimestamp(f.timestamp)}</td>
      </tr>
    `).join('');

    // Attach Row Click event
    tableBody.querySelectorAll('.finding-row').forEach(row => {
      row.addEventListener('click', () => {
        const id = row.getAttribute('data-id');
        const finding = findings.find(f => f.finding_id === id);
        if (finding) openFindingModal(finding);
      });
    });
  }

  function getBadgeClass(tier) {
    switch (tier.toLowerCase()) {
      case 'critical': return 'badge-critical';
      case 'high': return 'badge-high';
      case 'medium': return 'badge-medium';
      case 'low': return 'badge-low';
      default: return 'badge-low';
    }
  }

  // --- View: Drift Scores ---
  async function renderScores() {
    viewContainer.innerHTML = `<div class="loading-spinner">Loading Drift Matrices...</div>`;

    try {
      const scores = await window.api.getDriftScores();
      
      let html = `
        <div style="margin-bottom: 24px;">
          <h3 class="section-title" style="font-size: 1.3rem; margin-bottom:6px;">Configuration File Drift Scoring</h3>
          <p style="color: var(--text-secondary); font-size:0.9rem;">Files with critical drift velocity flags require immediate baseline syncing.</p>
        </div>

        <div class="score-card-grid">
          ${scores.map(s => {
            const riskClass = s.cumulative_score >= 40 ? 'high-risk' : s.cumulative_score >= 15 ? 'medium-risk' : 'low-risk';
            const progressColor = s.cumulative_score >= 40 ? 'var(--neon-pink)' : s.cumulative_score >= 15 ? 'var(--color-high)' : 'var(--color-success)';
            
            return `
              <div class="glass-panel file-score-card">
                <div class="card-header-main">
                  <div class="file-name-text" title="${s.file}">${s.file.split('/').pop()}</div>
                  <div class="score-badge-circle ${riskClass}">${s.cumulative_score}</div>
                </div>
                
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 12px; word-break: break-all;">
                  Baseline Commit: <code style="color:var(--text-secondary)">${s.baseline_commit}</code>
                </div>

                <div class="progress-bar-container">
                  <div class="progress-fill" style="width: ${Math.min(100, s.cumulative_score * 2)}%; background: ${progressColor};"></div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:auto;">
                  <span style="font-size:0.8rem; color:var(--text-secondary);">Findings: 
                    <strong style="color:var(--color-critical)">${s.findings_count.critical}C</strong>, 
                    <strong style="color:var(--color-high)">${s.findings_count.high}H</strong>, 
                    <strong style="color:var(--color-medium)">${s.findings_count.medium}M</strong>
                  </span>
                  
                  ${s.velocity_flag ? `
                    <span class="badge badge-velocity">
                      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flame" style="margin-right:2px;"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
                      Velocity Alert
                    </span>
                  ` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;

      viewContainer.innerHTML = html;

    } catch (e) {
      console.error(e);
      viewContainer.innerHTML = `<div style="color: var(--color-critical);">Failed to load drift score matrices.</div>`;
    }
  }

  // --- View: Pipeline Architecture Map ---
  function renderArchitecture() {
    let html = `
      <div style="margin-bottom: 24px;">
        <h3 class="section-title" style="font-size: 1.3rem; margin-bottom: 6px;">DriftGuard Processing Pipeline</h3>
        <p style="color: var(--text-secondary); font-size: 0.9rem;">
          Hover or click on individual pipeline components to view details. Highlighted components run in the 2-day POC.
        </p>
      </div>

      <div class="glass-panel" style="padding:30px; position:relative;">
        <div class="arch-svg-container">
          <svg width="860" height="280" viewBox="0 0 860 280" fill="none" xmlns="http://www.w3.org/2000/svg" style="overflow: visible;">
            <!-- Connector Lines -->
            <!-- Git to Ingestion -->
            <path d="M120 140 H180" class="arch-line active-line" />
            <!-- Ingestion to Diff -->
            <path d="M280 140 H340" class="arch-line active-line" />
            <!-- Diff to Classifier -->
            <path d="M440 140 H500" class="arch-line active-line" />
            <!-- Classifier to LLM -->
            <path d="M600 140 H660" class="arch-line active-line" />
            <!-- LLM to Storage -->
            <path d="M760 140 H800" class="arch-line active-line" />
            
            <!-- Roadmap paths branch -->
            <!-- Webhook to Redis queue -->
            <path d="M60 80 V50 H180" class="arch-line roadmap-line" />
            <!-- Ingestion Queue to Diff -->
            <path d="M280 50 H310 V140" class="arch-line roadmap-line" />
            <!-- Storage to Slack Notification -->
            <path d="M820 180 V220 H660" class="arch-line roadmap-line" />

            <!-- Pipeline Nodes -->
            
            <!-- Git Ingestion Source -->
            <g class="arch-node active-node" id="node-git" style="cursor:pointer;">
              <rect x="20" y="80" width="100" height="120" rx="8" />
              <text x="70" y="125" class="arch-text" text-anchor="middle">Git Hook</text>
              <text x="70" y="145" class="arch-subtext" text-anchor="middle">PyDriller Engine</text>
              <text x="70" y="170" fill="var(--color-success)" class="arch-badge" text-anchor="middle" font-size="8">POC BUILT</text>
            </g>

            <!-- Ingestion Queue (Roadmap) -->
            <g class="arch-node roadmap-node" id="node-queue" style="cursor:pointer;">
              <rect x="180" y="10" width="100" height="80" rx="8" />
              <text x="230" y="45" class="arch-text" text-anchor="middle">Celery+Redis</text>
              <text x="230" y="60" class="arch-subtext" text-anchor="middle">Async Queue</text>
              <text x="230" y="75" fill="var(--neon-cyan)" class="arch-badge" text-anchor="middle" font-size="8">ROADMAP</text>
            </g>

            <!-- Ingestion parser -->
            <g class="arch-node active-node" id="node-parser" style="cursor:pointer;">
              <rect x="180" y="100" width="100" height="80" rx="8" />
              <text x="230" y="135" class="arch-text" text-anchor="middle">Diff Parser</text>
              <text x="230" y="150" class="arch-subtext" text-anchor="middle">YAML / Nginx</text>
              <text x="230" y="165" fill="var(--color-success)" class="arch-badge" text-anchor="middle" font-size="8">POC BUILT</text>
            </g>

            <!-- Risk Classifier Engine -->
            <g class="arch-node active-node" id="node-rules" style="cursor:pointer;">
              <rect x="340" y="100" width="100" height="80" rx="8" />
              <text x="390" y="135" class="arch-text" text-anchor="middle">Rules Engine</text>
              <text x="390" y="150" class="arch-subtext" text-anchor="middle">P1 Risk Matrix</text>
              <text x="390" y="165" fill="var(--color-success)" class="arch-badge" text-anchor="middle" font-size="8">POC BUILT</text>
            </g>

            <!-- LLM Rationale -->
            <g class="arch-node active-node" id="node-llm" style="cursor:pointer;">
              <rect x="500" y="100" width="100" height="80" rx="8" />
              <text x="550" y="135" class="arch-text" text-anchor="middle">LLM API</text>
              <text x="550" y="150" class="arch-subtext" text-anchor="middle">Claude Explainer</text>
              <text x="550" y="165" fill="var(--color-success)" class="arch-badge" text-anchor="middle" font-size="8">POC BUILT</text>
            </g>

            <!-- Postgres Storage -->
            <g class="arch-node active-node" id="node-db" style="cursor:pointer;">
              <rect x="660" y="100" width="100" height="80" rx="8" />
              <text x="710" y="135" class="arch-text" text-anchor="middle">PostgreSQL</text>
              <text x="710" y="150" class="arch-subtext" text-anchor="middle">Findings Store</text>
              <text x="710" y="165" fill="var(--color-success)" class="arch-badge" text-anchor="middle" font-size="8">POC BUILT</text>
            </g>

            <!-- Slack / Email Notifications (Roadmap) -->
            <g class="arch-node roadmap-node" id="node-alert" style="cursor:pointer;">
              <rect x="560" y="200" width="100" height="70" rx="8" />
              <text x="610" y="235" class="arch-text" text-anchor="middle">Alerts Hub</text>
              <text x="610" y="250" class="arch-subtext" text-anchor="middle">Slack Webhooks</text>
              <text x="610" y="260" fill="var(--neon-cyan)" class="arch-badge" text-anchor="middle" font-size="8">ROADMAP</text>
            </g>
          </svg>
        </div>

        <div id="arch-description-box" class="glass-panel" style="margin-top: 24px; padding: 20px; border-color: rgba(255,255,255,0.08); background: rgba(0,0,0,0.2);">
          <h4 style="font-family: var(--font-display); font-weight:700; color: #fff; margin-bottom: 8px;" id="arch-detail-title">Pipeline component: Select a node</h4>
          <p style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6;" id="arch-detail-desc">
            Click on any module in the pipeline diagram above to view details, its scope boundary, data contracts, and implementation design.
          </p>
        </div>
      </div>
    `;

    viewContainer.innerHTML = html;

    // Attach click events to SVG nodes
    const nodeDetails = {
      'node-git': {
        title: 'Git Ingestion Engine (POC Built)',
        desc: 'Extracts code commits and files configuration. Uses PyDriller to parse Git repositories locally over a specified commit history window, searching for target configuration files (YAML manifest, nginx configs, Terraform modules, Ansible playbooks).'
      },
      'node-queue': {
        title: 'Celery + Redis Async Queue (Roadmap feature)',
        desc: 'Planned scaling enhancement. In production, webhooks from GitHub/GitLab will push jobs to a Redis broker. Celery workers will execute ingestion tasks asynchronously in background containers to avoid blocking the main API thread.'
      },
      'node-parser': {
        title: 'Structural Diff Parser (POC Built)',
        desc: 'Computes differences structurally. Instead of evaluating plain text lines, this parses YAML and nginx configurations into structured dictionary trees and compares values at specific path nodes (e.g., server.listen or securityContext.privileged).'
      },
      'node-rules': {
        title: 'Hybrid Rules-Based Risk Classifier (POC Built)',
        desc: 'Classifies configuration risk levels. Evaluates configuration changes against predefined security rules (such as unencrypted TLS endpoints, exposed container privilege settings, or plaintext secrets) to compute severity tags and confidence.'
      },
      'node-llm': {
        title: 'Large Language Model Rationale Generator (POC Built)',
        desc: 'Generates plain-English security compliance explanations. For Critical and High severity findings, the prompt builder compiles the diff data and sends it to the LLM (e.g., Claude/GPT) to output clear, understandable compliance rationales.'
      },
      'node-db': {
        title: 'PostgreSQL Relational DB (POC Built)',
        desc: 'Persists user accounts, findings records, cumulative drift scores, and audit activities. Provides transactional compliance records with relational safety guarantees.'
      },
      'node-alert': {
        title: 'Alerting & Notifications (Roadmap feature)',
        desc: 'Planned notification sync. Integrates Slack apps, Teams notifications, and secure email alerts to notify SREs and DevSecOps engineers the instant a high-risk drift event is classified.'
      }
    };

    Object.keys(nodeDetails).forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('click', () => {
          document.getElementById('arch-detail-title').innerText = nodeDetails[id].title;
          document.getElementById('arch-detail-desc').innerText = nodeDetails[id].desc;
          
          // Briefly flash border glow
          const box = document.getElementById('arch-description-box');
          box.style.borderColor = id.includes('roadmap') ? 'var(--neon-cyan)' : 'var(--neon-pink)';
        });
      }
    });
  }

  // --- View: Admin Audit Activity Logs ---
  async function renderAudit() {
    viewContainer.innerHTML = `<div class="loading-spinner">Loading audit trails...</div>`;

    try {
      const logs = await window.api.getAuditLogs();
      
      let html = `
        <div style="margin-bottom: 24px;">
          <h3 class="section-title" style="font-size: 1.3rem; margin-bottom: 6px;">Audit Security Activity Trails</h3>
          <p style="color: var(--text-secondary); font-size: 0.9rem;">Immutable administrative and auth tracking records (RBAC Restrained).</p>
        </div>

        <div class="glass-panel table-wrapper">
          <table class="custom-table">
            <thead>
              <tr>
                <th>Audit ID</th>
                <th>Operator (User)</th>
                <th>Action</th>
                <th>Target Resource</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              ${logs.map(l => `
                <tr>
                  <td style="font-family: monospace; color: var(--text-secondary);">LOG-${1000 + l.id}</td>
                  <td style="font-weight: 500;">${l.user}</td>
                  <td>
                    <span class="badge ${l.action === 'TRIGGER_SCAN' ? 'badge-critical' : 'badge-low'}" style="font-size: 0.65rem;">
                      ${l.action}
                    </span>
                  </td>
                  <td style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted);">${l.resource}</td>
                  <td style="color: var(--text-secondary); font-size:0.8rem;">${formatTimestamp(l.timestamp)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;

      viewContainer.innerHTML = html;

    } catch (e) {
      console.error(e);
      viewContainer.innerHTML = `<div style="color: var(--color-critical);">Permission Denied or API request failed.</div>`;
    }
  }

  // --- Drill-down Detail Modal ---
  function openFindingModal(finding) {
    state.selectedFinding = finding;

    const modalTitle = document.getElementById('modal-title-text');
    const modalBody = document.getElementById('modal-body-content');

    modalTitle.innerText = `Compliance Issue Detail: ${finding.finding_id}`;
    
    // Construct old/new code diff viewer layout
    const oldCode = finding.old_value || 'None (Null)';
    const newCode = finding.new_value || 'None (Null)';

    modalBody.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px; flex-wrap:wrap; gap:10px;">
        <div style="font-size:0.95rem; font-weight:600; color: #fff; word-break:break-all; max-width:70%;">
          Target Configuration File: <br/>
          <span style="color: var(--neon-cyan); font-family:monospace; font-size:0.85rem;">${finding.file}</span>
        </div>
        <span class="badge ${getBadgeClass(finding.risk_tier)}" style="font-size: 0.8rem; padding: 6px 12px;">
          ${finding.risk_tier} Severity
        </span>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px; font-size:0.85rem;">
        <div style="padding:12px; background:rgba(0,0,0,0.2); border-radius:6px; border:1px solid rgba(255,255,255,0.05)">
          <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; margin-bottom:4px;">Rule Triggered</div>
          <div style="font-family:monospace; font-weight:600; color:#fff;">${finding.rule_triggered}</div>
        </div>
        <div style="padding:12px; background:rgba(0,0,0,0.2); border-radius:6px; border:1px solid rgba(255,255,255,0.05)">
          <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; margin-bottom:4px;">Target Key Path</div>
          <div style="font-family:monospace; font-weight:600; color:#fff;">${finding.field_path}</div>
        </div>
      </div>

      <div style="margin-bottom:8px; font-size:0.85rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Structural Value Diff</div>
      <div class="diff-viewer">
        <div class="diff-line deletion">
          <div class="diff-label">REVERT</div>
          <div class="diff-value">${escapeHtml(oldCode)}</div>
        </div>
        <div class="diff-line addition">
          <div class="diff-label">CURRENT</div>
          <div class="diff-value">${escapeHtml(newCode)}</div>
        </div>
      </div>

      <div class="llm-rationale-box">
        <div class="llm-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
          DriftGuard LLM Compliance Analyzer
        </div>
        <div class="llm-body" id="llm-rationale-text">
          <!-- Text animates here -->
        </div>
      </div>
      
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
        <button class="btn-scan" id="mitigate-btn" style="background:linear-gradient(90deg, #3b82f6, var(--neon-cyan)); color:#070913; display:flex; align-items:center; gap:6px;">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-undo-2"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></svg>
          Revert Configurations (Fix)
        </button>
      </div>
    `;

    findingModal.classList.add('active');

    // Mitigate Button (Role Restricted)
    const mitigateBtn = document.getElementById('mitigate-btn');
    if (state.currentUser && state.currentUser.role === 'viewer') {
      mitigateBtn.setAttribute('disabled', 'true');
      mitigateBtn.style.opacity = '0.5';
      mitigateBtn.title = 'Viewers cannot modify configuration states';
    } else {
      mitigateBtn.addEventListener('click', () => {
        showToast('Initiating automatic patch PR rollout to Git repo...');
        findingModal.classList.remove('active');
      });
    }

    // Typewriter effect for LLM rationale
    animateText('llm-rationale-text', finding.rationale, 15);
  }

  modalClose.addEventListener('click', () => {
    findingModal.classList.remove('active');
  });

  findingModal.addEventListener('click', (e) => {
    if (e.target === findingModal) {
      findingModal.classList.remove('active');
    }
  });

  // --- Manual Scan execution UI triggers ---
  scanBtn.addEventListener('click', async () => {
    if (state.currentUser.role !== 'admin') return;
    
    state.isScanning = true;
    scanOverlay.classList.add('active');
    scanPercentEl.innerText = '0%';
    scanProgressFill.style.width = '0%';
    scanLogEl.innerHTML = '';

    const logs = [
      'Establishing API tunnel to Git repository...',
      'Polling commit index changes against master branch...',
      'Ingesting commit window (a1b2c3d -> eb3a772)...',
      'Executing AST config parses on changed files...',
      'Running DriftGuard structural rule triggers...',
      'Flagging security policy deviations...',
      'Requesting LLM security context summaries...',
      'Updating compliance metrics database tables...'
    ];

    let progress = 0;
    let logIndex = 0;

    const interval = setInterval(async () => {
      progress += Math.floor(Math.random() * 8) + 4;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        
        // Execute API Scan Trigger
        try {
          const res = await window.api.triggerScan();
          appendScanLog('Scan completed successfully! database tables updated.');
          setTimeout(() => {
            scanOverlay.classList.remove('active');
            state.isScanning = false;
            // Reload Dashboard view
            switchTab(state.activeTab);
            showToast('Git compliance scan completed.');
          }, 1000);
        } catch (e) {
          appendScanLog(`Error during database persistence: ${e.message}`);
          setTimeout(() => {
            scanOverlay.classList.remove('active');
            state.isScanning = false;
          }, 3000);
        }
      }

      scanPercentEl.innerText = `${progress}%`;
      scanProgressFill.style.width = `${progress}%`;

      // Append log statements periodically
      const step = Math.floor(100 / logs.length);
      if (progress >= logIndex * step && logIndex < logs.length) {
        appendScanLog(logs[logIndex]);
        logIndex++;
      }
    }, 150);
  });

  function appendScanLog(text) {
    const line = document.createElement('div');
    line.style.fontSize = '0.85rem';
    line.style.fontFamily = 'monospace';
    line.style.color = 'var(--text-secondary)';
    line.style.marginBottom = '4px';
    line.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
    scanLogEl.appendChild(line);
    scanLogEl.scrollTop = scanLogEl.scrollHeight;
  }

  // --- Utility functions ---
  function formatTimestamp(isoString) {
    const d = new Date(isoString);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }

  function animateText(elementId, text, speed) {
    const container = document.getElementById(elementId);
    if (!container) return;
    container.innerHTML = '';
    
    let index = 0;
    function type() {
      if (index < text.length) {
        container.innerHTML += text.charAt(index);
        index++;
        setTimeout(type, speed);
      }
    }
    type();
  }

  function showToast(message) {
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '30px';
    toast.style.right = '30px';
    toast.style.background = 'var(--bg-tertiary)';
    toast.style.border = '1px solid var(--neon-pink)';
    toast.style.color = '#fff';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 0 15px var(--neon-pink-glow)';
    toast.style.zIndex = '500';
    toast.style.fontFamily = 'var(--font-display)';
    toast.style.fontWeight = '600';
    toast.style.fontSize = '0.9rem';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';

    document.body.appendChild(toast);
    
    // Trigger transition reflow
    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
      toast.innerText = message;
    }, 50);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 3500);
  }

  // Run initialization
  init();
});
