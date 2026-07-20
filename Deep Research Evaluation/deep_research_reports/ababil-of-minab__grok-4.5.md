# Produce a full hunt-ready dossier on actor "Ababil of Minab". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity. Add the groups beliefs and reason for existing/fighting/doing what they do



## Summary

Ababil of Minab is a pro-Iranian threat actor that publicly presents as an emerging standalone hacktivist collective while being forensically linked to infrastructure and activity previously attributed to Iran’s Ministry of Intelligence and Security (MOIS). [2][4][12] The group surfaced in late March 2026 with claims of destructive intrusions and data exfiltration against organizations in the United States, Israel, Saudi Arabia, and Turkey, most prominently advertising administrative access to the Los Angeles County Metropolitan Transportation Authority (LACMTA/LA Metro) VMware vCenter environment, OT rail systems, massive data wipes, and exfiltration. [2][4][9][12] It communicates via Telegram (t[.]me/ababilofminab) and a website (ababilofminab[.]io) that display explicit pro-Iranian messaging, framing operations as signaling, pressure, and disruption within the broader Iran–U.S. critical-infrastructure cyber contest while affording Tehran deniability through a proxy persona. [2][5] Observed tradecraft includes opportunistic compromise of exposed systems, credential theft, custom upload/exfiltration tooling, archive-based exfiltration, and dual-mode destruction (scripted automation plus interactive hands-on-keyboard wiping of VMs, partitions, SQL Server instances, Veeam backups, and filesystems). [4][9][10][12] Claims of scale (hundreds of terabytes wiped, >1 TB stolen) remain unverified in open sources, attribution is contested among some analysts, and the actor’s verified history is limited, yet the operational patterns, MOIS ties via INCD-attributed infrastructure, and escalatory language (“only the beginning”) make it a priority hunting and monitoring target for transportation, OT-dependent public infrastructure, and regional peers. [2][5][7]

## Identity, Aliases, Beliefs, and Motivation

Ababil of Minab (also referred to simply as Ababil of Minab) is an Iran-origin, Iran-linked actor that self-identifies as a pro-Iranian hacking group or hacktivist crew. [2][5][7][10] It maintains a limited public profile and little verifiable prior activity, presenting itself as a new standalone collective; analysis, however, rejects the standalone-hacktivist framing. [4][5][7] Primary public channels are the Telegram channel t[.]me/ababilofminab and the website ababilofminab[.]io, both of which display explicitly pro-Iranian messaging. [2]

The group’s stated and demonstrated beliefs center on pro-Iranian alignment. Actions are framed through explicit pro-Iran messaging used for signaling and pressure. [2][5][7] It operates within the evolving cyber contest surrounding Iran and U.S. critical infrastructure, employing pro-Iran rhetoric to generate political effect while providing deniability to Tehran via proxy or persona constructs. [5] Forensic linkage to MOIS infrastructure (previously attributed by Israel’s National Cyber Directorate) indicates the persona serves Iranian intelligence objectives rather than purely independent ideological activism. [4][12] Motivation therefore combines disruption of adversary critical infrastructure (especially public transit and OT-dependent systems), reconnaissance, signaling of capability, and coercive pressure against the United States, Israel, Saudi Arabia, and Turkey. [4][5][9] Escalatory language stating that incidents are “only the beginning” and threatening further severe actions reinforces an intent for sustained or expanding operations. [2][7]

## Attribution and Organizational Context

Attribution is contested in open reporting, with the actor described by some as an emergent group with limited verified history and by others as Iranian-aligned proxy activity. [5][7] Stronger forensic analysis ties Ababil of Minab’s campaign infrastructure and activity to that previously attributed by Israel’s INCD to Iran’s Ministry of Intelligence and Security (MOIS). [4] The group is therefore characterized as an Iranian group that frames itself as a pro-Iran hacktivist collective but is forensically linked to MOIS, offering Tehran deniability. [12][5] It is also labeled an Iran-linked threat actor originating from Iran (IR). [10] No malware families are consistently associated in some reporting, while other reporting notes one malware family attributed across sources; custom exfiltration tooling is repeatedly recovered in connection with the campaign. [4][7][10] The actor is not assessed as a true independent hacktivist crew. [4]

