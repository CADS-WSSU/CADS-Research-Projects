# Produce a full hunt-ready dossier on actor "MuddyWater". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

MuddyWater is a persistently active Iranian cyber-espionage and advanced persistent threat (APT) group assessed as a subordinate element of Iran’s Ministry of Intelligence and Security (MOIS), tracked by MITRE ATT&CK as G0069 and known under multiple aliases including Seedworm, Static Kitten, TEMP.Zagros, Earth Vetala, MERCURY, Mango Sandstorm, TA450, MuddyKrill, and Boggy Serpens [1][3][5][8]. Active since at least 2017—with continuous operations spanning nearly a decade and confirmed activity in 113 countries across 48 industry sectors—the group conducts cyberespionage and disruptive operations in support of Iranian state interests, providing stolen data and accesses both to the Iranian government and to other malicious cyber actors [1][3][7][8]. Tradecraft emphasizes spear-phishing, living-off-the-land (LotL) techniques, PowerShell-based tooling, abuse of legitimate remote monitoring and management (RMM) tools, DLL side-loading, custom and commodity malware, and continuous retooling that renders static signature detection unreliable [3][4][7][8]. Recent campaigns (late 2025–early 2026), including Operation Olalampo, have incorporated Starlink-based C2, Telegram C2 channels, Rclone exfiltration to Wasabi, and multi-continent targeting of industrial/electronics manufacturing, defense-adjacent software suppliers, education, public sector, finance, and professional services—often with an Israel focus following regional military activity [1][4][5][7][19]. This dossier consolidates identity, attribution, ATT&CK-mapped TTPs, classified IOCs, infrastructure patterns, timeline, hunting guidance, mitigations, pivots, and gaps for detection, blocking, hunting, and investigation.

---

## 1. Identity, Aliases & Attribution

MuddyWater is widely assessed as an Iranian state-backed APT subordinate to, or part of, the Iranian Ministry of Intelligence and Security (MOIS) [1][3][5][8]. The moniker “MuddyWater” was coined by Palo Alto Networks in 2017 because early campaigns were difficult to attribute and frequently confused with other intrusion sets [3]. The group is tracked under MITRE ATT&CK group ID **G0069**; the MITRE page was created on 18 April 2018 and last modified on 12 May 2026 [1].

**Aliases (consolidated):** Earth Vetala, MERCURY, Static Kitten, Seedworm, TEMP.Zagros, Mango Sandstorm, TA450, MuddyKrill, Boggy Serpens [1][3].

**Mission and positioning:** The group’s purpose is cyberespionage and disruptive cyber operations supporting Iranian state interests [3]. Actors are positioned both to provide stolen data and network accesses to the Iranian government and to share them with other malicious cyber actors [8]. Broad cyber campaigns in support of MOIS objectives have been conducted since approximately 2018 [8]. Recent activity has been assessed as beginning in early February following U.S. and Israeli military strikes on Iran, with a software-company supplier to defense/aerospace industries (Israel presence) as a focus [5]. The group is one of the most persistently active Iranian threat actors, with over nine years of continuous operations, confirmed activity in 113 countries and 48 targeted industry sectors, and a pattern of prioritizing rapid operations over stealth—producing OPSEC mistakes that aid tracking [7].

**Target profile:** Since at least 2017, MuddyWater has targeted government and private organizations across telecommunications, local government, finance, defense, oil and natural gas, industrial and electronics manufacturing, education, public-sector, financial services, and professional services in the Middle East (notably UAE and Saudi Arabia), Asia, Africa, Europe, and North America [1][4][8]. In Q1 2026 alone, at least nine organizations across nine countries on four continents were affected; in February 2026 the group spent a week inside a major South Korean electronics manufacturer; activity has also been observed against an Israeli company customer environment [4][19].

---

## 2. Observed TTPs Mapped to MITRE ATT&CK

