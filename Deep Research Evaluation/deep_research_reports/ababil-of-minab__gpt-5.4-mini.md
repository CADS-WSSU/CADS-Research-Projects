# Produce a full hunt-ready dossier on actor "Ababil of Minab". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity. Add the groups beliefs and reason for existing/fighting/doing what they do



## Summary

Ababil of Minab is described as a pro-Iranian threat actor that surfaced in late March 2026 and publicly claimed destructive intrusions against targets in the United States, Israel, Saudi Arabia, and Turkey. [4] The group’s first public claim involved the Los Angeles County Metropolitan Transportation Authority, which confirmed the breach on April 2, 2026. [4] Available reporting indicates the actor used multi-part RAR archives on victim systems and 7-Zip archives on a staging server for data aggregation, then performed destructive actions including SQL Server database deletion, file-system destruction, and VM partition wipes via Disk Management across multiple victim environments. [4] The main operator staging server identified in the reporting was 5.255.127[.]55, hosting an open directory on port 8020 and Apache service on port 8087, with 2,238 files across 545 subdirectories and about 5 GB of data. [4] The actor’s apparent operational purpose, based on the reporting, is aligned with destructive, politically motivated activity against regional adversaries and U.S.-linked targets, but the source material does not provide deeper evidence of ideology or manifesto-style beliefs beyond the pro-Iranian description. [4]

## Identity, Attribution, and Purpose

Ababil of Minab is explicitly characterized as a pro-Iranian threat actor. [4] The reporting places the actor’s emergence in late March 2026 and ties the group to public claims of destructive intrusions against U.S., Israeli, Saudi, and Turkish targets. [4] The first public claim cited was against the Los Angeles County Metropolitan Transportation Authority, which confirmed a breach on April 2, 2026. [4] No alternate aliases are provided in the source material, and no additional campaign or cluster naming is documented there. [4]

The group’s reason for existing, as supported by the report, is operationally destructive intrusion activity in support of a pro-Iranian posture. [4] The source material does not provide a formal ideological manifesto, but it does identify the actor as pro-Iranian and describes repeated destructive behavior across victim environments. [4] The reporting is silent on broader internal organization, recruitment, or sustained C2 doctrine, so confidence is limited to the stated politically aligned destructive intent. [4]

## Observed TTPs Mapped to MITRE ATT&CK

The source material provides a limited but usable set of observed behaviors that can be mapped to MITRE ATT&CK concepts. [4]

- **Archive-based staging and aggregation**: the actor used multi-part RAR archives on victim systems and 7-Zip archives on the staging server for data aggregation. [4] This supports a file collection / archive staging pattern consistent with preparation for exfiltration or operational handling, though the report does not explicitly confirm exfiltration. [4]
- **Destructive data manipulation**: the actor performed SQL Server database deletion and file-system destruction. [4] This is consistent with destructive impact activity against data stores and host files. [4]
- **Hypervisor / VM destruction**: the actor executed VM partition wipes via Disk Management across multiple victim environments. [4] This indicates deliberate destructive actions against virtualized infrastructure. [4]
- **Staging server exposure**: the operator staging server was an exposed open directory at 5.255.127[.]55:8020 with Apache on 8087, containing large volumes of files. [4] This indicates operational reliance on exposed web-accessible staging infrastructure. [4]

The reporting does not supply enough detail to map every step to a precise ATT&CK technique ID with high confidence, and no exploit vector, initial access method, persistence mechanism, or command-and-control tradecraft is documented. [4] The best-supported ATT&CK-aligned interpretation is that the actor used archive staging for data handling and destructive host/VM actions for impact. [4]

## Infrastructure Patterns, IOCs, and Pivot Points

The primary infrastructure indicator named in the report is **5.255.127[.]55**. [4] The source identifies this IP as the operator staging server, with an open directory on port **8020** and Apache service on port **8087**. [4] The directory contained **2,238 files** across **545 subdirectories** and about **5 GB of data**. [4]

### IOC classification

#### Block
- **5.255.127[.]55** — identified operator staging server. [4]
- **TCP/8020 on 5.255.127[.]55** — open directory service. [4]
- **TCP/8087 on 5.255.127[.]55** — Apache service on the staging server. [4]

#### Hunt
- Sequential multi-part archive downloads such as **data.part1.rar** and **data.part2.rar** in web server access logs. [4]
- Outbound connections to **port 443 from server-class machines** where the TLS certificate subject contains **acmecloud.example**. [4]
- Presence of **Exchangedb.exe** on endpoints not tied to a legitimate Exchange Server installation. [4]

#### Forensics-only
- Multi-part RAR archives on victim systems. [4]
- 7-Zip archives on the staging server used for data aggregation. [4]
- Evidence of SQL Server database deletion. [4]
- Evidence of file-system destruction. [4]
- Evidence of VM partition wipes via Disk Management. [4]

