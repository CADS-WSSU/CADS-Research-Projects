# Produce a full hunt-ready dossier on actor "forest blizzard". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

Forest Blizzard is a Russian state-sponsored threat actor that Microsoft also tracks as APT28 and previously DEV-0586, with the attribution confidence stated as high in the source text. [3][5][2] Microsoft says Forest Blizzard is associated with the Russian GRU, specifically the GRU 85th Main Special Service Center, military unit 26165, and that it operates separately from other known GRU-affiliated groups. [2][4] The actor primarily targets government organizations, critical infrastructure, and IT providers, with operations reported in Ukraine, Europe, Latin America, and across more than 120 countries in a router-compromise campaign. [2][5] Its playbook includes exploitation of vulnerable web-facing applications and devices, spear phishing, password spraying/brute force over TOR, DNS hijacking, adversary-in-the-middle credential interception, custom malware, and living-off-the-land post-compromise tradecraft. [3][5][6][7]

## 1) Identity, aliases, and attribution

Forest Blizzard is identified as the actor formerly known as STRONTIUM, and Microsoft also says the previously tracked DEV-0586 is now known as Cadet Blizzard. [3][2] The source material also equates Forest Blizzard with APT28, and states that APT28 has been attributed to Russia’s GRU 85th Main Special Service Center, military unit 26165, and has been active since at least 2004. [4][5] The alias set associated with APT28 in the source includes IRON TWILIGHT, SNAKEMACKEREL, Swallowtail, Sednit, Sofacy, Pawn Storm, Fancy Bear, STRONTIUM, Tsar Team, Threat Group-4127, TG-4127, Forest Blizzard, FROZENLAKE, and GruesomeLarch. [4] The source also notes that some designations have been used for both the threat group and associated malware, indicating public attribution overlap. [4]

Microsoft believes Cadet Blizzard is associated with the Russian GRU, but says it operates separately from other known GRU-affiliated groups. [2] Microsoft further describes Forest Blizzard as a Russian military intelligence actor that primarily collects intelligence in support of Russian government foreign policy initiatives. [6] The source text states the attribution confidence for Forest Blizzard as high. [5]

## 2) Observed TTPs mapped to MITRE ATT&CK

### Initial access and credential acquisition
Forest Blizzard uses vulnerable web-facing applications as an initial access technique. [3] Microsoft also says Cadet Blizzard achieved initial access by exploiting web servers and vulnerabilities in Confluence, Exchange, and open-source platforms. [2] The actor uses spear phishing to obtain credentials, and APT28 has used phishing attachments and malicious links, including spearphishing emails with Microsoft Office and RAR attachments. [3][4] Forest Blizzard also deploys an automated password spray/brute force tool through TOR to obtain credentials. [3]

### Post-compromise persistence, privilege escalation, and lateral movement
Cadet Blizzard established persistence using web shells such as P0wnyshell and reGeorg. [2] Cadet Blizzard escalated privileges through living-off-the-land techniques and harvested credentials. [2] Cadet Blizzard conducted lateral movement using obtained network credentials and modules from the Impacket framework. [2] Forest Blizzard is capable of compromising both on-premises and cloud-hosted environments, and it deploys custom tools and malware to support operations. [3]

### Network compromise and adversary-in-the-middle activity
In a large-scale campaign, Forest Blizzard compromised more than 18,000 routers across 120 countries in early 2026 by exploiting known vulnerabilities in TP-Link and MikroTik devices. [5] The actor hijacked DNS settings to redirect traffic and support adversary-in-the-middle activity. [5] Microsoft says the actor used DNS hijacking to support post-compromise adversary-in-the-middle attacks on TLS connections against Microsoft Outlook on the web domains. [6] The campaign intercepted credentials and tokens for Microsoft Outlook Web Access. [5]

### ATT&CK mapping explicitly stated in the source
The source explicitly maps the use of valid accounts to MITRE ATT&CK technique T1078. [5] The source also explicitly maps stored-data manipulation to MITRE ATT&CK technique T1565.001. [5] The source notes that APT28 used event-log clearing commands such as `wevtutil cl System` and `wevtutil cl Security`, which are useful detection pivots. [4]

## 3) Infrastructure, campaign patterns, and victimology

Forest Blizzard has repeatedly targeted government organizations and IT providers in Ukraine, with occasional operations in Europe and Latin America. [2] The actor also targeted more than 200 organizations, including government agencies and critical infrastructure sectors, in the router and DNS-hijacking campaign. [5] Microsoft says that campaign impacted over 200 organizations and 5,000 consumer devices through malicious DNS infrastructure. [6]