MuddyWater employs spear-phishing, exploitation of public vulnerabilities, LotL techniques, abuse of RMM tools, custom malware, dual-use utilities, commodity malware (including ransomware), and continuous retooling of malware variants, infrastructure, and delivery mechanisms in every major campaign [3][7]. Static signature-based detection is fundamentally unreliable against this actor due to continuous retooling [7]. The group has abused nine legitimate RMM tools for persistent remote access, including ScreenConnect, SimpleHelp, and Atera [3][7].

### Initial Access & Execution
| Technique | ATT&CK ID | Observation |
|-----------|-----------|-------------|
| Spearphishing Attachment | T1566.001 | Coax victims into downloading ZIP files containing Excel with malicious macro or PDF that drops a malicious file [8] |
| User Execution: Malicious File | T1204.002 | Same ZIP/Excel/PDF delivery chain [8] |
| External Remote Services / RDP | — | Initial access via Terminal Services/RDP login [19] |
| PowerShell | T1059.001 | Obfuscated PowerShell scripts; POWERSTATS backdoor runs PowerShell for persistent access; PowGoop uses obfuscated PowerShell [8] |
| Python | T1059.006 | Small Sieve Python backdoor distributed via NSIS installer [8] |
| Exploitation of Public-Facing Application / Privilege Escalation | — | Exploited CVE-2020-1472 (Microsoft Netlogon elevation of privilege) and CVE-2020-0688 (Microsoft Exchange memory corruption) [8] |

### Persistence, Privilege Escalation & Defense Evasion
| Technique | ATT&CK ID | Observation |
|-----------|-----------|-------------|
| Registry Run Keys / Startup Folder | T1547.001 | Small Sieve adds registry run key for persistence [8] |
| Bypass User Account Control | T1548.002 | Various UAC bypass techniques [1] |
| DLL Side-Loading | T1574.002 | PowGoop DLL loader renamed as Goopdate.dll; DLL side-loading via legitimately signed Fortemedia (fmapp.exe) and SentinelOne (sentinelmemoryscanner.exe) binaries to load malicious DLLs (fmapp.dll, sentinelagentcore.dll); also used in Operation Olalampo [4][8][19] |
| Obfuscated Files or Information | T1027 | PowerShell obfuscation; Small Sieve custom hex byte swapping and Base64 [8] |
| Data Obfuscation: Junk Data | T1001.001 | Mori backdoor includes junk data [8] |
| Data Encoding: Non-Standard Encoding | T1132.002 | Small Sieve hex byte swapping + Base64 [8] |

### Discovery & Credential Access
| Technique | ATT&CK ID | Observation |
|-----------|-----------|-------------|
| Account Discovery: Domain Account | T1087.002 | cmd.exe `net user /domain` to enumerate domain users [1] |
| Credential Access (browser) | — | Malicious DLLs embed ChromElevator to siphon passwords, cookies, and payment card data from Chromium-based browsers, bypassing App-Bound Encryption [4] |

### Command and Control & Exfiltration
| Technique | ATT&CK ID | Observation |
|-----------|-----------|-------------|
| Application Layer Protocol: Web Protocols | T1071.001 | Small Sieve uses Telegram API over HTTPS; Mori uses HTTP over IPv4/IPv6; Canopy/Starwhale HTTP POST [8] |
| Protocol Tunneling | T1572 | Mori communicates via DNS tunneling [8] |
| Acquire Infrastructure: Domains | T1583.001 | Established domains, some spoofing legitimate domains [1] |
| Telegram-based C2 | — | Introduced Telegram-based C2 channel in Operation Olalampo (previously undocumented in group tradecraft); Small Sieve Telegram beacons/taskings [7][8] |
| Satellite internet C2 | — | Late 2025 and early 2026: commercial satellite internet (Starlink) for C2 [1] |
| SSH reverse tunnels | — | OpenSSH with no host key checking and remote port forwarding [19] |
| Cloud storage exfil | — | Attempted data exfiltration using Rclone utility to a Wasabi cloud storage bucket [5] |

