# Produce a full hunt-ready dossier on actor "Storm-1849". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

Storm-1849 (also tracked as UAT4356) is a state-sponsored threat actor focused on espionage against government, critical infrastructure, and high-value enterprise networks worldwide, primarily via the ArcaneDoor campaign. [4][8][25] The actor demonstrates deep knowledge of Cisco Adaptive Security Appliances (ASA) and other networking devices, exploiting zero-days and known CVEs to deploy custom implants including the memory-resident shellcode interpreter Line Dancer, the persistent Line Runner backdoor, and more recently RayInitiator (a GRUB bootkit) and LINEVIPER (user-mode implant). [3][4][7][8][25] Activity spans capability development from July 2023, with ArcaneDoor operations peaking December 2023–April 2024 and related 2025 activity against Cisco ASA 5500-X Series. [3][4][7] TTPs emphasize infrastructure acquisition (VPS and OpenConnect VPN), adversary-in-the-middle HTTP interception for C2, automated collection/exfiltration, anti-forensics (log clearing, ACL/AAA/syslog tampering, boot scripts), and potential lateral movement. [3][4][13] No associated malware families are publicly catalogued beyond the named implants. [8] Actor-controlled infrastructure IPs and multi-tenant nodes support C2 and actions-on-objectives; initial access remains undetermined. [4]

## Identity, Aliases, and Attribution

Storm-1849 is the Microsoft Threat Intelligence Center designation for the actor also tracked by Cisco Talos as UAT4356. [4][8] It is assessed as a state-sponsored threat actor. [8] Cisco assesses with high confidence that 2025 activity targeting Cisco ASA 5500-X Series devices (associated with CVE-2025-20333, CVE-2025-20362, and CVE-2025-20363) is related to the same actor responsible for the 2024 ArcaneDoor campaign. [4] The actor has shown deliberate anti-forensic measures and deep understanding of Cisco systems. [8] Targeting focuses on government networks globally, critical infrastructure, and high-value enterprises, with interest also noted in Microsoft Exchange servers and network devices from multiple vendors. [3][4][8][25]

## Campaigns, Timeline, and Targeting

The primary observed campaign is ArcaneDoor, an espionage-focused operation against perimeter networking devices (Cisco and other vendors) that first occurred in July 2023 and was last seen in April 2024. [3][8] Actor-controlled infrastructure dates to early November 2023, with most activity December 2023–early January 2024 and capability testing/development as early as July 2023. [4][7] All identified ArcaneDoor victims involved government networks globally; broader interest includes critical infrastructure. [3][4][25] In ArcaneDoor, Storm-1849 exploited two zero-day vulnerabilities in Cisco Adaptive Security Appliances to deploy Line Runner and Line Dancer, enabling configuration modification, reconnaissance, network traffic capture/exfiltration, and potentially lateral movement. [4][8] Related 2025 activity continues targeting of Cisco ASA 5500-X Series. [4] The initial access vector for ArcaneDoor has not been determined, with no evidence of pre-authentication exploitation identified to date. [4]

## Observed TTPs Mapped to MITRE ATT&CK

Storm-1849 TTPs center on network-device compromise, persistence via bootkits/implants, C2 via HTTP and tunnels, collection of configs/PCAPs, and anti-forensics. Key mappings include:

- **Resource Development**: Acquire Infrastructure: Virtual Private Server (T1583.003) via dedicated adversary-controlled VPS for C2; Acquire Infrastructure: Web Services (T1583.006) via OpenConnect VPN Server instances; compromise of intermediate routers; use of publicly available code (siet.py) and tooling (map.tcl, tclproxy.tcl, wodSSHServer); multi-hop pivoting tools such as STOWAWAY. [3][13]
- **Reconnaissance**: Active scanning for open ports/services; gathering victim network topology from configuration files. [13]
- **Initial Access**: Exploitation of public-facing applications via known CVEs (including CVE-2023-20198 authentication bypass, CVE-2023-20273 privilege escalation, CVE-2018-0171 Smart Install RCE, CVE-2024-21887 Ivanti command injection, CVE-2024-3400 PAN-OS arbitrary file creation/RCE); leveraging trusted provider connections to pivot. [13] (ArcaneDoor initial access undetermined.) [4]
- **Execution**: CLI command execution (T1059); Python script siet.py; SNMP as system service; Guest Shell for open-source tools and reconnaissance. [4][13]
- **Persistence**: Malicious boot scripts to install Line Runner (T1037); creation of new local users; Linux-based Guest Shell containers; SSH authorized keys; RayInitiator GRUB bootkit and LINEVIPER implant for long-term covert access. [3][4][7][13][25]
- **Privilege Escalation**: Exploitation of CVE-2023-20273 for root-level privileges. [13]
- **Defense Evasion**: Base64 obfuscation (T1140); double encoding of paths; source IP obfuscation in logs (appearing as local IPs); disabling syslog and tampering with AAA (T1562.001); file removal (T1070.004); Guest Shell destroy to uninstall containers; code injection into AAA and Crash Dump (T1055); ACL modification to permit actor IPs. [4][13]
- **Credential Access**: Brute-forcing weak Cisco Type 7/5 passwords from configs; modifying TACACS+/AAA to less secure methods or actor-controlled servers for capture; collecting network device configurations. [13]
- **Discovery**: CLI/SNMP enumeration of interfaces/VRFs/routing/ACLs/system information; targeting MIB via SNMP. [13]
- **Lateral Movement**: Enumerating/altering SNMP community configurations; potential via captured traffic and trusted connections. [4][13]
- **Collection**: Automated collection of packet captures and system configuration (T1119); network sniffing (T1040); passive PCAP from ISP customer networks; compiling configs and PCAPs into archives. [3][4][13]
- **Command and Control**: HTTP application-layer protocol (T1071.001); HTTP interception/adversary-in-the-middle (T1557); one-way HTTP C2 backdoor (T1102.003); OpenConnect VPN; VPS as C2 proxy; non-standard ports; tunnels over GRE/mGRE/IPsec (protocol tunneling); exposure of SSH/SFTP/RDP/FTP/HTTP/HTTPS. [3][4][13]
- **Exfiltration**: Automated/scripted exfiltration (T1020); data exfiltration over C2 (T1041); tunnels for exfiltration. [3][4][13]
- **Impact/Other**: Reboot via CVE-2024-20353 (T1653); AAA bypass (T1556); hooking processHostScanReply() (T0874). [4]

Line Dancer functions as a memory-resident shellcode interpreter for command execution; Line Runner provides persistence. [4][7] The attack chain supports configuration modification, reconnaissance, traffic capture/exfiltration, and potential lateral movement. [4][8]

## Infrastructure Patterns and IOCs

Infrastructure patterns include dedicated adversary-controlled virtual private servers for C2 and OpenConnect VPN Server instances for actions on victim devices. [3] Actor-controlled infrastructure was active from November 2023 (testing from July 2023). [4][7] Some associated IPs belong to publicly known anonymization infrastructure and are not directly actor-controlled. [4]

**IOCs Classified**:
- **Block (actor-controlled infrastructure – high confidence for blocking at perimeter/firewall/proxy)**: 192.36.57.181, 185.167.60.85, 185.227.111.17, 176.31.18.153, 172.105.90.154, 185.244.210.120, 45.86.163.224, 172.105.94.93, 213.156.138.77, 89.44.198.189, 45.77.52.253, 103.114.200.230, 212.193.2.48, 51.15.145.37, 89.44.198.196, 131.196.252.148, 213.156.138.78, 121.227.168.69, 213.156.138.68, 194.4.49.6, 185.244.210.65, 216.238.75.155. [4]
- **Hunt (multi-tenant / shared infrastructure – prioritize for outbound connection hunting and enrichment; higher false-positive risk)**: 5.183.95.95, 45.63.119.131, 45.76.118.87, 45.77.54.14, 45.86.163.244, 45.128.134.189, 89.44.198.16, 96.44.159.46, 103.20.222.218, 103.27.132.69, 103.51.140.101, 103.119.3.230, 103.125.218.198, 104.156.232.22, 107.148.19.88, 107.172.16.208, 107.173.140.111, 121.37.174.139, 139.162.135.12, 149.28.166.244, 152.70.83.47, 154.22.235.13, 154.22.235.17, 154.39.142.47, 172.233.245.241, 185.123.101.250, 192.210.137.35, 194.32.78.183, 205.234.232.196, 207.148.74.250, 216.155.157.136, 216.238.66.251, 216.238.71.49, 216.238.72.201, 216.238.74.95, 216.238.81.149, 216.238.85.220, 216.238.86.24. [4]
- **Forensics-only (host/device artifacts requiring deep inspection; do not block blindly)**: More than one executable memory region (r-xp permissions) in the output of `show memory region | include lina`, especially if one is exactly 0x1000 bytes; gaps in logs or unexpected reboots; presence of Line Runner/Line Dancer artifacts, RayInitiator GRUB bootkit, or LINEVIPER implant; unexpected Guest Shell containers, modified ACLs/AAA/TACACS+/syslog settings, unauthorized local users or SSH keys, GRE/IPsec tunnels, or OpenConnect VPN instances. [4][7][13][25]

