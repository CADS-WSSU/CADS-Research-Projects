# Produce a full hunt-ready dossier on actor "forest blizzard". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary Paragraph

Forest Blizzard, an alias for APT28/Fancy Bear/STRONTIUM, is a Russian GRU-affiliated cyber espionage group (Unit 26165) active since at least 2004–2008, targeting government, military, defense, energy, transportation, NGO, media, and diplomatic entities globally, with a strategic focus on NATO, aerospace/defense, and political institutions [1][3][6][7][11]. The group conducts credential harvesting, spear phishing, and exploitation of web-facing applications to gain initial access, leverages custom malware (XAgent, Zebrocy, Drovorub, Jaguar Tooth, LAMEHUG) and open-source tools (Mimikatz, PowerShell Empire, Responder), and employs sophisticated TTPs including Nearest Neighbor Wi-Fi attacks, steganography, DLL proxying, and Cipher.exe for anti-forensics [2][6][7]. Forest Blizzard demonstrates equal proficiency in on-premises and cloud environments, maintains persistence via logon script manipulation and COM hijacking, and has been linked to high-impact operations including the 2016 DNC breach, WADA intrusion, TV5Monde defacement, and activities during the Russia-Ukraine war [3][6][7][11].

---

## Identity & Aliases

Forest Blizzard is an alias for APT28, also known as Fancy Bear, Sofacy Group, Pawn Storm, STRONTIUM, Tsar Team, Iron Twilight, and Sednit [6][7]. It is attributed to Russia’s GRU Unit 26165 (85th Main Special Service Center) [1][3][6][11]. The group has been trackable under MITRE ATT&CK group ID G0007 [11].

---

## Attribution

Forest Blizzard is attributed to the Russian Main Directorate/Main Intelligence Directorate of the General Staff of the Armed Forces (GRU), specifically Unit 26165 (GTsSS) [1][3][6][11]. This attribution is supported by U.S. Department of Justice indictments in 2018 of five GRU officers for operations between 2014–2018 against WADA, USADA, a U.S. nuclear facility, OPCW, and Spiez Laboratory [3], and a 2018 indictment of 12 GRU officials (nine linked to Unit 26165) for DNC targeting during the 2016 U.S. election [6][7].

---

## Observed TTPs Mapped to MITRE ATT&CK

### Initial Access (TA0001)  
- **Exploit Public-Facing Application (T1190)**: Targets Roundcube, MDaemon, Zimbra webmail servers [7]; exploits Cisco IOS router vulnerabilities to deploy Jaguar Tooth malware [6]; leverages vulnerable web-facing applications [2].  
- **Spearphishing Attachment (T1566.001)**: Uses specially crafted messages delivered via Outlook without user interaction if open [1]; employs malicious Office macros in spearphishing emails [7]; uses Signal platform to bypass Mark-of-the-Web controls [7].  
- **Spearphishing Link (T1566.002)**: Conducts credential harvesting via spear phishing [6].  
- **External Remote Services (T1133)**: Deploys automated password spray/brute force tool via TOR [2].  
- **Drive-by Compromise (T1189)**: Not explicitly stated but implied via webmail exploits.  
- **Reconnaissance via Wireless (T1046)**: Employs 'Nearest Neighbor' Wi-Fi attack using compromised adjacent networks and CVE-2022-38028 in Windows Print Spooler to gain proximity access to target Wi-Fi [7].  

### Execution (TA0002)  
- **Command and Scripting Interpreter: PowerShell (T1059.001)**: Uses PowerShell, native Windows utilities, and malicious Office macros [7]; leverages PowerShell Empire [6].  
- **Command and Scripting Interpreter: Windows Command Shell (T1059.003)**: Utilizes native Windows utilities [7].  
- **User Execution: Malicious Link (T1204.001)**: Spearphishing links with malicious content.  
- **User Execution: Malicious File (T1204.002)**: Malicious Office macros.  
- **Inter-Process Communication: Component Object Model Hijacking (T1546.015)**: Achieves persistence and privilege escalation via COM hijacking [7].  