Infrastructure patterns in the available source material center on exploitation of web-facing servers, SOHO routers, and DNS redirection. [2][5][6] Forest Blizzard compromised SOHO routers and modified their settings to use actor-controlled DNS resolvers, causing thousands of devices to send DNS requests to malicious servers. [6] The actor then used that control to facilitate adversary-in-the-middle interception against TLS connections for Microsoft Outlook on the web. [6] The campaign also leveraged valid accounts, indicating a mix of network-device compromise and identity abuse. [5]

## 4) Timeline and notable activity

The source material places APT28’s activity as far back as at least 2004. [4] Microsoft says Cadet Blizzard targeted government organizations and IT providers in Ukraine, with occasional operations in Europe and Latin America, but the source excerpt does not provide dates for those operations. [2] Microsoft observed the Forest Blizzard/Storm-2754 SOHO-device exploitation campaign since at least August 2025. [6] The source further states that Forest Blizzard compromised more than 18,000 routers across 120 countries in early 2026. [5]

A separate source notes Forest Blizzard’s use of GooseEgg, a custom tool, to exploit CVE-2022-38028 in the Windows Print Spooler by modifying a JavaScript constraints file and running it with SYSTEM-level permissions, but the excerpt does not provide a precise date for that behavior. [7]

## 5) Hunt-ready detections, IOCs, mitigations, and pivot points

### Detection and hunting pivots
The clearest hunt pivots provided by the sources are malicious DNS infrastructure, actor-controlled DNS resolvers, compromised routers, credential interception against Microsoft Outlook on the web, and event-log clearing commands. [5][6][4] The source specifically calls out `wevtutil cl System` and `wevtutil cl Security` as useful detection pivots. [4] Because Forest Blizzard uses valid accounts, password spraying, spear phishing, and web shells, defenders should hunt for those behaviors across identity, email, endpoint, and server telemetry. [3][2][5]

### IOCs and classification
The source material does not provide concrete hash, domain, IP, file path, or filename IOCs to classify as block, hunt, or forensics-only. [2][3][4][5][6][7] The observable infrastructure indicators available from the text are high-level: vulnerable web-facing applications, compromised TP-Link and MikroTik devices, actor-controlled DNS resolvers, malicious DNS servers, web shells such as P0wnyshell and reGeorg, and the custom tool GooseEgg. [2][5][6][7] Since the sources do not provide specific, actionable IOCs, no exact blocklist entries can be derived from the excerpt alone. [2][3][4][5][6][7]

### Example hunting logic
**Sigma concept:** detect suspicious clearing of Windows event logs via `wevtutil`. [4]  
```yaml
title: Suspicious Event Log Clearing via wevtutil
status: experimental
logsource:
  category: process_creation
detection:
  selection:
    Image|endswith: '\wevtutil.exe'
    CommandLine|contains:
      - 'cl System'
      - 'cl Security'
  condition: selection
level: high
```
This is justified because APT28 is documented using `wevtutil cl System` and `wevtutil cl Security` as a detection pivot. [4]

**KQL concept:** hunt for devices using unusual DNS resolvers or DNS redirection consistent with actor-controlled DNS infrastructure. [6][5]  
```kusto
DeviceNetworkEvents
| where RemotePort == 53 or ActionType has "Dns"
| summarize count() by DeviceName, RemoteIP, RemoteUrl
| where count_ > 100
```
This is aligned to the source reporting on compromised SOHO routers using actor-controlled DNS resolvers and thousands of devices sending DNS requests to malicious servers. [6]

**Splunk concept:** identify use of `wevtutil` for clearing System or Security logs. [4]  
```spl
index=win* sourcetype=WinEventLog:Security OR sourcetype=WinEventLog:Sysmon
(Image="*\\wevtutil.exe" AND (CommandLine="*cl System*" OR CommandLine="*cl Security*"))
```
This maps directly to the source-described event-log clearing behavior. [4]

### Mitigations
Microsoft recommends enforcing domain-name-based network access controls using Zero Trust DNS on Windows endpoints so devices only resolve DNS through trusted servers. [6] Microsoft also recommends enabling network protection and web protection in Microsoft Defender for Endpoint to safeguard against malicious sites and internet-based threats. [6] In addition, Microsoft recommends strict multifactor authentication and Conditional Access policies, especially for privileged and high-risk accounts, to reduce the impact of credential compromise. [6] A separate source recommends regularly updating and patching network devices to reduce risk from known vulnerabilities and implementing comprehensive monitoring to detect and mitigate sophisticated attacks. [5]

## Key Findings

