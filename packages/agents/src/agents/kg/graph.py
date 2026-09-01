import networkx as nx
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)

# Mirror of packages/shared/src/constants/owasp.ts + mitre.ts + scenarios.ts
OWASP_TOP10 = [
    {"id":"A01","name":"Broken Access Control","mitre":["T1548","T1083","T1005"]},
    {"id":"A02","name":"Cryptographic Failures","mitre":["T1557","T1040","T1552"]},
    {"id":"A03","name":"Injection","mitre":["T1190","T1059","T1059.007"]},
    {"id":"A04","name":"Insecure Design","mitre":["T1599","T1585"]},
    {"id":"A05","name":"Security Misconfiguration","mitre":["T1599","T1585","T1592"]},
    {"id":"A06","name":"Vulnerable Components","mitre":["T1190","T1585"]},
    {"id":"A07","name":"Identification & Authentication Failures","mitre":["T1110","T1556","T1539"]},
    {"id":"A08","name":"Software & Data Integrity Failures","mitre":["T1195","T1553","T1584"]},
    {"id":"A09","name":"Logging & Monitoring Failures","mitre":["T1562","T1070","T1556"]},
    {"id":"A10","name":"Server-Side Request Forgery","mitre":["T1590","T1592","T1580"]},
]
MITRE_TECHNIQUES = [
    {"id":"T1190","name":"Exploit Public-Facing Application","tactic":"initial-access","owasp":["A03","A06"],"mitigations":["WAF","Input Validation","Patch"]},
    {"id":"T1199","name":"Trusted Relationship","tactic":"initial-access","owasp":["A01","A04"],"mitigations":["Zero Trust","Token Validation"]},
    {"id":"T1059","name":"Command and Scripting Interpreter","tactic":"execution","owasp":["A03"],"mitigations":["Disable Shell","Container Hardening"]},
    {"id":"T1059.007","name":"JavaScript","tactic":"execution","owasp":["A03"],"mitigations":["CSP","Sanitization"]},
    {"id":"T1505","name":"Server Software Component","tactic":"persistence","owasp":["A03","A08"],"mitigations":["FIM","RO FS"]},
    {"id":"T1548","name":"Abuse Elevation Control","tactic":"privilege-escalation","owasp":["A01","A07"],"mitigations":["Least Privilege","RBAC"]},
    {"id":"T1070","name":"Indicator Removal","tactic":"defense-evasion","owasp":["A09"],"mitigations":["Centralized Logging"]},
    {"id":"T1562","name":"Impair Defenses","tactic":"defense-evasion","owasp":["A05","A09"],"mitigations":["Tamper Protection"]},
    {"id":"T1552","name":"Unsecured Credentials","tactic":"credential-access","owasp":["A02","A07"],"mitigations":["Secrets Mgmt"]},
    {"id":"T1556","name":"Modify Auth Process","tactic":"credential-access","owasp":["A07"],"mitigations":["Secure Cookies"]},
    {"id":"T1083","name":"File and Directory Discovery","tactic":"discovery","owasp":["A01","A05"],"mitigations":["Access Controls"]},
    {"id":"T1590","name":"Active Scanning","tactic":"reconnaissance","owasp":["A05","A10"],"mitigations":["Rate Limiting","WAF"]},
    {"id":"T1592","name":"Gather Victim Host Info","tactic":"reconnaissance","owasp":["A05","A10"],"mitigations":["Error Handling"]},
    {"id":"T1570","name":"Lateral Tool Transfer","tactic":"lateral-movement","owasp":["A03","A08"],"mitigations":["File Upload Validation"]},
    {"id":"T1005","name":"Data from Local System","tactic":"collection","owasp":["A01","A02"],"mitigations":["DLP"]},
    {"id":"T1071","name":"Application Layer Protocol","tactic":"command-and-control","owasp":["A03","A10"],"mitigations":["Network Monitoring"]},
    {"id":"T1485","name":"Data Destruction","tactic":"impact","owasp":["A03","A04"],"mitigations":["Backups"]},
    {"id":"T1491","name":"Defacement","tactic":"impact","owasp":["A03","A04"],"mitigations":["CSP"]},
    # Added for business logic / injection fidelity
    {"id":"T1599","name":"Network Denial of Service","tactic":"impact","owasp":["A04"],"mitigations":["Rate Limiting","Business Rule Enforcement"]},
    {"id":"T1585","name":"Establish Accounts","tactic":"persistence","owasp":["A04","A05"],"mitigations":["Account Validation"]},
    {"id":"T1110","name":"Brute Force","tactic":"credential-access","owasp":["A07"],"mitigations":["MFA","Lockout"]},
    {"id":"T1539","name":"Steal Web Session Cookie","tactic":"credential-access","owasp":["A07"],"mitigations":["Secure Cookie","HttpOnly"]},
    {"id":"T1590.005","name":"SSRF","tactic":"reconnaissance","owasp":["A10"],"mitigations":["Allowlist URLs","Block Private IPs"]},
]
SCENARIOS = [
    {"id":"idor","name":"IDOR / Auth Abuse","owasp":["A01","A07"],"mitre":["T1190","T1548","T1083"]},
    {"id":"injection","name":"Injection","owasp":["A03"],"mitre":["T1190","T1059","T1059.007"]},
    {"id":"business_logic","name":"Business Logic Abuse","owasp":["A04","A01"],"mitre":["T1199","T1548","T1485"]},
    {"id":"ssrf","name":"SSRF","owasp":["A10"],"mitre":["T1590","T1592","T1580"]},
    {"id":"broken_auth","name":"Broken Authentication","owasp":["A07"],"mitre":["T1110","T1556","T1539"]},
]

