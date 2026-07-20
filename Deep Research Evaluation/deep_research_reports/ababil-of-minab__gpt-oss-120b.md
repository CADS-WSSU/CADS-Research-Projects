# Produce a full hunt-ready dossier on actor "Ababil of Minab". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity. Add the groups beliefs and reason for existing/fighting/doing what they do

**Summary**  
Ababil of Minab is an emerging pro‑Iranian hacktivist collective that publicly surfaced in late March 2026.  The group claims destructive intrusions against U.S., Israeli, Saudi, and Turkish targets, most notably the Los Angeles County Metropolitan Transportation Authority (LACMTA) where it alleged administrative control of a VMware vCenter environment and the exfiltration of hundreds of gigabytes of data 【1†L1-L3】【5†L5-L7】.  While the persona is presented as an independent hacktivist crew, multiple sources tie it to Iran’s Ministry of Intelligence and Security (MOIS) and describe it as a front for state‑aligned operations 【11†L1-L3】【16†L1-L3】【18†L1-L3】.  The group disseminates claims via a Telegram channel and a public website, uses a Netherlands‑hosted staging server, and leverages a blend of data‑theft, data‑destruction, and credential‑theft techniques (38 distinct ATT&CK techniques reported) 【5†L5-L7】【2†L2-L4】【18†L2-L4】.  Because concrete technical indicators (hashes, additional domains, IPs) have not been publicly released, detection relies on the few known IOCs, observed tactics, and the group’s psychological‑operations (PSYOP) posture 【9†L1-L2】【13†L13-L15】.  

---

## 1. Identity, Aliases & Attribution

| Aspect | Details | Source |
|--------|---------|--------|
| **Primary name** | *Ababil of Minab* (also “Ababil of Minab”, “Ababil of Minab” – no other aliases reported) | 【18†L1-L3】 |
| **Ideological framing** | Pro‑Iranian messaging; named after the Iranian city where a 2022 school massacre killed >175 teachers and children 【11†L1-L2】 |
| **Claimed motivation** | Retaliation against U.S. critical infrastructure; amplify impact through overstated claims to erode public trust 【1†L3-L5】【13†L13-L15】 |
| **State linkage** | Believed to be a front for Iran’s Ministry of Intelligence and Security (MOIS); Gambit Security attributes the persona to Iranian government hackers 【11†L3-L4】【16†L1-L3】【18†L1-L3】 |
| **Public presence** | Telegram channel `t.me/ababilofminab/7` and website `ababilofminab.io` – both host claims, evidence, and propaganda 【5†L5-L7】 |
| **Attribution confidence** | Multiple independent analyses (e.g., researchers, Gambit Security) converge on MOIS affiliation, though the group self‑identifies as a “standalone hacktivist crew” 【11†L3-L4】【16†L1-L3】 |

---

## 2. Infrastructure & Observable Indicators

| Indicator Type | Observable | Classification | Notes |
|----------------|------------|----------------|-------|
| **Domain (C2 / propaganda)** | `ababilofminab.io` – hosts attack details and media | **Block / Hunt** – recommended to block outbound traffic and monitor DNS queries 【5†L9-L11】 | No additional domains disclosed. |
| **Telegram channel** | `t.me/ababilofminab/7` – public claim platform | **Hunt** – monitor for mention of new victims or data dumps | Not a direct C2 channel but useful for intel collection. |
| **Staging server IP** | `5.255.127.55` – Netherlands VPS (AS60404, range 5.255.96.0/19) | **Block / Hunt** – block inbound/outbound traffic; monitor connections to this netblock 【2†L3-L4】 | Server remained publicly accessible for ≥ 4 weeks, up to late May 2026 【2†L5-L6】 |
| **Other IOCs** | Ten observable indicators (domains, IPs, hashes) cited but not disclosed 【18†L2-L4】 | **Intelligence Gap** – cannot be directly used until released. |
| **Forensic artefacts** | Screenshots with “Activate Windows” watermark – indicate attacker‑controlled, un‑activated VM rather than victim endpoint 【5†L12-L13】 | **Forensics‑only** – useful for attribution, not for active blocking. |

*No file‑hashes, SSL certificates, or additional domains were published in the open‑source material* 【9†L1-L2】【11†L4-L5】.

---