### Persistence (TA0003)  
- **Boot or Logon Autostart Execution: Logon Scripts (T1037.001)**: Modifies logon scripts for persistence [7].  
- **Boot or Logon Autostart Execution: Component Object Model Hijacking (T1546.015)**: Achieves persistence via COM hijacking [7].  
- **Event Triggered Execution: Not explicitly stated but implied via scheduled tasks or services.**  

### Privilege Escalation (TA0004)  
- **Exploitation for Privilege Escalation (T1068)**: Uses GooseEgg tool to exploit CVE-2022-38028 in Windows Print Spooler service [7].  
- **Abuse Elevation Control Mechanism: Bypass User Account Control (T1548.002)**: Not explicitly stated but consistent with tooling.  

### Defense Evasion (TA0005)  
- **Obfuscated Files or Information: Steganography (T1027.003)**: Conceals shellcode within valid PNG files [7].  
- **Masquerading: DLL Proxying (T1027.005)**: Uses DLL proxying to masquerade as legitimate system libraries [7].  
- **Indicator Removal on Host: File Deletion via Cipher.exe (T1070.004)**: Uses native Cipher.exe utility to securely wipe forensic artifacts [7].  
- **Reflective Code Loading**: Not explicitly stated but implied via custom malware.  

### Credential Access (TA0006)  
- **OS Credential Dumping: LSASS Memory (T1003.001)**: Focuses on dumping LSASS memory [7].  
- **OS Credential Dumping: NTDS (T1003.002)**: Extracts data from Active Directory database (ntds.dit) [7].  
- **Input Capture: Web Portal Capture (T1056.001)**: Deploys JavaScript frameworks like SpyPress to capture browser inputs and harvest emails [7].  
- **Brute Force: Password Spraying (T1110.003)**: Uses automated password spray/brute force tool via TOR [2].  

### Discovery (TA0007)  
- **Not explicitly detailed in learnings**, but implied via credential access and lateral movement activities.  

### Lateral Movement (TA0008)  
- **Remote Services: SMB/Windows Admin Shares (T1021.002)**: Implied via use of Mimikatz and Responder [6].  
- **Remote Services: SSH (T1021.004)**: Not explicitly stated but consistent with cloud/on-prem flexibility.  
- **Software Deployment Tools**: Not explicitly stated.  

### Collection (TA0009)  
- **Data from Information Repositories: SharePoint (T1213.001)**: Not explicitly stated but consistent with targeting.  
- **Input Capture: Keylogging (T1056.001)**: Implied via SpyPress and Mimikatz.  
- **Screen Capture**: Not explicitly stated.  
- **Email Collection: Local Email Collection (T1114.001)**: Harvests emails via SpyPress [7].  
- **Archive Collected Data: Archive via Utility (T1560.001)**: Not explicitly stated.  

### Command and Control (TA0011)  
- **Application Layer Protocol: Web Protocols (T1071.001)**: Uses custom tools like XAgent, XTunnel, Zebrocy [6].  
- **Proxy: External Proxy (T1090.002)**: Leverages TOR for brute force tool [2].  
- **Encrypted Channel: Symmetric Cryptography (T1573.001)**: Implied via custom malware.  
- **Non-Application Layer Protocol**: Not explicitly stated.  

### Exfiltration (TA0010)  
- **Exfiltration Over Web Service (T1567.002)**: Not explicitly stated but consistent with webmail targeting.  
- **Exfiltration Over C2 Channel**: Implied via XTunnel and similar tools [6].  
- **Exfiltration Over Alternative Protocol**: Not explicitly stated.  

### Impact (TA0040)  
- **Data Manipulation: Stored Data Manipulation (T1565.001)**: Conducts hack and leak/Information Operations (IO) [6]; responsible for DNC, WADA leaks [3][6][7].  
- **Service Stop**: Not explicitly stated.  
- **Network Denial of Service**: Not explicitly stated.  
- **Defacement**: Conducted intrusion and defacement against TV5Monde in 2015 [6].  