class KnowledgeGraph:
    def __init__(self):
        self.g = nx.DiGraph()
        self._build()

    def _build(self):
        for o in OWASP_TOP10:
            self.g.add_node(o["id"], type="owasp", **o)
        for t in MITRE_TECHNIQUES:
            self.g.add_node(t["id"], type="mitre", **t)
            for ow in t.get("owasp", []):
                if self.g.has_node(ow) and self.g.has_node(t["id"]):
                    self.g.add_edge(t["id"], ow, relation="MAPS_TO")
                    self.g.add_edge(ow, t["id"], relation="MITIGATED_BY")
        for s in SCENARIOS:
            self.g.add_node(s["id"], type="scenario", **s)
            for ow in s.get("owasp", []):
                if self.g.has_node(s["id"]) and self.g.has_node(ow):
                    self.g.add_edge(s["id"], ow, relation="COVERS")
            for m in s.get("mitre", []):
                if self.g.has_node(s["id"]) and self.g.has_node(m):
                    self.g.add_edge(s["id"], m, relation="USES_TECHNIQUE")
        logger.info("KnowledgeGraph built", nodes=self.g.number_of_nodes(), edges=self.g.number_of_edges())

    def get_techniques_for_owasp(self, owasp_id: str) -> List[Dict[str, Any]]:
        if not self.g.has_node(owasp_id):
            return []
        return [self.g.nodes[n] for n in self.g.predecessors(owasp_id) if self.g.nodes[n].get("type")=="mitre"]

    def get_owasp_for_technique(self, technique_id: str) -> List[Dict[str, Any]]:
        if not self.g.has_node(technique_id):
            return []
        return [self.g.nodes[n] for n in self.g.successors(technique_id) if self.g.nodes[n].get("type")=="owasp"]

    def get_scenario_coverage(self, scenario_id: str) -> Dict[str, Any]:
        if not self.g.has_node(scenario_id):
            return {}
        succ = list(self.g.successors(scenario_id))
        owasp = [n for n in succ if self.g.nodes[n].get("type")=="owasp"]
        mitre = [n for n in succ if self.g.nodes[n].get("type")=="mitre"]
        return {"owasp": owasp, "mitre": mitre, "node": self.g.nodes[scenario_id]}

    def recommend_hardening(self, technique_id: str) -> List[str]:
        if not self.g.has_node(technique_id):
            return []
        node = self.g.nodes[technique_id]
        return node.get("mitigations", [])

    def expand_query(self, scenario: str, technique_id: Optional[str]=None) -> str:
        parts=[]
        if scenario and self.g.has_node(scenario):
            cov=self.get_scenario_coverage(scenario)
            parts.append(f"Scenario {scenario} covers OWASP {','.join(cov.get('owasp',[]))} via {','.join(cov.get('mitre',[]))}")
        if technique_id:
            ow=self.get_owasp_for_technique(technique_id)
            parts.append(f"Technique {technique_id} maps to {','.join([o['id'] for o in ow])}")
            parts.append(" mitigations: "+", ".join(self.recommend_hardening(technique_id)))
        return " | ".join(parts)

    def to_networkx(self) -> nx.DiGraph:
        return self.g

# Singleton for reuse
_graph_instance: Optional[KnowledgeGraph] = None
def get_knowledge_graph() -> KnowledgeGraph:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = KnowledgeGraph()
    return _graph_instance
