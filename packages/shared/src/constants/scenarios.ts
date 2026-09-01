export const SCENARIOS = [
  {
    id: "idor",
    name: "IDOR / Auth Abuse",
    description: "Insecure Direct Object References and Authorization Bypass",
    owaspCategories: ["A01", "A07"],
    mitreTechniques: ["T1190", "T1548", "T1083"],
    targetApps: ["juice_shop", "dvwa", "custom"],
    difficulty: "medium",
    estimatedDurationMinutes: 20,
    attackTypes: [
      "horizontal_idor",
      "vertical_idor",
      "parameter_tampering",
      "jwt_manipulation",
      "broken_object_level_auth",
      "broken_function_level_auth"
    ],
    detectionFocus: [
      "access_control_bypass",
      "unauthorized_data_access",
      "privilege_escalation",
      "session_manipulation"
    ],
    responseActions: [
      "add_authorization_checks",
      "implement_rbac",
      "validate_object_ownership",
      "rate_limit_sensitive_endpoints"
    ]
  },
  {
    id: "injection",
    name: "Injection Attacks",
    description: "SQL, NoSQL, Command, and LDAP Injection",
    owaspCategories: ["A03"],
    mitreTechniques: ["T1190", "T1059", "T1059.007"],
    targetApps: ["juice_shop", "dvwa", "custom"],
    difficulty: "high",
    estimatedDurationMinutes: 30,
    attackTypes: [
      "sql_injection",
      "nosql_injection",
      "command_injection",
      "ldap_injection",
      "xpath_injection",
      "template_injection"
    ],
    detectionFocus: [
      "anomalous_query_patterns",
      "command_execution_signatures",
      "input_sanitization_failures",
      "error_based_extraction"
    ],
    responseActions: [
      "parameterized_queries",
      "input_validation",
      "waf_rules",
      "disable_unused_interpreters"
    ]
  },
  {
    id: "business_logic",
    name: "Business Logic Abuse",
    description: "Multi-step workflow manipulation, race conditions, price manipulation",
    owaspCategories: ["A04", "A01"],
    mitreTechniques: ["T1199", "T1548", "T1485"],
    targetApps: ["custom", "juice-shop"],
    difficulty: "high",
    estimatedDurationMinutes: 25,
    attackTypes: [
      "race_condition",
      "price_manipulation",
      "workflow_bypass",
      "coupon_abuse",
      "inventory_manipulation",
      "business_rule_violation"
    ],
    detectionFocus: [
      "anomalous_state_transitions",
      "business_rule_violations",
      "concurrent_request_anomalies",
      "value_manipulation"
    ],
    responseActions: [
      "idempotency_keys",
      "server_side_validation",
      "transaction_locks",
      "business_rule_enforcement"
    ]
  },
  {
    id: "ssrf",
    name: "SSRF / Server-Side Request Forgery",
    description: "Server-Side Request Forgery attacks",
    owaspCategories: ["A10"],
    mitreTechniques: ["T1590", "T1592", "T1580"],
    targetApps: ["juice-shop", "custom"],
    difficulty: "medium",
    estimatedDurationMinutes: 15,
    attackTypes: [
      "basic_ssrf",
      "blind_ssrf",
      "cloud_metadata_access",
      "internal_port_scanning",
      "file_scheme_access"
    ],
    detectionFocus: [
      "outbound_request_anomalies",
      "internal_ip_access",
      "metadata_endpoint_access",
      "unexpected_dns_resolution"
    ],
    responseActions: [
      "allowlist_urls",
      "block_private_ips",
      "disable_unused_schemes",
      "egress_filtering"
    ]
  },
  {
    id: "broken_auth",
    name: "Broken Authentication",
    description: "Credential stuffing, session fixation, weak password reset",
    owaspCategories: ["A07"],
    mitreTechniques: ["T1110", "T1556", "T1539"],
    targetApps: ["juice-shop", "dvwa", "custom"],
    difficulty: "medium",
    estimatedDurationMinutes: 20,
    attackTypes: [
      "credential_stuffing",
      "session_fixation",
      "weak_password_reset",
      "password_spraying",
      "jwt_algorithm_confusion",
      "token_replay"
    ],
    detectionFocus: [
      "failed_login_patterns",
      "session_anomalies",
      "token_reuse",
      "password_reset_abuse"
    ],
    responseActions: [
      "rate_limiting",
      "mfa_enforcement",
      "secure_password_policy",
      "token_rotation",
      "account_lockout"
    ]
  }
] as const;

export type ScenarioId = typeof SCENARIOS[number]["id"];
export type AttackType = typeof SCENARIOS[number]["attackTypes"][number];
export type DetectionFocus = typeof SCENARIOS[number]["detectionFocus"][number];
export type ResponseAction = typeof SCENARIOS[number]["responseActions"][number];

export function getScenario(id: string) {
  return SCENARIOS.find(s => s.id === id);
}

export function getScenarios() {
  return SCENARIOS.map(s => ({
    id: s.id,
    name: s.name,
    description: s.description,
    difficulty: s.difficulty,
    estimatedDurationMinutes: s.estimatedDurationMinutes
  }));
}

export function getScenariosForTargetApp(targetApp: string) {
  return SCENARIOS.filter(s => s.targetApps.includes(targetApp as any));
}