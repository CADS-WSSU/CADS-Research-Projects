# Produce a full hunt-ready dossier on actor "Ababil of Minab". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity. Add the groups beliefs and reason for existing/fighting/doing what they do



## Summary Paragraph

Ababil of Minab is a pro-Iranian threat actor that emerged in late March 2026, presenting itself as a hacktivist group but demonstrating strong forensic and operational ties to Iran’s Ministry of Intelligence and Security (MOIS) through infrastructure and TTP overlap with the previously identified Black Shadow cluster [6][11][16]. The actor has claimed responsibility for destructive intrusions against targets in the United States (including LA Metro/LACMTA), Israel, Saudi Arabia, and Turkey, with a focus on maximizing psychological impact through exaggerated claims of data exfiltration and destruction [11][19]. Ababil of Minab employs a mature tradecraft involving credential theft, lateral movement, data staging via web roots, encrypted exfiltration using custom tools (FileFiend/Exchangedb.exe), and multi-stage destruction of virtualized environments, databases, and backups [6][11][19]. The group leverages Telegram for amplification and uses open, long-lived staging infrastructure (notably 5.255.127[.]55 in the Netherlands) to host exfiltrated data [11]. While asserting independent hacktivist motives, evidence indicates state sponsorship or direction, with potential alignment to broader Iranian influence operations, including possible targeting of events like the World Cup [16][19]. Key IOCs include specific file hashes, staging server IPs, and behavioral patterns such as sequential RAR chunk downloads, enabling effective hunting and detection [11].

## Identity & Attribution

- **Primary Alias**: Ababil of Minab (also referenced as "Ababil of Minab" in Telegram claims and public attributions) [6][11][16][19]
- **Attribution**: Forensic evidence links the actor to infrastructure and activity previously attributed by Israel’s National Cyber Directorate (INCD) to Iran’s Ministry of Intelligence and Security (MOIS), specifically overlapping with the Black Shadow cluster [6][11]. Insikt Group tracks the likely operator as ION-87, an Iran state-sponsored threat actor [16].
- **Nature of Actor**: Not a standalone hacktivist crew as claimed; represents a persona or front used by state-linked operators to conduct and amplify attacks [6][11][16]. The naming is tied to wartime symbolism, referencing the February 28, 2026, bombing of Shajareh Tayyebeh Elementary School in Minab, Iran, where 168 civilians were killed [16].
- **Beliefs and Motivations**: Aims to undermine confidence in critical services, generate disproportionate media coverage, and force organizations into costly defensive postures through psychological operations, including exaggerating impact (e.g., claiming 4 TB exfiltrated, 250 TB wiped) [11][19]. Motivated by Iranian malign influence operations, potentially targeting high-visibility events like the World Cup [16].

## Observed TTPs Mapped to MITRE ATT&CK

