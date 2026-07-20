# Produce a full hunt-ready dossier on actor "Storm-1849". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

Storm-1849 is the Microsoft-tracked name for the same actor Cisco Talos identifies as UAT4356, associated with the ArcaneDoor campaign. [1][24][34] Open-source reporting characterizes the actor as a state-sponsored, espionage-focused threat group that targeted government and critical infrastructure networks globally, with additional reporting tying activity to U.S. financial institutions, defense contractors, and military organizations. [1][4][6][24][34] The actor exploited zero-day vulnerabilities in Cisco ASA appliances, deployed custom backdoors named Line Runner and Line Dancer, used anti-forensic tradecraft such as log tampering and file deletion, and relied on adversary-controlled infrastructure for HTTP-based command and control and exfiltration. [1][4][9][17][34] The initial access vector remains unknown across the available reporting, which is the most important intelligence gap for prevention and upstream detection. [9][14][34]

## 1) Identity, aliases, and attribution

Storm-1849 is the Microsoft naming for the actor Cisco Talos tracks as UAT4356. [1][24][34] The associated campaign name is ArcaneDoor. [1][4][9][24] Public reporting describes the actor as state-sponsored, and Talos assessed with high confidence that the campaign was carried out by a state-sponsored actor. [1][34] The activity is also described as China-linked in one source, though another source notes the actor’s identity remains uncertain, so attribution confidence is not absolute in the open reporting. [6][14] The actor targeted government networks globally, with related reporting also citing government and critical infrastructure environments, and other public reporting adding financial institutions, defense contractors, and military organizations. [1][4][6][24][34]

Microsoft’s naming taxonomy note is relevant context: Microsoft uses weather-family naming conventions and can revise mappings as more information becomes available, so naming and attribution may change over time. [3] That same taxonomy note also explains that “groups in development” are used for unknown or emerging activity until high-confidence attribution is possible. [3]

## 2) Observed TTPs and MITRE ATT&CK mapping

The actor used two custom implants/backdoors: Line Runner and Line Dancer. [1][4][13][17][24] Line Runner is described as a persistent Lua-based webshell and data exfiltrator that uploads and executes arbitrary Lua scripts, while Line Dancer is an in-memory loader and data stager using Lua scripting and a persistent Lua-based shellcode loader. [13][17] The malware was deployed through malicious boot scripts and persistence mechanisms tied to Cisco ASA startup behavior. [4][9] Cisco also mapped the Line Runner persistence mechanism to T1037, and the malware was delivered through boot or logon initialization scripts. [4][9]

The actor exploited Cisco ASA vulnerabilities to gain and maintain access, but the exact initial access vector remains unknown in the available reporting. [9][14][34] Post-compromise activity included configuration modification, reconnaissance, network traffic capture, exfiltration, and potentially lateral movement on compromised devices. [1] The actor captured packet data and system configuration information, exfiltrated device configurations as text versions of config files, and used scripted exfiltration over existing command-and-control channels. [4][17] The actor also demonstrated defense evasion by disabling logging, tampering with AAA, deleting files, and removing artifacts. [4][9][17]

### ATT&CK mapping from the reporting

- **Acquire Infrastructure: Virtual Private Server (T1583.003)** — adversary-controlled VPS for C2. [4]
- **Acquire Infrastructure: Web Services (T1583.006)** — OpenConnect VPN Server instances used on victim devices. [4]
- **Adversary-in-the-Middle (T1557)** — HTTP traffic interception to identify and parse C2 information. [4]
- **Application Layer Protocol: Web Protocols (T1071.001)** — HTTP-based C2. [4]
- **Automated Collection (T1119)** — packet capture and collection of configuration/system data. [4]
- **System Information Discovery (T1082)** — collection of system configuration information. [4]
- **Automated Exfiltration (T1020)** — scripted exfiltration of collected data. [4]
- **Exfiltration Over C2 Channel (T1041)** — exfiltration via existing C2 channels. [4]
- **Boot or Logon Initialization Scripts (T1037)** — malicious boot scripts installing Line Runner. [4][9]
- **Develop Capabilities: Malware (T1587.001)** — creation of Line Runner and Line Dancer. [4]
- **Indicator Removal: File Deletion (T1070.004)** — file/artifact deletion. [4][9]
- **Prevent Command History Logging (T1690)** — disabled logging on Cisco ASA appliances. [4]
- **Process Injection (T1055)** — code injected into AAA and Crash Dump processes. [4]
- **Rootkit (T1014)** — hook on `processHostScanReply()`. [4]
- **Hardware/OS-specific ATT&CK mapping from Cisco**:
  - **T0874** — Line Dancer host-scan-reply hook. [9]
  - **T1562-001** — disabling syslog and tampering with AAA. [9]
  - **T1556** — AAA bypass. [9]
  - **T1653** — reboot action via CVE-2024-20353 triggering installation of the second malware component. [9]
  - **T1140** — base64 decoding behavior. [9]
  - **T1059** — CLI command execution. [9]
  - **T1040** — network sniffing. [9]