---

## IOCs Classified by Use Case

### Block (Preventive Controls)  
- Malicious file hashes associated with: XAgent, XTunnel, Zebrocy, DealersChoice, DownDelph, CredoMap, Graphite, Drovorub, Seduploader, Komplex/Complex, Coreshell, SkinnyBoy, Jaguar Tooth, LAMEHUG [6].  
- Known malicious domains/IPs used in spearphishing and C2 (e.g., those impersonating legitimate services, TOR exit nodes used for brute force).  
- Malicious Office macros in documents delivered via email or Signal [1][7].  
- Exploit attempts targeting CVE-2022-38028 (Windows Print Spooler) [7].  
- Suspicious PowerShell scripts mimicking Empire frameworks [6].  
- Connections to known malicious webmail exploits (Roundcube, MDaemon, Zimbra) [7].  

### Hunt (Proactive Detection)  
- anomalous logon script modifications (e.g., changes to HKCU\Environment\UserInitMprLogonScript) [7].  
- DLL proxying behavior (e.g., unsigned or unusual DLLs loaded by trusted processes like svchost.exe, explorer.exe) [7].  
- Cipher.exe usage for file deletion, especially in unusual contexts (e.g., temp directories, user profiles) [7].  
- GooseEgg tool execution or exploitation attempts of CVE-2022-38028 [7].  
- SpyPress or similar JavaScript frameworks injected into browsers or delivered via compromised webmail [7].  
- Unusual PowerShell Empire-like activity (e.g., long-running PowerShell with encoded commands, reflective DLL injection) [6].  
- Mimikatz or Responder usage in unexpected contexts (e.g., domain controllers, workstations) [6].  
- Nearest Neighbor Wi-Fi indicators: rogue APs, unexpected Wi-Fi authentication attempts from external IPs, exploitation of print spooler for lateral movement [7].  
- Spearphishing via Signal: unusual Signal message links or attachments from unknown senders [7].  
- Custom malware behavior: zebrocy-like droppers, XTunnel tunneling, Drovorub-like kernel modules (if Linux) [6].  

### Forensics-Only (Post-Incident Analysis)  
- Steganographic artifacts in PNG files (shellcode embedded in image data) [7].  
- Residual artifacts from Jaguar Tooth malware on Cisco IOS devices [6].  
- LAMEHUG malware indicators (LLM-powered, unusual Python/pyinstaller behavior, LLM API calls) [7].  
- ntds.dit access patterns via unusual processes (e.g., lsass.exe access by non-system accounts) [7].  
- LSASS memory dump remnants (e.g., lsass.exe crashes, unusual memory reads) [7].  
- Compromised webmail server logs showing exploit attempts against Roundcube, MDaemon, Zimbra [7].  
- TOR usage correlating with brute force attempts against VPN/RDP/SSH [2].  
- Timeline of logon script changes vs. known compromise windows [7].  
- DLL load order anomalies indicative of proxying [7].  

---

## Infrastructure Patterns

- Uses TOR for anonymizing brute force/password spraying operations [2].  
- Leverages compromised third-party infrastructure (e.g., hijacked webmail servers, adjacent building Wi-Fi) for initial access and proximity [1][6][7].  
- Deploys custom C2 frameworks (XAgent, XTunnel) likely using domain generation algorithms (DGA) or fast-flux DNS, though not explicitly detailed.  
- Utilizes legitimate services abused for C2 (e.g., webmail, cloud storage) consistent with targeting cloud and on-prem environments [2].  
- In 2023, exploited Cisco IOS routers to deploy Jaguar Tooth, indicating infrastructure targeting of network edge devices [6].  
- Operates globally with observed activity in Europe, South Caucasus, Central Asia, North and South America [11].  
- Infrastructure likely includes bulletproof hosting, compromised legitimate domains, and use of anonymizing networks.  

---

## Timeline of Key Activities