### Pivot points

The reporting provides three especially useful pivots for investigation. First, investigators should pivot on the staging IP **5.255.127[.]55** and associated service exposure on ports **8020** and **8087**. [4] Second, defenders should pivot on web server logs for sequential archive download names like **data.part1.rar** and **data.part2.rar**. [4] Third, analysts should pivot on endpoint sightings of **Exchangedb.exe**, especially when the host is not a legitimate Exchange Server system. [4]

## Detection, Hunting, and Investigation Guidance

The report itself recommends specific monitoring and alerting actions. [4] A seasoned analyst should monitor web server access logs for sequential multi-part archive downloads such as **data.part1.rar** and **data.part2.rar**. [4] The report also recommends blocking or alerting on outbound connections to **port 443 from server-class machines** where the TLS certificate subject contains **acmecloud.example**. [4] In addition, analysts should hunt for **Exchangedb.exe** across endpoints and alert on any instance not tied to a legitimate Exchange Server installation. [4]

### Example hunting logic

#### Sigma
```yaml
title: Multi-part archive download pattern
logsource:
  category: webserver
detection:
  selection1:
    request|contains: 'data.part1.rar'
  selection2:
    request|contains: 'data.part2.rar'
  condition: selection1 or selection2
level: high
```
This is based on the report’s recommendation to monitor for sequential archive downloads such as **data.part1.rar** and **data.part2.rar**. [4]

#### KQL
```kusto
DeviceNetworkEvents
| where RemotePort == 443
| where DeviceType in ("Server","Virtual Machine")
| where tostring(TlsSubject) contains "acmecloud.example"
```
This is aligned to the report’s recommendation to block or alert on outbound connections to port 443 from server-class machines where the TLS certificate subject contains **acmecloud.example**. [4]

#### Splunk
```spl
index=web sourcetype=*access*
("data.part1.rar" OR "data.part2.rar")
| stats count by src_ip, uri_path, host
```
This reflects the report’s suggested log hunting for sequential archive downloads. [4]

#### Endpoint hunt
```kusto
DeviceProcessEvents
| where FileName =~ "Exchangedb.exe"
| where not(ParentProcessName has_any ("Microsoft.Exchange", "Exchange"))
```
This follows the report’s guidance to hunt for **Exchangedb.exe** and alert when it is not associated with a legitimate Exchange Server installation. [4]

### Investigation workflow

If the actor is suspected, investigators should validate whether the endpoint or VM shows signs of destructive actions against SQL Server databases, file systems, or partitions. [4] They should then correlate those findings with web log evidence of multi-part archive retrieval and with any connections to the staging server at **5.255.127[.]55:8020/8087**. [4] Because some larger files and data segments could not be fully retrieved, the captured victim data may be incomplete, so triage should assume partial visibility and verify local evidence directly on the affected systems. [4]

## Mitigations and Defensive Actions

The source material provides limited mitigation guidance, but it does include clear defensive actions. [4] Defenders should block or alert on outbound connections to **port 443** from server-class systems when the TLS certificate subject contains **acmecloud.example**. [4] They should also monitor web logs for archive-download sequences such as **data.part1.rar** and **data.part2.rar**. [4] Endpoint monitoring should include detection for **Exchangedb.exe** on non-Exchange systems. [4]

Given the observed destructive behavior, incident response should prioritize isolation of affected hosts and preservation of forensic evidence before remediation, especially where SQL Server data, file systems, or VM partitions show signs of deletion or wipe activity. [4] The report does not provide additional hardening advice, so any broader mitigation beyond these points is not supported by the source. [4]

## Timeline

- **Late March 2026**: Ababil of Minab surfaced as a pro-Iranian threat actor. [4]
- **Late March 2026 onward**: The group claimed destructive intrusions against targets in the United States, Israel, Saudi Arabia, and Turkey. [4]
- **April 2, 2026**: The Los Angeles County Metropolitan Transportation Authority confirmed the breach tied to the group’s first public claim. [4]
- **Reported period**: The actor used multi-part RAR archives on victim systems and 7-Zip archives on the staging server, and executed SQL Server deletion, file-system destruction, and VM partition wipes. [4]
- **Reported period**: The staging server **5.255.127[.]55** hosted an open directory on port 8020 and Apache on port 8087, containing 2,238 files across 545 subdirectories and about 5 GB of data. [4]

## Key Findings

