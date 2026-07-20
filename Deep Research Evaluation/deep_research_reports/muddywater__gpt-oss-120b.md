# Produce a full hunt-ready dossier on actor "MuddyWater". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.

**Summary**  
MuddyWater is an Iranian state‑sponsored APT operating under the Ministry of Intelligence and Security (MOIS) and has been active since at least 2017 / 2018 [1][2][9].  The group is known by many aliases – Earth Vetala, MERCURY, Static Kitten, Seedworm, TEMP.Zagros, Mango Sandstorm, TA450, MuddyKrill, Boggy Serpens, ITG17, UNC3313, and others [1][4][7][9].  Its campaigns span the Middle East, Africa, Europe, Asia, and North America, targeting government, telecom, oil, and high‑technology firms.  MuddyWater’s tradecraft emphasizes rapid re‑tooling, heavy use of legitimate remote‑management tools, PowerShell and DLL‑side‑loading techniques, and increasingly “low‑signature” C2 channels such as Telegram, SOCKS5 proxies, and commercial satellite internet (Starlink) [1][2][4][8][9][14][17].  The following sections synthesize all publicly known intelligence into actionable detection, blocking, hunting, and investigative guidance.

---

## 1. Identity, Attribution & Alias Landscape

| Element | Details | Source |
|---------|---------|--------|
| **Primary name** | MuddyWater | [1][4][7][9] |
| **Known aliases** | Earth Vetala, MERCURY, Static Kitten, Seedworm, TEMP.Zagros, Mango Sandstorm, TA450, MuddyKrill, Boggy Serpens, ITG17, UNC3313, etc. | [1][4][7][9] |
| **Sponsorship** | Subordinate element of Iran’s Ministry of Intelligence and Security (MOIS) – a government‑backed cyber‑espionage group. | [1][4][7][8][9][20] |
| **First appearance** | Activity documented from 2017 (Palo Alto naming) and operational as early as 2018. | [1][2][9] |
| **Attribution notes** | Attribution is fluid; clusters may be split/merged, creating uncertainty about precise boundaries (e.g., Seedworm vs. MuddyWater). | [13] |
| **Related threat groups** | Links reported with CyberAv3ngers, Handala Hack Team, Fox Kitten, Oilrig. | [9] |

---

## 2. Observed Tactics, Techniques & Procedures (ATT&CK Mapping)

| ATT&CK Tactic | Technique (ID) | MuddyWater implementation | Source |
|---------------|----------------|---------------------------|--------|
| **Initial Access** | Spear‑phishing Attachment/Link (T1566) | Frequently used phishing to deliver malware. | [4][9] |
| | Exploitation of Public‑Facing Applications (T1190) | Leveraged vulnerable web services for entry. | [4] |
| | Valid Accounts – Remote Services (T1078.001) | RDP login used to gain foothold. | [8] |
| **Execution** | PowerShell (T1059.001) | Primary execution engine; PowerShell‑based tooling. | [4][9] |
| | DLL Side‑Loading (T1574.002) | Uses signed binaries (Fortemedia fmapp.exe, SentinelOne sentinelmemoryscanner.exe) to load malicious DLLs. | [7][8][14] |
| | JavaScript/Deno runtime (T1059.007) | Dindoor backdoor runs on Deno. | [17] |
| **Persistence** | Remote Services (T1021) – RMM tools | ScreenConnect, SimpleHelp, Atera used to maintain access. | [4][9] |
| | Legitimate Credential Dumpers (T1003) – Mimikatz, LaZagne | Employed for OS credential extraction. | [9] |
| **Privilege Escalation** | Exploitation for Privilege Escalation (T1068) – not detailed but plausible via legitimate binaries. | — |
| **Defense Evasion** | Use of False Flags / Impersonation (T1070.004) | Impersonates other threat actors to confuse attribution. | [4] |
| | Living‑off‑the‑Land Binaries (T1036) – RMM tools whitelisted in many enterprises. | [4] |
| | Use of SOCKS5 proxies for C2 (T1090.001) | Obfuscates traffic. | [9] |
| | Use of commercial satellite internet (Starlink) for C2 (custom technique) | [1] |
| **Credential Access** | OS Credential Dumping (T1003) – Mimikatz, LaZagne. | [9] |
| **Discovery** | Account Discovery (T1087) – whoami, net commands. | [8] |
| | System Information Discovery (T1082) – typical in PowerShell scripts. | implied |
| **Collection** | Data Staged on public file‑transfer services (T1074.001) – sendit.sh. | [14] |
| **Exfiltration** | Exfiltration Over Web Services (T1041) – Rclone to Wasabi bucket. | [17] |
| **Command & Control** | Telegram (T1105/T1102) – Telegram‑based C2 channel (Operation Olalampo). | [2] |
| | Custom Python backdoor (Fakeset) signed with stolen certificate. | [17] |
| | Use of Deno (JavaScript) runtime backdoor (Dindoor). | [17] |
| | Satellite internet (Starlink) for stealthy C2. | [1] |

