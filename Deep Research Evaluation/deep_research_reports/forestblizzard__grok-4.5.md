# Produce a full hunt-ready dossier on actor "forest blizzard". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

Forest Blizzard is a Russian state-backed threat actor, also tracked as Fancy Bear and APT28, with activity dating to at least 2004 and links to GRU Unit 26165. [2][4][12][23] The group conducts cyber espionage against government, non-governmental, energy, transportation, military, and critical infrastructure targets in the US, Europe, and the Middle East, including Poland. [2][4][23] Documented operations include exploitation of Microsoft Outlook vulnerability CVE-2023-23397 (as early as April 2022) for mailbox access and permission abuse via Exchange Web Services, as well as large-scale compromise of MikroTik and TP-Link routers for DNS hijacking and malicious infrastructure (peaking in late 2025 before disruption). [2][4][23] Exploitation leaves few forensic traces; primary mitigations center on patching. [4] No specific IOCs, hunting queries, or detailed pivot points appear in the available reporting. [10]

## Identity, Aliases, and Attribution

Forest Blizzard is the Microsoft-tracked name for a Russian state-backed hacking group also known as Fancy Bear and APT28. [2][4][12][23] It is Russia-linked and associated with officers from GRU Unit 26165, as evidenced by a 2018 US indictment of five such officers for operations spanning 2014–2018. [12][23] The actor has conducted cyber operations in support of Russian intelligence interests, including election interference and targeting of individuals and organizations of interest to the Kremlin (military, government, critical infrastructure). [12][23] APT28 has been active since at least 2004. [12]

## Observed TTPs Mapped to MITRE ATT&CK

Available reporting details several core behaviors that map to ATT&CK techniques as follows (mappings derived directly from described actions):

- **Initial Access / Exploitation**: Delivery of a specially crafted Outlook message that requires no user interaction if Outlook is open on a Windows device, exploiting CVE-2023-23397 to gain unauthorized access to email accounts on Microsoft Exchange servers. [4] This maps to T1190 (Exploit Public-Facing Application) and T1566.001 (Phishing: Spearphishing Attachment / Link, specialized for zero-interaction). Access is also obtained via brute-force attacks against email accounts. [2] This maps to T1110 (Brute Force).
- **Collection / Persistence via Mailbox Abuse**: After access, the actor modifies folder permissions within the victim’s mailbox. [2] This enables unauthorized access to high-value informational mailboxes through any compromised email account using the Exchange Web Services (EWS) protocol and allows continued unauthorized access to mailbox contents even after loss of direct account access. [2] These behaviors map to T1114 (Email Collection), T1098 (Account Manipulation), and T1078 (Valid Accounts) for persistence and lateral mailbox access.
- **Infrastructure Compromise for Espionage Support**: The actor compromises insecure MikroTik and TP-Link routers, modifies their settings, and converts them into malicious infrastructure under their control. [23] This includes DNS hijacking/redirection to target individuals of interest. [23] These actions map to T1584 (Compromise Infrastructure), T1599 (Network Boundary Bridging), and T1557 (Adversary-in-the-Middle) for DNS-based redirection and traffic control.
- **Operational Security**: Exploitation of CVE-2023-23397 leaves very few forensic traces, complicating detection of hacker activity. [4]

No additional TTPs (e.g., malware families, C2 protocols, or lateral movement beyond the above) are detailed in the provided sources.

## Infrastructure Patterns and IOCs

Forest Blizzard converts compromised MikroTik and TP-Link routers into controlled malicious infrastructure supporting cyber espionage via DNS hijacking and redirection. [23] At peak (December 2025), more than 18,000 unique IP addresses from no fewer than 120 countries communicated with the associated APT28 infrastructure before it was disrupted and taken offline via a joint operation by the US Department of Justice, FBI, and international partners. [23] Earlier activity involved limited router exploitation from May 2025, expanding to widespread use in early August 2025. [23]

**IOC Classification** (none of the sources provide concrete indicators such as hashes, domains, specific IPs, or file names):
- **Block**: None available.
- **Hunt**: Router configuration anomalies (MikroTik/TP-Link DNS/settings modifications), unusual EWS protocol usage from unexpected accounts, and mailbox folder-permission changes. [2][23]
- **Forensics-only**: Residual traces of Outlook CVE-2023-23397 exploitation (noted as extremely limited). [4]