### Malware & Tooling Ecosystem
- **PowGoop:** Main loader—DLL loader renamed Goopdate.dll for side-loading + obfuscated PowerShell [8]
- **Small Sieve:** Python backdoor via NSIS installer; Telegram C2 [8]
- **Mori:** DNS tunneling + HTTP (IPv4/IPv6) with junk-data obfuscation [8]
- **POWERSTATS:** PowerShell backdoor for persistent access [8]
- **Canopy/Starwhale:** Sends collected data via HTTP POST [8]
- **Fakeset backdoor:** Digital certificate also used to sign Stagecomp and Darkcomp malware previously linked to MuddyWater; Microsoft/Kaspersky signatures Trojan:Python/MuddyWater.DB!MTB and Backdoor.Python.MuddyWater.a associate Stagecomp/Darkcomp with MuddyWater [5]
- **ChromElevator** embedded in malicious DLLs for browser data theft [4]
- Dual-use: Rclone, OpenSSH, 9 legitimate RMM tools, commodity malware including ransomware [5][7][19]

---

## 3. Infrastructure Patterns & Classified IOCs

### Infrastructure Patterns
- **Domain infrastructure:** Preference for NameCheap and Hosterdaddy Private Limited (AS136557); some domains spoof legitimate brands; domain reuse dating back to October 2025 [1]
- **C2 diversity:** Traditional VPS IPs; Telegram API over HTTPS; DNS tunneling; Starlink commercial satellite internet (late 2025–early 2026); Wasabi cloud storage buckets for exfil staging [1][5][8]
- **Code-signing & shared artifacts:** Shared digital certificates linking Fakeset, Stagecomp, and Darkcomp [5]
- **OPSEC:** Rapid operations produce mistakes enabling tracking; continuous retooling of infrastructure configurations per major campaign [7]
- **RMM abuse:** Nine legitimate RMM tools for persistent remote access [7]

### IOCs Classified for Operational Use

**BLOCK (network / endpoint deny-list priority)**  
| Indicator | Type | Context | Source |
|-----------|------|---------|--------|
| 157.20.182.49 | IP | C2 used by malicious DLL (FMAPP.dll) | [4][19] |
| 162.0.230.185 | IP | SSH activity | [19] |
| 88.119.170.124 | IP | Canopy/Starwhale HTTP POST exfil destination | [8] |
| 5.199.133.149, 45.142.213.17, 45.142.212.61, 45.153.231.104, 46.166.129.159, 80.85.158.49, 87.236.212.22, 88.119.171.213, 89.163.252.232, 95.181.161.49, 95.181.161.50, 164.132.237.65, 185.25.51.108, 185.45.192.228, 185.117.75.34, 185.118.164.21, 185.141.27.143, 185.141.27.248, 185.183.96.7, 185.183.96.44, 192.210.191.188, 192.210.226.128 | IPs | Documented MuddyWater-associated addresses | [8] |
| SHA-256 b75208393fa17c0bcbc1a07857686b8c0d7e0471d00a167a07fd0d52e1fc9054 (MD5 15fa3b32539d7453a9a85958b77d4c95; SHA-1 11d594f3b3cf8525682f6214acb7b7782056d282) | File hash | Small Sieve NSIS installer gram_app.exe | [8] |
| SHA-256 bf090cf7078414c9e157da7002ca727f06053b39fa4e377f9a0050f2af37d3a2 (MD5 5763530f25ed0ec08fb26a30c04009f1; SHA-1 2a6ddf89a8366a262b56a251b00aafaed5321992) | File hash | Small Sieve backdoor index.exe | [8] |
| fmapp.dll; sentinelagentcore.dll | Filenames | Malicious sideloaded DLLs | [4] |