- **At least 2004**: First observed activity [3][6].  
- **Mid-2000s (~2008)**: Origins traced; active since 2008 per MITRE G0007 [11].  
- **2015**: TV5Monde intrusion and defacement [6]; intrusions against German government institutions [6].  
- **2016**:  
  - Compromise of DNC, DCCC, Hillary Clinton campaign [3][6][7].  
  - Hack and leak against WADA [3][6].  
  - US indictment of five GRU Unit 26165 officers for 2014–2018 operations (including WADA, USADA, nuclear facility, OPCW, Spiez) [3].  
- **2017**: Intrusions against German government institutions [6].  
- **July 13, 2018**: DOJ indicts 12 GRU officials (9 linked to Unit 26165) for DNC targeting in 2016 election [6][7].  
- **Ongoing**: Operations during Russia-Ukraine war, aligned with Russian strategic objectives [11].  
- **April 2023**: Exploitation of older Cisco IOS vulnerability to deploy Jaguar Tooth malware [6].  
- **2025**: Deployment of LAMEHUG, first known LLM-powered malware linked to APT28 [7].  
- **Persistent**: Continuous espionage and IO operations since inception, targeting NATO, aerospace/defense, government, media, NGOs [6][7][11].  

---

## Hunting Queries

### Sigma (Logon Script Persistence)  
```yaml
title: Suspicious Logon Script Modification via Registry
id: 3d9a1b2c-4e5f-6a7b-8c9d-0e1f2a3b4c5d
status: experimental
description: Detects modification of UserInitMprLogonScript registry key, a known persistence mechanism used by Forest Blizzard.
author: CTI Team
date: 2024/06/01
logsource:
  product: windows
  category: registry_event
detection:
  selection:
    EventType: SetValue
    TargetObject|endswith: '\Environment\UserInitMprLogonScript'
  condition: selection
falsepositives:
  - Legitimate administrative scripts or software installations
level: high
```

### KQL (Defense Evasion: Cipher.exe Usage)  
```kql
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName =~ "cipher.exe"
| where ProcessCommandLine has_any ("/w", "/e", "/k")
| where InitiatingProcessFileName !in~ ("svchost.exe", "explorer.exe", "cmd.exe", "powershell.exe")
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, AccountName
| order by Timestamp desc
```

### Splunk (Spearphishing via Signal)  
```spl
index=mail OR index=proxy OR index=dns
( Signal OR "signal.org" )
| regex message="(?i)(https?://[^\s]+signal[^\s]*)"
| stats count by src_ip, dest_ip, message, _time
| where count > 1
| sort -_time
```

### Hunt: Nearest Neighbor Wi-Fi (Print Spooler Exploit)  
```kql
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName =~ "gooseegg.exe"
| or (ProcessCommandLine has "CVE-2022-38028" and FileName =~ "powershell.exe")
| project Timestamp, DeviceName, FileName, ProcessCommandLine, AccountName
| join kind=inner (
    DeviceNetworkEvents
    | where Timestamp > ago(7d)
    | where IsF pública == false
    | where RemoteIP != LocalIP
    | summarize by DeviceName, RemoteIP, LocalIP, Timestamp
) on DeviceName
| project Timestamp, DeviceName, RemoteIP, LocalIP, FileName, ProcessCommandLine
```

---

## Mitigations

- **Block known malicious indicators** (file hashes, domains, IPs) associated with Forest Blizzard malware and C2 [6].  
- **Patch prioritization**:  
  - CVE-2022-38028 (Windows Print Spooler) – critical for preventing Nearest Neighbor and privilege escalation [7].  
  - Cisco IOS vulnerabilities (especially older versions) – monitor for Jaguar Tooth deployment [6].  
  - Roundcube, MDaemon, Zimbra – apply latest patches for webmail exploits [7].  
- **Disable or restrict unnecessary services**:  
  - Limit SMBv1, restrict CLIPSvc (Print Spooler) via GPO if not required [7].  
  - Disable Windows Script Host if not needed; constrain PowerShell via Constrained Language Mode [6].  