No blockable IOCs (IPs, domains, hashes) are listed.

## Timeline of Activity

- At least 2004: APT28 activity begins. [12]
- 2014–2018: Cyber operations against organizations including WADA and OPCW (leading to 2018 US indictment of five GRU Unit 26165 officers). [12]
- 2016: Compromise of the Hillary Clinton campaign, Democratic National Committee, and Democratic Congressional Campaign Committee to interfere with the US presidential election. [12]
- As early as April 2022: Evidence of CVE-2023-23397 exploitation against limited organizations in government, transportation, energy, and military sectors in Europe. [2][4]
- March 2023 / spring 2023: Microsoft patches CVE-2023-23397. [2][4]
- May 2025: Limited-capacity router compromise activity begins. [23]
- Early August 2025: Widespread MikroTik/TP-Link router exploitation and DNS redirection commence. [23]
- December 2025: Peak of >18,000 unique IPs from ≥120 countries communicating with APT28 infrastructure; infrastructure subsequently disrupted by US DOJ/FBI and partners. [23]
- Ongoing focus includes Poland (public/private entities via Outlook vuln) and broader US/Europe/Middle East government, energy, transportation, and critical infrastructure targets. [2][4][23]

## Detection, Hunting, Mitigations, and Pivot Points

**Mitigations**: Ensure Microsoft Outlook is patched and kept up to date (CVE-2023-23397 was addressed in March/spring 2023). [2][4] No other specific mitigations (e.g., network hardening for routers or EWS controls) are detailed. [10]

**Hunting Queries**: The available sources provide no Sigma, KQL, Splunk, or other hunting queries. [10] Analysts should therefore construct custom queries around:
- Mailbox folder-permission modifications and anomalous EWS access patterns. [2]
- Unexpected DNS configuration changes on MikroTik/TP-Link devices and communications with large volumes of router IPs. [23]
- Zero-interaction Outlook message processing and residual signs of CVE-2023-23397 (noting scarcity of forensic artifacts). [4]

**Pivot Points**: None are explicitly provided. [10] Logical pivots from described activity include historical GRU Unit 26165 indictments, prior APT28 election-related infrastructure, and post-disruption residual router telemetry from the 2025 campaign. [12][23]

## Intelligence Gaps

Available reporting is incomplete on multiple hunt-ready elements. [10] No concrete IOCs (hashes, domains, IPs, file artifacts) are supplied for blocking or forensic matching. [10] No ready-to-use Sigma/KQL/Splunk hunting queries, detailed mitigation playbooks beyond Outlook patching, or explicit pivot points (e.g., shared infrastructure, tooling overlaps, or victim lists) appear. [10] Specific malware implants, full C2 patterns, post-exploitation tooling, and quantitative impact data beyond the 2025 router peak remain undescribed. Forensic recovery techniques for the low-trace Outlook exploitation and long-term residual detection after the 2025 infrastructure takedown are not addressed. [4][10][23] Further collection on post-disruption reconstitution and any new aliases or tooling evolution is required for comprehensive coverage.

## Key Findings

- Forest Blizzard = APT28 = Fancy Bear; Russian GRU-linked actor active since ≥2004 with high-profile espionage and interference operations. [2][4][12][23]
- Dual focus on Outlook/Exchange mailbox persistence (CVE-2023-23397 + permission abuse, few forensic traces) and mass SOHO-router (MikroTik/TP-Link) DNS hijacking for targeting. [2][4][23]
- CVE exploitation predated the March 2023 patch by nearly a year; 2025 router campaign scaled to global levels before disruption. [2][4][23]
- Primary defensive action is timely Outlook patching; detection relies on behavioral monitoring of permissions, EWS, and router configs due to lack of hard IOCs. [2][4][10]
- Targets consistently align with Russian intelligence priorities (government, energy, transport, military, critical infrastructure) across US, Europe, Middle East, and Poland. [2][4][23]

## Gaps

- unverified claims removed

---

## Sources