## Hunting Queries, Mitigations, and Pivot Points

**Hunting Queries** (derived from observed IOCs, TTPs, and device behaviors; adapt to environment):
- **KQL (Microsoft Sentinel / Defender – network connections)**:  
  `DeviceNetworkEvents | where RemoteIP in ("192.36.57.181","185.167.60.85","185.227.111.17","176.31.18.153","172.105.90.154","185.244.210.120","45.86.163.224","172.105.94.93","213.156.138.77","89.44.198.189","45.77.52.253","103.114.200.230","212.193.2.48","51.15.145.37","89.44.198.196","131.196.252.148","213.156.138.78","121.227.168.69","213.156.138.68","194.4.49.6","185.244.210.65","216.238.75.155") or RemoteIP in ("5.183.95.95","45.63.119.131","45.76.118.87","45.77.54.14","45.86.163.244","45.128.134.189","89.44.198.16","96.44.159.46","103.20.222.218","103.27.132.69","103.51.140.101","103.119.3.230","103.125.218.198","104.156.232.22","107.148.19.88","107.172.16.208","107.173.140.111","121.37.174.139","139.162.135.12","149.28.166.244","152.70.83.47","154.22.235.13","154.22.235.17","154.39.142.47","172.233.245.241","185.123.101.250","192.210.137.35","194.32.78.183","205.234.232.196","207.148.74.250","216.155.157.136","216.238.66.251","216.238.71.49","216.238.72.201","216.238.74.95","216.238.81.149","216.238.85.220","216.238.86.24") | project Timestamp, DeviceName, RemoteIP, RemotePort, InitiatingProcessFileName, ActionType`
- **Splunk (proxy/firewall logs)**:  
  `index=network OR index=firewall (src_ip OR dest_ip) IN (192.36.57.181,185.167.60.85,185.227.111.17,176.31.18.153,172.105.90.154,185.244.210.120,45.86.163.224,172.105.94.93,213.156.138.77,89.44.198.189,45.77.52.253,103.114.200.230,212.193.2.48,51.15.145.37,89.44.198.196,131.196.252.148,213.156.138.78,121.227.168.69,213.156.138.68,194.4.49.6,185.244.210.65,216.238.75.155,5.183.95.95,45.63.119.131,45.76.118.87,45.77.54.14,45.86.163.244,45.128.134.189,89.44.198.16,96.44.159.46,103.20.222.218,103.27.132.69,103.51.140.101,103.119.3.230,103.125.218.198,104.156.232.22,107.148.19.88,107.172.16.208,107.173.140.111,121.37.174.139,139.162.135.12,149.28.166.244,152.70.83.47,154.22.235.13,154.22.235.17,154.39.142.47,172.233.245.241,185.123.101.250,192.210.137.35,194.32.78.183,205.234.232.196,207.148.74.250,216.155.157.136,216.238.66.251,216.238.71.49,216.238.72.201,216.238.74.95,216.238.81.149,216.238.85.220,216.238.86.24) | stats count by src_ip, dest_ip, dest_port, action`
- **Sigma-style (conceptual – network device CLI / syslog for Cisco)**: Detect unexpected reboots, syslog disablement, AAA/TACACS+ changes, new local users, Guest Shell activation, or multiple r-xp memory regions under `show memory region | include lina` (especially 0x1000-byte regions); also unexpected GRE/IPsec tunnels, ACL modifications permitting external IPs, or PCAP collection. [4][7][13]
- Additional hunts: Outbound HTTP from network devices to unknown destinations; non-standard port usage; SNMP configuration changes; presence of siet.py, map.tcl, or STOWAWAY artifacts; OpenConnect VPN processes. [3][13]