- Forest Blizzard is the current name for an actor also tracked as APT28, STRONTIUM, and previously DEV-0586/Cadet Blizzard in the provided sources. [3][2][4][5]
- Microsoft attributes the actor to the Russian GRU and describes it as operating separately from other known GRU-affiliated groups. [2][5]
- The actor’s primary tradecraft includes exploiting vulnerable web-facing applications, spear phishing, password spraying over TOR, web shells, living-off-the-land privilege escalation, credential harvesting, and Impacket-assisted lateral movement. [3][2]
- A major campaign involved compromising SOHO routers, hijacking DNS, and intercepting Outlook Web Access credentials/tokens through adversary-in-the-middle activity. [5][6]
- The most concrete detection pivots in the source are event-log clearing with `wevtutil` and malicious DNS infrastructure tied to router compromise. [4][6]
- The sources recommend patching exposed network devices, monitoring aggressively, using Zero Trust DNS, and enforcing MFA/Conditional Access. [5][6]

## Gaps

- unverified claims removed
- The source set provides no specific domain, IP, hash, certificate, user-agent, or filename IOCs that could be confidently categorized as block, hunt, or forensics-only. [2][3][4][5][6][7]
- No detailed, source-backed ATT&CK technique list beyond T1078 and T1565.001 is explicitly mapped in the excerpt, so additional technique mapping would require outside research. [5]
- The sources do not provide concrete telemetry examples for web-shell detection, Impacket activity, TOR password-spraying infrastructure, or GooseEgg execution beyond descriptive behavior. [2][3][7]
- The excerpts do not include a full timeline of campaigns, only anchor points such as at least August 2025, early 2026, and the historical “since at least 2004” context for APT28. [4][5][6]
- The source material does not include actor-specific mitigations for the custom tool GooseEgg or for the web-shell set P0wnyshell and reGeorg. [2][7]
- The sources do not provide fully formed hunting rules tied to process, network, or cloud telemetry beyond the `wevtutil` detection pivot and high-level DNS guidance. [4][6]

---

## Sources

[1] Forest | Definition, Ecology, Types, Trees, Examples, & Facts | Britannica — https://www.britannica.com/science/forest  
[2] Microsoft Names Russian Threat Actor "Cadet Blizzard" - Infosecu… — https://www.infosecurity-magazine.com/news/microsoft-exposes-russia-cadet/  
[3] Threat Actor Forest Blizzard | Security Insider — https://www.microsoft.com/en-us/security/security-insider/threat-landscape/forest-blizzard  
[4] APT28, IRON TWILIGHT, SNAKEMACKEREL, Swallowtail, Group 74, Sednit, Sofacy, Pawn Storm, Fancy Bear, STRONTIUM, Tsar Team, Threat Group-4127, TG-4127, Forest Blizzard, FROZENLAKE, GruesomeLarch, Group G0007 | MITRE ATT&CK&reg; — https://attack.mitre.org/groups/G0007/  
[5] What vulnerabilities did Forest Blizzard exploit in their 2026 campaign? — https://aviatrix.ai/threat-research-center/forest-blizzard-2026-russia-backed-espionage-campaign/  
[6] SOHO router compromise leads to DNS hijacking and adversary-in-the-middle attacks | Microsoft Security Blog — https://www.microsoft.com/en-us/security/blog/2026/04/07/soho-router-compromise-leads-to-dns-hijacking-and-adversary-in-the-middle-attacks/  
[7] Forest Blizzard aka Fancy Bear Attack Detection: russian-backed Hackers Apply a Custom GooseEgg Tool to Exploit CVE-2022-38028 in Attacks Against Ukraine, Western Europe, and North America | SOC Prime — https://socprime.com/blog/forest-blizzard-aka-fancy-bear-attack-detection-russian-backed-hackers-apply-a-custom-gooseegg-tool-to-exploit-cve-2022-38028-in-attacks-against-ukraine-western-europe-and-north-america/  
[8] Forest — The #1 Focus App for Time Well Spent — https://www.forestapp.cc/  
[9] N.C. Forest Service - About the N.C. Forest Service — https://www.ncagr.gov/divisions/nc-forest-service/about  
[10] Home | National Forests in North Carolina | Forest Service — https://www.fs.usda.gov/r08/northcarolina  
[11] Home | US Forest Service — https://www.fs.usda.gov/  
[12] Forests - WWF — https://www.wwf.org.uk/learn/landscapes/forests  
[13] Forest Biome - Education — https://education.nationalgeographic.org/resource/forest-biome/  
[14] Schenck Forest — https://schenckforest.ncsu.edu/  
[15] Types of Forests: Definitions, Examples, and Importance — https://www.treehugger.com/types-of-forests-definitions-examples-5180645  

---

## Metadata

- **Model:** openai/gpt-5.4-mini (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 2m 40s
- **Depth reached:** 4
- **Sources read:** 15
- **Learnings:** 122
- **Verified learnings:** 65
- **Prompt tokens:** 59739
- **Completion tokens:** 14359