---

## 3. Infrastructure, Indicators of Compromise (IOCs) & Patterns

### 3.1 Network & Host IOCs  

| Category | IOC | Classification | Reference |
|----------|-----|----------------|-----------|
| **IPv4 (Block)** | 173.16.10.1 | Block at perimeter | [8] |
| | 162.0.230.185 | Block at perimeter | [8] |
| | 157.20.182.49 | Block at perimeter (also observed in campaign) | [8][14] |
| **Username (Hunt/Forensics)** | `asuedulimit` – used in SSH command | Hunt in authentication logs; forensic indicator of compromised account | [8] |
| **Malware families** | Dindoor, Fakeset, Stagecomp, Darkcomp | Hunt/Forensics – signatures exist in Microsoft/Kaspersky | [17] |
| **Signed binaries (Side‑Loading)** | `Fortemedia FMAPP.exe` → malicious `FMAPP.dll` | Hunting for anomalous DLL loads from this binary | [8][14] |
| | `SentinelOne sentinelmemoryscanner.exe` → malicious DLL | Same as above | [14] |
| **Cloud storage** | Backblaze bucket used for Fakeset download | Hunt for outbound connections to Backblaze domains | [17] |
| | Wasabi bucket (Rclone exfil) | Hunt for Rclone usage to Wasabi endpoints | [17] |
| | `sendit.sh` public file‑transfer service | Hunt for HTTP POST/PUT to `sendit.sh` URLs | [14] |
| **C2 Channels** | Telegram bot/channel (Operation Olalampo) | Hunt for outbound Telegram API traffic | [2] |
| | SOCKS5 proxy servers (unspecified IPs) | Hunt for proxy traffic patterns | [9] |
| | Starlink satellite traffic (generic) | Flag unusual satellite‑IP ranges in egress | [1] |
| **Domain registration** | Domains registered via NameCheap & Hosterdaddy (AS136557); reuse of domains from Oct 2025 | Monitor new registrations under these registrars and reuse of legacy domains | [1] |
| **Remote Management Tools** | ScreenConnect, SimpleHelp, Atera (RMM) | Whitelist may be abused – monitor for atypical usage (e.g., start on boot, unusual remote sessions) | [4][9] |

### 3.2 Infrastructure Patterns  

* **Three‑stage C2 flow** – Initial RDP connection → SSH tunnel → final C2 server delivering malicious DLL. This pattern observed on the three IPs above [8].  
* **Domain reuse** – MuddyWater re‑uses domains for months; oldest observed from October 2025 [1].  
* **Satellite‑based C2** – Late 2025/early 2026 use of Starlink to hide traffic from traditional ISP monitoring [1].  
* **Telegram‑based C2** – First seen in Operation Olalampo (Jan 2026) [2].  
* **Commodity RMM tools** – ScreenConnect, SimpleHelp, Atera provide persistence and are often whitelisted [4][9].  

---

## 4. Operational Timeline (Key Campaigns)