**Mitigations**:
- Immediately apply Cisco patches for CVE-2024-20353, CVE-2024-20359, and relevant 2025 CVEs (CVE-2025-20333/20362/20363); update all networking devices to supported versions. [7][13]
- Regularly review network device logs and configurations for unexpected activity, especially changes to network tunnels, AAA configurations, ACLs, packet captures/network mirroring, or virtual containers. [13]
- Check for unexpected GRE/other tunneling protocols, unexpected TACACS+/RADIUS servers, or unusual traffic. [13]
- Disable outbound connections from management interfaces; disable all unused ports/protocols, Cisco Smart Install, and Cisco Guest Shell; use only strong cryptographic algorithms. [13]
- Change all default administrative credentials and SNMP community strings; disable password authentication where possible; enforce strong PKI-based or multifactor authentication, strong cryptographic password storage (Cisco Type 8), and lockouts. [13]
- Implement management-plane isolation and control-plane policing (CoPP); ensure management VRFs cannot receive traffic from the data plane. [13]

**Pivot Points**:
- Enrich all listed IPs (actor-controlled and multi-tenant) for historical resolution, certificates, and co-occurring infrastructure; pivot on OpenConnect VPN Server fingerprints and VPS providers used. [3][4]
- Search for Line Runner/Line Dancer/RayInitiator/LINEVIPER artifacts, memory region anomalies, and Guest Shell remnants across Cisco ASA/IOS XE estates. [4][7][25]
- Correlate with exploitation of listed CVEs (Cisco IOS XE, Ivanti, Palo Alto) and any Microsoft Exchange targeting. [4][13]
- Review government/critical-infrastructure perimeter devices for log gaps, unexpected reboots, or configuration modifications dating to July 2023–April 2024 and into 2025. [3][4][7]
- Hunt for STOWAWAY, siet.py, and related open-source tooling in device Guest Shell environments. [13]

## Intelligence Gaps

- Initial access vector for ArcaneDoor remains undetermined; ongoing investigation into possible pre-authentication exploitation with no evidence identified to date. [4]
- Limited public detail on exact zero-day exploitation mechanics beyond the two Cisco ASA vulnerabilities used to deploy implants, and incomplete mapping of 2025 CVEs (CVE-2025-20333/20362/20363) to specific TTPs. [4][8]
- No malware family associations catalogued beyond named implants; full technical details of RayInitiator and LINEVIPER, as well as any additional implants, are sparse. [8][25]
- Scope of targeting beyond government/critical infrastructure (e.g., confirmed Microsoft Exchange or non-Cisco vendor compromises) and precise attribution to a nation-state sponsor remain open. [4]
- Full extent of multi-tenant infrastructure usage versus pure actor-controlled nodes, and historical activity prior to July 2023, require further enrichment. [4]
- Specific Sigma/KQL/Splunk rules for Line Dancer memory artifacts or RayInitiator bootkit detection are not yet standardized in available reporting.

## Key Findings

- Storm-1849/UAT4356 is a sophisticated state-sponsored actor specializing in high-value perimeter network device compromise for espionage, with confirmed ArcaneDoor campaign (July 2023–April 2024) and related 2025 ASA activity. [3][4][8]
- Custom implants (Line Runner for persistence via boot scripts, Line Dancer as memory-resident shellcode interpreter; later RayInitiator GRUB bootkit and LINEVIPER) enable long-term covert access, traffic capture, config modification, and C2. [3][4][7][25]
- Strong preference for VPS-based C2, OpenConnect VPN, HTTP AiTM interception, automated PCAP/config collection + exfiltration, and extensive anti-forensics (log clearing, AAA/syslog/ACL tampering). [3][4][13]
- High-confidence actor-controlled IP list enables immediate blocking; multi-tenant list supports hunting. [4]
- Deep Cisco expertise (including memory region indicators and process hooking) and use of publicly available tooling indicate both custom development and opportunistic reuse. [4][8][13]
- All confirmed ArcaneDoor victims were government networks; broader targeting includes critical infrastructure. [4][25]

## Gaps

- unverified claims removed

---

## Sources