**HUNT (behavioral / telemetry hunting; do not purely block without context)**  
| Indicator / Pattern | Type | Context | Source |
|---------------------|------|---------|--------|
| asuedulimit | SSH username | Observed with MuddyWater SSH reverse tunnels | [19] |
| fmapp.exe loading fmapp.dll; sentinelmemoryscanner.exe loading sentinelagentcore.dll | Process/DLL load | Legitimate signed binaries (Fortemedia, SentinelOne) used for DLL side-loading | [4][19] |
| %AppData%\OutlookMicrosift\index.exe | Path | Small Sieve install path (note typo “Microsift”) | [8] |
| HKCU\Software\Microsoft\Windows\CurrentVersion\Run\OutlookMicrosift | Registry | Small Sieve persistence run key | [8] |
| %LocalAppData%\MicrosoftWindowsOutlookDataPlus.txt | Path | Small Sieve Telegram session file | [8] |
| OpenSSH with no host-key checking + remote port forwarding | Process cmdline | SSH reverse tunnel establishment | [19] |
| Rclone → Wasabi cloud storage | Process / network | Attempted exfiltration from software company | [5] |
| ScreenConnect, SimpleHelp, Atera (and other RMMs) | Process / network | Abuse of legitimate RMM for persistence (9 tools total) | [3][7] |
| Telegram API over HTTPS from non-standard hosts/processes | Network | Small Sieve / Olalampo Telegram C2 | [7][8] |
| Starlink-associated egress for C2 | Network | Late 2025–early 2026 C2 pattern | [1] |
| Domain registration via NameCheap or Hosterdaddy (AS136557); spoofed legitimate-looking domains | Infra | Preferred registrars / ASN; domain reuse from Oct 2025 | [1] |
| `net user /domain` via cmd.exe | Process cmdline | Domain user enumeration | [1] |
| Trojan:Python/MuddyWater.DB!MTB; Backdoor.Python.MuddyWater.a | AV signatures | Stagecomp / Darkcomp / MuddyWater-linked Python malware | [5] |

**FORENSICS-ONLY (context, timeline reconstruction, attribution—not primary block/hunt alone)**  
| Artifact | Context | Source |
|----------|---------|--------|
| gram_app.exe compile time 2021-09-25 21:57:46 UTC; index.exe compile time 2021-08-01 04:39:46 UTC | Small Sieve build timestamps | [8] |
| Shared digital certificate across Fakeset, Stagecomp, Darkcomp | Attribution linkage when Stagecomp/Darkcomp not present on host | [5] |
| Operation Olalampo campaign labeling / first-observed Jan 2026 | Campaign correlation | [7] |
| Prior Group-IB documentation of fmapp.exe side-loading in Olalampo | Historical linkage | [4][7] |

---

## 4. Operational Timeline & Major Campaigns

| Period | Activity |
|--------|----------|
| 2017 onward | Continuous operations; Palo Alto names group MuddyWater; targeting begins across Middle East, Asia, Africa, Europe, North America [1][3][7] |
| ~2018 | Broad cyber campaigns in support of MOIS objectives [8] |
| 18 Apr 2018 | MITRE ATT&CK G0069 page created [1] |
| Aug–Sep 2021 | Small Sieve components compiled (index.exe 2021-08-01; gram_app.exe 2021-09-25) [8] |
| Oct 2025 – Mar 2026 | At least three distinct campaigns; domain reuse from October 2025; continuous retooling with previously undocumented malware variants and commodity malware [1][7] |
| Late 2025 – early 2026 | Use of commercial satellite internet (Starlink) for C2 [1] |
| Jan 2026 | Operation Olalampo first observed; Telegram-based C2 introduced; fmapp.exe DLL side-loading documented by Group-IB [4][7] |
| Early Feb 2026 | Campaign assessed to begin following U.S. and Israeli military strikes on Iran; targeting of defense/aerospace supplier software company with Israel presence; Rclone→Wasabi exfil attempt [5] |
| Feb 2026 | Week-long presence inside major South Korean electronics manufacturer [4] |
| Q1 2026 | Campaign affecting ≥9 organizations across 9 countries / 4 continents (industrial/electronics manufacturing, education, public-sector, financial services, professional services); DLL side-loading with ChromElevator credential theft [4] |
| 4 Mar 2026 | Hunt.io publishes Iranian-linked APT infrastructure indicators; Huntress conducts retroactive hunt across customer signals [19] |
| 12 May 2026 | MITRE ATT&CK MuddyWater page last modified [1] |

