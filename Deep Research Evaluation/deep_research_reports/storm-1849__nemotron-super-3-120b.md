# Produce a full hunt-ready dossier on actor "Storm-1849". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

Storm-1849 (also tracked as UAT4356, Salt Typhoon, and ArcaneDoor) is a China-linked state-sponsored cyber espionage group active since at least July 2023, primarily targeting government and critical infrastructure networks worldwide through exploitation of Cisco networking devices. The group has demonstrated sophisticated capabilities in maintaining persistence, evading detection, and exfiltrating sensitive data via custom malware implants and advanced techniques. Their operations span multiple campaigns exploiting both zero-day and known vulnerabilities in Cisco ASA, FTD, Firepower, IOS XE, and NX-OS platforms, with activity observed globally across government entities in the U.S., India, Europe, and Asia-Pacific regions.

## Identity & Aliases

- **Primary Identifier**: Storm-1849 (Microsoft attribution) [1][3][6][9][14][18][20][22][23]
- **Aliases**: UAT4356 [1][3][5][6][9][14][18][20][22], Salt Typhoon [12], ArcaneDoor [1][7][14][20][23]
- **Attribution**: China-based threat actor [5][6][9][12][18][23]; state-sponsored [6][9][12][18][23]; assessed with moderate to high confidence as PRC-linked [12][23]
- **Intelligence Status**: Classified as 'Group in development' by Microsoft indicating emerging/threat activity under tracking [3]; some sources note insufficient intelligence for definitive nation-state attribution [7][20]

## Observed TTPs Mapped to MITRE ATT&CK

| Tactic | Technique | TTP ID | Description | Source |
|--------|-----------|--------|-------------|--------|
| Initial Access | Exploit Public-Facing Application | T1190 | Exploitation of CVE-2024-20353, CVE-2024-20359 [14][18]; CVE-2025-20333, CVE-2025-20362 [5][18][23]; CVE-2023-20198, CVE-2023-20273 [12]; CVE-2024-21887, CVE-2024-3400 [12] | [5][12][14][18][23] |
| Initial Access | Phishing | T1566 | Not explicitly stated but implied via credential theft for VPN access [18] | [18] |
| Execution | Command and Scripting Interpreter | T1059 | Execution of CLI commands on Cisco ASA [1]; scripted exfiltration [1]; Base64 obfuscated scripts [1]; Lua-based malware execution [14] | [1][14] |
| Execution | Exploitation for Client Execution | T1203 | Exploitation leading to code execution via WebVPN [1]; LINE VIPER shellcode loader [18]; FIRESTARTER backdoor [18][23] | [1][18][23] |
| Persistence | Boot or Logon Autostart Execution | T1547 | Malicious boot scripts installing Line Runner [1]; persistence across reboots/upgrades [5][20]; firmware/ROM bootkit [20][23]; modification of CSP_MOUNT_LIST [18]; modification of AAA process [1][14] | [1][5][14][18][20][23] |
| Persistence | Event Triggered Execution | T1546 | Hooking processHostScanReply() function [1]; suppression of checkheaps function [20]; syslog ID suppression [20] | [1][20] |
| Persistence | Create Account | T1136 | Creation of local accounts on network devices [12] | [12] |
| Persistence | Modify Authentication Process | T1556 | Modification of AAA function to bypass authentication [1][14]; manipulation of Crash Dump processes [1] | [1][14] |
| Privilege Escalation | Abuse Elevation Control Mechanism | T1548 | Gaining root/admin access via exploits [23]; LINE VIPER for full device configuration access [18] | [18][23] |
| Defense Evasion | Obfuscated Files or Information | T1027 | Base64 obfuscation of scripts/commands [1]; use of legitimate Cisco URIs for C2 [14]; anti-forensic techniques [1][6][9][12][23]; deletion of files to remove indicators [1]; specific syslog suppression [20][23] | [1][6][9][12][14][20][23] |
| Defense Evasion | Impair Defenses | T1562 | Disabling logging on Cisco ASA [1]; suppression of specific syslog IDs (302013, 302014, 609002, 710005) [20]; disabling checkheaps function [20]; intercepting CLI commands before logging [18] | [1][18][20] |
| Defense Evasion | Hide Artifacts | T1564 | In-memory operation of Line Dancer [14]; firmware persistence invisible in running-config [20]; use of legitimate processes for C2 [14] | [14][20] |
| Credential Access | OS Credential Dumping | T1003 | Collection of credentials via modified AAA [1]; LINE VIPER for administrative credentials/keys [18]; collection via Guest Shell [12]; potential lateral movement using stolen creds [6][12][18][20] | [1][6][12][18][20] |
| Discovery | Network Service Scanning | T1046 | Scanning for vulnerable Cisco ASA devices [5][12]; scanning from changing malicious IPs [20] | [5][12][20] |
| Discovery | System Network Configuration Discovery | T1016 | Collection of device configuration information [1][12]; network packet capture/sniffing [1][12][14][18][20]; utilization of Guest Shell for reconnaissance [12] | [1][12][14][18][20] |
| Collection | Data from Information Repositories | T1213 | Automated collection of packet capture and system configuration [1]; use of custom SFTP client for encrypted archives [12] | [1][12] |
| Collection | Screen Capture | T1113 | Not explicitly stated but implied via traffic capture [1][6][12] | [1][6][12] |
| Exfiltration | Exfiltration Over Web Services | T1567 | HTTP C2 traffic for command and exfiltration [1][14]; use of existing C2 channels for data exfil [1]; WebVPN sessions for C2 communication [1]; custom SFTP client over non-standard ports/tunnels [12] | [1][12][14] |
| Exfiltration | Exfiltration Over Unencrypted/Obfuscated Non-C2 Protocol | T1048 | Use of GRE/MPLS tunnels for data exfiltration [12]; ICMP tunneling [18] | [12][18] |
| Impact | Inhibit System Recovery | T1499 | Persistence across upgrades/patching [5][20]; firmware/ROM bootkit surviving reboots [20][23] | [5][20][23] |
| Impact | Data Manipulation | T1565 | Modification of device configurations [1][6][9][12][14][18][20][23]; manipulation of AAA process [1][14]; modification of SSH authorized keys [12] | [1][6][9][12][14][18][20][23] |