- **T1102 (Web Service)**: Staged victim data in the victim's own web root and retrieved remotely using Axel over HTTP [11].
- **T1048 (Exfiltration Over Alternative Protocol)**: Used custom Flask-based receiver (http.flask.py) with AES-CBC encryption for chunked file uploads over HTTPS on port 443 [11].
- **T1560.001 (Archive via Utility)**: Created multi-part RAR archives on victim systems and used 7-Zip on staging server for data aggregation [11].
- **T1036.005 (Masquerading: Match Legitimate Name or Location)**: Disguised FileFiend malware as Exchangedb.exe to mimic a legitimate Microsoft Exchange utility [11].
- **T1059.003 (Command and Scripting Interpreter: Windows Command Shell)**: Utilized .bash_history on staging server and Python scripts (main.py) for database enumeration and lateral movement [11][19].
- **T1021.002 (Remote Services: SMB/Windows Admin Shares)**: Demonstrated lateral access across multiple SQL Server instances (serverb0–serverb7) in Vyncs environment [19].
- **T1083 (File and Directory Discovery)**: Enumerated databases and file systems on victim systems, including ASP.NET source code and configuration files [19].
- **T1485 (Data Destruction)**: Performed destructive operations across IT, applications, virtualization, and backups: deleted VMs, databases, storage volumes via scripts and hands-on-keyboard; combined techniques to deny recovery [6][11]. Observed actions include SQL Server database deletion, file system destruction via Windows Explorer, and VM partition wipes via Disk Management [11].
- **T1566.002 (Phishing: Spearphishing Link)**: Likely initial vector, though not explicitly detailed in learns; implied by access to web.config and API keys [19].
- **T1078 (Valid Accounts)**: Implied by use of compromised credentials for SQL Server and application access; mitigation includes credential rotation [19].
- **T1057 (Process Discovery)**: Identified via hunting for Exchangedb.exe processes not tied to legitimate Exchange [11].
- **T1041 (Exfiltration Over C2 Channel)**: Behavioral signature includes sequential download of data.part1.rar, data.part2.rar from staging server [11].
- **T1105 (Ingress Tool Transfer)**: Custom exfiltration tooling (FileFiend/Exchangedb.exe) recovered and deployed on victim systems [6][11].
- **T1566.001 (Phishing: Spearphishing Attachment)**: Not explicitly observed but consistent with Iranian TTPs; inferred from script execution (main.py) from Downloads directory [19].
- **T1090 (Proxy)**: Use of staging infrastructure as relay for C2 and exfiltration [11].
- **T1562.001 (Impair Defenses: Disable or Modify Tools)**: Destruction of backups and logs to impede recovery and forensics [6].

## IOCs Classified

### Block (Network/Endpoint Prevention)
- **IP**: 5.255.127[.]55 (Staging server, Netherlands, AS60404) – Block outbound connections [11]
- **Domain**: nefeshhope[.]com (associated with secondary staging) [11]
- **TLS Certificate Subject**: Contains `acmecloud.example` (hardcoded in Flask receiver) – Block/alert on outbound HTTPS to port 443 with this subject [11]
- **File Name**: Exchangedb.exe (when not associated with legitimate Exchange) – Block execution [11][19]
- **Process**: FileFiend variants (executables masquerading as legitimate tools) – Block via EDR [11]

### Hunt (Behavioral/Anomaly Detection)
- **SHA-256 Hashes**:
  - 81a25357d027d0f04a43139377d5d58384b8e9b0770e699cdcc37e600641cf90 (FileFiend/Exchangedb.exe Variant 1) [11]
  - (Two additional FileFiend hashes implied but not fully specified in learns; hunt for all three as referenced) [11]
- **Behavioral**:
  - Sequential multi-part RAR downloads (data.part1.rar, data.part2.rar) in web access logs – Clearest exfiltration signature [11]
  - HTTP 200 on port 8020 (SimpleHTTP/Python) and Apache on port 8087 from staging IP – Indicates active data staging [11]
  - SASL/SCP transfers to 31.172.87[.]20 (secondary staging tied to nefeshhope[.]com) [11]
  - Python Script (main.py) using pyodbc to connect to SQL Server instances in 74.112.202.x–203.x range – Indicates lateral DB access [19]
  - Presence of Vyncs source code, SSL certificates, and web.config in E:\myvyncs or similar paths – Indicates deep application access [19]
  - Archive creation: multi-part RAR on victims, 7-Zip on server – T1560.001 hunting via process/monitor [11]
  - Web root staging of sensitive data (backups, configs) – Monitor for abnormal file placement [11]
  - Telegram channel monitoring for Ababil of Minab claims – Correlate with intrusion timelines [19]

### Forensics-Only (Post-Compromise Analysis)
- **.bash_history** from staging server (5.255.127[.]55) – Confirms exfiltration methods and tool usage [11]
- **FileFiend/Exchangedb.exe** artifacts (strings, PDB paths, compilation timestamps) – For malware reverse engineering [11]
- **Accz.7z (renamed from accz.zip)** – Contains 'accz' abbreviation pointing to unconfirmed organization; requires contextual analysis [11]
- **Deleted VM snapshots, database logs, backup catalogs** – To reconstruct destruction scope [6]
- **Telegram channel metadata** – For operator attribution and timing correlation [19]
- **Web server access/error logs** from victim web roots – To identify staging and retrieval timing [11]
- **SQL Server audit logs** – To trace pyodbc connections and database enumeration [19]
- **Disk Management and VSS snapshot traces** – To confirm VM/wipe operations [11]

