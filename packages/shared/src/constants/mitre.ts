export const MITRE_ATTACK_WEB_TECHNIQUES = [
  // Initial Access
  {
    id: "T1190",
    name: "Exploit Public-Facing Application",
    tactic: "initial-access",
    description: "Exploit vulnerabilities in web applications",
    owaspCategories: ["A03", "A06"],
    detectionPatterns: ["sql injection", "rce", "deserialization", "path traversal"],
    mitigations: ["WAF", "Input Validation", "Patch Management"]
  },
  {
    id: "T1199",
    name: "Trusted Relationship",
    tactic: "initial-access",
    description: "Exploit trust relationships between systems",
    owaspCategories: ["A01", "A04"],
    detectionPatterns: ["sso bypass", "oauth misuse", "jwt manipulation"],
    mitigations: ["Zero Trust", "Token Validation", "Scope Enforcement"]
  },
  // Execution
  {
    id: "T1059",
    name: "Command and Scripting Interpreter",
    tactic: "execution",
    description: "Execute commands through web shell or injection",
    owaspCategories: ["A03"],
    detectionPatterns: ["command injection", "webshell", "reverse shell"],
    mitigations: ["Disable Shell Functions", "Container Hardening", "Runtime Protection"]
  },
  {
    id: "T1059.007",
    name: "JavaScript/JScript",
    tactic: "execution",
    description: "Execute JavaScript through XSS or SSJI",
    owaspCategories: ["A03"],
    detectionPatterns: ["xss", "ssji", "template injection"],
    mitigations: ["CSP", "Input Sanitization", "Sandboxed Evaluation"]
  },
  // Persistence
  {
    id: "T1505",
    name: "Server Software Component",
    tactic: "persistence",
    description: "Install web shell or malicious module",
    owaspCategories: ["A03", "A08"],
    detectionPatterns: ["webshell", "malicious plugin", "backdoor"],
    mitigations: ["File Integrity Monitoring", "Read-only Filesystem", "Runtime Protection"]
  },
  // Privilege Escalation
  {
    id: "T1548",
    name: "Abuse Elevation Control Mechanism",
    tactic: "privilege-escalation",
    description: "Bypass authorization controls",
    owaspCategories: ["A01", "A07"],
    detectionPatterns: ["privilege escalation", "role bypass", "admin bypass"],
    mitigations: ["Least Privilege", "RBAC", "Authorization Checks"]
  },
  // Defense Evasion
  {
    id: "T1070",
    name: "Indicator Removal",
    tactic: "defense-evasion",
    description: "Clear logs or evidence",
    owaspCategories: ["A09"],
    detectionPatterns: ["log clearing", "history deletion", "timestamp modification"],
    mitigations: ["Centralized Logging", "Immutable Logs", "Log Monitoring"]
  },
  {
    id: "T1562",
    name: "Impair Defenses",
    tactic: "defense-evasion",
    description: "Disable security tools",
    owaspCategories: ["A05", "A09"],
    detectionPatterns: ["waf bypass", "disable security headers", "csp bypass"],
    mitigations: ["Tamper Protection", "Security Headers", "CSP Enforcement"]
  },
  // Credential Access
  {
    id: "T1552",
    name: "Unsecured Credentials",
    tactic: "credential-access",
    description: "Find credentials in files, config, or code",
    owaspCategories: ["A02", "A07"],
    detectionPatterns: ["credential exposure", "api key leak", "password in code"],
    mitigations: ["Secrets Management", "Git Hooks", "Credential Scanning"]
  },
  {
    id: "T1556",
    name: "Modify Authentication Process",
    tactic: "credential-access",
    description: "Intercept or modify authentication",
    owaspCategories: ["A07"],
    detectionPatterns: ["session hijacking", "token theft", "password reset abuse"],
    mitigations: ["Secure Cookies", "HTTPS Only", "Short Token Expiry"]
  },
  // Discovery
  {
    id: "T1083",
    name: "File and Directory Discovery",
    tactic: "discovery",
    description: "Enumerate files and directories",
    owaspCategories: ["A01", "A05"],
    detectionPatterns: ["directory traversal", "file enumeration", "backup file access"],
    mitigations: ["Access Controls", "Directory Indexing Disabled", "File Permissions"]
  },
  {
    id: "T1590",
    name: "Active Scanning",
    tactic: "reconnaissance",
    description: "Scan for vulnerabilities",
    owaspCategories: ["A05", "A10"],
    detectionPatterns: ["port scanning", "vulnerability scanning", "directory brute force"],
    mitigations: ["Rate Limiting", "WAF", "Honeypots"]
  },
  {
    id: "T1592",
    name: "Gather Victim Host Information",
    tactic: "reconnaissance",
    description: "Gather info about target",
    owaspCategories: ["A05", "A10"],
    detectionPatterns: ["technology fingerprinting", "version detection", "error enumeration"],
    mitigations: ["Error Handling", "Version Hiding", "Security Headers"]
  },
  // Lateral Movement
  {
    id: "T1570",
    name: "Lateral Tool Transfer",
    tactic: "lateral-movement",
    description: "Transfer tools between systems",
    owaspCategories: ["A03", "A08"],
    detectionPatterns: ["file upload", "tool download", "malicious payload"],
    mitigations: ["File Upload Validation", "Network Segmentation", "Egress Filtering"]
  },
  // Collection
  {
    id: "T1005",
    name: "Data from Local System",
    tactic: "collection",
    description: "Collect sensitive data",
    owaspCategories: ["A01", "A02"],
    detectionPatterns: ["data exfiltration", "database dump", "file download"],
    mitigations: ["DLP", "Access Controls", "Encryption"]
  },
  // Command and Control
  {
    id: "T1071",
    name: "Application Layer Protocol",
    tactic: "command-and-control",
    description: "C2 over HTTP/HTTPS",
    owaspCategories: ["A03", "A10"],
    detectionPatterns: ["beaconing", "c2 traffic", "dns tunneling"],
    mitigations: ["Network Monitoring", "DNS Filtering", "Traffic Analysis"]
  },
  // Impact
  {
    id: "T1485",
    name: "Data Destruction",
    tactic: "impact",
    description: "Destroy data",
    owaspCategories: ["A03", "A04"],
    detectionPatterns: ["data deletion", "drop table", "rm -rf"],
    mitigations: ["Backups", "Immutable Storage", "Access Controls"]
  },
  {
    id: "T1491",
    name: "Defacement",
    tactic: "impact",
    description: "Modify visual appearance",
    owaspCategories: ["A03", "A04"],
    detectionPatterns: ["content modification", "html injection", "stored xss"],
    mitigations: ["CSP", "Input Validation", "File Integrity Monitoring"]
  }
] as const;

export type MitreTechniqueId = typeof MITRE_ATTACK_WEB_TECHNIQUES[number]["id"];
export type MitreTactic = typeof MITRE_ATTACK_WEB_TECHNIQUES[number]["tactic"];

export function getMitreTechnique(id: string) {
  return MITRE_ATTACK_WEB_TECHNIQUES.find(t => t.id === id);
}

export function getMitreTechniquesByTactic(tactic: MitreTactic) {
  return MITRE_ATTACK_WEB_TECHNIQUES.filter(t => t.tactic === tactic);
}

export function getMitreTechniquesByOwasp(owaspCategory: string) {
  return MITRE_ATTACK_WEB_TECHNIQUES.filter(t => t.owaspCategories.some(c => c === owaspCategory));
}

export const MITRE_TACTICS = [
  "reconnaissance",
  "resource-development",
  "initial-access",
  "execution",
  "persistence",
  "privilege-escalation",
  "defense-evasion",
  "credential-access",
  "discovery",
  "lateral-movement",
  "collection",
  "command-and-control",
  "exfiltration",
  "impact"
] as const;