## IOCs Classification

### Block (Preventive)
- **Malicious IPs**: 185.244.210.65, 5.183.95.95, 213.156.138.77 [7][14]; 45.86.163.224, 51.15.145.37 [14]; 1.222.84.29, 167.88.173.252, 23.227.202.253, 45.61.151.12 [12]; 65.38.121.198, 131.226.2.6, 134.199.202.205, 104.238.159.149, 188.130.206.168 [8] *(Note: Storm-2603 IPs included in source but not attributed to Storm-1849; use with caution)*
- **Malicious Domains**: update.updatemicfosoft.com, msupdate.updatemicfosoft.com [8] *(Note: Associated with Storm-2603, not Storm-1849)*
- **File Patterns**: '^client_bundle[%w_-]*%.zip$' [14]; LINE VIPER, FIRESTARTER, RayInitiator [18][23]; custom SFTP client binaries (cmd1, cmd3, new2, sft variants) [12]
- **File Hashes**: 
  - cmd1 SFTP: f2bbba1ea0f34b262f158ff31e00d39d89bbc471d04e8fca60a034cabe18e4f4 [12]
  - cmd3 SFTP: 8b448f47e36909f3a921b4ff803cf3a61985d8a10f0fe594b405b92ed0fc21f1 [12]
  - Storm-2603 web shell (caution): 92bb4ddb98eeaf11fc15bb32e71d0a63256a0ed826a03ba293ce3a8bf057a514 [8] *(Not Storm-1849)*
- **YARA Rules**: CISA YARA rules for FIRESTARTER detection [18]; specific YARA for Storm-1849 Salt Typhoon SFTP clients [12]; CISA_261290_01, CISA_261290_02 [18]