## Timeline of Observed Activity

- **Late March 2026**: Ababil of Minab surfaces publicly, posting videos and screenshots claiming the LA Metro breach involving wiping of hundreds of terabytes and theft of more than a terabyte of files. [4][12] Activity also includes claims of destructive intrusions against targets in the United States, Israel, Saudi Arabia, and Turkey. [9]
- **On or about 17 March 2026**: Attacker footage and a public tweet at 03:37 AM regarding delayed service alerts and TAP Mobile App issues occur hours after virtual machines were deleted from the vCenter environment, providing a temporal anchor for the intrusion. [12]
- **2 April 2026**: LA Metro confirms the breach. [12]
- **9 April 2026**: Ababil of Minab claims responsibility for the cyberattack targeting LACMTA, asserting administrative access to the VMware vCenter environment managing approximately 1,421 VMs across 28 physical hosts, access to a real-time rail-yard/OT train-control display (Division 11), 500 TB wiped, and 1 TB of sensitive user data exfiltrated (claims unverified). [2]
- **On or around 13 April 2026**: Public reporting of the LA Metro claim. [7]
- **On or around 20 April 2026**: Additional claim of intrusion into LACMTA without disruption of transit operations (reporting variance exists with earlier dates). [5]
- **June 2026**: Actor exposed for leaving LA Metro SCADA backups and Israeli victim data open on an Iranian staging server as part of the destructive intrusion and exfiltration campaign. [10]
- **July 2026**: Reporting notes the actor as an Iran-linked hacktivist focusing attacks beyond pure critical infrastructure via opportunistic methods. [10]
Throughout, the group has stated the LACMTA incident is “only the beginning.” [2] Campaigns have targeted transportation, academia, media, and insurance entities across the listed countries; additional Israeli and Turkish victims were not publicly exposed by the group. [4][10]

## Observed TTPs and MITRE ATT&CK Mapping

Ababil of Minab has 38 distinct MITRE ATT&CK techniques observed across reporting, grouped by tactic; specific technique IDs are not enumerated in available sources. [10] Core observed behaviors include:

- **Opportunistic initial access and compromise**: Attacks against exposed systems, including compromising Vyncs, taking systems offline, and defacing websites. [10]
- **Credential access and staging**: Credential theft; use of exposed staging servers (Iranian-hosted) that later contained victim data such as LA Metro SCADA backups and Israeli data. [10]
- **Collection and exfiltration**: Custom exfiltration tooling; custom upload tooling; archive-based exfiltration; claims of >1 TB sensitive user data exfiltrated. [4][2][10]
- **Impact / destruction (dual execution modes)**: 
  - Scripted automation that iterates through an inventory issuing destructive commands. [12]
  - Hands-on-keyboard interactive mode using management consoles and OS tools: in the LA Metro case, opening vCenter, selecting virtual machines, issuing Power Off followed by Delete from Disk, then moving into Windows guest VMs to open Disk Management and delete partitions one by one. [12]
  - Specific destructive actions: SQL Server deletion, VM partition wipes, Veeam backup destruction, and file-system damage. [9]
- **OT/ICS interest**: Access to real-time rail-yard management and train-control display systems; broader Iranian-aligned pattern of interest in public infrastructure with OT dependencies, including programmable logic controllers (PLCs) for disruption, signaling, and reconnaissance. [2][5]
- **Persistence and access claims**: Administrative access to VMware vCenter managing large VM estates. [2]
- **Publicity and signaling**: Publication of screenshots, videos, and claims via Telegram and website to maximize political effect. [2][12]

These map primarily under Initial Access, Credential Access, Collection, Exfiltration, Impact, and Discovery tactics, with heavy emphasis on Impact (data destruction) and Exfiltration. Related Iranian-aligned activity shows persistent focus on OT environments that are unevenly secured and integrated with legacy systems. [5]

## Infrastructure Patterns, IOCs, Hunting Guidance, Mitigations, and Pivot Points