---

## 5. Hunting Queries, Detection Logic & Mitigations

### Hunting Queries (derived strictly from documented TTPs/IOCs)

**Sigma-style (DLL side-loading / suspicious process loads)**  
```yaml
title: MuddyWater DLL Side-Loading via Fortemedia or SentinelOne Binaries
status: experimental
logsource:
  product: windows
  category: image_load
detection:
  selection_fmapp:
    Image|endswith: '\fmapp.exe'
    ImageLoaded|endswith: '\fmapp.dll'
  selection_sentinel:
    Image|endswith: '\sentinelmemoryscanner.exe'
    ImageLoaded|endswith: '\sentinelagentcore.dll'
  condition: selection_fmapp or selection_sentinel
level: high
# Context: [4][19]
```

**Sigma-style (Small Sieve persistence artifacts)**  
```yaml
title: MuddyWater Small Sieve Persistence Path and Run Key
logsource:
  product: windows
  category: registry_event  # also file_event for path
detection:
  selection_reg:
    TargetObject|contains: '\Software\Microsoft\Windows\CurrentVersion\Run\OutlookMicrosift'
  selection_path:
    TargetFilename|contains: '\OutlookMicrosift\index.exe'
  condition: selection_reg or selection_path
# Context: [8]
```

**KQL (Microsoft Sentinel / Defender) – C2 IPs and SSH username**  
```kusto
// Network connections to known MuddyWater C2 / infra IPs [4][8][19]
DeviceNetworkEvents
| where RemoteIP in (
    "157.20.182.49","162.0.230.185","88.119.170.124",
    "5.199.133.149","45.142.213.17","45.142.212.61","45.153.231.104",
    "46.166.129.159","80.85.158.49","87.236.212.22","88.119.171.213",
    "89.163.252.232","95.181.161.49","95.181.161.50","164.132.237.65",
    "185.25.51.108","185.45.192.228","185.117.75.34","185.118.164.21",
    "185.141.27.143","185.141.27.248","185.183.96.7","185.183.96.44",
    "192.210.191.188","192.210.226.128"
)
| project Timestamp, DeviceName, InitiatingProcessFileName, RemoteIP, RemotePort, ActionType

// SSH reverse tunnel indicators [19]
DeviceProcessEvents
| where FileName in ("ssh.exe","sshd.exe")
    and (ProcessCommandLine has "-R" or ProcessCommandLine has "StrictHostKeyChecking=no"
         or ProcessCommandLine has "asuedulimit")
```

**KQL – Domain enumeration LotL**  
```kusto
DeviceProcessEvents
| where FileName =~ "cmd.exe"
    and ProcessCommandLine has_all ("net","user","/domain")
// Maps to T1087.002 [1]
```

**KQL – Rclone / Wasabi exfil and RMM abuse**  
```kusto
DeviceProcessEvents
| where FileName =~ "rclone.exe"
    or ProcessCommandLine has "wasabi"
// [5]
DeviceProcessEvents
| where FileName in~ ("ScreenConnect.ClientService.exe","SimpleHelp","AteraAgent.exe")
    or InitiatingProcessFileName in~ ("ScreenConnect.ClientService.exe","AteraAgent.exe")
// RMM abuse context [3][7] — tune to environment baseline
```

**Splunk SPL – Hash and path hunt**  
```spl
index=endpoint (hash_sha256="b75208393fa17c0bcbc1a07857686b8c0d7e0471d00a167a07fd0d52e1fc9054"
  OR hash_sha256="bf090cf7078414c9e157da7002ca727f06053b39fa4e377f9a0050f2af37d3a2"
  OR file_path="*\\OutlookMicrosift\\index.exe"
  OR file_path="*\\MicrosoftWindowsOutlookDataPlus.txt")
// Small Sieve [8]
```