## 3. Observed Tactics, Techniques & Procedures (TTPs)

| ATT&CK Tactic | Technique (ID) | Observed Activity | Source |
|---------------|----------------|-------------------|--------|
| **Collection** | T1005 – Data from Local System | Exfiltration of MSSQL backups, PST archives, config files 【2†L2-L3】 | |
| **Impact** | T1485 – Data Destruction | SQL Server database deletions and file‑system wiping 【2†L4-L5】 | |
| **Credential Access** | (unspecified) – Credential theft reported via “custom upload tooling” & “credential theft” 【18†L4-L5】 | |
| **Exfiltration** | Archive‑based exfiltration (e.g., ZIP/TAR) 【18†L4-L5】 | |
| **Command & Control** | Use of exposed staging servers for staging exfiltrated data 【18†L4-L5】 | |
| **Defense Evasion** | Psychological operations – overstating impact to cause reputational damage 【13†L13-L15】 | |
| **Discovery** | Targeting of VMware vCenter environment (1,421 VMs across 28 hosts) 【5†L5-L7】 | |
| **Lateral Movement** | Not explicitly disclosed, but presence in vCenter implies potential VM‑to‑VM movement. | |
| **Overall breadth** | 38 distinct ATT&CK techniques observed across reporting 【18†L2-L4】 | |

*Because the public reporting does not enumerate each technique, analysts should treat the above as a representative sample.*

---

## 4. Timeline & Campaign Narrative

| Date | Event | Source |
|------|-------|--------|
| **Late March 2026** | First public appearance of Ababil of Minab, claiming destructive intrusions against U.S., Israeli, Saudi, and Turkish entities 【2†L1-L2】 | |
| **13 April 2026** | Public claim of administrative access to LACMTA’s VMware vCenter (≈ 1,421 VMs) 【1†L2-L3】【5†L5-L7】 | |
| **9 April 2026** | Separate claim of LACMTA attack posted on the group’s website 【5†L9-L11】 | |
| **April 2026 – May 2026** | Staging server (`5.255.127.55`) remains accessible, providing continuous visibility 【2†L5-L6】 | |
| **May 2026** | Researchers note the staging server stays up through late May 2026 【2†L5-L6】 | |
| **June 2026 (reported)** | No further public claims; intelligence gaps grow due to lack of verifiable technical evidence (e.g., 4 TB exfiltration, 250 TB destruction remain unverified) 【13†L13-L15】 | |

---

## 5. Detection, Hunting & Mitigation Guidance

### 5.1 Blocking / Network Controls  

| Action | Rationale | Implementation |
|--------|-----------|----------------|
| **Block outbound DNS & HTTP(S) to `ababilofminab.io`** | Domain is used for propaganda and potentially for C2 or data drop 【5†L9-L11】 | Firewall or DNS sinkhole. |
| **Block all traffic to/from `5.255.127.55` and its /19 netblock (5.255.96.0/19)** | Known staging server; remained active for weeks 【2†L3-L6】 | Network ACLs, IDS/IPS signatures. |
| **Restrict internet egress from critical OT/IT segments (e.g., rail‑yard management systems)** | Guidance to segment OT from internet‑facing IT 【5†L13-L14】 | VLAN segmentation, proxy enforcement. |

### 5.2 Hunting Queries (Sigma / KQL / Splunk)  

*The following queries are derived from the known IOCs and tactics; they can be adapted to organizational log sources.*

#### Sigma (generic) – DNS query to malicious domain  

```yaml
title: DNS Query to ababilofminab.io
id: 9f8c9d2e-1d34-4d8a-9e87-3f5f8b5c9a1b
status: experimental
description: Detect DNS lookups for the known propaganda domain used by Ababil of Minab.
author: CTI Analyst
logsource:
    product: dns
    service: resolver
detection:
    selection:
        QueryName|contains: 'ababilofminab.io'
    condition: selection
level: medium
```

#### Kusto Query Language (Azure Sentinel) – Connections to staging IP  

```kql
// Detect outbound connections to the known staging server IP
Heartbeat
| where RemoteIP == "5.255.127.55"
| summarize Count = count() by Computer, RemoteIP, TimeGenerated
| where Count > 0
```

#### Splunk SPL – Web server access to the group’s site  