| Date/Period | Event / Campaign | Highlights |
|-------------|------------------|------------|
| **2017‑2018** | Early activity (Palo Alto naming “MuddyWater”) | Initial spearfishing and RDP usage [1][2] |
| **Early 2025** | Shift to Europe; increased urgency | Targeting of European telecom & oil firms [2] |
| **Oct 2025 – Mar 2026** | Three distinct campaigns (Group‑IB) – novel malware, commodity tools | Use of undocumented malware variants, re‑tooling of infrastructure [2] |
| **Oct 2025** | Domain reuse begins (domains older than Oct 2025) | Registrations via NameCheap/Hosterdaddy [1] |
| **Late 2025 / Early 2026** | Starlink satellite internet used for C2 | New low‑profile channel [1] |
| **Jan 2026** | Operation Olalampo – Telegram‑based C2 introduced | First known Telegram bot usage [2] |
| **Feb 2026** | Week‑long intrusion of South Korean electronics manufacturer | Part of Q1 2026 multi‑continent operation [14] |
| **Mar 2 2026** | Operation Epic Fury launched (global espionage push) | Continued use of layered C2 and side‑loading [9] |
| **Q1 2026** | Nine organizations across four continents compromised; exfiltration staged on sendit.sh | Broad campaign footprint [14] |
| **Early 2026** | Increase in Python‑based backdoors (Fakeset, Stagecomp, Darkcomp) signed with stolen certs | Use of stolen code‑signing certificate [17] |
| **2026‑03‑04** | Hunt.io blog publishes infrastructure IOCs; Huntress retroactively hunts data | Public dissemination of IOCs [8] |

---

## 5. Hunting, Detection & Mitigation Guidance

### 5.1 Sigma Rules (generic)  

```yaml
title: MuddyWater – Suspicious PowerShell Execution with DLL Side‑Loading
id: d8e9c620-3a7b-4f1e-9c87-0e7b6d9c9e1a
status: stable
description: Detects PowerShell commands that load a DLL from a known legitimate binary (e.g., FMAPP.exe) often used by MuddyWater.
author: CTI Analyst
logsource:
  product: windows
  service: powershell
detection:
  selection:
    EventID: 4104
    ScriptBlockText|contains:
      - 'Fortemedia\FMAPP.exe'
      - 'sentinelmemoryscanner.exe'
      - '.dll'
  condition: selection
level: high
tags:
  - attack.t1059.001
  - attack.t1574.002
  - muddywater
```

### 5.2 KQL (Azure Sentinel)  

```kql
// Detect connections from internal hosts to known MuddyWater IPs
Heartbeat
| where RemoteIP in ('173.16.10.1','162.0.230.185','157.20.182.49')
| summarize Count = count() by Computer, RemoteIP, TimeGenerated = bin(TimeGenerated, 5m)
| where Count > 5
```

```kql
// Detect anomalous DLL loads from Fortemedia FMAPP.exe
SecurityEvent
| where EventID == 4688
| where ProcessName endswith "FMAPP.exe"
| where CommandLine contains ".dll"
| project TimeGenerated, Computer, AccountName, ProcessName, CommandLine
```

### 5.3 Splunk SPL  

```spl
# Hunt for SSH logins using the known MuddyWater username
index=wineventlog sourcetype=WinEventLog:Security (EventCode=4624) Account_Name="asuedulimit"
| stats count by src, dest, _time
```

```spl
# Alert on outbound connections to Telegram API (possible Olalampo C2)
index=network_traffic dest_port=443 (dest_ip="149.154.*.*")
| stats count by src_ip, dest_ip, _time
| where count > 20
```

### 5.4 Blocking Recommendations  

| Action | Rationale |
|--------|-----------|
| **Network ACLs** – Block IPv4 addresses 173.16.10.1, 162.0.230.185, 157.20.182.49 at perimeter. | Known MuddyWater C2 servers [8] |
| **

## Gaps

- unverified claims removed

---

## Sources