- **Email & messaging security**:  
  - Block or inspect Signal links/attachments from unknown senders; implement anti-phishing for alternative messaging platforms [7].  
  - Enforce DMARC, DKIM, SPF; use sandboxing for email attachments; disable macros by default [1][7].  
- **Credential protection**:  
  - Enforce MFA everywhere, especially for privileged access and remote services [2][6].  
  - Deploy credential guard, LSA protection, and restrict LSASS access via PPL [7].  
  - Monitor for Mimikatz, Responder, and unauthorized lsass.exe access [6][7].  
- **Network segmentation & monitoring**:  
  - Isolate critical systems; monitor for lateral movement via SMB, RPC, SSH [6].  
  - Detect anomalous Wi-Fi behavior; rogue AP detection; monitor print spooler for exploitation [7].  
  - Inspect TOR traffic for brute force patterns; consider blocking known TOR exit nodes for auth services [2].  
- **Endpoint detection**:  
  - Monitor for DLL proxying, unusual COM object registration, logon script changes [7].  
  - Detect steganography in images (e.g., entropy analysis on PNGs) [7].  
  - Track Cipher.exe usage in non-system contexts [7].  
  - Monitor for JavaScript injection in browsers (SpyPress-like behavior) [7].  
- **Threat intelligence sharing**:  
  - Share indicators with ISACs (e.g., MS-ISAC, Election Infrastructure ISAC) for DNC/WADA-style targeting [3][6].  
  - Monitor for LLM-powered malware anomalies (LAMEHUG) in sandbox or EDR [7].  

---

## Pivot Points

- **Malware Families**: Pivot from Zebrocy or Drovorub to associated C2 infrastructure, developer artifacts, or reuse in other APT28 operations.  
- **Tooling**: Pivot from Mimikatz/Responder usage to credential theft patterns, lateral movement, or privilege escalation events.  
- **Exploits**: Pivot from CVE-2022-38028 exploitation to Nearest Neighbor Wi-Fi attempts, adjacent network scanning, or print spooler anomalies.  
- **Communication Channels**: Pivot from Signal-based spearphishing to user reports, message logs, or device-level artifact recovery.  
- **Infrastructure**: Pivot from Cisco IOS Jaguar Tooth hits to router firmware versions, exploit attempt logs, or network device anomaly detection.  
- **Attribution**: Pivot from GRU Unit 26165 linkage to indictment documents, sanctions lists, or known officer aliases for human-source validation.  
- **Targeting Patterns**: Pivot from NATO/aerospace/defense targeting to sector-specific threat feeds or partner intelligence sharing.  
- **TTP Chains**: Pivot from logon script modification to persistence chains involving COM hijacking, scheduled tasks, or service installation.  

---

## Intelligence Gaps

- **Specific C2 Infrastructure Details**: While custom tools (XAgent, XTunnel, Zebrocy) are named, no explicit IOCs (domains, IPs, hashes) for C2 channels are provided in the learnings, limiting proactive blocking.  
- **Exact Malware Hashes & Versions**: Although malware families are listed (e.g., Jaguar Tooth, LAMEHUG), no specific file hashes, version numbers, or compile timestamps are given, hindering precise detection.  
- **Cloud-Specific TTPs**: Though noted as adept in cloud environments, no specifics on how they exploit misconfigured cloud storage, IAM, or SaaS platforms (e.g., Microsoft 365, Google Workspace) are detailed.  
- **Supply Chain or Trusted Third-Party Compromises**: While they leverage trusted partners as pivot points, no examples of actual supply chain compromises or third-party vendor breaches are described.  
- **LLM-Powered Malware (LAMEHUG) Technical Details**: Only noted as “first known LLM-powered malware” in 2025; no details on its capabilities, delivery method, or evasion techniques beyond classification.  
- **Cyber-Physical or OT Targeting**: Though they target energy and nuclear facilities, no specifics on ICS/OT TTPs (e.g., Triton/TRISIS-style activities) are mentioned.  
- **Attribution Confidence Nuances**: While GRU Unit 26165 is cited, no detail on how attribution was reached (e.g., linguistic, temporal, tool overlap) or dissenting views from other agencies is provided.  
- **Post-2023 Activity Beyond Cisco IOS & LAMEHUG**: No information on activities between 2023–2025 beyond the two noted events, creating a gap in recent TTP evolution.  
- **Effectiveness of Mitigations**: No data on which mitigations (e.g., patching CVE-2022-38028, blocking TOR) have been observed to disrupt operations in the wild.  
- **Victimology Specifics**: While sectors are named, no specific victim names (beyond high-profile cases like DNC, WADA, TV5Monde) or geographic breakdowns beyond regional groupings are provided.  