```spl
index=webproxy (dest="ababilofminab.io" OR cs-host="ababilofminab.io")
| stats count by src_ip, uri_path, http_status, _time
| where count > 5
```

#### Sigma – Potential credential‑theft activity (generic)  

```yaml
title: Suspicious Credential Dumping Tools
id: 4a2b3c7d-5e6f-8a9b-0c1d-2e3f4g5h6i7j
status: experimental
description: Detect execution of known credential‑dumping utilities (e.g., mimikatz, lsass.exe) indicative of the group’s credential‑theft behavior.
logsource:
    product: windows
    service: sysmon
detection:
    selection:
        Image|endswith: 
          - '\mimikatz.exe'
          - '\lsass.exe'
    condition: selection
level: high
```

> **Note:** No publicly released hashes or file names exist; analysts should tune generic credential‑theft detection suites to the environment and watch for the above patterns.

### 5.3 Mitigations  

| Control | Recommendation | Source |
|---------|----------------|--------|
| **Domain & IP blocking** | Block `ababilofminab.io` and `5.255.127.55` (and its /19 netblock) | 【5†L9-L11】【2†L3-L4】 |
| **DNS monitoring** | Alert on any DNS lookup for the group’s domain from internal hosts (especially LACMTA, OT assets) | 【5†L12-L13】 |
| **vCenter hardening** | Isolate & audit VMware vCenter; enforce least‑privilege for privileged accounts | 【5†L13-L14】 |
| **IIS server review** | Examine web server logs for unauthorized changes or web‑shell deployments | 【5†L13-L14】 |
| **Password hygiene** | Force password resets for all privileged accounts after suspected breach | 【5†L13-L14】 |
| **OT segmentation** | Ensure rail‑yard management & train‑control systems are fully isolated from internet‑facing networks | 【5†L13-L14】 |
| **Multi‑factor authentication** | Deploy phishing‑resistant MFA (e.g., FIDO2 hardware keys) to reduce credential‑based access | 【13†L13-L14】 |
| **Log retention & forensic readiness** | Preserve VM‑level logs, hypervisor audit trails, and network flow data to aid post‑incident analysis | Derived from forensic artefact note (watermarked screenshots) 【5†L12-L13】 |

### 5.4 Pivot Points for Investigation  

| Pivot | Why it matters |
|-------|----------------|
| **Telegram channel** | Provides real‑time claims, potential clues to upcoming targets, and can be used to correlate with internal alerts. |
| **Public website** | Hosts screenshots and evidence – can be used to verify claimed artifacts (e.g., IAM screenshots) and to extract hidden indicators (e.g., hidden URLs). |
| **Staging server (`5.255.127.55`)** | Likely used to receive exfiltrated data; traffic to/from this host is a strong indicator of compromise. |
| **VMware vCenter** | If compromised, provides a “golden goose” for lateral movement across dozens of VMs; investigation should start here. |

---

## Intelligence Gaps

1. **Concrete Technical Indicators** – No publicly disclosed file hashes, additional command‑and‑control domains, or malware samples. The “ten observable indicators” are referenced but not enumerated 【18†L2-L4】.  
2. **Verification of Claims** – Exfiltration volumes (4 TB) and data‑destruction amounts (250 TB) remain unverified by independent sources 【13†L13-L15】.  
3. **Tooling Details** – While “custom upload tooling” and “archive‑based exfiltration” are mentioned, the specific binaries, scripts, or protocols used are unknown 【18†L4-L5】.  
4. **Full ATT&CK Mapping** – Only two techniques (T1005, T1485) are explicitly cited; the remaining 36 observed techniques are not detailed, limiting precise detection rule creation 【18†L2-L4】.  
5. **C2 Infrastructure** – Beyond the staging server, no further C2 servers, domains, or IP ranges have been identified.  
6. **Operational Leadership & Funding** – The relationship between the front‑personas

## Gaps

- unverified claims removed

---

## Sources