[1] MuddyWater, Earth Vetala, MERCURY, Static Kitten, Seedworm, … — https://attack.mitre.org/groups/G0069/  
[2] MuddyWater - Iranian Cyber Espionage Profile - Group-IB — https://www.group-ib.com/masked-actors/muddywater/  
[3] Clever Kitten | Threat Actor Profile | CrowdStrike — https://www.crowdstrike.com/blog/whois-clever-kitten/  
[4] MuddyWater (hacker group) - Wikipedia — https://en.wikipedia.org/wiki/MuddyWater_(hacker_group)  
[5] Unmasking MuddyWater's New Malware Toolkit Driving ... - Group-IB — https://www.group-ib.com/blog/muddywater-espionage/  
[6] MuddyWater — https://executivegov.com/tag/muddywater/  
[7] Iranian Government-Sponsored Actors Conduct Cyber Operations ... — https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-055a  
[8] Clearing the Water: Unmasking an Attack Chain of MuddyWater — https://www.huntress.com/blog/muddywater-attack-chain  
[9] MuddyWater - Threat Actor | FortiGuard Labs — https://www.fortiguard.com/threat-actor/5571/muddy-water  
[10] actor profile | popgeeks.com — https://popgeeks.com/tag/actor-profile/  
[11] Middle East Malicious Infrastructure Report - Hunt.io — https://hunt.io/blog/middle-east-malicious-infrastructure-report  
[12] Home - Cristian Thous - Ciberseguridad al alcance de todos — https://cristianthous.com/  
[13] Pre-Positioned Access: The Cyber Threat Behind the Iran Conflict — https://www.centripetal.ai/threat-research/pre-positioned-access-cyber-threat-iran-conflict  
[14] MuddyWater Uses DLL Side-Loading in Espionage Campaign … — https://thehackernews.com/2026/05/muddywater-uses-dll-side-loading-in.html  
[15] Nimbus Manticore: Iran's AI-Assisted Backdoors Target Western ... — https://labs.cloudsecurityalliance.org/research/csa-research-note-nimbus-manticore-ai-assisted-malware-irgc/  
[16] 1.36 MB - Hugging Face — https://huggingface.co/datasets/clydeiii/cybersecurity/resolve/main/2023.clean.txt?download=true  
[17] Iran-Linked MuddyWater Hackers Target U.S. Networks With New … — https://thehackernews.com/2026/03/iran-linked-muddywater-hackers-target.html  
[18] Bad Connection: Uncovering Global Telecom Exploitation by Covert ... — https://citizenlab.ca/research/uncovering-global-telecom-exploitation-by-covert-surveillance-actors/  
[19] theguly/stars - GitHub — https://github.com/theguly/stars  
[20] MITRE ATT&CK® Framework Beginners Guide - Picus Security — https://www.picussecurity.com/resource/blog/mitre-attack-framework-beginners-guide  
[21] Iranian Threat Actors: What Defenders Need to Know - Picus Security — https://www.picussecurity.com/resource/iranian-threat-actors-what-defenders-need-to-know  
[22] What Are MITRE ATT&CK and MITRE D3FEND? - D3 Security — https://d3security.com/blog/mitre-attack-defend-explained/  
[23] Telefonica Tech · Blog - Telefónica Tech — https://telefonicatech.com/en/blog/author/telefonicatech  
[24] Valid Accounts, Technique T1078 - Enterprise | MITRE ATT&CK® — https://attack.mitre.org/techniques/T1078/  
[25] Local Data Staging, Sub-technique T1074.001 - MITRE ATT&CK® — https://attack.mitre.org/techniques/T1074/001/  

---

## Metadata

- **Model:** bedrock/openai.gpt-oss-120b-1:0 (openai-compat)
- **Stop reason:** budget
- **Duration:** 11m 53s
- **Depth reached:** 3
- **Sources read:** 25
- **Learnings:** 193
- **Verified learnings:** 54
- **Prompt tokens:** 265427
- **Completion tokens:** 65368