**Infrastructure patterns**: Public-facing claim infrastructure (Telegram channel t[.]me/ababilofminab and website ababilofminab[.]io with pro-Iranian content). [2] Operational use of exposed Iranian staging servers left open containing victim data (LA Metro SCADA backups, Israeli victim data). [10] Targeting of public infrastructure, operational technology, PLCs, and systems in water, energy, government services, and transit. [5] Opportunistic focus on exposed systems; custom tooling for upload and exfiltration. [10] Large-scale VMware vCenter environments as high-value targets. [2][12]

**IOCs (classified)**: Sources attribute 10 indicators of compromise consisting of domains, IPs, hashes, and other artifacts; specific values beyond the actor’s public channels are not detailed in the provided material. [10][5]
- **Block**: ababilofminab[.]io and related claim infrastructure if observed in internal traffic or as beacon destinations; any confirmed Iranian staging-server IPs once identified from forensic recovery. [2][10]
- **Hunt**: Connections to or from known Iranian staging servers; large archive creation/transfer patterns consistent with archive-based exfiltration; anomalous vCenter Power Off / Delete from Disk sequences; Disk Management partition deletion activity; Veeam backup deletion events; credential-dumping or custom-upload tooling execution. [10][12][9]
- **Forensics-only**: Screenshots/videos released by the actor (may contain environment-specific metadata); recovered custom exfiltration tooling samples; residual data left on exposed staging servers (SCADA backups, victim files). [4][10][12]

**Hunting queries**: No specific Sigma, KQL, or Splunk queries are provided in the source material. [9] Defenders should therefore construct detections from the TTPs above (vCenter destructive API/console actions, partition deletion, Veeam destruction, large archival exfil, credential theft followed by staging-server upload). Continuous monitoring of OT environments and edge exposure is emphasized. [5]

**Mitigations**: Focus on exposure management at the edge, workforce vigilance, network segmentation (especially IT/OT), and continuous monitoring of operational technology environments that are often unevenly secured and integrated with legacy systems. [5] Protect VMware vCenter and backup infrastructure (Veeam) with strict access controls, MFA, and immutable backups. Monitor for and rapidly isolate exposed staging-like systems. Validate claims of access even when unverified, as they force defensive responses. [5]

**Pivot points**: 
- Actor claim channels (Telegram, website) for new victim announcements and messaging. [2]
- Iranian staging servers previously left exposed (search for residual LA Metro SCADA or Israeli data, then reverse for additional victims). [10]
- Custom exfiltration/upload tooling recovered from the campaign (hash/family pivots once samples are obtained). [4][10]
- MOIS/INCD-attributed infrastructure overlaps. [4]
- Victimology expansion: transportation, academia, media, insurance across US/Israel/Saudi Arabia/Turkey; non-public Israeli/Turkish victims. [4][10]
- Temporal correlation of service disruptions (e.g., March 17 delayed-service tweets) with destructive actions. [12]

## Key Findings

- Ababil of Minab is a MOIS-linked Iranian persona operating under a pro-Iran hacktivist cover for deniability, not a genuine independent crew. [4][12]
- Primary public operation is the late-March/early-April 2026 LACMTA intrusion involving vCenter admin access, OT system visibility, dual-mode destruction (scripted + interactive partition/VM/backup wipes), and claimed large-scale exfiltration; LA Metro confirmed the breach. [2][12]
- Campaign scope includes destructive and exfiltration operations against US, Israeli, Saudi, and Turkish organizations in transportation and other sectors; additional victims remain unclaimed. [4][9][10]
- Tradecraft signature: opportunistic edge compromise, credential theft, custom tooling, archive exfil, and aggressive multi-vector destruction (SQL, VMs, partitions, Veeam, files). [9][10][12]
- Infrastructure hygiene failures (open staging servers containing victim SCADA data) have already exposed additional intelligence. [10]
- Escalatory rhetoric and “only the beginning” language indicate intent for continued or intensified activity. [2][7]
- Beliefs and purpose: pro-Iranian signaling, disruption of adversary critical/OT infrastructure, political pressure, and support to Iranian intelligence objectives under proxy cover. [2][5][12]

## Gaps

- unverified claims removed

---

## Sources