[1] Ababil of Minab (Threat Actor) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/actor/ababil_of_minab  
[2] Ababil of Minab Exposed: LA Metro SCADA Backups and Israeli Victim Data Left Open on an Iranian Staging Server — https://hunt.io/blog/ababil-of-minab-iranian-hackers-exposed-la-metro-breach-open-directory  
[3] CISA Rereleases Strategy Outline for MITRE ATT&CK Mapping — https://executivegov.com/2023/01/cyber-agency-rereleases-strategy-outline-for-mitre-attandck-mapping/  
[4] MITRE ATT&CK mapping and visualization - IBM Documentation — https://www.ibm.com/docs/en/qradar-common?topic=app-mitre-attck-mapping-visualization  
[5] Cyber Intel Brief: Pro-Iran Actor Claims Cyberattack on LA Metro — https://www.dataminr.com/resources/intel-brief/pro-iran-actor-ababil-of-minab-claims-cyberattack-on-la-metro/  
[6] STRATEGIC CYBER THREAT INTELLIGENCE BRIEFING — https://cyberwarrior76.substack.com/p/strategic-cyber-threat-intelligence-765  
[7] Searchlight Cyber integrates MITRE ATT&CK Mapping into DarkIQ fo… — https://www.helpnetsecurity.com/2024/02/21/searchlight-cyber-mitre-attck-mapping-darkiq/  
[8] MITRE ATT&CK&reg; — https://attack.mitre.org/  
[9] Weekly Intelligence Report – 05 Jun 2026 - Cyfirma — https://www.cyfirma.com/news/weekly-intelligence-report-05-jun-2026/  
[10] Detecting malicious activities with Sigma rules - Splunk Lantern — https://lantern.splunk.com/Security_Use_Cases/Threat_Hunting/Detecting_malicious_activities_with_Sigma_rules  
[11] Iranian intelligence service behind hack of LA transit system ... — https://therecord.media/iranian-intelligence-behind-hack-of-la-transit-system  
[12] Whats The Hax? A Fraud, Infosec, and Security News Aggregator — https://whatsthehax.com/  
[13] Cyber Intel Brief: Ababil of Minab Breach of Vyncs GPS Platform — https://www.dataminr.com/resources/ababil-of-minab-breach-of-vyncs-gps-platform/  
[14] P4T12ICK/Sigma-Hunting-App - GitHub — https://github.com/P4T12ICK/Sigma-Hunting-App  
[15] Security Community - Whats The Hax? — https://whatsthehax.com/community.html  
[16] Iranian State Hackers Stole 700GB From Los Angeles Metro in ... — https://mlq.ai/news/iranian-state-hackers-stole-700gb-from-los-angeles-metro-in-weeks-long-breach-israeli-researchers-say/  
[17] (PDF) AI-Driven Threat Hunting: Sigma Rules, Elastic EQL, and ... — https://www.researchgate.net/publication/393794211_AI-Driven_Threat_Hunting_Sigma_Rules_Elastic_EQL_and_MITRE_CAR_Analytics_in_Splunk_UBA  
[18] Ababil of Minab - Mallory.ai — https://mallory.ai/actors/019d98e8-c6c1-7c68-8ab0-f4daf622dad7  
[19] Introduction to Sigma Rules and Detection of Credential Harvesti… — https://www.recordedfuture.com/sigma-rules-and-credential-harvesting/  
[20] Ababil of Minab claims cyberattack on LACMTA, exposing risks to ... — https://industrialcyber.co/industrial-cyber-attacks/ababil-of-minab-claims-cyberattack-on-lacmta-exposing-risks-to-rail-control-systems-and-critical-transit-infrastructure/  
[21] Threats to the 2026 FIFA World Cup - Recorded Future — https://www.recordedfuture.com/research/2026-fifa-world-cup-threats  
[22] a Python-to-X transpiler for scientific high-performance computing — https://joss.theoj.org/papers/10.21105/joss.04991  
[23] News | Cyber Florida at USF — https://cyberflorida.org/news/  
[24] Charter / ShinyHunters 13M Breach, Palo Alto GlobalProtect CVE ... — https://itbriefcase.net/top-10-cybersecurity-stories-this-week-june-5-2026/  
[25] Untitled — https://ui.adsabs.harvard.edu/abs/2022doe..soft..363L/abstract  

---

## Metadata

- **Model:** bedrock/openai.gpt-oss-120b-1:0 (openai-compat)
- **Stop reason:** budget
- **Duration:** 4m 25s
- **Depth reached:** 4
- **Sources read:** 25
- **Learnings:** 150
- **Verified learnings:** 43
- **Prompt tokens:** 197643
- **Completion tokens:** 50636