Cisco Talos also described the actor as demonstrating a deep understanding of Cisco systems and using anti-forensic measures to evade detection. [1] The source material notes that the available ATT&CK coverage reflects only the subset of techniques visible in open reporting, not the full campaign behavior. [7]

## 3) Infrastructure patterns, timeline, and operational tradecraft

The campaign used dedicated adversary-controlled virtual private servers for command and control and OpenConnect VPN Server instances for actions on victim devices. [4] Reporting also notes some actor IPs may be anonymization infrastructure rather than direct attacker infrastructure, which makes attribution and blocking decisions partly uncertain. [9] Cisco recommended monitoring flows to and from ASA devices involving the listed IOC IPs, which suggests network-side visibility is important for detection and triage. [9][34]

The campaign targeted government and critical infrastructure networks globally, indicating broad operational reach rather than a single localized infrastructure pattern. [1][4][8] Another report describes the actor as targeting Cisco and other vendors’ networking devices, especially Cisco ASA devices, in government and critical infrastructure networks. [4] Public reporting also ties the activity to U.S. financial institutions, defense contractors, and military organizations. [6]

The timeline in the reporting spans several phases:
- Capability development as early as **July 2023**. [34]
- Actor-controlled infrastructure established between **November and December 2023**. [14]
- Initial detection in **early January 2024**. [14]
- First seen in **July 2023** and last seen in **April 2024** in one summary of the campaign. [4]
- A Cisco Talos reference date of **2024-04-24** is tied to ArcaneDoor reporting. [1]
- Another source notes October activity against Cisco ASA devices, a pause during China’s Golden Week holiday in the first week of October, and continuation after a Sept. 25 patch order for federal agencies. [6]

Operationally, the actor used malicious boot scripts, packet capture, syslog disabling, AAA tampering, reboot-triggered installation of a second component, and code hooking to maintain access and reduce visibility. [4][9][17] The actor’s technique profile is consistent with long-term espionage on perimeter devices rather than noisy, one-shot exploitation. [4][24][34]

## 4) IOCs, classification, and hunt/investigation value

The source material does not provide a complete hash/domain/IP list, but it does provide several IOC classes and investigation cues. [4][9][34] Cisco recommended looking for flows to or from ASA devices involving the listed IOC IP addresses and specifically noted that more than one executable memory region in `show memory region | include lina` can indicate tampering. [34] Cisco also advised checking for unexpected reboots and gaps in logging as suspicious activity. [9][17]

### Block
- **Known malicious IP addresses from the Talos/authorized IOC lists** should be blocked or denied at the perimeter where feasible. Cisco specifically recommends ACLs to block external access to VPN devices from known malicious IPs. [17][34]
- **Geofencing** VPN access to expected countries can be used as a preventive block control. [17]

### Hunt
- **Flows to/from ASA devices involving IOC IPs**. [9][34]
- **Unexpected reboots** on Cisco ASA appliances. [9][17]
- **Gaps in logging / syslog cessation**. [9][17]
- **Unauthorized access or changes to devices**. [17]
- **Large transfers to unknown IP addresses**. [17]
- **More than one executable memory region in `show memory region | include lina`**. [34]
- **Unexpected or unauthorized local accounts** on IOS XE in related Cisco exploitation contexts via `show running-config | section username`. [32]

### Forensics-only / confirmatory
- **Evidence of tampered executable memory regions** and other appliance-memory artifacts. [34]
- **Device configuration artifacts** exfiltrated or rewritten as text versions of config files. [4][17]
- **Deleted files and removed artifacts** from the device filesystem. [4][9]
- **AAA, crash dump, and syslog process tampering/hooking evidence**. [4][9]
- **Packet-capture artifacts** and collected traffic metadata on the device. [4][17]

### Malicious tooling / implant indicators
- **Line Runner**: persistent Lua-based webshell and data exfiltrator. [13][17]
- **Line Dancer**: in-memory loader, data stager, and shellcode loader. [13][17]