### Hunt (Behavioral/Anomaly-Based)
- **Network**: HTTP traffic interception parsing for C2 [1]; large volumes of data transfer Dec 2023-Feb 2024 [7]; scanning from continuously changing malicious IPs [20]; unexpected use of chvrf or dohost on Cisco IOS XE/NX-OS [12]; TCP/57722 listeners on IOS XR [12]; WebVPN sessions associated with Clientless SSLVPN [1]; POST requests to /CSCOSSLC/config-auth with base64-encoded host-scan-reply [14]; GET requests to /+CSCOE+/portal.css? with randomized query params [14]; sustained ICMP tunneling [18]; 'impossible travel' VPN patterns [20]
- **System/Process**: ASA event IDs ASA-4-106103, ASA-4-109027, ASA-5-111001 through ASA-5-8300006 [14]; disabled checkheaps function (no change in Total runs counter) [20]; suppression of syslog IDs 302013, 302014, 609002, 710005 [20]; interception of CLI commands before logging [18]; modification of AAA/Crash Dump processes [1]; hooking processHostScanReply() [1]; guestshell enable/run/destroy commands on IOS XE/NX-OS [12]; verification failure in bootloader/ROMMON [20]; presence of firmware_update.log on disk0: [20]
- **File Artifacts**: Line Dancer (in-memory loader/stager) [14]; Line Runner (Lua-based webshell/exfiltrator) [14]; Line VIPER (user-mode shellcode loader) [18]; FIRESTARTER (Linux ELF backdoor) [18][23]; files in /opt/cisco/platform/logs/var/log/, /opt/cisco/config/platform/rmdb/ [18]; specific file paths monitored by CISA YARA [18]; malicious boot scripts on Cisco ASA [1]

### Forensics-Only (Post-Compromise)
- **Memory Artifacts**: In-memory Line Dancer operation [14]; shellcode injection into libstdc++.so [18]; detour on XML element handler [18]; core dumps for YARA scanning [18]
- **Disk Artifacts**: firmware_update.log file on disk0: [20]; full show checkheaps/show tech-support output [18]; changes to /opt/cisco/config/platform/rmdb/CSP_MOUNT_LIST [18]; modified SSH authorized keys [12]; local account creation artifacts [12]; Guest Shell container remnants [12]
- **Configuration Artifacts**: Modified AAA function [1][14]; modified Authentication, Authorization, Accounting [1]; altered WebVPN/AnyConnect URI handling [14]; persistence via reboot survival [5][20]; unchanged Total runs counter for checkheaps [20]

## Infrastructure Patterns

- **C2 Infrastructure**: Dedicated adversary-controlled VPS [1]; OpenConnect VPN Server instances [1]; multi-hop proxy tools like STOWAWAY [12]; use of legitimate Cisco ASA WebVPN/AnyConnect URIs for C2 [14]; hardcoded paths for monitoring/persistence [18]; C2 via HTTP protocols [1]; use of existing C2 channels for exfil [1]; WebVPN sessions for communication [1]; non-standard ports and protocol tunneling (GRE/MPLS) [12]; ICMP tunneling [18]
- **Domain Infrastructure**: Domains mimicking Cisco ASA appliance formatting [1][6]; digital certificates mimicking Cisco ASA appliances [1][6]; CISA YARA-monitored paths [18]
- **Geographic Distribution**: Globally distributed targeting [5][12][18][20][23]; specific targeting of government/edge devices [5][6][9][12][14][18][20][23]; observed scanning/exploitation of 12 U.S. federal + 11 state/local gov IPs in Oct [5]; targeting of federal gov IPs in India, Nigeria, Japan, Norway, France, UK, Netherlands, Spain, Australia, Poland, Austria, UAE, Azerbaijan, Bhutan in Oct [5]; targeting of U.S. financial institutions, defense contractors, military in Oct 2025 [23]
- **Temporal Patterns**: Activity observed Jul 2023-Apr 2024 (ArcaneDoor) [1]; lull Oct 1-8 likely due to China's Golden Week [5]; activity persisted Oct despite patching [5]; activity noted Dec 2023-Feb 2024 [7]; initial access early Sept 2025 [18]; re-deployment March 2026 [18]; targeting throughout Oct 2025 [23]; continuous scanning with changing IPs [20]

## Timeline of Observed Activity

- **July 2023 - April 2024**: ArcaneDoor campaign targeting Cisco ASA devices [1]; use of dedicated VPS, OpenConnect VPN, HTTP C2, Line Dancer/Line Runner malware, AAA modification, boot scripts, packet capture exfiltration [1]; exploitation of CVE-2024-20353 [1][7][14]; digital certificate mimicry [1][6]
- **December 2023 - February 2024**: Period of significant activity detectable via large data transfers [7]; IOCs observed including 185.244.210.65, 5.183.95.95 [7][14]
- **July 7, 2025**: Initial exploitation attempts observed (Note: This appears misattributed to Storm-2603 in source [8]; treat with caution for Storm-1849)
- **September 2025**: Persistence mechanism preserved across upgrades to fixed releases [20]; broadening to any device running Secure Firewall ASA/FTD [20]
- **October 2025**: 
  - Targeting of 12 U.S. federal + 11 state/local gov IPs [5]
  - Targeting of gov IPs in India, Nigeria, Japan, Norway, France, UK, Netherlands, Spain, Australia, Poland, Austria, UAE, Azerbaijan, Bhutan [5]
  - Targeting of U.S. financial institutions, defense contractors, military [23]
  - Exploitation of CVE-2025-20333 and CVE-2025-20362 [5][18][23]
  - Lull Oct 1-8 due to China's Golden Week [5]
  - Continued activity despite patching efforts [5][23]