**Behavioral hunt themes (prioritize over pure IOCs given continuous retooling [7]):**  
1. Legitimate signed binaries (fmapp.exe, sentinelmemoryscanner.exe, googledate-style Goopdate.dll) loading unexpected DLLs from non-standard paths [4][8][19]  
2. PowerShell with heavy obfuscation establishing outbound HTTPS to Telegram API endpoints or atypical C2 [8]  
3. New RMM agent installs (especially ScreenConnect, SimpleHelp, Atera) outside change-management windows [3][7]  
4. SSH with remote port forwarding and disabled host-key checking from servers that do not normally run OpenSSH clients [19]  
5. Rclone or similar sync tools writing to Wasabi or other object storage from endpoints that are not backup infrastructure [5]  
6. DNS tunneling / high-entropy DNS or dual-stack HTTP C2 consistent with Mori [8]  
7. Egress via Starlink/satellite providers from enterprise networks that do not use satellite as primary connectivity [1]

### Recommended Mitigations
- Search environments for the indicators of compromise listed above [8]  
- Enable and keep current antivirus / anti-malware signature definitions [8]  
- Patch operating systems, software, and firmware promptly, prioritizing known exploited vulnerabilities (including historically exploited CVE-2020-1472 and CVE-2020-0688) [8]  
- Train users to recognize and report phishing and social engineering; run awareness simulations [8]  
- Enforce multi-factor authentication (especially webmail, VPN, and accounts accessing critical systems) and limit administrator privileges [8]  
- Deploy application control / allow-listing to restrict which applications and executable code users can run—critical against LotL, RMM abuse, and side-loading [8]  
- Because static signatures are unreliable against continuous retooling, emphasize behavioral detection, application control, and rapid IOC hunting over sole reliance on AV signatures [7][8]

### Pivot Points for Investigation
- Group-IB reporting on Operation Olalampo (SSH IP IOC, fmapp.exe side-loading) [4][7][19]  
- Hunt.io blog (4 March 2026) Iranian-linked APT infrastructure indicators used for retroactive hunts [19]  
- Shared digital certificates linking Fakeset ↔ Stagecomp ↔ Darkcomp [5]  
- Domain registration patterns: NameCheap, Hosterdaddy Private Limited (AS136557), spoofed legitimate domains, reuse from October 2025 [1]  
- Additional public resources: Malware Analysis Report MAR-10369127-1.v1; CISA Iran Cyber Threat Overview and Advisories; NCSC-UK MAR on Small Sieve; CNMF press release on Iranian intel cyber suite of malware [8]  
- Microsoft / Kaspersky detection names Trojan:Python/MuddyWater.DB!MTB and Backdoor.Python.MuddyWater.a [5]  
- RMM tool installation telemetry and Telegram API traffic from unexpected processes [3][7][8]

---

## Intelligence Gaps