## 5) Hunting queries and analytic leads

The source set does not provide ready-made Sigma/KQL/Splunk detections, so the following are hunt-oriented analytic starting points based strictly on reported behaviors. [9][17][34] These are not vendor-validated detections, but they are aligned to the reported tradecraft and device telemetry.

### Cisco ASA / network-hunt logic

**Hunt 1: ASA flows to Talos-listed IOC IPs**
```spl
index=netflow (src_device_type=ASA OR dest_device_type=ASA)
| search ip IN (<talos_ioc_ips>)
| stats count min(_time) max(_time) by src_ip dest_ip action
```
Use this to identify communications to or from ASA devices involving known IOC IPs. [9][34]

**Hunt 2: Unexpected reboots + logging gaps on ASA**
```kql
DeviceEvents
| where DeviceName contains "ASA" or DeviceName contains "Cisco"
| where ActionType in ("Reboot", "ServiceStopped", "LoggingDisabled", "SyslogStopped")
| summarize count(), min(Timestamp), max(Timestamp) by DeviceName, ActionType
```
This matches the reporting that unexpected reboots and gaps in logging are suspicious indicators. [9][17]

**Hunt 3: Multiple executable memory regions in lina**
```spl
index=cisco_asa "show memory region | include lina"
| rex field=_raw "(?<memory_line>lina.*)"
| search "exec"
```
Use this to flag the Cisco-recommended memory-region check for possible tampering. [34]

### Sigma-style behavioral concepts

**Sigma concept: syslog disabled or AAA tampering**
```yaml
title: Cisco ASA Syslog Disabled or AAA Tampering
logsource:
  product: cisco
  service: asa
detection:
  selection:
    message|contains:
      - "syslog"
      - "AAA"
      - "logging"
      - "disable"
  condition: selection
level: high
```
This is based on reported disabling of syslog and tampering with AAA. [9][17]

**Sigma concept: suspicious reboot followed by no logging**
```yaml
title: Cisco ASA Reboot Followed by Logging Gap
logsource:
  product: cisco
  service: asa
detection:
  reboot:
    message|contains: "reboot"
  no_log:
    message|contains:
      - "syslog stopped"
      - "logging disabled"
  condition: reboot and no_log
level: medium
```
This reflects the recommendation to treat unexpected reboots and log gaps as suspicious. [9][17]

### Splunk / KQL concepts for Line Runner and Line Dancer

**Line Runner: HTTP GET with randomized query parameters to WebVPN/AnyConnect URIs**
```spl
index=proxy OR index=web
(method=GET)
(uri_path="*WebVPN*" OR uri_path="*AnyConnect*")
| eval qlen=len(uri_query)
| stats count avg(qlen) by src_ip dest_ip uri_path
```
Line Runner sends arbitrary Lua code via HTTP GET requests to legitimate Cisco ASA WebVPN or AnyConnect URIs using randomized query parameters. [17]

**Line Dancer: HTTP POST with base64-decoded shellcode payload**
```kql
DeviceNetworkEvents
| where RemoteUrl has_any ("WebVPN","AnyConnect")
| where HttpMethod == "POST"
| summarize count() by RemoteIP, RemoteUrl, InitiatingProcessFileName
```
Line Dancer processes base64-decoded shellcode payloads delivered in HTTP POST requests to Cisco ASA WebVPN or AnyConnect URIs. [17]

**Device-side analytical lead: config exfiltration**
```spl
index=proxy OR index=asa_logs ("configuration" OR "config" OR "text version")
| stats count by src_ip dest_ip uri_path
```
The actor exfiltrated device configurations by generating text versions of the configuration file and sending them through web requests. [17]

## 6) Mitigations, response actions, and pivot points

Cisco and partner agencies recommended immediate patching of the affected ASA vulnerabilities, central secure logging, and strong multi-factor authentication for network devices. [34] Cisco also recommended ACLs to block known malicious IPs and geofencing to limit VPN access to expected countries. [17] Because the initial access vector remains unknown, perimeter hardening and device telemetry are especially important. [9][14][34]

### Priority mitigations
- Patch affected Cisco ASA vulnerabilities immediately. [34]
- Enable central secure logging. [34]
- Enforce strong MFA on network devices. [34]
- Block known malicious IPs with ACLs where feasible. [17]
- Restrict VPN access by geography to expected user locations. [17]
- Review logs for unknown, unexpected, or unauthorized access or changes. [17]
- Investigate unexpected reboots and gaps in logging. [9][17]