[1] ESPN - Serving Sports Fans. Anytime. Anywhere. — https://www.espn.com/  
[2] Cyber Intel Brief: Pro-Iran Actor Claims Cyberattack on LA Metro — https://www.dataminr.com/resources/intel-brief/pro-iran-actor-ababil-of-minab-claims-cyberattack-on-la-metro/  
[3] Ababil of Minab claims cyberattack on LACMTA, exposing risks to rail control systems and critical transit infrastructure - Industrial Cyber — https://industrialcyber.co/industrial-cyber-attacks/ababil-of-minab-claims-cyberattack-on-lacmta-exposing-risks-to-rail-control-systems-and-critical-transit-infrastructure/  
[4] Attacking the recovery layer: an Iran-MOIS case study — https://gambit.security/blog-posts/babil-of-minab-iran-mois-destruction-campaign  
[5] Increased Attacks on Physical Infrastructure by Pro-Iran Hackers — https://smallwarsjournal.com/2026/04/20/increased-attacks-on-physical-infrastructure-by-pro-iran-hackers-defense-one/  
[6] Gambit links Iran-linked Black Shadow group to destructive cyber campaign targeting US, Middle East organizations - Industrial Cyber — https://industrialcyber.co/industrial-cyber-attacks/gambit-links-iran-linked-black-shadow-group-to-destructive-cyber-campaign-targeting-us-middle-east-organizations/  
[7] Ababil of Minab (Threat Actor) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/actor/ababil_of_minab  
[8] MITRE ATT&CK mapping and visualization - IBM — https://www.ibm.com/docs/en/qradar-common?topic=app-mitre-attck-mapping-visualization  
[9] Ababil of Minab Exposed: LA Metro SCADA Backups and Israeli ... — https://hunt.io/blog/ababil-of-minab-iranian-hackers-exposed-la-metro-breach-open-directory  
[10] Ababil of Minab - Mallory.ai — https://mallory.ai/actors/019d98e8-c6c1-7c68-8ab0-f4daf622dad7  
[11] Agent Tesla (Malware Family) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/details/win.agent_tesla  
[12] The LA Metro Attack Wasn't Hacktivism. It Was a State Operation ... — https://securityaffairs.com/192764/hacktivism/the-la-metro-attack-wasnt-hacktivism-it-was-a-state-operation-with-a-costume-on.html  
[13] MuddyWater Uses DLL Side-Loading in Espionage Campaign ... — https://thehackernews.com/2026/05/muddywater-uses-dll-side-loading-in.html  
[14] Whats The Hax? A Fraud, Infosec, and Security News Aggregator — https://whatsthehax.com/  
[15] Ghost RAT (Malware Family) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/details/win.ghost_rat  
[16] CTO at NCSC Summary: week ending June 21st — https://ctoatncsc.substack.com/p/cto-at-ncsc-summary-week-ending-june-dcb  
[17] Charter / ShinyHunters 13M Breach, Palo Alto GlobalProtect CVE ... — https://itbriefcase.net/top-10-cybersecurity-stories-this-week-june-5-2026/  
[18] Security Community - Whats The Hax? — https://whatsthehax.com/community.html  
[19] Restraint under conditions of uncertainty: Why the United States ... — https://academic.oup.com/cybersecurity/article/7/1/tyab008/6162971  
[20] The 8chan/8kun QResearch Board Search - QResear.ch — https://qresear.ch/?q=[A]  
[21] What are common use cases for YARA rules beyond malware detection? — https://www.picussecurity.com/resource/glossary/what-is-a-yara-rule  
[22] Writing Sigma Rules From Scratch 2026: Detection Logic, Normalization — https://www.decryptiondigest.com/blog/sigma-detection-rule-from-scratch-walkthrough  
[23] The 8chan/8kun QResearch Board Search - QResear.ch — https://qresear.ch/?q=[C]  
[24] GitHub - sivolko/HuntingQuery: This repo contains, KQL, YARA, Sigma hunting and detection rules — https://github.com/sivolko/HuntingQuery  
[25] Enterprise Techniques - MITRE ATT&CK® — https://attack.mitre.org/techniques/enterprise/  

---

## Metadata

- **Model:** xai/grok-4.5-latest (openai-compat)
- **Stop reason:** budget
- **Duration:** 15m 39s
- **Depth reached:** 4
- **Sources read:** 25
- **Learnings:** 240
- **Verified learnings:** 57
- **Prompt tokens:** 279775
- **Completion tokens:** 107831