[1] National Weather Service — https://www.weather.gov/  
[2] How Microsoft names threat actors - Unified security operations — https://learn.microsoft.com/en-us/unified-secops/microsoft-threat-actor-naming  
[3] ArcaneDoor, Campaign C0046 - MITRE ATT&CK® — https://attack.mitre.org/campaigns/C0046/  
[4] ArcaneDoor - New espionage-focused campaign found targeting ... — https://blog.talosintelligence.com/arcanedoor-new-espionage-focused-campaign-found-targeting-perimeter-network-devices/  
[5] National Weather Service — https://www.weather.gov/source/crh/lsrmap.html  
[6] ArcaneDoor Vulnerabilities [CVE-2024-20353, CVE-2024-20359] — https://help.bitsighttech.com/hc/en-us/articles/23191250656151-ArcaneDoor-Vulnerabilities-CVE-2024-20353-CVE-2024-20359  
[7] Cisco devices again targeted by state-linked threat campaign — https://www.cybersecuritydive.com/news/cisco-network-devices-malicious-backdoors/714283/  
[8] Storm-1849 (Threat Actor) - Malpedia — https://malpedia.caad.fkie.fraunhofer.de/actor/storm-1849  
[9] Campaigns | MITRE ATT&CK® — https://attack.mitre.org/campaigns/  
[10] Contact Us - Microsoft Support — https://support.microsoft.com/en-gb/contactus  
[11] Microsoft 365 Customer Service and Support — https://support.microsoft.com/en-us/office/microsoft-365-customer-service-and-support-96162163-b3aa-498b-bbbb-5e757b0f31da  
[12] CISA orders feds to patch Cisco flaws used in multiple agency hacks — https://www.cybersecuritydive.com/news/cisa-emergency-directive-cisco-vulnerabilities-arcanedoor/761150/  
[13] Countering Chinese State-Sponsored Actors Compromise of ... - CISA — https://www.cisa.gov/news-events/cybersecurity-advisories/aa25-239a  
[14] Home | Microsoft Community Hub — https://techcommunity.microsoft.com/  
[15] Visit The Falkland Islands | Falklands — https://www.falklandislands.com/  
[16] Analysis of ArcaneDoor Threat Infrastructure Suggests Potential Ties ... — https://censys.com/blog/analysis-of-arcanedoor-threat-infrastructure-suggests-potential-ties-to-chinese-based-actor/  
[17] AI Infrastructure, Secure Networking, and Software Solutions - Cisco — https://www.cisco.com/  
[18] Puebla - Sistema Estatal de Protección Civil — https://proteccioncivil.puebla.gob.mx/  
[19] Getting Here - Falkland islands — https://www.falklandislands.com/plan-your-trip/getting-here  
[20] Threat Insights: Active Exploitation of Cisco ASA Zero Days — https://unit42.paloaltonetworks.com/zero-day-vulnerabilities-affect-cisco-software/  
[21] Cisco Products: Networking, Security, Data Center — https://www.cisco.com/site/us/en/products/index.html  
[22] Coronavirus - World Health Organization (WHO) — https://www.who.int/health-topics/coronavirus  
[23] Men's College Basketball Standings, 2025-26 season - ESPN — https://www.espn.com/mens-college-basketball/standings  
[24] Cisco Event Response: Continued Attacks Against Cisco Firewalls — https://sec.cloudapps.cisco.com/security/center/resources/asa_ftd_continued_attacks  
[25] Ongoing Exploitation of Cisco Firewalls | Quorum Cyber — https://www.quorumcyber.com/threat-intelligence/ongoing-exploitation-of-cisco-firewalls-via-vpn-web-server-zero-days/  
[26] Coronavirus disease (COVID-19) – World Health Organization — https://www.who.int/emergencies/diseases/novel-coronavirus-2019  
[27] 2025-26 Men's College Basketball Conference Standings | College ... — https://www.sports-reference.com/cbb/seasons/men/2026-standings.html  
[28] Release Notes for the Cisco Secure Firewall ASA, 9.22(x) — https://www.cisco.com/c/en/us/td/docs/security/asa/asa922/release/notes/asarn922.html  
[29] Cyber Activity Impacting CISCO ASA VPNs - Canadian Centre for ... — https://www.cyber.gc.ca/en/news-events/cyber-activity-impacting-cisco-asa-vpns  

---

## Metadata

- **Model:** xai/grok-4.5-latest (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 15m 53s
- **Depth reached:** 4
- **Sources read:** 29
- **Learnings:** 164
- **Verified learnings:** 98
- **Prompt tokens:** 243525
- **Completion tokens:** 78454