### Response / investigation workflow
1. Validate whether the ASA device communicates with IOC IPs or suspicious infrastructure. [9][34]
2. Check for unexpected reboots and missing syslog coverage. [9][17]
3. Inspect `show memory region | include lina` for multiple executable memory regions. [34]
4. Search for unauthorized device changes, AAA tampering, and disabled logging. [4][9][17]
5. Look for packet-capture activity and configuration exfiltration behavior. [4][17]
6. Preserve evidence using Cisco ASA forensic procedures for first responders. [34]

### High-value pivot points
- **Device family pivot**: Cisco ASA and other perimeter networking devices. [4][24]
- **Campaign pivot**: ArcaneDoor / UAT4356 / STORM-1849. [1][4][24][34]
- **Malware pivot**: Line Runner, Line Dancer. [1][4][13][17]
- **Infrastructure pivot**: adversary-controlled VPS, OpenConnect VPN Server instances, and IOC IPs. [4][9]
- **TTP pivot**: syslog disablement, AAA tampering, reboot-triggered persistence, HTTP C2, packet capture, and config exfiltration. [4][9][17][34]
- **Targeting pivot**: government and critical infrastructure networks globally, plus the additional public-reporting set of financial, defense, and military organizations. [1][4][6][34]

## Key Findings

- Storm-1849 is the Microsoft name for the actor Cisco Talos tracks as UAT4356, associated with ArcaneDoor. [1][24][34]
- The actor is assessed as state-sponsored and espionage-focused. [1][24][34]
- The campaign targeted government networks globally and also appears in reporting against critical infrastructure and other high-value sectors. [1][4][6][34]
- The actor used two custom implants: Line Runner and Line Dancer. [1][4][13][17]
- The actor exploited Cisco ASA vulnerabilities, used malicious boot scripts, disabled logging, tampered with AAA, injected into processes, and deleted artifacts. [1][4][9][17][34]
- The campaign used HTTP-based C2, adversary-controlled VPS infrastructure, and OpenConnect VPN Server instances. [4]
- The actor collected packet captures and system configurations and exfiltrated data over existing C2 channels. [4][17]
- The most important intelligence gap is the initial access vector, which remains unknown. [9][14][34]
- Cisco advises device-memory checks, flow analysis, and forensic evidence collection as the most useful immediate investigative actions. [9][34]

## Gaps

- unverified claims removed
- The initial access vector is unknown, and the reporting explicitly says there is no evidence yet of pre-authentication exploitation in at least one advisory. [9][14][34]
- The full extent of victimology is incomplete; reporting confirms government networks globally and mentions other sectors, but not a complete victim list. [1][4][6][34]
- Some actor IPs may be anonymization infrastructure, so IP-based attribution and blocking are partly uncertain. [9]
- The open reporting provides only a subset of techniques, not a complete campaign behavior set. [7]
- Cisco notes that Line Runner may persist even if Line Dancer is not detected, so absence of one implant does not rule out compromise. [17]
- The values in Line Runner GET requests are assumed to be victim-specific, but that is not confirmed. [17]
- The exact relationship between the actor’s China-linked clues and final attribution remains not fully settled in the available reporting. [6][14]
- No source provided concrete domain, hash, or full IP lists, so the dossier cannot supply a complete blocklist from the supplied material alone. [4][9][34]
- No source provided vendor-ready Sigma/KQL/Splunk detections, so all hunt logic here is derived behavioral guidance rather than validated rules. [9][17][34]

---

## Sources