## Infrastructure Patterns

- **Staging Server**: Long-lived, openly accessible HTTP/FTP services on non-standard ports (8020, 8087) hosted in the Netherlands (AS60404) [11]
- **Use of Legitimate Services**: Abuse of Python SimpleHTTP, Apache HTTPD, and SCP for data hosting and transfer – Designed to blend with benign traffic [11]
- **Encrypted Chunked Uploads**: Custom Flask receiver (http.flask.py) accepting AES-CBC encrypted chunks over HTTPS (443) – Avoids standard DLP triggers [11]
- **Multi-Part Archiving**: Reliance on RAR/7-Zip for data segmentation and reassembly – Enables stealthy exfiltration under size limits [11]
- **Secondary Staging**: IP 31.172.87[.]20 used for SCP transfers, linked to nefeshhope[.]com infrastructure [11]
- **Duration**: Infrastructure remained active for weeks after public reporting and actor silence on Telegram – Suggests possible reuse or lax OPSEC [11]
- **Geography**: Hosting in EU/NL likely chosen for permissive hosting and proximity to targets; no evidence of fast-flux or bulletproof hosting [11]

## Timeline of Activity

- **February 28, 2026**: Bombing of Shajareh Tayyebeh Elementary School in Minab, Iran – 168 civilians killed; becomes symbolic reference for actor naming [16]
- **Late March 2026**: Ababil of Minab persona surfaces publicly, claiming intrusions against US, Israeli, Saudi, and Turkish targets [6][11]
- **Early April 2026**: Claims responsibility for LA Metro (LACMTA) intrusion, destruction, and exfiltration [6]
- **April 2026**: Insikt Group reports Ababil of Minab as new hacktivist persona likely tied to ION-87 (Iran state-sponsored) [16]
- **April 28, 2026**: HTTP 200 observed on 5.255.127[.]55:8020 (Python SimpleHTTP directory listing) [11]
- **May 4, 2026**: Apache HTTPD service activated on port 8087 of same host – Likely for web access to staged data [11]
- **May 16, 2026**: Directory snapshot captured – 2,238 files, 545 subdirs, ~5 GB of data archived from staging server [11]
- **May 26, 2026**: Gambit Security publishes report detailing intrusion activity; staging IP (5.255.127[.]55) not disclosed in report [11]
- **Post-May 26, 2026**: Staging server remained active through at least late May 2026, weeks after report and after actor went quiet on Telegram [11]
- **Ongoing**: Potential reuse of infrastructure or TTPs in future operations, especially aligned with Iranian influence cycles (e.g., World Cup) [16]

## Hunting Queries

### Sigma (Sysmon/Windows)
```yaml
title: Potential FileFiend/Exchangedb.exe Execution
id: 3f1a2b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c
status: experimental
description: Detects execution of Exchangedb.exe not associated with legitimate Microsoft Exchange
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    Image:
      - '*\Exchangedb.exe'
    OriginalFileName:
      - 'Exchangedb.exe'
  condition: selection and not (Image contains 'Microsoft Exchange' or Image contains '\\Exchange\\')
fields:
  - Image
  - ParentImage
  - CommandLine
  - User
falsepositives:
  - Legitimate Exchange Server utilities
level: high
```

