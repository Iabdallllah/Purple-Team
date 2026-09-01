export const OWASP_TOP_10_2021 = [
  {
    id: "A01",
    name: "Broken Access Control",
    description: "Users can act outside of their intended permissions",
    examples: ["IDOR", "Path Traversal", "Missing Function Level Access Control"],
    mitreTechniques: ["T1548", "T1083", "T1005"]
  },
  {
    id: "A02",
    name: "Cryptographic Failures",
    description: "Failures related to cryptography which often leads to sensitive data exposure",
    examples: ["Weak Encryption", "Clear Text Transmission", "Weak Hashing"],
    mitreTechniques: ["T1557", "T1040", "T1552"]
  },
  {
    id: "A03",
    name: "Injection",
    description: "Untrusted data sent to interpreter as part of command or query",
    examples: ["SQL Injection", "NoSQL Injection", "Command Injection", "LDAP Injection"],
    mitreTechniques: ["T1190", "T1059", "T1059.007"]
  },
  {
    id: "A04",
    name: "Insecure Design",
    description: "Missing or ineffective control design",
    examples: ["Missing Business Logic Validation", "Insecure Password Recovery"],
    mitreTechniques: ["T1599", "T1585"]
  },
  {
    id: "A05",
    name: "Security Misconfiguration",
    description: "Security settings not defined, implemented, or maintained properly",
    examples: ["Default Credentials", "Unnecessary Features", "Verbose Error Messages"],
    mitreTechniques: ["T1599", "T1585", "T1592"]
  },
  {
    id: "A06",
    name: "Vulnerable and Outdated Components",
    description: "Using components with known vulnerabilities",
    examples: ["Outdated Libraries", "Unpatched Frameworks"],
    mitreTechniques: ["T1190", "T1585"]
  },
  {
    id: "A07",
    name: "Identification and Authentication Failures",
    description: "Confirmation of user identity, authentication, and session management failures",
    examples: ["Credential Stuffing", "Weak Password Policy", "Session Fixation"],
    mitreTechniques: ["T1110", "T1556", "T1539"]
  },
  {
    id: "A08",
    name: "Software and Data Integrity Failures",
    description: "Code and infrastructure not protected against integrity violations",
    examples: ["Unsigned Updates", "CI/CD Pipeline Compromise", "Auto-update without verification"],
    mitreTechniques: ["T1195", "T1553", "T1584"]
  },
  {
    id: "A09",
    name: "Security Logging and Monitoring Failures",
    description: "Insufficient logging, detection, monitoring, and alerting",
    examples: ["No Audit Logs", "Logs Not Monitored", "Alerting Not Configured"],
    mitreTechniques: ["T1562", "T1070", "T1556"]
  },
  {
    id: "A10",
    name: "Server-Side Request Forgery (SSRF)",
    description: "Fetching remote resources without validating user-supplied URL",
    examples: ["Internal Port Scanning", "Cloud Metadata Access", "File System Access"],
    mitreTechniques: ["T1590", "T1592", "T1580"]
  }
] as const;

export type OwaspCategory = typeof OWASP_TOP_10_2021[number]["id"];

export function getOwaspCategory(id: string) {
  return OWASP_TOP_10_2021.find(c => c.id === id);
}

export function getOwaspCategories() {
  return OWASP_TOP_10_2021.map(c => ({ id: c.id, name: c.name }));
}