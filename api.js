const API_BASE_URL = 'http://localhost:8000';

class DriftGuardAPI {
  constructor() {
    this.isLive = false;
    this.token = localStorage.getItem('dg_access_token') || null;
    this.currentUser = JSON.parse(localStorage.getItem('dg_user')) || null;
    this.listeners = [];

    // Mock Database State
    this.mockUsers = [
      { email: 'admin@driftguard.io', role: 'admin', passwordHash: 'admin123' },
      { email: 'viewer@driftguard.io', role: 'viewer', passwordHash: 'viewer123' }
    ];

    this.mockFindings = [
      {
        finding_id: 'f-0091',
        file: 'nginx/sites-available/default.conf',
        commit_hash: 'a1b2c3d',
        timestamp: '2026-07-19T10:22:00Z',
        risk_tier: 'Critical',
        confidence: 0.92,
        rule_triggered: 'TLS_DISABLED',
        field_path: 'server.listen',
        old_value: '443 ssl http2;',
        new_value: '80;',
        rationale: 'This change removes TLS termination on the default server block, exposing all web traffic on unencrypted port 80. This is a critical security regression that compromises data in transit.'
      },
      {
        finding_id: 'f-0092',
        file: 'k8s/production/billing-deployment.yaml',
        commit_hash: 'c8e1a3f',
        timestamp: '2026-07-18T14:45:00Z',
        risk_tier: 'Critical',
        confidence: 0.96,
        rule_triggered: 'PRIVILEGED_CONTAINER',
        field_path: 'spec.template.spec.containers[0].securityContext.privileged',
        old_value: 'false',
        new_value: 'true',
        rationale: 'Allowing container privilege escalation grants the container root-level access to the host system. This bypasses container isolation boundaries and exposes the underlying node to potential takeover.'
      },
      {
        finding_id: 'f-0093',
        file: 'nginx/nginx.conf',
        commit_hash: 'd2b7e9a',
        timestamp: '2026-07-17T09:12:00Z',
        risk_tier: 'High',
        confidence: 0.88,
        rule_triggered: 'BODY_SIZE_UNLIMITED',
        field_path: 'http.client_max_body_size',
        old_value: '10M',
        new_value: '0',
        rationale: 'Setting client_max_body_size to 0 disables limits on client request body size. This leaves the HTTP server vulnerable to Denial of Service (DoS) attacks via oversized payload uploads.'
      },
      {
        finding_id: 'f-0094',
        file: 'terraform/aws/security_groups.tf',
        commit_hash: 'f9a2d8e',
        timestamp: '2026-07-16T16:30:00Z',
        risk_tier: 'High',
        confidence: 0.95,
        rule_triggered: 'SSH_OPEN_TO_WORLD',
        field_path: 'resource.aws_security_group.ssh.ingress[0].cidr_blocks',
        old_value: '["10.0.0.0/16"]',
        new_value: '["0.0.0.0/0"]',
        rationale: 'Ingress rules allowing SSH port 22 access from 0.0.0.0/0 expose the server management interface to the public internet. This leaves the virtual machine open to brute force SSH login attacks.'
      },
      {
        finding_id: 'f-0095',
        file: 'ansible/playbooks/deploy-app.yml',
        commit_hash: 'e5b1c7d',
        timestamp: '2026-07-15T11:05:00Z',
        risk_tier: 'Medium',
        confidence: 0.82,
        rule_triggered: 'HOST_KEY_CHECKING_DISABLED',
        field_path: 'env.ANSIBLE_HOST_KEY_CHECKING',
        old_value: 'True',
        new_value: 'False',
        rationale: 'Disabling host key checking in Ansible scripts prevents the runner from verifying host identity signatures. This makes SSH connections susceptible to Man-in-the-Middle (MitM) attacks during execution.'
      },
      {
        finding_id: 'f-0096',
        file: 'nginx/nginx.conf',
        commit_hash: 'd2b7e9a',
        timestamp: '2026-07-17T09:12:00Z',
        risk_tier: 'Low',
        confidence: 0.90,
        rule_triggered: 'SERVER_TOKENS_ON',
        field_path: 'http.server_tokens',
        old_value: 'off',
        new_value: 'on',
        rationale: 'Exposing server tokens leaks the exact version of Nginx running on the system in HTTP response headers. This assists attackers in identifying specific version exploits.'
      },
      {
        finding_id: 'f-0097',
        file: 'ansible/ansible.cfg',
        commit_hash: 'b3f4d6c',
        timestamp: '2026-07-14T08:15:00Z',
        risk_tier: 'Low',
        confidence: 0.78,
        rule_triggered: 'WORLD_WRITABLE_CONFIG',
        field_path: 'defaults.config_file_permissions',
        old_value: '0644',
        new_value: '0666',
        rationale: 'Setting config permissions to world-writable (0666) allows any local system user to modify the Ansible configuration file, which can lead to privilege escalation via malicious task insertions.'
      }
    ];

    this.mockDriftScores = [
      { file: 'nginx/sites-available/default.conf', baseline_commit: '9f8e7d6', cumulative_score: 34, velocity_flag: true, findings_count: { critical: 1, high: 0, medium: 0, low: 0 } },
      { file: 'k8s/production/billing-deployment.yaml', baseline_commit: 'e2a8c3d', cumulative_score: 45, velocity_flag: true, findings_count: { critical: 1, high: 0, medium: 0, low: 0 } },
      { file: 'nginx/nginx.conf', baseline_commit: '9f8e7d6', cumulative_score: 18, velocity_flag: false, findings_count: { critical: 0, high: 1, medium: 0, low: 1 } },
      { file: 'terraform/aws/security_groups.tf', baseline_commit: 'bc9f2e4', cumulative_score: 25, velocity_flag: false, findings_count: { critical: 0, high: 1, medium: 0, low: 0 } },
      { file: 'ansible/playbooks/deploy-app.yml', baseline_commit: 'de8c7a1', cumulative_score: 12, velocity_flag: false, findings_count: { critical: 0, high: 0, medium: 1, low: 0 } },
      { file: 'ansible/ansible.cfg', baseline_commit: 'de8c7a1', cumulative_score: 5, velocity_flag: false, findings_count: { critical: 0, high: 0, medium: 0, low: 1 } }
    ];

    this.mockTimeline = [
      { date: '2026-07-14', score: 5, events: 1 },
      { date: '2026-07-15', score: 17, events: 1 },
      { date: '2026-07-16', score: 42, events: 1 },
      { date: '2026-07-17', score: 65, events: 2 },
      { date: '2026-07-18', score: 110, events: 1 },
      { date: '2026-07-19', score: 144, events: 1 }
    ];

    this.mockAuditLogs = [
      { id: 1, user: 'admin@driftguard.io', action: 'SIGN_IN', resource: 'Auth API', timestamp: '2026-07-20T00:52:10Z' },
      { id: 2, user: 'admin@driftguard.io', action: 'TRIGGER_SCAN', resource: 'Git: Synergy-2026/k8s-nginx-config-repo', timestamp: '2026-07-20T00:53:15Z' },
      { id: 3, user: 'admin@driftguard.io', action: 'REPORT_EXPORT', resource: 'Markdown Summary PDF', timestamp: '2026-07-20T00:55:00Z' }
    ];
  }