- **Exfiltration success unknown:** It is not known whether the Rclone-to-Wasabi data exfiltration attempt against the targeted software company succeeded [5].  
- **Partial implant visibility:** Stagecomp and Darkcomp were not observed on the targeted U.S. company networks; attribution relied on shared digital certificates rather than on-host malware presence—leaving uncertainty about full tool deployment scope [5].  
- **Incomplete RMM inventory:** The group has abused nine legitimate RMM tools, but only ScreenConnect, SimpleHelp, and Atera are named in the available material; the remaining six tools are unspecified [3][7].  
- **Starlink C2 operational details sparse:** Use of commercial satellite internet for C2 in late 2025/early 2026 is confirmed, but terminal types, how Starlink connectivity was obtained, beaconing patterns, and detection heuristics beyond “satellite egress” are not detailed [1].  
- **Domain and certificate corpus incomplete:** Preference for NameCheap/Hosterdaddy (AS136557) and domain reuse from October 2025 are noted, but a full list of active or historical spoofed domains and certificate serials/thumbprints is not provided in the learnings [1][5].  
- **Telegram C2 novelty vs. depth:** Telegram-based C2 in Operation Olalampo is described as previously undocumented for the group, yet full protocol, bot IDs, channel identifiers, and tasking formats beyond Small Sieve’s hex-swap/Base64 scheme are not fully specified [7][8].  
- **Ransomware/commodity malware specifics:** Commodity malware including ransomware is cited as part of the toolkit, but family names, deployment conditions, and whether ransomware is used for disruption, distraction, or monetization are not elaborated [7].  
- **Post-compromise dwell and lateral movement depth:** Specific lateral-movement techniques beyond domain user enumeration, RDP initial access, and SSH tunneling are under-specified relative to the group’s multi-week presence (e.g., South Korean electronics manufacturer) [1][4][19].  
- **Victimology completeness for 2026:** Q1 2026 affected “at least nine” organizations across nine countries; full victim list, exact sectors per country, and whether destructive components were used remain incomplete [4].  
- **Linkage confidence across aliases:** While aliases are consolidated, the learnings do not detail which clusters (e.g., Boggy Serpens vs. Mango Sandstorm) map to which campaigns or tooling generations [1][3].

## Gaps

- unverified claims removed

---

## Sources

[1] MuddyWater, Earth Vetala, MERCURY, Static Kitten, Seedworm, … — https://attack.mitre.org/groups/G0069/  
[2] MITRE ATT&CK v11 - a small update that can help (not just) with … — https://isc.sans.edu/diary/28590  
[3] MuddyWater (hacker group) - Wikipedia — https://en.wikipedia.org/wiki/MuddyWater_(hacker_group)  
[4] MuddyWater Uses DLL Side-Loading in Espionage Campaign … — https://thehackernews.com/2026/05/muddywater-uses-dll-side-loading-in.html  
[5] Iran-Linked MuddyWater Hackers Target U.S. Networks With New … — https://thehackernews.com/2026/03/iran-linked-muddywater-hackers-target.html  
[6] Muddy Water Kava - Authentic Kava in St. Petersburg, FL - (727) 520 … — https://www.mwkava.com/  
[7] MuddyWater APT Group | Iranian Cyber Espionage Profile — https://www.group-ib.com/masked-actors/muddywater/  
[8] Iranian Government-Sponsored Actors Conduct Cyber Operations — https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-055a  
[9] Muddy Water Kava, Saint Petersburg - Restaurantji — https://www.restaurantji.com/fl/saint-petersburg/muddy-water-kava-/  
[10] Sigma Rules Search Engine for Threat Detection, Threat Hunting, … — http://socprime.com  
[11] GitHub - wortell/KQL: KQL queries for Advanced Hunting — https://github.com/wortell/KQL  
[12] Microsoft – AI, Cloud, Productivity, Computing, Gaming & Apps — https://www.microsoft.com/en-us?msockid=3a755eae60256eb72414493861b96f98  
[13] Top 23 Siem Open-Source Projects | LibHunt — https://www.libhunt.com/topic/siem  
[14] GitHub - rev10d/KQL: KQL queries for Advanced Hunting — https://github.com/rev10d/KQL  
[15] Office 365 login — https://www.office.com/  
[16] Microsoft - Wikipedia — https://en.wikipedia.org/wiki/Microsoft  
[17] Create your Microsoft account — https://signup.live.com/  
[18] Microsoft Outlook Personal Email and Calendar | Microsoft 365 — https://www.outlook.com/  
[19] Unmasking an Attack Chain of MuddyWater | Huntress — https://www.huntress.com/blog/muddywater-attack-chain  

---

## Metadata

- **Model:** xai/grok-4.5-latest (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 10m 18s
- **Depth reached:** 4
- **Sources read:** 19
- **Learnings:** 214
- **Verified learnings:** 85
- **Prompt tokens:** 135957
- **Completion tokens:** 84646