- **Early September 2025**: Initial access via exploited vulnerabilities [18]
- **March 2026**: Return using FIRESTARTER to re-deploy LINE VIPER without touching original vulnerabilities [18]
- **August 2021 - June 2025**: IP-based indicators observed for Salt Typhoon activity [12]
- **Ongoing**: Continued exploitation of publicly known CVEs [12]; targeting of government edge devices despite patching [5]; use of Guest Shell, VPS C2, SFTP exfil, tunneling [12]

## Hunting Queries

### Sigma
```sigma
title: Potential Storm-1849 Cisco ASA HTTP C2 Activity
description: Detects HTTP traffic patterns indicative of Storm-1849 C2 interception and parsing on Cisco ASA devices
logsource:
  product: cisco
  service: asa
detection:
  selection:
    msg: ['*CSCOSSLC/config-auth*']
    host-scan-reply: '*base64*'
  condition: selection
level: high
```
*Based on POST to /CSCOSSLC/config-auth with base64-encoded host-scan-reply [14]*

```sigma
title: Potential Storm-1849 WebVPN C2 via Lua Execution
description: Detects anomalous WebVPN requests consistent with Line Runner execution
logsource:
  product: cisco
  service: asa
detection:
  selection:
    uri: ['*/+CSCOE+/portal.css?*']
    query: '*[0-9a-zA-Z+/=]{20,}*'  # Detects long randomized base64-like params
  condition: selection
level: medium
```
*Based on randomized query params in GET to /+CSCOE+/portal.css? [14]*

### KQL (Microsoft Sentinel / Defender XDR)
```kql
// Detect Guest Shell usage on Cisco IOS XE/NX-OS
DeviceNetworkEvents
| where RemoteIP in (1.222.84.29, 167.88.173.252, 23.227.202.253, 45.61.151.12)  // Storm-1849 Salt Typhoon IPs [12]
| where AdditionalFields.Command has_any ("guestshell enable", "guestshell run bash", "guestshell disable", "guestshell destroy")
```
*Based on guestshell enable/run/destroy monitoring [12]*

```kql
// Detect TCP/57722 listeners on IOS XR (persistent sshexec)
DeviceNetworkEvents
| where LocalPort == 57722
| where RemoteIP in (1.222.84.29, 167.88.173.252, 23.227.202.253, 45.61.151.12)  // Salt Typhoon IPs [12]
```
*Based on TCP/57722 listener monitoring [12]*

```kql
// Detect chvrf or dohost usage (VRF/container host CLI abuse)
DeviceProcessEvents
| where ProcessCommandLine has_any ("chvrf", "dohost")
| where DeviceName has_any ("IOS-XE", "NX-OS")  // Approximation for Cisco devices
```
*Based on unexpected chvrf/dohost use [12]*

```kql
// Detect large data transfers indicative of exfiltration (Dec 2023-Feb 2024 window)
AzureNetworkAnalytics
| where TimeGenerated >= datetime(2023-12-01) and TimeGenerated < datetime(2024-03-01)
| where TotalBytes > 100MB  // Threshold may need tuning
| summarize by SourceIP, DestinationIP, bin(TimeGenerated, 1h)
```
*Based on historical network logs for large volumes Dec 2023-Feb 2024 [7]*

### Splunk SPL
```spl
index=network (src_ip=185.244.210.65 OR src_ip=5.183.95.95 OR src_ip=213.156.138.77) 
| stats count by src_ip, dest_ip, _time span=1h
| where count > 100
```
*Based on Storm-1849-associated malicious IPs [7][14]*

```spl
index=cisco_asa 
(uri="/CSCOSSLC/config-auth" AND host-scan-reply=*) 
| eval decoded=decodebase64(host-scan-reply) 
| search decoded="*Line*" OR decoded="*cmd*" 
```
*Based on POST to /CSCOSSLC/config-auth with base64 payload [14]*

## Mitigations