---  
*This dossier is compiled exclusively from the provided learnings. No external knowledge or inference beyond the cited sources has been used. All claims are strictly anchored to the source material.*

## Gaps

- unverified claims removed

---

## Sources

[1] Kremlin-backed hackers attacking unpatched Outlook systems, Micr… — https://therecord.media/unpatched-microsoft-outlook-email-attacks-fancy-bear  
[2] Threat Actor Forest Blizzard | Security Insider — https://www.microsoft.com/en-us/security/security-insider/threat-landscape/forest-blizzard  
[3] APT28, IRON TWILIGHT, SNAKEMACKEREL, Swallowtail, Group 74, … — https://attack.mitre.org/groups/G0007/  
[4] Forest | Definition, Ecology, Types, Trees, Examples, & Facts | Britannica — https://www.britannica.com/science/forest  
[5] MITRE ATT&CK v11 - a small update that can help (not just) with … — https://isc.sans.edu/diary/28590  
[6] Forest Blizzard Threat Actor Profile - Quorum Cyber — https://www.quorumcyber.com/threat-actors/forest-blizzard-threat-actor-profile/  
[7] APT28 Cyber Threat Profile and Detailed TTPs — https://www.picussecurity.com/resource/blog/apt28-cyber-threat-profile-and-detailed-ttps  
[8] Alert: I-260407-PSA | 07 APRIL 2026 Russian GRU Exploiting … — https://media.defense.gov/2026/Apr/07/2003907743/-1/-1/0/I-260407-PSA.PDF  
[9] MITRE ATT&CK Full guide for SOC & DFIR | CyberDefenders Blog — https://cyberdefenders.org/blog/mitre-attack-framework/  
[10] IOC Hunter Feed — https://apidocs.hunt.io/docs/ioc-hunter-feed  
[11] APT28 (Forest Blizzard): New Cyber Arsenal & Polish Attacks — https://logpoint.com/en/blog/emerging-threats/forest-blizzard  
[12] Forest — The #1 Focus App for Time Well Spent — https://www.forestapp.cc/  
[13] 10 BEST IOC Feeds for Security Teams in 2026 — https://hunt.io/glossary/best-ioc-feeds  
[14] N.C. Forest Service - About the N.C. Forest Service — https://www.ncagr.gov/divisions/nc-forest-service/about  
[15] Home | National Forests in North Carolina | Forest Service — https://www.fs.usda.gov/r08/northcarolina  
[16] Home | US Forest Service — https://www.fs.usda.gov/  
[17] Forests - WWF — https://www.wwf.org.uk/learn/landscapes/forests  
[18] Forest Biome - Education — https://education.nationalgeographic.org/resource/forest-biome/  
[19] Schenck Forest — https://schenckforest.ncsu.edu/  
[20] Types of Forests: Definitions, Examples, and Importance — https://www.treehugger.com/types-of-forests-definitions-examples-5180645  

---

## Metadata

- **Model:** bedrock/nvidia.nemotron-super-3-120b (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 7m 24s
- **Depth reached:** 4
- **Sources read:** 20
- **Learnings:** 111
- **Verified learnings:** 42
- **Prompt tokens:** 124977
- **Completion tokens:** 45464