```yaml
title: Sequential Multi-Part RAR Download from Staging Infrastructure
id: 8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d
status: experimental
description: Detects behavioral signature of pull-based exfiltration (data.part1.rar followed by data.part2.rar)
logsource:
  product: http
  service: proxy/web
detection:
  selection:
    url:
      - '*data.part1.rar'
      - '*data.part2.rar'
    status: 200
  condition: selection
  timeframe: 5s
  aggregation:
    - count by url_stem, src_ip, dest_ip
    - having count >= 2
fields:
  - src_ip
  - dest_ip
  - url
  - timestamp
falsepositives:
  - Legitimate software update mechanisms using multi-part archives
level: medium
```

### KQL (Azure Sentinel / Microsoft Defender)
```kql
// Hunt for Exchangedb.exe not on Exchange servers
DeviceProcessEvents
| where FileName == "Exchangedb.exe"
| where not(AdditionalFields has "Microsoft Exchange" or FolderPath contains @"\Exchange\")
| project TimeGenerated, DeviceName, FileName, FolderPath, CommandLine, InitiatingProcessFileName
| order by TimeGenerated desc
```

```kql
// Detect sequential RAR chunk downloads from known malicious IP
DeviceNetworkEvents
| where RemoteIP == "5.255.127.55" and RemotePort in (8020, 8080, 8080, 443)
| where RemoteUrl endswith ".rar"
| sort by Timestamp
| extend Part = extract(@"data.part(\d+)\.rar", 1, RemoteUrl)
| where isnotnull(Part)
| summarize Makespan() = max(Timestamp) - min(Timestamp), PartList = make_set(Part) by DeviceName, RemoteIP
| where array_length(PartList) >= 2 and PartList has "1" and PartList has "2"
| project DeviceName, RemoteIP, PartList, Timestamp
```

```kql
// Detect pyodbc usage from non-SQL servers (lateral movement)
DeviceProcessEvents
| where FileName has "python" and CommandLine has "pyodbc"
| where not(AdditionalFields has "SQL Server" or FolderPath contains @"\Program Files\Microsoft SQL Server\")
| project TimeGenerated, DeviceName, FileName, CommandLine, InitiatingProcessFileName
| order by TimeGenerated desc
```

### Splunk SPL
```spl
index=wineventlog sourcetype=Microsoft-Windows-Sysmon/Operational EventID=1 (Image="*\\Exchangedb.exe" OR OriginalFileName="Exchangedb.exe") NOT (Image="*\\Exchange\\*" OR OriginalFileName="*Microsoft Exchange*")
| table _time, host, Image, CommandLine, User
| sort -_time
```

```spl
index=proxy sourcetype=cisco:wsd OR sourcetype=squid:access
(dest_ip=5.255.127.55 OR dest_ip=31.172.87.20) uri_path="*data.part*.rar" status=200
| eval part=match(uri_path, "data.part(\\d+)\\.rar")
| where isnumber(part)
| stats values(part) as parts, dc(part) as part_count by src_ip, dest_ip, _time span=5m
| where part_count>=2 AND mvfind(parts, "1")!=0 AND mvfind(parts, "2")!=0
| table _time, src_ip, dest_ip, parts
```

## Mitigations

- **Credential Security**: Rotate all credentials for systems where Web.config, running-config, or connection string files were accessible; enforce phishing-resistant MFA (FIDO2) for admin, API, and platform access [11][19]
- **Backup Hardening**: Ensure database backups are never stored in or accessible from web root; avoid naming conventions that expose server/instance details [11]
- **Application Security**: Audit application-layer and API access; review API keys, connected accounts, and active sessions for unauthorized use [19]
- **Network Controls**: Block or alert on outbound HTTPS (443) connections to server-class machines where TLS subject contains `acmecloud.example` [11]; enforce egress filtering and proxy authentication for SCP/SSH to known bad IPs (5.255.127.55, 31.172.87.20) [11]; review DDoS mitigations and rate limiting on public-facing APIs [19]
- **Endpoint Protection**: Deploy EDR with behavioral blocking for masqueraded executables (e.g., Exchangedb.exe); enable script blockling for unauthorized Python/pyodbc usage [11][19]
- **Log Monitoring**: Monitor web access logs for sequential RAR chunk downloads; audit Windows Event Logs for suspicious service creations (e.g., Apache on 8087) and Disk Management usage [11][19]
- **Deception & Detection**: Deploy honeytokens in web roots and config files to detect staging and exfiltration attempts [11]; use canary credentials for SQL Server and application access [19]
- **User Training**: Increase awareness of phishing lures impersonating trusted entities (e.g., Vyncs support) during incident recovery [19]