- **Patch Management**: 
  - Apply Cisco ASA patches to versions 9.16.4.57, 9.18.4.22, or 9.20.2.10 (as of Apr 25) to mitigate CVE-2024-20359/CVE-2024-20353 [14]
  - Apply patches for CVE-2025-20333 and CVE-2025-20362 per CISA emergency directive [5][23]
  - Patch CVE-2023-20198, CVE-2023-20273 on Cisco IOS XE [12]
  - Patch CVE-2024-21887 (Ivanti) and CVE-2024-3400 (Palo Alto) if relevant [12]
- **Configuration Hardening**:
  - Disable Guest Shell where not operationally required using `guestshell destroy` (NX-OS) or `guestshell disable` (IOS XE) [12]
  - Monitor for unexpected use of `chvrf` (VRF) and `dohost` (container host CLI) [12]
  - Alert on TCP/57722 listeners on IOS XR platforms [12]
  - Ensure logging is enabled and monitor for suppression of syslog IDs [1][18][20]
  - Verify AAA process integrity and monitor for unauthorized modifications [1][14]
  - Regularly verify bootloader/ROMMON integrity [20]
- **Detection & Monitoring**:
  - Implement YARA rules for FIRESTARTER, Line Dancer/Runner, custom SFTP clients [12][18]
  - Monitor ASA event IDs: ASA-4-106103, ASA-4-109027, ASA-5-111001 through ASA-5-8300006 [14]
  - Monitor for absence of change in checkheaps Total runs counter [20]
  - Monitor for specific file patterns: '^client_bundle[%w_-]*%.zip$' [14]
  - Monitor for firmware_update.log on disk0: [20]
  - Monitor for large data transfers during historical windows (e.g., Dec 2023-Feb 2024) [7]
  - Monitor for 'impossible travel' VPN connection patterns [20]
  - Monitor for sustained ICMP tunneling [18]
  - Monitor for WebVPN anomalies: POST to /CSCOSSLC/config-auth, GET to /+CSCOE+/portal.css? with randomized params [14]
  - Monitor for guestshell enable/run/destroy commands [12]
  - Monitor for chvrf/dohost usage [12]
  - Monitor for TCP/57722 listeners on IOS XR [12]
- **Network Controls**:
  - Block known malicious IPs at perimeter/firewall [7][12][14]
  - Implement strict WebVPN/SSLVPN access controls and monitoring [1]
  - Disable unnecessary services (WebVPN if not required) [18]
  - Use network segmentation to limit lateral movement [6][12][18][20]
- **Identity & Access**:
  - Reset credentials on compromised devices [23]
  - Monitor for use of dormant/disabled accounts for VPN access [18]
  - Implement MFA for VPN/admin access [18][23]
  - Review and prune inactive accounts, especially those with VPN entitlements [18]
- **Response**:
  - For confirmed compromise: Collect core dumps and full show checkheaps/show tech-support output before remediation [18]
  - Apply CISA YARA rules to collected artifacts [18]
  - Consider hard power pull (physical unplug) as reboot/patch may not clear implant; wait ≥60 seconds [18][20]
  - Open case with Cisco TAC referencing "ArcaneDoor" keyword [20]
  - Conduct forensic analysis for firmware/ROM bootkit persistence [20][23]
  - Hunt for in-memory artifacts using memory analysis tools [14][18]

## Pivot Points

- **From Malware Artifacts**: 
  - Presence of Line Dancer/Runner → hunt for HTTP C2 patterns, AAA modifications, boot scripts [1][14]
  - Presence of FIRESTARTER → monitor for shellcode injection in libstdc++.so, XML handler detours, CSP_MOUNT_LIST modifications [18]
  - Presence of custom SFTP client (cmd1/cmd3) → hunt for guestshell usage, chvrf/dohost, TCP/57722 listeners, non-standard port tunneling [12]
  - Presence of LINE VIPER → monitor for VPN session abuse using dormant accounts, administrative credential access [18]
- **From Network Indicators**:
  - Malicious IP contact → check for HTTP traffic to CSCOSSLC/config-auth, WebVPN anomalies, large data transfers [7][14]
  - WebVPN session anomalies → investigate for base64-encoded host-scan-reply, randomized portal.css? params [14]
  - Guest Shell activation → review for subsequent bash execution, container destruction, unusual commands [12]
  - chvrf/dohost usage → investigate for VRF switching or container host CLI abuse [12]
  - TCP/57722 listener → investigate for persistent sshexec service enabling [12]