- Ababil of Minab is a **pro-Iranian destructive threat actor** that emerged in late March 2026. [4]
- The actor publicly claimed attacks against targets in the **United States, Israel, Saudi Arabia, and Turkey**. [4]
- The first public claim was tied to the **Los Angeles County Metropolitan Transportation Authority**, which confirmed a breach on **April 2, 2026**. [4]
- The actor used **multi-part RAR archives** on victim systems and **7-Zip archives** on the staging server. [4]
- Destructive actions included **SQL Server database deletion**, **file-system destruction**, and **VM partition wipes via Disk Management**. [4]
- The main staging infrastructure identified was **5.255.127[.]55** with services on **8020** and **8087**. [4]
- The most actionable hunts are for **archive-download sequences**, **outbound connections involving acmecloud.example on 443**, and **Exchangedb.exe on non-Exchange systems**. [4]
- Some large files and data segments could not be fully retrieved, so the evidence base is **incomplete**. [4]

## Gaps

- unverified claims removed

---

## Sources

[1] Cancel or pause your YouTube TV membership — https://support.google.com/youtubetv/answer/7129668?hl=en&co=GENIE.Platform%3DDesktop  
[2] Cars, SUVs, Trucks, Hybrids & Electrified Vehicles | Toyota Canada — https://www.toyota.ca/en/?msockid=1d105d90999960ec0be14a0698056106  
[3] The 21 best destinations for summer 2026 - Lonely Planet — https://www.lonelyplanet.com/articles/where-to-go-in-summer  
[4] Ababil of Minab Exposed: LA Metro SCADA Backups and Israeli ... — https://hunt.io/blog/ababil-of-minab-iranian-hackers-exposed-la-metro-breach-open-directory  
[5] Bowling Alley | Family Fun | Fairview Lanes | Fairview Park, OH — https://fairviewlanes.com/  
[6] Ababil of Minab claims cyberattack on LACMTA, exposing risks to ... — https://industrialcyber.co/industrial-cyber-attacks/ababil-of-minab-claims-cyberattack-on-lacmta-exposing-risks-to-rail-control-systems-and-critical-transit-infrastructure/  
[7] YouTube の検索履歴を表示または削除する - パソコン ... — https://support.google.com/youtube/answer/57711?hl=ja&co=GENIE.Platform%3DDesktop  
[8] Top 10 Best Summer Attractions in Kigali Rwanda — https://touristplaces.guide/top-10-best-summer-attractions-in-kigali-rwanda/  
[9] IBM X-Force OSINT Advisory Ababil of Minab Exposed: LA Metro ... — https://exchange.xforce.ibmcloud.com/osint/guid:7abaa6cafb5c4ff5921e7bc4e3aae072  
[10] Kopitiam - Lowyat.NET — https://forum.lowyat.net/Kopitiam  
[11] Últimas noticias de Bolivia y todo el mundo | Red Uno de Bolivia — https://www.reduno.com.bo/  
[12] Anyone know their center of gravity? - Ford-Trucks.com — https://www.ford-trucks.com/forums/738649-anyone-know-their-center-of-gravity.html  
[13] Lowyat.NET - Insanely Addictive Malaysia Forum — https://forum.lowyat.net/  
[14] Últimas Noticias - Unitel Bolivia — https://unitel.bo/ultimas-noticias  
[15] Oil life % calculation - Ford Truck Enthusiasts Forums — https://www.ford-trucks.com/forums/1595544-oil-life-calculation.html  
[16] Word Mobile - how to turn off autosave - Microsoft Q&A — https://answers.microsoft.com/en-us/msoffice/forum/all/word-mobile-how-to-turn-off-autosave/385dee51-dcbf-4abe-8a90-09ca0ed9145a  
[17] EL DEBER | Noticias de Bolivia y el mundo — https://eldeber.com.bo/  
[18] Minds Over Matter - KALW — https://www.kalw.org/show/minds-over-matter  
[19] Kick — https://kick.com/  
[20] Paychex Flex Login and Other Platforms Logins — https://www.paychex.com/login  
[21] Portal Regularize terá novas regras de acesso e melhorias — https://www.contabeis.com.br/noticias/69887/portal-regularize-tera-novas-regras-de-acesso-e-melhorias/  
[22] Minds Over Matter - NPR — https://www.npr.org/podcasts/381443492/minds-over-matter  
[23] What is KICK? - Live Stream & Watch Streamers Online on KICK — https://about.kick.com/  
[24] Acesso Portal Regularize com Gov.br ou Procuração do Contador — https://www.contabeis.com.br/forum/tributos-federais/396236/acesso-portal-regularize-com-gov-br-ou-procuracao-do-contador/  
[25] Minds Over Matter - Podcast - Apple Podcasts — https://podcasts.apple.com/us/podcast/minds-over-matter/id299787022  

---

## Metadata

- **Model:** openai/gpt-5.4-mini (openai-compat)
- **Stop reason:** done
- **Duration:** 4m 33s
- **Depth reached:** 3
- **Sources read:** 25
- **Learnings:** 142
- **Verified learnings:** 123
- **Prompt tokens:** 75564
- **Completion tokens:** 16196