## Pivot Points

- **Infrastructure**: 
  - Pivot from 5.255.127.55 to associated domains (nefeshhope[.]com) and secondary IP (31.172.87.20) [11]
  - Investigate AS60404 (Netherlands) for other hosting linked to Iran-linked clusters [11]
- **Malware**: 
  - Hash 81a25357d027d0f04a43139377d5d58384b8e9b0770e699cdcc37e600641cf90 → search VirusTotal, hybrid analysis for linked samples or C2 configs [11]
  - Analyze FileFiend strings for hardcoded C2, encryption keys, or victim IDs [11]
- **Victimology**: 
  - From claimed targets (LA Metro, Vyncs, Israeli/Turkish orgs) → assess shared technologies (e.g., SQL Server, ASP.NET, web-centric infra) [6][11][19]
  - Focus on organizations with public-facing web apps and database backups in accessible locations [11]
- **TTPs**: 
  - Use of Axel for retrieval → hunt for Axel usage in web server logs [11]
  - Multi-part RAR → monitor for WinRAR/7-Zip command lines with suspicious switches (e.g., -v for volume splitting) [11]
  - pyodbc usage → correlate with abnormal SQL Server connection strings or login times [19]
- **Operator**: 
  - Telegram channel analysis for Ababil of Minab → correlate posting times with intrusion events [19]
  - Linguistic and timing analysis of claims for IRGC-affiliated patterns [16][19]
- **Symbolism**: 
  - "Minab-168" naming → pivot to Iranian state media coverage of the school bombing and World Cup messaging [16]
  - Monitor for reuse of "Ababil" or similar avian/martyr-themed personas in future operations [16]

## Intelligence Gaps

- **Attribution Certainty**: While forensic ties to MOIS/Black Shadow are strong, no direct evidence (e.g., defector testimony, SIGINT) confirms Ababil of Minab as an official IRGC/MOIS unit; remains assessed as likely state-sponsored proxy [6][11][16]
- **Actual Impact vs. Claims**: The claimed exfiltration (4 TB) and destruction (250 TB) from incidents like Vyncs have not been independently verified; true technical impact may be inflated for psychological effect [11][19]
- **Full Toolchain**: Only FileFiend/Exchangedb.exe and http.flask.py are confirmed; other tools (initial access, privilege escalation, persistence) remain未知 [6][11]
- **Initial Access Vector**: No explicit details on how Ababil of Minab gained entry to victim environments (e.g., phishing, vuln exploit, cred theft) beyond implication of web.config exposure [11][19]
- **Secondary Objectives**: Beyond destruction and exfiltration, whether data was used for influence ops, sold, or leveraged for further intrusion is unknown [11][19]
- **accz Abbreviation**: The 'accz' tag in accz.7z points to an unconfirmed organization; its true identity and relevance to targeting are unclear [11]
- **Future Intentions**: While linked to potential World Cup targeting via symbolic naming, no concrete planning or prep has been observed [16]
- **Operator OPSEC Gaps**: Reasons for leaving staging infrastructure openly accessible for weeks post-report are unknown — possible negligence, false flag, or deliberate misdirection [11]
- **Broader Campaign Links**: Full overlap with other Iran-linked clusters (e.g., APT33, APT34, MuddyWater) beyond Black Shadow is not detailed in learns [6][11]

## Gaps

- unverified claims removed

---

## Sources