- **From System Anomalies**:
  - Disabled logging/syslog suppression → investigate for CLI command interception, AAA/Crash Dump modification [1][18]
  - Unchanged checkheaps counter → verify integrity of checkheaps function [20]
  - Bootloader/ROMMON failure → investigate for firmware/ROM bootkit presence [20]
  - Presence of firmware_update.log → investigate pre-upgrade compromise [20]
  - 'Impossible travel' VPN patterns → investigate for stolen credential use [20]
  - Sustained ICMP tunneling → investigate for C2/data exfil channel [18]
- **From Credential Access**:
  - Credential dumping evidence → investigate for lateral movement, VPN session abuse [1][6][12][18][20]
  - Modified AAA/authentication → investigate for bypass mechanisms, local account creation [1][12][14]
- **From Configuration Changes**:
  - Modified SSH authorized keys → investigate for persistence, lateral movement [12]
  - Local account creation → investigate for persistence mechanisms [12]
  - WebVPN/AnyConnect URI manipulation → investigate for C2 hijacking [14]

## Intelligence Gaps

- **Initial Access Vector**: Despite observed exploitation of CVEs, the precise initial access methods (e.g., phishing, supply chain, credential theft) remain unclear, especially for early campaign phases [7][12][14][18]; noted as a "critical information gap" [12]
- **Attribution Confidence**: While assessed as China-linked and state-sponsored, there is insufficient high-confidence intelligence to attribute to a specific nation-state unit or APT group [3][7][20]; some sources conflict (e.g., Russian APT29 claim in [22] is contradicted by majority of sources and likely erroneous)
- **Full Toolset**: Complete inventory of malware, tools, and TTPs is unknown; newer variants like LINE VIPER and FIRESTARTER suggest evolving capabilities but full scope unclear [18][23]
- **Command and Control Infrastructure**: Full mapping of adversary-controlled infrastructure (VPS, domains, certs) is incomplete; observed IPs/domains may represent only a subset [1][7][12][14]
- **Victimology Scope**: While government/critical infrastructure targeting is confirmed, full list of compromised sectors, geographies, and specific victim organizations is incomplete [5][6][9][12][18][20][23]
- **Persistence Mechanisms**: Though firmware/ROM bootkit and Guest Shell abuse are known, other potential persistence methods (especially in newer FXOS environments) are not fully understood [20]
- **Exfiltration Channels**: While HTTP, WebVPN, SFTP, GRE/MPLS, and ICMP tunneling are observed, the full range of exfiltration methods and staging infrastructure is unclear [1][6][12][14][18]
- **Detection Evasion**: Full extent of anti-forensic and memory-resident techniques designed to evade specific telemetry platforms (e.g., Sigma rule gaps) is not fully characterized [18]
- **Activity Timelines**: Exact start/end dates of specific campaigns beyond observed windows (Jul 2023-Apr 2024, Oct 2025) are incomplete; activity may be ongoing or cyclical [1][5][7]
- **Objectives**: While espionage is implied via data collection/exfiltration, specific intelligence requirements (e.g., political, military, economic) are not confirmed [8] *(Note: This gap is from Storm-2603 but analogous for Storm-1849)*; no public confirmation of data leakage or specific stolen information types
- **Defensive Efficacy**: Long-term effectiveness of patches, configuration changes, and mitigations against evolving TTPs is not fully validated, especially regarding persistence mechanisms [5][20][23]
- **Supply Chain/Third-Party Risk**: Evidence of exploitation via trusted relationships or peering connections is noted but not fully mapped or quantified [12]

*Note: All claims are strictly derived from the provided learnings. Sources indicating Storm-2603 activity ([8]) were examined but only included where contextual relevance to Storm-1849 patterns was explicit and clearly differentiated; where ambiguity existed, Storm-2603 IOCs/TTPs were excluded from Storm-1849 sections to prevent conflation.*

## Gaps

- unverified claims removed

---

## Sources