[1] Storm-1849 (Threat Actor) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/actor/storm-1849  
[2] National Weather Service — https://www.weather.gov/  
[3] How Microsoft names threat actors - Unified security operations — https://learn.microsoft.com/en-us/unified-secops/microsoft-threat-actor-naming  
[4] ArcaneDoor, Campaign C0046 - MITRE ATT&CK® — https://attack.mitre.org/campaigns/C0046/  
[5] MITRE ATT&CK - Page 2 of 2 - Cisco Blogs — https://blogs.cisco.com/tag/mitre-attck/page/2  
[6] China-linked Storm-1849 spent October targeting Cisco ASA firewalls — https://www.scworld.com/news/china-linked-storm-1849-spent-october-targeting-cisco-asa-firewalls  
[7] Campaigns | MITRE ATT&CK® — https://attack.mitre.org/campaigns/  
[8] MITRE ATT&CK® — http://attack.mitre.org/  
[9] ArcaneDoor - New espionage-focused campaign found targeting ... — https://blog.talosintelligence.com/arcanedoor-new-espionage-focused-campaign-found-targeting-perimeter-network-devices/  
[10] AI Infrastructure, Secure Networking, and Software Solutions - Cisco — https://www.cisco.com/  
[11] USDA Forest Service FSGeodata Clearinghouse - Raster Data Gateway — https://data.fs.usda.gov/geodata/rastergateway/index.php  
[12] Cisco Networking Academy: Learn Cybersecurity, Python & More — https://www.netacad.com/  
[13] Espionage Campaign Impacting Cisco ASA Devices - Deepwatch — https://www.deepwatch.com/labs/new-espionage-campaign-exploits-vulnerabilities-in-cisco-asa-devices/  
[14] Analysis of ArcaneDoor Threat Infrastructure Suggests Potential Ties ... — https://censys.com/blog/analysis-of-arcanedoor-threat-infrastructure-suggests-potential-ties-to-chinese-based-actor/  
[15] Caribbean Island Land Cover - US Forest Service — https://data.fs.usda.gov/geodata/rastergateway/caribbean/index.php  
[16] Cisco Products: Networking, Security, Data Center — https://www.cisco.com/site/us/en/products/index.html  
[17] Cyber Activity Impacting CISCO ASA VPNs - Canadian Centre for ... — https://www.cyber.gc.ca/en/news-events/cyber-activity-impacting-cisco-asa-vpns  
[18] F5 Threat Report - October 1st, 2025 - DevCentral — https://community.f5.com/kb/security-insights/f5-threat-report---october-1st-2025/343733  
[19] Dr. Robert Moore, MD - Family Medicine Physician in Dayton ... — https://www.healthgrades.com/physician/dr-robert-moore-2665s  
[20] 2025-26 Chicago Blackhawks Roster, Stats, Injuries, Scores, Results ... — https://www.hockey-reference.com/teams/CHI/2026.html  
[21] Robert W. Moore, MD | Kettering Health — https://ketteringhealth.org/doctors/robert-w-moore-1780741058/  
[22] 2025–26 Chicago Blackhawks season - Wikipedia — https://en.wikipedia.org/wiki/2025%E2%80%9326_Chicago_Blackhawks_season  
[23] Tidal Groups - MISP galaxy — https://misp-galaxy.org/tidal-groups/  
[24] スパイ活動に重点を置く新たな攻撃 ArcaneDoor を発見 - Cisco Blogs — https://gblogs.cisco.com/jp/2024/05/talos-arcanedoor-new-espionage-focused-campaign-found-targeting-perimeter-network-devices/  
[25] Dr. Robert W Moore - Hospitalist, Kettering OH - HealthCare4PPL — https://www.healthcare4ppl.com/physician/ohio/kettering/robert-w-moore-1780741058.html  
[26] RELEASE: Blackhawks 2025-26 Season Schedule Announced — https://www.nhl.com/blackhawks/news/release-blackhawks-2025-26-season-schedule-announced  
[27] Telefonica Tech · Blog - Telefónica Tech — https://telefonicatech.com/en/blog/author/telefonicatech  
[28] Urgent Cisco Firewall Zero-Day Alert: New DoS Attack Exploiting CVE-2025–20333 & CVE-2025–20362… - Freedium — https://freedium-mirror.cfd/f22c3504d71a  
[29] How to get help in Windows - Microsoft Support — https://support.microsoft.com/en-us/windows/how-to-get-help-in-windows-711b6492-0435-0038-8706-7c6b0feb200a  
[30] busETA: Route M22 — https://buseta.wmata.com/m/index?q=1_M22+M22  
[31] Manual - OpenConnect VPN Server — https://ocserv.openconnect-vpn.net/ocserv.8.html  
[32] CVE-2023-20198 Explained: Cisco IOS XE Zero-Day, 50,000 Devices — https://www.decryptiondigest.com/blog/cve-2023-20198-cisco-ios-xe-explained  
[33] Windows help and learning | Microsoft Support — https://support.microsoft.com/en-us/windows/  
[34] State-Sponsored Espionage Campaign Exploits Cisco Vulnerabilities - Infosecurity Magazine — https://www.infosecurity-magazine.com/news/stateespionage-campaign-cisco/  

---

## Metadata

- **Model:** openai/gpt-5.4-mini (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 11m 14s
- **Depth reached:** 4
- **Sources read:** 34
- **Learnings:** 635
- **Verified learnings:** 405
- **Prompt tokens:** 289868
- **Completion tokens:** 73366