[1] Turn Restricted Mode on or off on YouTube — https://support.google.com/youtube/answer/174084?hl=en&co=GENIE.Platform%3DDesktop  
[2] Aeistiva Avenue — https://aeistivaavenue.com/  
[3] Pode levar power bank no avião? Veja limite, regras, riscos e mais — https://www.techtudo.com.br/guia/2026/02/pode-levar-power-bank-no-aviao-veja-limite-regras-da-anac-riscos-e-mais-edmobile.ghtml  
[4] MITRE ATT&CK - Page 2 of 2 - Cisco Blogs — https://blogs.cisco.com/tag/mitre-attck/page/2  
[5] Cirurgia para nódulo da mama: como é feita, riscos e recuperação — https://www.tuasaude.com/cirurgia-de-mama/  
[6] Attacking the recovery layer: an Iran-MOIS case study — https://gambit.security/blog-posts/babil-of-minab-iran-mois-destruction-campaign  
[7] Verify your YouTube account - Google Help — https://support.google.com/youtube/answer/171664?hl=en  
[8] Threat Actor - Cisco Blogs — https://blogs.cisco.com/tag/threat-actor  
[9] Shop – Aeistiva Avenue — https://aeistivaavenue.com/shop/  
[10] Cracker Barrel Menu | Homestyle Food For The Family — https://www.crackerbarrel.com/menu  
[11] Ababil of Minab Exposed: LA Metro SCADA Backups and Israeli ... — https://hunt.io/blog/ababil-of-minab-iranian-hackers-exposed-la-metro-breach-open-directory  
[12] ‎Apps para iPhone - App Store — https://apps.apple.com/es/iphone/apps  
[13] LockBit (Malware Family) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/details/win.lockbit  
[14] ring°werk – The Motorsport Experience Museum at the | Nürburgring — https://nuerburgring.de/experience/at-the-ring/ringwerk?locale=en  
[15] How Bad Is Propane for the Environment? - Biology Insights — https://biologyinsights.com/how-bad-is-propane-for-the-environment/  
[16] Threats to the 2026 FIFA World Cup - Recorded Future — https://www.recordedfuture.com/research/2026-fifa-world-cup-threats  
[17] ‎Apps para iPhone - App Store — https://apps.apple.com/mx/iphone/apps  
[18] GHOST-BOT-V2-/README.md at main · Atomic-tech-Shadow/GHOST … — https://github.com/Atomic-tech-Shadow/GHOST-BOT-V2-/blob/main/README.md  
[19] Cyber Intel Brief: Ababil of Minab Breach of Vyncs GPS Platform — https://www.dataminr.com/resources/ababil-of-minab-breach-of-vyncs-gps-platform/  
[20] Microsoft – AI, Cloud, Productivity, Computing, Gaming & Apps — https://www.microsoft.com/en-us?msockid=01a47aecef05621127c66d7beee86386  
[21] Ababil of Minab claims cyberattack on LACMTA, exposing risks to ... — https://industrialcyber.co/industrial-cyber-attacks/ababil-of-minab-claims-cyberattack-on-lacmta-exposing-risks-to-rail-control-systems-and-critical-transit-infrastructure/  
[22] Sistemas - Secretaria Municipal de Educação — https://educacao.prefeitura.rio/sistemas-3/  
[23] What the Iran Conflict Means for Critical Infrastructure Operators ... — https://www.lexology.com/library/detail.aspx?g=481d1169-da35-4053-b7d7-dc4e86969f57  
[24] Iranian Revolutionary Guard Corps (IRGC) - Iran Special Weapons … — https://fas.org/nuke/guide/iran/agency/irgc.htm  
[25] Mercury-Mercruiser 8M0168463 Joystick Piloting GPS/IMU Kit — https://www.mercruiserparts.com/mercury-mercruiser-8m0168463-gps-imu-kit  

---

## Metadata

- **Model:** bedrock/nvidia.nemotron-super-3-120b (openai-compat)
- **Stop reason:** budget
- **Duration:** 7m 35s
- **Depth reached:** 4
- **Sources read:** 25
- **Learnings:** 83
- **Verified learnings:** 65
- **Prompt tokens:** 154348
- **Completion tokens:** 25348