[1] Forest | Definition, Ecology, Types, Trees, Examples, & Facts | Britannica — https://www.britannica.com/science/forest  
[2] Russian hackers use old Outlook vulnerability to target Polish o… — https://www.helpnetsecurity.com/2023/12/05/apt28-poland-cve-2023-23397/  
[3] MITRE ATT&CK v11 - a small update that can help (not just) with … — https://isc.sans.edu/diary/28590  
[4] Kremlin-backed hackers attacking unpatched Outlook systems, Micr… — https://therecord.media/unpatched-microsoft-outlook-email-attacks-fancy-bear  
[5] Forest — The #1 Focus App for Time Well Spent — https://www.forestapp.cc/  
[6] N.C. Forest Service - About the N.C. Forest Service — https://www.ncagr.gov/divisions/nc-forest-service/about  
[7] Home | National Forests in North Carolina | Forest Service — https://www.fs.usda.gov/r08/northcarolina  
[8] Home | US Forest Service — https://www.fs.usda.gov/  
[9] Forests - WWF — https://www.wwf.org.uk/learn/landscapes/forests  
[10] Fancy Bear - Wikipedia — https://en.wikipedia.org/wiki/Unit_26165  
[11] CVE: Common Vulnerabilities and Exposures — https://www.cve.org/  
[12] APT28, IRON TWILIGHT, SNAKEMACKEREL, Swallowtail, Group 74, … — https://attack.mitre.org/groups/G0007/  
[13] NVD - Vulnerabilities — https://nvd.nist.gov/vuln  
[14] APT28 Cyber Threat Profile and Detailed TTPs — https://www.picussecurity.com/resource/blog/apt28-cyber-threat-profile-and-detailed-ttps  
[15] CVEs and Security Vulnerabilities - OpenCVE — https://app.opencve.io/  
[16] Alert: I-260407-PSA | 07 APRIL 2026 Russian GRU Exploiting … — https://media.defense.gov/2026/Apr/07/2003907743/-1/-1/0/I-260407-PSA.PDF  
[17] NVD - Home — https://nvd.nist.gov/  
[18] APT28 Uses Microsoft Office CVE-2026-21509 in Espionage-Focused … — https://thehackernews.com/2026/02/apt28-uses-microsoft-office-cve-2026.html  
[19] Office of Commercial Vehicle Enforcement — https://www.flhsmv.gov/florida-highway-patrol/commercial-vehicle-enforcement/  
[20] Microsoft – AI, Cloud, Productivity, Computing, Gaming & Apps — https://www.microsoft.com/en-us?msockid=075e5b5e97c16432261d4cc896a665b4  
[21] Office 365 login — https://www.office.com/  
[22] Microsoft - Wikipedia — https://en.wikipedia.org/wiki/Microsoft  
[23] Russian State-Linked APT28 Exploits SOHO Routers in Global DNS ... — https://thehackernews.com/2026/04/russian-state-linked-apt28-exploits.html  
[24] Create your Microsoft account — https://signup.live.com/  
[25] APT28’s Stealthy Multi-Stage Campaign Leveraging CVE‑2026‑21509 … — https://www.trellix.com/blogs/research/apt28-stealthy-campaign-leveraging-cve-2026-21509-cloud-c2/  
[26] Microsoft Outlook Personal Email and Calendar | Microsoft 365 — https://www.outlook.com/  
[27] Microsoft Store | XBOX — https://www.xbox.com/en-us/microsoft-store?msockid=075e5b5e97c16432261d4cc896a665b4  
[28] Lenses | SIGMA Corporation of America — https://www.sigmaphoto.com/lenses  
[29] SIGMA Corporation of America — https://www.sigmaphoto.com/  
[30] Sigma — https://www.sigma-global.com/en/  
[31] The AI runtime for business | Sigma — https://www.sigmacomputing.com/  
[32] Sigma Corporation — https://www.sigmaco.com/  
[33] APT28 exploit routers to enable DNS hijacking operations — https://www.ncsc.gov.uk/news/apt28-exploit-routers-to-enable-dns-hijacking-operations  
[34] Forest Biome - Education — https://education.nationalgeographic.org/resource/forest-biome/  
[35] SIGMA - State of Michigan — https://www.michigan.gov/budget/Budget-Offices/SIGMA  

---

## Metadata

- **Model:** xai/grok-4.5-latest (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 10m 32s
- **Depth reached:** 4
- **Sources read:** 35
- **Learnings:** 164
- **Verified learnings:** 27
- **Prompt tokens:** 164684
- **Completion tokens:** 80909