  // Register listener for backend connection changes
  onStatusChange(callback) {
    this.listeners.push(callback);
    callback(this.isLive ? 'live' : 'simulated');
  }

  notifyListeners(status) {
    this.listeners.forEach(cb => cb(status));
  }

  // Health-check backend
  async checkBackendStatus() {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 1200); // 1.2s timeout
      
      const response = await fetch(`${API_BASE_URL}/findings`, {
        signal: controller.signal,
        headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {}
      });
      clearTimeout(id);
      
      // If we got a 200 or even a 401/403 (unauthorized/forbidden), the backend is online!
      if (response.status === 200 || response.status === 401 || response.status === 403) {
        this.isLive = true;
        this.notifyListeners('live');
        return true;
      }
    } catch (e) {
      // Failed to connect, use mock fallback
    }
    
    this.isLive = false;
    this.notifyListeners('simulated');
    return false;
  }

  async login(email, password) {
    if (this.isLive) {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Login failed');
        }
        const data = await response.json();
        this.token = data.access_token;
        this.currentUser = { email, role: data.role };
        localStorage.setItem('dg_access_token', this.token);
        localStorage.setItem('dg_user', JSON.stringify(this.currentUser));
        return this.currentUser;
      } catch (e) {
        console.error('Backend Login failed, trying mock fallback if credentials match default admins', e);
      }
    }

    // Mock Login
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const user = this.mockUsers.find(u => u.email === email && u.passwordHash === password);
        if (user) {
          this.currentUser = { email: user.email, role: user.role };
          this.token = 'mock-jwt-token-12345';
          localStorage.setItem('dg_access_token', this.token);
          localStorage.setItem('dg_user', JSON.stringify(this.currentUser));
          
          this.addMockAuditLog('SIGN_IN', 'Simulated Auth API');
          resolve(this.currentUser);
        } else {
          reject(new Error('Invalid email or password. Hint: Use admin@driftguard.io / admin123 or viewer@driftguard.io / viewer123'));
        }
      }, 500);
    });
  }

  async signup(email, password, role = 'viewer') {
    if (this.isLive) {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, role })
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Signup failed');
        }
        return await response.json();
      } catch (e) {
        console.error('Backend Signup failed, falling back to mock registration', e);
      }
    }

    // Mock Signup
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const exists = this.mockUsers.some(u => u.email === email);
        if (exists) {
          reject(new Error('User already exists'));
        } else {
          this.mockUsers.push({ email, role, passwordHash: password });
          resolve({ email, role, msg: 'User created successfully' });
        }
      }, 500);
    });
  }

  logout() {
    this.token = null;
    this.currentUser = null;
    localStorage.removeItem('dg_access_token');
    localStorage.removeItem('dg_user');
  }

  async getFindings(riskTier = '') {
    if (this.isLive) {
      try {
        let url = `${API_BASE_URL}/findings`;
        if (riskTier) url += `?risk_tier=${riskTier}`;
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        if (response.ok) return await response.json();
      } catch (e) {
        console.error('Failed to get live findings, returning mock data', e);
      }
    }

    // Mock getFindings
    return new Promise(resolve => {
      setTimeout(() => {
        if (riskTier) {
          resolve(this.mockFindings.filter(f => f.risk_tier.toLowerCase() === riskTier.toLowerCase()));
        } else {
          resolve(this.mockFindings);
        }
      }, 200);
    });
  }

  async getDriftScores() {
    if (this.isLive) {
      try {
        const response = await fetch(`${API_BASE_URL}/drift-scores`, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        if (response.ok) return await response.json();
      } catch (e) {
        console.error('Failed to get live drift scores, returning mock', e);
      }
    }

    return new Promise(resolve => {
      setTimeout(() => resolve(this.mockDriftScores), 200);
    });
  }

  async getTimeline() {
    if (this.isLive) {
      try {
        const response = await fetch(`${API_BASE_URL}/timeline`, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        if (response.ok) return await response.json();
      } catch (e) {
        console.error('Failed to get live timeline data, returning mock', e);
      }
    }

    return new Promise(resolve => {
      setTimeout(() => resolve(this.mockTimeline), 200);
    });
  }

  async getAuditLogs() {
    if (this.isLive) {
      try {
        const response = await fetch(`${API_BASE_URL}/audit-log`, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        if (response.ok) return await response.json();
      } catch (e) {
        console.error('Failed to get live audit logs, returning mock', e);
      }
    }

    return new Promise(resolve => {
      resolve(this.mockAuditLogs);
    });
  }

  async triggerScan() {
    if (this.isLive) {
      const response = await fetch(`${API_BASE_URL}/scan`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Scan failed');
      }
      return await response.json();
    }

    // Mock Scan execution trigger
    return new Promise((resolve) => {
      setTimeout(() => {
        // Add a new mock finding and update drift score to simulate scan discoveries!
        const timestamp = new Date().toISOString();
        const randId = Math.floor(1000 + Math.random() * 9000);
        
        const newFinding = {
          finding_id: `f-${randId}`,
          file: 'terraform/aws/variables.tf',
          commit_hash: 'eb3a772',
          timestamp: timestamp,
          risk_tier: 'High',
          confidence: 0.91,
          rule_triggered: 'PLAINTEXT_SECRET',
          field_path: 'variable.db_password.default',
          old_value: 'null',
          new_value: '"super-secret-pass-2026!"',
          rationale: 'Detects a hardcoded database password in the default block of a Terraform variable. Hardcoding passwords in source files violates secure configuration standards and leads to secret exposures in Git repositories.'
        };

        this.mockFindings.unshift(newFinding);

        // Update score
        const scoreIndex = this.mockDriftScores.findIndex(s => s.file === 'terraform/aws/security_groups.tf');
        if (scoreIndex !== -1) {
          this.mockDriftScores[scoreIndex].cumulative_score += 15;
          this.mockDriftScores[scoreIndex].findings_count.high += 1;
        }

        // Add a new score file entry
        this.mockDriftScores.unshift({
          file: 'terraform/aws/variables.tf',
          baseline_commit: 'bc9f2e4',
          cumulative_score: 30,
          velocity_flag: true,
          findings_count: { critical: 0, high: 1, medium: 0, low: 0 }
        });

        // Add to timeline
        this.mockTimeline.push({
          date: timestamp.substring(0, 10),
          score: this.mockTimeline[this.mockTimeline.length - 1].score + 30,
          events: 1
        });

        this.addMockAuditLog('TRIGGER_SCAN', 'Git: Synergy-2026/k8s-nginx-config-repo (Triggered manually)');
        resolve({ status: 'success', message: 'Scan finished. Ingested 1 new commit, detected 1 new High risk drift finding.' });
      }, 3500); // 3.5s simulation duration
    });
  }

  async exportReport() {
    if (this.isLive) {
      try {
        const response = await fetch(`${API_BASE_URL}/report/export`, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'driftguard-compliance-report.pdf';
          document.body.appendChild(a);
          a.click();
          a.remove();
          return;
        }
      } catch (e) {
        console.error('Failed to export live report, downloading mock file', e);
      }
    }

    // Mock Report Generation
    return new Promise(resolve => {
      this.addMockAuditLog('REPORT_EXPORT', 'Markdown Compliance Summary');
      setTimeout(() => {
        let content = `# DRIFTGUARD COMPLIANCE DRIFT REPORT\n`;
        content += `Generated on: ${new Date().toUTCString()}\n`;
        content += `Target Environment: Synergy 2026 - Production Infrastructure\n`;
        content += `Compliance Status: WARNING (Cumulative Drift Score: ${this.mockTimeline[this.mockTimeline.length - 1].score})\n\n`;
        content += `## Executive Summary\n`;
        content += `DriftGuard has monitored configuration file commits across your infrastructure repository. We detected total of ${this.mockFindings.length} risk finding(s) with varying severity levels. Cumulative drift velocity has flagged 2 files with high-velocity changes.\n\n`;
        content += `## Critical Risks Detected\n`;
        
        this.mockFindings.filter(f => f.risk_tier === 'Critical').forEach(f => {
          content += `### [${f.risk_tier}] ${f.file} (${f.rule_triggered})\n`;
          content += `- **Location**: \`${f.field_path}\`\n`;
          content += `- **Diff**: \`${f.old_value}\` ➔ \`${f.new_value}\`\n`;
          content += `- **Rationale**: ${f.rationale}\n\n`;
        });

        content += `## Drift Remediation Action Items\n`;
        this.mockFindings.forEach((f, idx) => {
          content += `- [ ] [ ] **DG-REM-${100 + idx}**: Revert configuration change in \`${f.file}\` for rule \`${f.rule_triggered}\` (Commit: \`${f.commit_hash}\`).\n`;
        });

        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'driftguard-compliance-report.md';
        document.body.appendChild(a);
        a.click();
        a.remove();
        resolve(true);
      }, 1000);
    });
  }

  addMockAuditLog(action, resource) {
    const user = this.currentUser ? this.currentUser.email : 'anonymous';
    this.mockAuditLogs.unshift({
      id: this.mockAuditLogs.length + 1,
      user,
      action,
      resource,
      timestamp: new Date().toISOString()
    });
  }
}

// Global instantiation
const api = new DriftGuardAPI();
window.api = api;