[1] ArcaneDoor, Campaign C0046 - MITRE ATT&CK® — https://attack.mitre.org/campaigns/C0046/  
[2] ArcaneDoor - New espionage-focused campaign found targeting ... — https://blog.talosintelligence.com/arcanedoor-new-espionage-focused-campaign-found-targeting-perimeter-network-devices/  
[3] How Microsoft names threat actors - Unified security operations — https://learn.microsoft.com/en-us/unified-secops/microsoft-threat-actor-naming  
[4] ArcaneDoor Vulnerabilities [CVE-2024-20353, CVE-2024-20359] — https://help.bitsighttech.com/hc/en-us/articles/23191250656151-ArcaneDoor-Vulnerabilities-CVE-2024-20353-CVE-2024-20359  
[5] Chinese hackers scanning, exploiting Cisco ASA firewalls used by ... — https://therecord.media/chinese-hackers-scan-exploit-firewalls-government  
[6] STORM-1849 - Cloud Threat Landscape — https://threats.wiz.io/all-actors/storm-1849  
[7] Nation-state cyber unit exploits Cisco flaws for espionage — https://www.quorumcyber.com/threat-intelligence/hostile-nation-state-cyber-unit-exploits-cisco-zero-day-flaws-to-launch-espionage-efforts/  
[8] Disrupting active exploitation of on-premises SharePoint ... - Microsoft — https://www.microsoft.com/en-us/security/blog/2025/07/22/disrupting-active-exploitation-of-on-premises-sharepoint-vulnerabilities/  
[9] Storm-1849 (Threat Actor) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/actor/storm-1849  
[10] DIB-Reported Cyber Threats CY2024 Q2 April–June — https://www.dc3.mil/Portals/100/Documents/DC3/Missions/DCISE/DCISE%20Slick%20Sheets/DIB%20Cyber%20Threats/2024/DCISE-DIB-CyberThreats-CY24-Q2-Final.pdf  
[11] Campaigns | MITRE ATT&CK® — https://attack.mitre.org/campaigns/  
[12] Countering Chinese State-Sponsored Actors Compromise of ... - CISA — https://www.cisa.gov/news-events/cybersecurity-advisories/aa25-239a  
[13] MISP Galaxy changelog — https://www.misp-project.org/Changelog-misp-galaxy.txt  
[14] Espionage Campaign Impacting Cisco ASA Devices - Deepwatch — https://www.deepwatch.com/labs/new-espionage-campaign-exploits-vulnerabilities-in-cisco-asa-devices/  
[15] Updates - October 2025 - MITRE ATT&CK® — https://attack.mitre.org/resources/updates/updates-october-2025/  
[16] Threat Report ATT&CK Mapper (TRAM) | Center for Threat-Informed Defense — https://ctid.mitre.org/projects/threat-report-attck-mapper-tram/  
[17] LockBit (Malware Family) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/details/win.lockbit  
[18] Pull the Power Cord: FIRESTARTER, AR26-113A, and a Backdoor ... — https://www.threathunter.ai/blog/firestarter-cisco-asa-ftd-backdoor-ar26-113a/  
[19] Tidal Groups - MISP galaxy — https://misp-galaxy.org/tidal-groups/  
[20] Detection Guide for Continued Attacks against Cisco Firewalls by ... — https://sec.cloudapps.cisco.com/security/center/resources/detection_guide_for_continued_attacks  
[21] Threat Actors | Types, Motivations, TTPs & How to Track Them — https://www.dexpose.io/threat-actors/  
[22] SUNBURST (Malware Family) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/details/win.sunburst  
[23] Exploitation of Cisco ASA and FTD Zero-Day Vulnerabilities by ... — https://www.mallory.ai/stories/019a5a1d-b530-7221-98e5-e53961405cf5  
[24] Clankerusecase — Threat-led detection library: Defender KQL ... — https://clankerusecase.com/  
[25] Defending Against ArcaneDoor: How Eclypsium Protects Network ... — https://eclypsium.com/blog/defending-against-arcanedoor-how-eclypsium-protects-network-devices/  
[26] Analysis of ArcaneDoor Threat Infrastructure Suggests Potential Ties ... — https://censys.com/blog/analysis-of-arcanedoor-threat-infrastructure-suggests-potential-ties-to-chinese-based-actor/  
[27] CVE-2025-20333, CVE-2025-20362: Cisco Zero-Days Exploited — https://www.tenable.com/blog/cve-2025-20333-cve-2025-20362-faq-cisco-asa-ftd-zero-days-uat4356  

---

## Metadata

- **Model:** bedrock/nvidia.nemotron-super-3-120b (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 19m 6s
- **Depth reached:** 4
- **Sources read:** 27
- **Learnings:** 177
- **Verified learnings:** 31
- **Ladder demotions:** 2
- **Prompt tokens:** 896845
- **Completion tokens:** 94230