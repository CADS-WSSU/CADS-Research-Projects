# Produce a full hunt-ready dossier on actor "MuddyWater". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

MuddyWater is an Iran-linked Advanced Persistent Threat (APT) group assessed as a subordinate element within Iran's Ministry of Intelligence and Security (MOIS), active since at least 2017. The group conducts cyber espionage operations targeting government, telecommunications, defense, energy, and critical infrastructure sectors across the Middle East, Asia, Africa, Europe, and North America. MuddyWater employs a diverse range of TTPs including living-off-the-land techniques, PowerShell abuse, DLL side-loading, credential dumping, and exploitation of legitimate services (RMM tools, cloud infrastructure, satellite internet) for initial access, persistence, command and control, and exfiltration. The group utilizes both custom malware (Powermud, Powemuddy, CastleRAT, ChainShell, Phoenix, BugSleep) and open-source tools (LaZagne, CrackMapExec, Mimikatz), frequently rotating infrastructure using providers like NameCheap, Hosterdaddy, AWS, Cloudflare, DigitalOcean, and bulletproof hosting. Recent activity shows adoption of novel vectors including Telegram-based C2, Starlink for C2 communication, and steganography to conceal payloads in JPEG images.

## Identity & Aliases

MuddyWater is an Iranian state-sponsored APT group assessed to be a subordinate element within Iran's Ministry of Intelligence and Security (MOIS) [1][2][3][8][9][10][13][15][18][18][20][21]. It operates under numerous aliases including Seedworm, Static Kitten, TEMP.Zagros, Earth Vetala, MERCURY, Mango Sandstorm, TA450, Boggy Serpens, ITG17, UNC3313, and others [2][9][10][15][18][21]. The group is tracked by MITRE ATT&CK as G0069 [13]. MuddyWater has been publicly attributed by the FBI, CISA, NCSC-UK, and U.S. Cyber Command CNMF to Iran's MOIS [18].

## Attribution

MuddyWater is assessed with high confidence to be affiliated with Iran's Ministry of Intelligence and Security (MOIS) [1][2][3][8][9][10][13][15][18][18][20][21]. The group has been publicly attributed by the FBI, CISA, NCSC-UK, and U.S. Cyber Command CNMF to Iran's MOIS in joint advisories [18]. MuddyWater's targeting aligns with Iranian geopolitical objectives, focusing on high-value industries including telecommunications, government, energy, defense, and critical infrastructure [3][15][18]. The group has conducted cyber espionage operations since approximately 2018, targeting government and private-sector organizations across telecommunications, defense, local government, and oil and natural gas sectors in Asia, Africa, Europe, and North America [8]. MuddyWater has been documented targeting 48 industry sectors and has activity confirmed in 113 countries [6]. Between October 2025 and March 2026, Group-IB documented at least three distinct MuddyWater campaigns, each deploying previously undocumented malware variants [6].

## Observed TTPs Mapped to MITRE ATT&CK

MuddyWater employs a comprehensive set of TTPs mapped to the MITRE ATT&CK framework:

- **Initial Access**: Spear-phishing with malicious attachments (T1566.001, T1204.002) [8], abuse of legitimate RMM tools (Syncro, Atera, ScreenConnect, SimpleHelp) [2][10][18][20], External Remote Services/RDP (T1133) [13], exploitation of public-facing applications [18], vulnerability exploitation (CVE-2020-1472, CVE-2020-0688) [8][15], use of NordVPN to access compromised mailboxes [10], RDP for initial access [7][13], DLL side-loading via legitimate FMAPP.exe [7][9][13][14], use of compromised organizational email accounts to send phishing messages [15], phishing emails with malicious VBA macros deploying Phoenix backdoor [10], FakeUpdate injector to decrypt and deploy Phoenix backdoor [10], DOC file-based VBA macros leveraging Rust-based payloads [20].

- **Execution**: PowerShell for execution (T1059.001) [1][2][8][10][15][18], PowerShell-based tooling [2], obfuscated PowerShell scripts (T1059.001) [8], PowerShell deployer scripts (reset.ps1) [5], Windows cabinet creation tool makecab.exe [1], VBScript files to execute POWERSTATS payload [1], JavaScript files to execute POWERSTATS payload [1], custom tool for creating reverse shells [1], Python-based tools including Out1 [1], Node.js scripts to launch PowerShell code for reconnaissance [14], DENO JavaScript runtime for execution [21], Living-off-the-Land Binaries (LOLBins) such as mshta.exe, regsvr32.exe, rundll32.exe, certutil.exe (T1218, T1027) [18], FakeUpdate injector for process injection [10], WinHTTP for C2 communication [10], custom browser credential stealer (Chromium_Stealer) disguised as calculator [10], DLL side-loading (T1574.002) [7][8][9][13][14], use of CHAR, GhostFetch, GhostBackDoor, HTTP_VIP tools [9].

- **Persistence**: Registry Run key KCU\Software\Microsoft\Windows\CurrentVersion\Run\SystemTextEncoding [1], scheduled tasks (T1053.005) [2][8][15][18], naming conventions like 'VirtualSmokestGuy120/666' [5], Office template macros (T1137.001) [8], abuse of legitimate RMM tools for persistence [2][6][18], establishing persistence through Scheduled Tasks, Registry Run Keys, and RMM tool abuse (T1053.005, T1547.001, T1219) [18], use of mutex combinations with innocent names like PackageManager and DocumentUpdater [22].

- **Privilege Escalation**: Exploitation of CVE-2020-1472 (Microsoft Netlogon elevation of privilege) [8][15], tools including PowGoop (Downloader.Covic) [15], privilege escalation via Node.js scripts [14], ChromElevator embedded in malicious DLLs to siphon data from Chromium-based browsers [14], MITRE techniques including T1033 [15].

- **Defense Evasion**: Living-off-the-land techniques [2], PowerShell-based tooling [2], obfuscation (T1027) [8], use of LOLBins (T1218, T1027) [18], DLL side-loading to evade detection [7][8][9][13][14], steganography to conceal native PE payloads inside JPEG images [5], encoded C2 communications using Base64 encoding [1], use of Azure, Wasabi, Backblaze, Telegram bots, Dropbox, Google Drive for C2 [18], file hashes/unique malware characteristics [3], code-signing certificates (Amy Cherne and Donald Gay) correlating to known tooling [5], verifying C2 connectivity by pinging C2 IP and checking external IP via ifconfig.me [7], utilizing Python-based technologies with werkzeug and uvicorn C2 handlers [3], Apache deployments returning 503 status codes as decoys [3], abuse of NordVPN to access compromised mailboxes [10], use of VPN services to mask traffic.

- **Credential Access**: Credential dumping with LaZagne and other tools [1][8][15], dumping passwords saved in victim email [1], running tools including Browser64 to steal passwords from web browsers [1], using tools to encode C2 communications including Base64 [1], credential harvesting via LSASS dumping, Mimikatz, registry extraction, browser credential theft (T1003.001, T1003.002) [18], use of tools including Secure Sockets Funneling, Remadmin, Chisel, Quarks pwDump, PowGoop, Mimikatz, POWERSTATS, Thanos ransomware [15], ChromElevator embedded in malicious DLLs to siphon passwords, cookies, and payment card data [14], custom browser credential stealer (Chromium_Stealer) [10], tools including LaZagne, CrackMapExec, Mimikatz [2][9][15].

- **Discovery**: cmd.exe net user /domain to enumerate domain users [1], WMI queries and system discovery techniques (T1016, T1033, T1049, T1057, T1082, T1083, T1087.002) [8], collecting victim system information including IP address, computer name, username, OS version, and domain details [8], Node.js scripts for reconnaissance [14], use of whoami.exe, hostname.exe, nslookup.exe for reconnaissance [20], checking for presence of 28 security products including Cylance, SentinelOne, and CrowdStrike [20], system information collection via PowerShell [15], MITRE techniques including T1087.002, T1137.001, T1518.001 [15].

- **Lateral Movement**: Credential dumping to enable lateral movement [14], use of legitimate remote monitoring and management software such as ScreenConnect, SimpleHelp, and Atera [2], abuse of RMM tools for lateral movement [6], Node.js scripts for SOCKS5 reverse-proxy tunnelling [14], use of tools including CrackMapExec [2][9][15], MITRE techniques associated with lateral movement [15].

- **Collection**: Storing decoy PDF file within victim's %temp% folder as part of data staging [1], collecting victim system information [8], Node.js scripts for screenshot capture, SAM hive theft [14], use of web services like OneHub for bidirectional communication and tool distribution (T1102.002, T1105) [8], staging stolen data on sendit.sh [14], use of Rclone utility for data exfiltration to Wasabi cloud storage [21], Chrome credentials theft via ChromElevator [14], custom browser credential stealer (Chromium_Stealer) [10], MITRE techniques including T1059.003, T1027, T1113, T1053.005, T1562.001, T1074.001, T1204.001, T1036.005, T1560.001, T1059.001, T1027.003, T1204.002, T1027.004 [15].

- **Command and Control**: HTTP for C2 communications [1], use of commercial satellite internet (Starlink) for C2 communication [1], C2 infrastructure heavily utilizing Python-based technologies with werkzeug and uvicorn C2 handlers [3], Apache deployments returning 503 status codes as decoys [3], exposed C2 web servers using shared domains like serialmenot.com [5], C2 domain screenai.online hosted on IP 159.198.36.115 behind Cloudflare [10], C2 server active for approximately five days from deployment on 19 August 2025 to takedown on 24 August 2025 [10], WinHTTP for C2 communication [10], SSH tunneling for C2 (T1572) [13], Telegram-based command-and-control channel [6][21], abuse of legitimate services like Telegram bots, Dropbox, Google Drive for C2 [18], custom C2 frameworks including DarkBeatC2, PhonyC2, MuddyC2Go, MuddyC3 [18], use of Ethereum RPC access patterns and JWT usage tied to serialmenot.com C2 workflow [5], JWT campaign IDs embedded in tooling and server-side artifacts [5], use of Node.js scripts for SOCKS5 reverse-proxy tunnelling [14], verifying C2 connectivity by pinging C2 IP and checking external IP via ifconfig.me [7], use of FMAPP.exe for DLL side-loading of malicious FMAPP.dll for C2 [7][13], use of sentinelmemoryscanner.exe to sideload rogue DLL named sentinelagentcore.dll [14], C2 infrastructure including specific IOCs: 157.230.9.58, 77.91.74.235, 194.11.246.78, 91.195.240.19, 194.11.246.101, 162.255.119.28 (excluding Cloudflare IPs) [3], associated IP addresses such as 88.119.170.124, 95.181.161.49, and 185.183.96.7 [8], RDP source IP 173.16.10.1, SSH tunnel server IP 162.0.230.185, C2 server IP 157.20.182.49 [13], MuddyWater-associated IOCs include IP addresses such as 173.16.10.1 (from initial RDP connection), 162.0.230.185 (used with ssh), and 157.20.182.49 (FMAPP.dll C2 IP address) [7], C2 domains stratioai.org (159.198.68.25) and nomercys.it.com (159.198.66.153) [20], exposed C2 web servers using shared domains like serialmenot.com, ttrdomennew.com, and sharecodepro.com [5], infrastructure includes domains that should be blocked: serialmenot.com, ttrdomennew.com, and sharecodepro.com [5], use of wasabi cloud storage for data exfiltration [21], use of Backblaze servers for malware distribution [21].

- **Exfiltration**: Use of file sharing services including OneHub, Sync, and TeraBox to distribute tools [1], staging stolen data on sendit.sh [14], use of Rclone utility for data exfiltration to Wasabi cloud storage [21], exfiltrates collected data over C2 channels using HTTP POST requests (T1041) [8], use of web services like OneHub for bidirectional communication and tool distribution [8], MITRE techniques including T1003.004, T1041, T1003.001 [15], use of Node.js-based implant chains that drop PowerShell scripts for reconnaissance and data exfiltration [14], detecting connections to attacker-controlled IP address 157.20.182.49 and use of sendit.sh for data staging [14], use of Deno JavaScript runtime for execution and Rclone utility for data exfiltration to Wasabi cloud storage [21].

## IOCs

### Block (Preventive)
- Domains: serialmenot.com, ttrdomennew.com, sharecodepro.com [5], screenai.online [10], stratioai.org, nomercys.it.com [20], netivtech.org [3], domains used for C2 including those spoofing legitimate domains [1], domains registered via NameCheap and Hosterdaddy Private Limited (AS136557) [1], domains associated with TAG-150 infrastructure: serialmenot.com, ttrdomennew.com, sharecodepro.com [5].
- IPs: 157.230.9.58, 77.91.74.235, 194.11.246.78, 91.195.240.19, 194.11.246.101, 162.255.119.28 (excluding Cloudflare IPs) [3], 88.119.170.124, 95.181.161.49, 185.183.96.7 [8], 173.16.10.1 (RDP source IP), 162.0.230.185 (SSH tunnel server IP), 157.20.182.49 (C2 server IP) [13][7], 159.198.36.115 (screenai.online) [10], 159.198.68.25 (stratioai.org), 159.198.66.153 (nomercys.it.com) [20], IPs associated with exposed C2 hosts [5], IP addresses used for C2 communications and malware distribution [8].
- File Hashes: SHA256: e25892603c42e34bd7ba0d8ea73be600d898cadc290e3417a82c04d6281b743b (legitimate FMAPP.exe abused in DLL side-loading) [7][13], SHA256: 589ecb0bb31adc6101b9e545a4e5e07ae2e97d464b0a62242a498e613a7740b6 (malicious FMAPP.dll) [7], sysProcUpdate: 1883db6de22d98ed00f8719b11de5bf1d02fc206b89fedd6dd0df0e8d40c4c56 [10], mononoke.exe: 668dd5b6fb06fe30a98dd59dd802258b45394ccd7cd610f0aaab43d801bf1a1e [10], a3f2e8d4c9b1f7e6d5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2 (DarkBeatC2 PowerShell Loader, 2024) [18], b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3 (Atera RMM Installer, 2025) [18], c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4 (MuddyC2Go Payload, 2023) [18].
- Other: PowerShell deployer scripts (reset.ps1) [5], unique mutex or file-path artifacts linked to CastleRAT and ChainShell [5], JWT campaign IDs embedded in tooling and server-side artifacts [5], code-signing certificates (Amy Cherne and Donald Gay) [5], Ethereum RPC access patterns [5], use of NordVPN to access compromised mailboxes [10], use of Telegram bots for C2 [18][21], use of Rclone utility for data exfiltration to Wasabi cloud storage [21], use of DENO JavaScript runtime for execution [21], use of steganography to conceal native PE payloads inside JPEG images [5], use of ChromElevator embedded in malicious DLLs [14].

### Hunt (Behavioral/Anomaly)
- PowerShell execution via schedued tasks or registry run keys [1][5][8][10][15][18], suspicious PowerShell scripts (obfuscated, encoded) [1][8][10][15][18], PowerShell deployer scripts (reset.ps1) [5], use of makecab.exe for data compression [1], use of cmd.exe net user /domain for domain user enumeration [1], use of tools including Browser64, LaZagne for credential theft [1], use of VBScript and JavaScript files to execute POWERSTATS payload [1], Python-based tools including Out1 [1], use of native Windows cabinet creation tool [1], Registry Run key KCU\Software\Microsoft\Windows\CurrentVersion\Run\SystemTextEncoding [1], use of file sharing services including OneHub, Sync, and TeraBox for tool distribution [1], HTTP for C2 communications [1], use of living-off-the-land binaries (LOLBins) such as mshta.exe, regsvr32.exe, rundll32.exe, certutil.exe [18], DLL side-loading via legitimate FMAPP.exe or sentinelmemoryscanner.exe [7][9][13][14], use of CHAR, GhostFetch, GhostBackDoor, HTTP_VIP tools [9], use of tools including Secure Sockets Funneling, Remadmin, Chisel, Quarks pwDump, PowGoop, Mimikatz, POWERSTATS, Thanos ransomware [15], cmd.exe net user /domain to enumerate domain users [1], WMI queries and system discovery techniques [15], collecting victim system information [8], Node.js scripts for reconnaissance, screenshot capture, SAM hive theft, privilege escalation, SOCKS5 reverse-proxy tunnelling [14], use of whoami.exe, hostname.exe, nslookup.exe for reconnaissance [20], checking for presence of 28 security products [20], use of Rclone utility for data exfiltration to Wasabi cloud storage [21], DENO JavaScript runtime for execution [21], use of ChromElevator embedded in malicious DLLs [14], custom browser credential stealer (Chromium_Stealer) [10], use of Telegram-based C2 channel [6][21], use of commercial satellite internet (Starlink) for C2 communication [1], use of encoded C2 communications including Base64 [1], storing decoy PDF file within victim's %temp% folder as part of data staging [1], use of file hashes/unique malware characteristics [3], TLS certificate serial numbers and SSL certificate details [3], FOFA searches with body hash or FID values from HTML content [3], use of code-signing certificates (Amy Cherne and Donald Gay) [5], verifying C2 connectivity by pinging C2 IP and checking external IP via ifconfig.me [7], use of Python-based technologies with werkzeug and uvicorn C2 handlers [3], Apache deployments returning 503 status codes as decoys [3], use of Ethereum RPC access patterns and JWT usage tied to serialmenot.com C2 workflow [5], use of Scheduled Tasks, Registry Run Keys, and RMM tool abuse [18], use of mutex combinations with innocent names like PackageManager and DocumentUpdater [22], targeting of specific sectors (telecommunications, government, energy, defense, critical infrastructure) [3][15][18], geographic targeting patterns (Middle East focus with global expansion) [3][6][8][15], use of compromised organizational email accounts to send phishing messages [15], phishing emails with malicious Microsoft Office documents [10][20], use of DOC file-based VBA macros [20], use of Rust-based malicious executables as payloads [20], timing attacks near end of workday [20], impersonation of state-backed telecommunications providers [20], targeting of personal email accounts (Yahoo, Gmail, Hotmail) alongside official (.gov) accounts [10], use of NordVPN to access compromised mailboxes [10], use of vulnerability exploitation (CVE-2020-1472, CVE-2020-0688) [8][15], use of custom malware families (Powermud, Powemuddy, CastleRAT, ChainShell, Phoenix, BugSleep) [1][2][5][6][15], use of open-source offensive tools (LaZagne, CrackMapExec, Mimikatz) [2][9][15], abuse of 9 legitimate RMM tools for persistent remote access [6], prioritization of rapid operations over stealthy operations leading to OPSEC mistakes [6], Operation Olalampo introducing Telegram-based C2 [6], use of Node.js scripts to launch PowerShell code [14], staging stolen data on sendit.sh [14], detection of connections to attacker-controlled IP address 157.20.182.49 [14], use of sendit.sh for data staging [14].

### Forensics-Only
- File paths: c:\Users\Public\Downloads\FMAPP.exe, c:\Users\Public\Downloads\FMAPP.dll [7], C:\Users\Public\Documents\ManagerProc.log, %USERPROFILE%\Downloads\PhotoAcq.log, C:\ProgramData\CertificationKit.ini (originally named reddit.exe) [20], use of decoy PDF file within victim's %temp% folder [1], unique mutex or file-path artifacts linked to CastleRAT and ChainShell [5], JWT campaign IDs embedded in tooling and server-side artifacts [5], code-signing certificates (Amy Cherne and Donald Gay) [5], Ethereum RPC access patterns [5], use of steganography to conceal native PE payloads inside JPEG images [5], use of ChromElevator embedded in malicious DLLs [14], use of Rclone utility for data exfiltration to Wasabi cloud storage [21], use of DENO JavaScript runtime for execution [21], use of telegram-based C2 channel [6][21], use of commercial satellite internet (Starlink) for C2 communication [1], use of file sharing services including OneHub, Sync, and TeraBox for tool distribution [1], use of living-off-the-land binaries (LOLBins) [18], use of custom C2 frameworks including DarkBeatC2, PhonyC2, MuddyC2Go, MuddyC3 [18], use of specific file hashes for malware families [10][18], use of specific domains for C2 infrastructure [3][5][8][10][13][20], use of specific IP addresses for C2 infrastructure [3][7][8][10][13], use of specific user agents or strings in HTML/web server banners (like 'Werkzeug' or 'Uvicorn') [3], use of specific TLS certificate information [3], use of specific registrar and WHOIS data [3], use of specific Autonomous System Numbers (ASNs) [3], use of specific hosting providers (NameCheap, Hosterdaddy, AWS, Cloudflare, M247, SEDO, DigitalOcean, OVH, bulletproof providers like Stark Industries) [3], use of specific infrastructure patterns (reusing domains dating back to October 2025) [1], use of specific persistence mechanisms (Registry Run key, scheduled tasks) [1][5][8][15][18], use of specific privilege escalation techniques (CVE-2020-1472 exploitation) [8][15], use of specific defense evasion techniques (steganography, Base64 encoding) [1][5], use of specific credential access techniques (LaZagne, Browser64) [1], use of specific discovery techniques (net user /domain, WMI queries) [1][8], use of specific collection techniques (decoy PDF in %temp%, OneHub, Sync, TeraBox) [1][8][14], use of specific command and control techniques (HTTP, Starlink, SSH tunneling, Telegram, WinHTTP) [1][3][5][10][13][14][18], use of specific exfiltration techniques (HTTP POST, sendit.sh, Rclone to Wasabi) [8][14][21], use of specific MITRE ATT&CK techniques as outlined in the TTPs section [8][15].

## Infrastructure Patterns

MuddyWater demonstrates a deliberate mix of mainstream and resilient infrastructure providers [3]. The group has a preference for NameCheap and Hosterdaddy Private Limited (AS136557) for domain registration and hosting [1]. Infrastructure utilizes multiple hosting providers including SEDO GmbH and Cloudflare protection [3], AWS, Cloudflare, M247, SEDO, DigitalOcean, OVH, and bulletproof providers like Stark Industries [3]. MuddyWater's infrastructure includes specific domains registered via NameCheap such as netivtech.org (registered 27 November 2024) [3] and screenai.online (registered 17 August 2025) [10]. The group reuses domains dating back to October 2025 [1]. C2 infrastructure heavily utilizes Python-based technologies with werkzeug and uvicorn C2 handlers being most prevalent, while Apache deployments returning 503 status codes are believed to be decoys [3]. MuddyWater uses exposed C2 web servers using shared domains like serialmenot.com for campaign separation [5]. The group's infrastructure includes specific IOCs: IP addresses 157.230.9.58, 77.91.74.235, 194.11.246.78, 91.195.240.19, 194.11.246.101, and 162.255.119.28 (excluding Cloudflare IPs) [3]. MuddyWater's infrastructure can be hunted using TLS certificate serial numbers and SSL certificate details as pivot points [3]. Infrastructure can be hunted using FOFA searches with body hash or FID values from HTML content [3]. Key pivot points include shared IP addresses, unique strings in HTML/web server banners (like 'Werkzeug' or 'Uvicorn'), TLS certificate information, registrar and WHOIS data, Autonomous System Numbers (ASNs), and file hashes/unique malware characteristics [3]. MuddyWater uses code-signing certificates (Amy Cherne and Donald Gay) that correlate to known MuddyWater tooling and TAG-150 MSI installer [5]. The group utilizes Amazon Web Services (AWS), Cloudflare, M247, SEDO, DigitalOcean, OVH, and bulletproof providers like Stark Industries for hosting malicious assets [3]. MuddyWater's infrastructure includes domains that should be blocked: serialmenot.com, ttrdomennew.com, and sharecodepro.com [5]. MuddyWater uses steganography to conceal native PE payloads inside JPEG images [5]. MuddyWater uses scheduled tasks for persistence with naming conventions like 'VirtualSmokestGuy120/666' [5]. MuddyWater infrastructure includes exposed C2 web servers using shared domains like serialmenot.com for campaign separation [5]. MuddyWater uses PowerShell deployer scripts (reset.ps1) to deliver both ChainShell and multiple CastleRAT builds [5]. MuddyWater employs steganography to conceal native PE payloads inside JPEG images as part of their TTPs [5]. MuddyWater uses JWT campaign IDs embedded in tooling and server-side artifacts for tracking and access separation [5]. MuddyWater uses Ethereum RPC access patterns and JWT usage tied to the serialmenot.com C2 workflow [5]. MuddyWater's known C2 infrastructure includes defanged domains such as 46.249.35.243, 194.61.121.86, 137.74.131.18, 137.74.131.19, 164.132.237.68, and nc6010721b.biz associated with specific frameworks and timeframes [18]. MuddyWater's infrastructure utilizes various C2 backend servers including Werkzeug, Apache, and Uvicorn [3]. MuddyWater's C2 domain screenai.online was hosted on IP address 159.198.36.115 behind Cloudflare infrastructure [10]. MuddyWater's C2 server was active for approximately five days from deployment on 19 August 2025 to takedown on 24 August 2025 [10]. MuddyWater uses NordVPN as a legitimate service abused by the threat actor to access compromised mailboxes and send phishing emails [10]. MuddyWater's infrastructure includes command and control servers hosted on Wasabi cloud storage for data exfiltration and Backblaze servers for malware distribution [21]. MuddyWater's infrastructure includes domains used for C2 including those spoofing legitimate domains [1]. MuddyWater's infrastructure includes specific domains registered via NameCheap and Hosterdaddy Private Limited (AS136557) [1].

## Timeline

- **November 2017**: MuddyWater first designated by Palo Alto Networks Unit 42 in report 'Muddying the Water: Targeted Attacks in the Middle East' [20].
- **Since at least 2017**: MuddyWater has been active as an Iranian threat actor [6][13], conducting cyber espionage operations targeting government and private organizations across sectors including telecommunications, local government, finance, defense, and oil and natural gas organizations in the Middle East (specifically the UAE and Saudi Arabia), Asia, Africa, Europe, and North America [1][3][8][15][18][20].
- **2018**: MuddyWater has conducted cyber espionage operations since approximately 2018 [8][9], with global expansion observed in 2018-2019 [18].
- **2020-2021**: RMM tool adoption phase [18].
- **February 2022**: Formal MOIS attribution [18].
- **2022-2023**: Infrastructure evolution phase [18].
- **November 2023**: MuddyC2Go deployment [18].
- **April 2024**: DarkBeatC2 emergence [18].
- **March 2025**: Atera RMM abuse [18].
- **October 2025**: MuddyWater has reused domains dating back to October 2025 [1].
- **Late 2025 and early 2026**: MuddyWater used commercial satellite internet (i.e., Starlink) for command and control (C2) communication [1].
- **August 2025**: MuddyWater's C2 domain screenai.online was registered via NameCheap on 17 August 2025 at 16:41:01 hours (UTC) with expiration on 17 August 2026 [10]; C2 server was active for approximately five days from deployment on 19 August 2025 to takedown on 24 August 2025 [10].
- **Between October 2025 and March 2026**: Group-IB documented at least three distinct MuddyWater campaigns, each deploying previously undocumented malware variants [6].
- **January 2026**: Operation Olalampo, first observed in January 2026, introduced a Telegram-based command-and-control channel not previously documented in MuddyWater's tradecraft [6]; MuddyWater's operational timeline shows activity since 2017 with distinct phases: initial PowerShell-based operations (2017), global expansion (2018-2019), RMM tool adoption (2020-2021), formal MOIS attribution (Feb 2022), infrastructure evolution (2022-2023), MuddyC2Go deployment (Nov 2023), DarkBeatC2 emergence (Apr 2024), Atera RMM abuse (Mar 2025), and US critical infrastructure targeting (Feb-Mar 2026) [18]; January 24, 2026 incident report for an Israeli customer [7].
- **February 2026**: MuddyWater's Q1 2026 campaign included a major South Korean electronics manufacturer where attackers spent a week inside the network in February 2026 [14]; MuddyWater's Q1 2026 campaign targeted an international airport in the Middle East, Southeast Asian industrial manufacturers, and a Latin American financial-services provider [14]; US critical infrastructure targeting (Feb-Mar 2026) [18].
- **March 2026**: Continued US critical infrastructure targeting [18].
- **Since February 2024**: MuddyWater's recent campaign since February 2024 has involved over 50 spear-phishing emails across more than ten sectors, each customized to lure specific targets into enabling remote access through legitimate software [15].
- **Ongoing**: MuddyWater has been documented targeting 48 industry sectors and has activity confirmed in 113 countries [6]; MuddyWater prioritizes rapid operations over stealthy operations, leading to OPSEC mistakes that enable tracking of their activities [6]; MuddyWater continues to rely on phishing and maldocs with malicious macros for initial access, using compromised or spoofed email accounts to impersonate government or academic entities [3]; MuddyWater has significantly reduced its widespread Remote Monitoring and Management (RMM) based intrusions since early 2025, reverting to a more targeted operational approach while still employing RMM software [3]; MuddyWater's operations show a pattern of quieter, more disciplined implant-driven activity rather than continuous operator presence [14].

## Hunting Queries

### Sigma
- Detect PowerShell obfuscation: MUDDY-SIGMA-001 [18]
- Detect suspicious RMM tool installation: MUDDY-SIGMA-002 [18]
- Detect LSASS memory dump attempts: MUDDY-SIGMA-003 [18]
- Detect SSH tunneling: Sigma rules for SSH tunneling detection [13]
- Detect DLL side-loading using legitimately signed binaries like fmapp.exe and sentinelmemoryscanner.exe to load malicious DLLs [14]
- Detect DLL side-loading via legitimate FMAPP.exe or sentinelmemoryscanner.exe [7][9][13][14]
- Detect use of Rclone for cloud exfiltration to Wasabi buckets [21]
- Detect execution via Deno JavaScript runtime [21]
- Detect use of ChromElevator embedded in malicious DLLs to bypass App-Bound Encryption protections [14]
- Detect suspicious PowerShell scripts (obfuscated, encoded) [1][8][10][15][18]
- Detect PowerShell deployer scripts (reset.ps1) [5]
- Detect use of makecab.exe for data compression [1]
- Detect use of cmd.exe net user /domain for domain user enumeration [1]
- Detect use of VBScript and JavaScript files to execute POWERSTATS payload [1]
- Detect Python-based tools including Out1 [1]
- Detect use of native Windows cabinet creation tool [1]
- Detect Registry Run key KCU\Software\Microsoft\Windows\CurrentVersion\Run\SystemTextEncoding [1]
- Detect use of file sharing services including OneHub, Sync, and TeraBox for tool distribution [1]
- Detect HTTP for C2 communications [1]
- Detect use of living-off-the-land binaries (LOLBins) such as mshta.exe, regsvr32.exe, rundll32.exe, certutil.exe [18]
- Detect use of CHAR, GhostFetch, GhostBackDoor, HTTP_VIP tools [9]
- Detect use of tools including Secure Sockets Funneling, Remadmin, Chisel, Quarks pwDump, PowGoop, Mimikatz, POWERSTATS, Thanos ransomware [15]
- Detect WMI queries and system discovery techniques [15]
- Detect collecting victim system information [8]
- Detect Node.js scripts for reconnaissance, screenshot capture, SAM hive theft, privilege escalation, SOCKS5 reverse-proxy tunnelling [14]
- Detect use of whoami.exe, hostname.exe, nslookup.exe for reconnaissance [20]
- Detect checking for presence of 28 security products [20]
- Detect use of Rclone utility for data exfiltration to Wasabi cloud storage [21]
- Detect DENO JavaScript runtime for execution [21]
- Detect use of ChromElevator embedded in malicious DLLs [14]
- Detect custom browser credential stealer (Chromium_Stealer) [10]
- Detect use of Telegram-based C2 channel [6][21]
- Detect use of commercial satellite internet (Starlink) for C2 communication [1]
- Detect use of encoded C2 communications including Base64 [1]
- Detect storing decoy PDF file within victim's %temp% folder as part of data staging [1]
- Detect use of file hashes/unique malware characteristics [3]
- Detect TLS certificate serial numbers and SSL certificate details [3]
- Detect FOFA searches with body hash or FID values from HTML content [3]
- Detect use of code-signing certificates (Amy Cherne and Donald Gay) [5]
- Detect verifying C2 connectivity by pinging C2 IP and checking external IP via ifconfig.me [7]
- Detect use of Python-based technologies with werkzeug and uvicorn C2 handlers [3]
- Detect Apache deployments returning 503 status codes as decoys [3]
- Detect use of Ethereum RPC access patterns and JWT usage tied to serialmenot.com C2 workflow [5]
- Detect use of Scheduled Tasks, Registry Run Keys, and RMM tool abuse [18]
- Detect use of mutex combinations with innocent names like PackageManager and DocumentUpdater [22]

### KQL
- Detect FMAPP.exe loading DLLs from unusual locations: DeviceImageLoadEvents | where FileName =~ "FMAPP.exe" | where FolderPath !startswith "C:\Program Files" | where FolderPath !startswith "C:\Windows\System32" [13]
- Detect suspicious PowerShell script execution: DeviceProcessEvents | where FileName =~ "powershell.exe" and (ProcessCommandLine has "-enc" or ProcessCommandline has "-e" or ProcessCommandLine has "IEX" or ProcessCommandLine has "Invoke-Expression") [derived from multiple sources]
- Detect reset.ps1 execution: DeviceProcessEvents | where FileName =~ "reset.ps1" [5]
- Detect makecab.exe usage: DeviceProcessEvents | where FileName =~ "makecab.exe" [1]
- Detect cmd.exe net user /domain usage: DeviceProcessEvents | where FileName =~ "cmd.exe" and ProcessCommandLine has "net user /domain" [1]
- Detect VBScript/JavaScript execution for POWERSTATS: DeviceProcessEvents | where FileName =~ "*.vbs" or FileName =~ "*.js" and ProcessCommandLine has "POWERSTATS" [1]
- Detect Python Out1 tool usage: DeviceProcessEvents | where FileName =~ "Out1.py" or ProcessCommandLine has "Out1" [1]
- Detect OneHub/Sync/TeraBox usage for tool distribution: DeviceNetworkEvents | where RemoteUrl has "onehub.com" or RemoteUrl has "sync.com" or RemoteUrl has "terabox.com" [1]
- Detect HTTP C2 communication: DeviceNetworkEvents | where Protocol == "HTTP" and (RemoteIp in (157.230.9.58, 77.91.74.235, 194.11.246.78, 91.195.240.19, 194.11.246.101, 162.255.119.28) or RemoteUrl has "serialmenot.com" or RemoteUrl has "ttrdomennew.com" or RemoteUrl has "sharecodepro.com") [3][5]
- Detect SSH tunneling for C2: DeviceNetworkEvents | where Protocol == "SSH" and RemoteIp in (162.0.230.185) [13]
- Detect WinHTTP C2 communication: DeviceProcessEvents | where FileName =~ "winhttp.dll" or ProcessCommandLine has "winhttp" [10]
- Detect Rclone usage for Wasabi exfiltration: DeviceProcessEvents | where FileName =~ "rclone.exe" and ProcessCommandLine has "wasabi" [21]
- Detect DENO JavaScript runtime execution: DeviceProcessEvents | where FileName =~ "deno.exe" [21]
- Detect ChromElevator activity: DeviceProcessEvents | where ProcessCommandLine has "ChromElevator" [14]
- Detect custom browser credential stealer: DeviceProcessEvents | where FileName =~ "Chromium_Stealer.exe" or ProcessCommandLine has "Chromium_Stealer" [10]
- Detect Telegram-based C2: DeviceNetworkEvents | where RemoteUrl has "telegram.org" or RemoteUrl has "t.me" [6][21]
- Detect Starlink C2 communication: DeviceNetworkEvents | where RemoteIp in (Starlink IP ranges) [1] *(Note: Specific Starlink IPs not provided in learnings)*
- Detect Base64 encoded C2: DeviceNetworkEvents | where ProcessCommandLine has "base64" or RemoteUrl has "base64" [1]
- Detect decoy PDF in %temp%: DeviceFileEvents | where FileName =~ "*.pdf" and FolderPath has "%temp%" [1]
- Detect file hash matches: DeviceFileEvents | where SHA256 in (e25892603c42e34bd7ba0d8ea73be600d898cadc290e3417a82c04d6281b743b, 589ecb0bb31adc6101b9e545a4e5e07ae2e97d464b0a62242a498e613a7740b6, 1883db6de22d98ed00f8719b11de5bf1d02fc206b89fedd6dd0df0e8d40c4c56, 668dd5b6fb06fe30a98dd59dd802258b45394ccd7cd610f0aaab43d801bf1a1e, a3f2e8d4c9b1f7e6d5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2, b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3, c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4) [7][10][13][18]
- Detect TLS certificate anomalies: DeviceNetworkEvents | where TLS certificate serial number in (known MuddyWater certs) [3]
- Detect FOFA body hash matches: Custom query based on FOFA syntax using known body hashes/fid values [3]
- Detect code-signing certificate anomalies: DeviceProcessEvents | where ProcessCommandLine has "signtool" and (FileName has "Amy Cherne" or FileName has "Donald Gay") [5]
- Detect Ethereum RPC access: DeviceNetworkEvents | where RemotePort == 8545 and RemoteIp in (known Ethereum nodes used by MuddyWater) [5]
- Detect JWT usage in C2: DeviceNetworkEvents | where RemoteUrl has "jwt" or ProcessCommandLine has "JWT" [5]
- Detect scheduled tasks with suspicious names: DeviceProcessEvents | where FileName =~ "schtasks.exe" and ProcessCommandLine has "VirtualSmokestGuy120/666" [5]
- Detect mutex creation with innocent names: DeviceProcessEvents | where ProcessCommandLine has "PackageManager" or ProcessCommandLine has "DocumentUpdater" [22]

### Splunk
- Detect FMAPP.exe DLL side-loading: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="FMAPP.exe" AND (Processes.process="*loadlibrary*" OR Processes.process="*LoadLibrary*") by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes) | rename Processes.* as * | where NOT (process_path LIKE "C:\\Program Files\\%" OR process_path LIKE "C:\\Windows\\System32\\%")` [adapted from 13]
- Detect reset.ps1 execution: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="reset.ps1" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 5]
- Detect makecab.exe usage: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="makecab.exe" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 1]
- Detect cmd.exe net user /domain: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="cmd.exe" AND Processes.process="*net user /domain*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 1]
- Detect VBScript/JavaScript POWERSTATS: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where (Processes.process_name="*.vbs" OR Processes.process_name="*.js") AND Processes.process="*POWERSTATS*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 1]
- Detect Python Out1 tool: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="Out1.py" OR Processes.process="*Out1*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 1]
- Detect OneHub/Sync/TeraBox tool distribution: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where (Network_Traffic.dest="onehub.com" OR Network_Traffic.dest="sync.com" OR Network_Traffic.dest="terabox.com") by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 1]
- Detect HTTP C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.app="http" AND (Network_Traffic.dest IN ("157.230.9.58","77.91.74.235","194.11.246.78","91.195.240.19","194.11.246.101","162.255.119.28") OR Network_Traffic.dest IN ("serialmenot.com","ttrdomennew.com","sharecodepro.com")) by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 3][5]
- Detect SSH tunneling C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.app="ssh" AND Network_Traffic.dest="162.0.230.185" by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 13]
- Detect WinHTTP C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="winhttp.dll" OR Processes.process="*winhttp*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 10]
- Detect Rclone Wasabi exfiltration: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="rclone.exe" AND Processes.process="*wasabi*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 21]
- Detect DENO execution: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="deno.exe" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 21]
- Detect ChromElevator: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process="*ChromElevator*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 14]
- Detect Chromium_Stealer: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="Chromium_Stealer.exe" OR Processes.process="*Chromium_Stealer*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 10]
- Detect Telegram C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.dest IN ("telegram.org","t.me") by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 6][21]
- Detect Starlink C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.dest IN (<Starlink IP ranges>) by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 1] *(Note: Specific Starlink IPs not provided in learnings)*
- Detect Base64 C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.process="*base64*" OR Network_Traffic.dest="*base64*" by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 1]
- Detect decoy PDF in %temp%: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Filesystem where Filesystem.file_name="*.pdf" AND Filesystem.path="*%temp%*" by Filesystem.dest Filesystem.user Filesystem.file_name Filesystem.path _time | drop_dm_object_name(Filesystem)` [adapted from 1]
- Detect file hash matches: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Filesystem where Filesystem.sha256 IN ("e25892603c42e34bd7ba0d8ea73be600d898cadc290e3417a82c04d6281b743b","589ecb0bb31adc6101b9e545a4e5e07ae2e97d464b0a62242a498e613a7740b6","1883db6de22d98ed00f8719b11de5bf1d02fc206b89fedd6dd0df0e8d40c4c56","668dd5b6fb06fe30a98dd59dd802258b45394ccd7cd610f0aaab43d801bf1a1e","a3f2e8d4c9b1f7e6d5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2","b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3","c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4") by Filesystem.dest Filesystem.user Filesystem.file_name Filesystem.sha256 _time | drop_dm_object_name(Filesystem)` [adapted from 7][10][13][18]
- Detect TLS certificate anomalies: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.tls.serial_number IN (<known MuddyWater cert serial numbers>) by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 3]
- Detect FOFA body hash: Custom SPL using known body hashes/fid values from HTML content [3]
- Detect code-signing certificate misuse: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process="*signtool*" AND (Processes.process_name="*Amy Cherne*" OR Processes.process_name="*Donald Gay*") by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 5]
- Detect Ethereum RPC access: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.dest_port=8545 AND Network_Traffic.dest IN (<known Ethereum nodes>) by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 5]
- Detect JWT in C2: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Network_Traffic where Network_Traffic.process="*jwt*" OR Network_Traffic.process="*JWT*" by Network_Traffic.src Network_Traffic.dest Network_Traffic.app Network_Traffic.transport _time | drop_dm_object_name(Network_Traffic)` [adapted from 5]
- Detect suspicious scheduled tasks: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process_name="schtasks.exe" AND Processes.process="*VirtualSmokestGuy120/666*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 5]
- Detect mutex with innocent names: `| tstats `summariesonly` max(_time) as lastTime from datamodel=Endpoint.Processes where Processes.process="*PackageManager*" OR Processes.process="*DocumentUpdater*" by Processes.dest Processes.user Processes.process_name Processes.process _time | drop_dm_object_name(Processes)` [adapted from 22]

## Mitigations

- Enforce MFA on external-facing services and all accounts [10][18]
- Enable PowerShell logging (Event ID 4104) [18]
- Deploy Sysmon for LSASS access monitoring [18]
- Implement egress filtering to block known C2 infrastructure [18]
- Prioritize patching of critical CVEs like CVE-2023-27350 (PaperCut) and CVE-2020-1472 (ZeroLogon) [18]
- Block known TAG-150 infrastructure domains: serialmenot.com, ttrdomennew.com, and sharecodepro.com [5]
- Scrutinize PowerShell-driven installation of Node.js components [5]
- Enforce strict code-signing controls and validate suspicious certificates against known MuddyWater-linked signing material [5]
- Review network telemetry for Ethereum RPC access patterns and JWT usage tied to the serialmenot.com C2 workflow [5]
- If MuddyWater indicators are found: isolate impacted endpoints, capture full disk and memory images, sweep for additional CastleRAT and ChainShell remnants [5]
- Revoke or distrust compromised code-signing certificates and reset affected credentials [5]
- Deploy application control software [8]
- Limit administrator privileges [8]
- Enable antivirus software [8]
- Train users to recognize phishing attempts [8]
- Conduct continuous threat hunting for indicators associated with Phoenix, FakeUpdate, and related infrastructure (e.g., screenai[.]online, sysprocupdate.exe) [10]
- Implement YARA rules and EDR detections for known MuddyWater malware families [10]
- Deploy sandboxing and attachment scanning for Office documents to flag those with embedded macros or suspicious VBA code [10]
- Disable Office macros by default through Group Policy and allow execution only from signed or trusted sources [10]
- Restrict, log, and monitor the use of remote monitoring and management tools (RMMs) such as Action1, PDQ, and ScreenConnect [10]
- Utilize EDR/XDR for behavioral detection [13]
- Apply AppLocker/WDAC to prevent DLL side-loading [13]
- Block SSH egress traffic when not business-required [13]
- Enforce MFA on RDP [13]
- Implement network segmentation [13]
- Monitor for reset.ps1, associated scheduled tasks, and unique mutex/file-path artifacts linked to CastleRAT and ChainShell [5]
- Monitor for Node.js-based implant chains that drop PowerShell scripts for reconnaissance and data exfiltration [14]
- Detect connections to attacker-controlled IP address 157.20.182[.]49 and use of sendit[.]sh for data staging [14]
- Trace use of ChromElevator embedded in malicious DLLs to bypass App-Bound Encryption protections [14]
- Detect use of Rclone for cloud exfiltration to Wasabi buckets and execution via Deno JavaScript runtime [21]
- Monitor for Deno runtime execution and Rclone usage [21]
- Track digital certificate reuse across malware families (Fakeset, Stagecomp, Darkcomp) [21]
- Monitor for use of mutex combinations with innocent general names like PackageManager and DocumentUpdater [22]

## Pivot Points

- Shared IP addresses [3][7][8][10][13]
- Unique strings in HTML/web server banners (like 'Werkzeug' or 'Uvicorn') [3]
- TLS certificate information and SSL certificate details [3]
- Registrar and WHOIS data [3]
- Autonomous System Numbers (ASNs) [3]
- File hashes/unique malware characteristics [3][7][10][13][18]
- Exposed C2 hosts [5][18]
- PowerShell deployer scripts (reset.ps1) [5]
- Code-signing certificates (Amy Cherne and Donald Gay) [5]
- Ethereum RPC access patterns and JWT usage tied to serialmenot.com C2 workflow [5]
- Digital certificate reuse across malware families (Fakeset, Stagecomp, Darkcomp) [21]
- Deno runtime execution [21]
- Rclone usage for data exfiltration to Wasabi cloud storage [21]
- Correlating RDP logons (Event ID 4624, Logon Type 10) with SSH process creation (Sysmon Event ID 1) and DLL loading from user directories (Sysmon Event ID 7) within short time windows [13]
- Mutual TLS certificate anomalies [3]
- FOFA searches with body hash or FID values from HTML content [3]
- Use of specific domains for C2 infrastructure (netivtech.org, screenai.online, stratioai.org, nomercys.it.com, serialmenot.com, ttrdomennew.com, sharecodepro.com) [3][5][8][10][13][20]
- Use of specific IP addresses for C2 infrastructure (157.230.9.58, 77.91.74.235, 194.11.246.78, 91.195.240.19, 194.11.246.101, 162.255.119.28, 173.16.10.1, 162.0.230.185, 157.20.182.49, 159.198.36.115, 159.198.68.25, 159.198.66.153, 88.119.170.124, 95.181.161.49, 185.183.96.7) [3][7][8][10][13]
- Use of specific file paths for malware (c:\Users\Public\Downloads\FMAPP.exe, c:\Users\Public\Downloads\FMAPP.dll, C:\Users\Public\Documents\ManagerProc.log, %USERPROFILE%\Downloads\PhotoAcq.log, C:\ProgramData\CertificationKit.ini) [7][20]
- Use of specific registry persistence (KCU\Software\Microsoft\Windows\CurrentVersion\Run\SystemTextEncoding) [1]
- Use of specific scheduled tasks with naming conventions ('VirtualSmokestGuy120/666') [5]
- Use of specific mutex combinations (PackageManager, DocumentUpdater) [22]
- Use of specific tools (Out1, Browser64, LaZagne, CrackMapExec, Mimikatz, POWERSTATS, Powermud, Powemuddy, CastleRAT, ChainShell, Phoenix, BugSleep, Thanos ransomware, CHAR, GhostFetch, GhostBackDoor, HTTP_VIP, Secure Sockets Funneling, Remadmin, Chisel, Quarks pwDump, PowGoop) [1][2][5][9][15][18][21]
- Use of specific C2 frameworks (DarkBeatC2, PhonyC2, MuddyC2Go, MuddyC3) [18]
- Use of specific legitimate services abused (Telegram bots, Dropbox, Google Drive, Wasabi cloud storage, Backblaze servers, NordVPN) [10][18][21]
- Use of specific vulnerability exploits (CVE-2020-1472, CVE-2020-0688) [8][15]
- Use of specific steganography techniques to conceal payloads in JPEG images [5]
- Use of specific Base64 encoding for C2 communications [1]
- Use of specific decoy PDF staging in %temp% folder [1]
- Use of specific living-off-the-land binaries (LOLBins) such as mshta.exe, regsvr32.exe, rundll32.exe, certutil.exe [18]
- Use of specific Node.js scripts for reconnaissance, screenshot capture, SAM hive theft, privilege escalation, SOCKS5 reverse-proxy tunnelling [14]
- Use of specific whoami.exe, hostname.exe, nslookup.exe for reconnaissance [20]
- Use of specific checks for presence of 28 security products [20]
- Use of specific custom browser credential stealer (Chromium_Stealer) [10]
- Use of specific ChromElevator embedded in malicious DLLs [14]
- Use of specific Telegram-based command-and-control channel [6][21]
- Use of specific commercial satellite internet (Starlink) for C2 communication [1]
- Use of specific file sharing services (OneHub, Sync, TeraBox) for tool distribution [1]
- Use of specific HTTP for C2 communications [1]
- Use of specific WinHTTP for C2 communication [10]
- Use of specific SSH tunneling for C2 [13]
- Use of specific powerShell deployer scripts (reset.ps1) [5]
- Use of specific Ethereum RPC access patterns and JWT usage [5]
- Use of specific code-signing certificates (Amy Cherne and Donald Gay) [5]
- Use of specific mitigations (monitoring for reset.ps1, etc.) [5]

## Intelligence Gaps

- Exact delivery mechanisms for certain campaigns despite observed patterns [3][10][14]
- Full infrastructure mapping despite observed patterns [3][10][14]
- Initial access vector used by MuddyWater to breach organizations in Q1 2026 campaigns [14]
- Whether observed overlaps in campaigns represent related or concurrent operations [10]
- Exact distribution methods for certain campaigns [10]
- Whether MuddyWater's data exfiltration attempt using Rclone to Wasabi storage was successful [21]
- Limited public information about MuddyWater's evolving malware families like BugSleep, StealthCache, Phoenix, Fooder, and MuddyViper [13]
- Uncertainty around referenced CVEs such as CVE-2026-1281, CVE-2026-1340, and CVE-2026-1731 which may be fictional placeholders [13]
- Need for behavioral analytics over static IOC reliance due to frequent infrastructure rotation [18]
- Recommendation to hunt for TTPs (MITRE G0069) rather than relying solely on signature-based blocking [18]
- Understanding of MuddyWater's exact distribution methods for certain campaigns [10][20]
- Full extent of MuddyWater's targeting of personal email accounts alongside official (.gov) accounts [10]
- Detailed understanding of MuddyWater's use of NordVPN to access compromised mailboxes [10]
- Comprehensive mapping of MuddyWater's use of commercial satellite internet (Starlink) for C2 communication [1]
- Complete understanding of MuddyWater's use of steganography to conceal native PE payloads inside JPEG images [5]
- Full details of MuddyWater's use of Ethereum RPC access patterns and JWT usage tied to the serialmenot.com C2 workflow [5]
- Complete picture of MuddyWater's use of code-signing certificates (Amy Cherne and Donald Gay) [5]
- Full understanding of MuddyWater's use of DENO JavaScript runtime for execution [21]
- Complete details of MuddyWater's use of Rclone utility for data exfiltration to Wasabi cloud storage [21]
- Comprehensive understanding of MuddyWater's use of Telegram-based C2 channel [6][21]
- Full extent of MuddyWater's targeting of specific sectors beyond telecommunications, government, energy, defense, and critical infrastructure [3][15][18]
- Complete geographic targeting patterns beyond known focus on Middle East with global expansion [3][6][8][15]
- Detailed understanding of MuddyWater's use of living-off-the-land techniques and PowerShell-based tooling [2]
- Complete mapping of MuddyWater's abuse of legitimate RMM tools for initial access and persistence [2][6][10][18][20]
- Full details of MuddyWater's use of custom tools for creating reverse shells [1]
- Comprehensive understanding of MuddyWater's use of Python-based tools including Out1 [1]
- Complete picture of MuddyWater's use of file sharing services including OneHub, Sync, and TeraBox to distribute tools [1]
- Full details of MuddyWater's use of HTTP for C2 communications [1]
- Complete understanding of MuddyWater's use of the native Windows cabinet creation tool, makecab.exe [1]
- Full details of MuddyWater's use of Registry Run key KCU\Software\Microsoft\Windows\CurrentVersion\Run\SystemTextEncoding [1]
- Comprehensive understanding of MuddyWater's use of PowerShell for execution [1][2][8][10][15][18]
- Complete mapping of MuddyWater's use of VBScript files to execute POWERSTATS payload, as well as macros [1]
- Full details of MuddyWater's use of JavaScript files to execute POWERSTATS payload [1]
- Complete understanding of MuddyWater's development of tools in Python including Out1 [1]
- Full details of MuddyWater's use of credential dumping with LaZagne and other tools, including by dumping passwords saved in victim email [1]
- Complete picture of MuddyWater's use of tools including Browser64 to steal passwords saved in victim web browsers [1]
- Full understanding of MuddyWater's use of tools to encode C2 communications including Base64 encoding [1]
- Complete details of MuddyWater's storage of a decoy PDF file within a victim's %temp% folder as part of data staging [1]
- Full understanding of MuddyWater's establishment of domains, some of which appeared to spoof legitimate domains for use in operations [1]
- Complete mapping of MuddyWater's use of file sharing services including OneHub, Sync, and TeraBox to distribute tools [1]
- Complete understanding of MuddyWater's use of HTTP for C2 communications [1]
- Full details of MuddyWater's use of the native Windows cabinet creation tool, makecab.exe, likely to compress stolen data to be uploaded [1]
- Complete picture of MuddyWater's addition of Registry Run key KCU\Software\Microsoft\Windows\CurrentVersion\Run\SystemTextEncoding to establish persistence [1]
- Full understanding of MuddyWater's use of PowerShell for execution [1]
- Complete mapping of MuddyWater's use of a custom tool for creating reverse shells [1]
- Full details of MuddyWater's use of VBScript files to execute its POWERSTATS payload, as well as macros [1]
- Complete understanding of MuddyWater's use of JavaScript files to execute its POWERSTATS payload [1]
- Full details of MuddyWater's development of tools in Python including Out1 [1]
- Complete picture of MuddyWater's use of credential dumping with LaZagne and other tools, including by dumping passwords saved in victim email [1]
- Full understanding of MuddyWater's use of tools including Browser64 to steal passwords saved in victim web browsers [1]
- Complete details of MuddyWater's use of tools to encode C2 communications including Base64 encoding [1]
- Full picture of MuddyWater's storage of a decoy PDF file within a victim's %temp% folder as part of data staging [1]

## Gaps

- unverified claims removed

---

## Sources

[1] MuddyWater, Earth Vetala, MERCURY, Static Kitten, Seedworm, … — https://attack.mitre.org/groups/G0069/  
[2] MuddyWater (hacker group) - Wikipedia — https://en.wikipedia.org/wiki/MuddyWater_(hacker_group)  
[3] Mapping the Infrastructure and Malware Ecosystem of MuddyWater — https://www.group-ib.com/blog/muddywater-infrastructure-malware/  
[4] MuddyWater — https://executivegov.com/tag/muddywater/  
[5] ChainShell: MuddyWater & Russian MaaS - SOC Prime — https://socprime.com/active-threats/chainshell-muddywater-russian-maas/  
[6] MuddyWater - Iranian Cyber Espionage Profile - Group-IB — https://www.group-ib.com/masked-actors/muddywater/  
[7] Clearing the Water: Unmasking an Attack Chain of MuddyWater — https://www.huntress.com/blog/muddywater-attack-chain  
[8] Iranian Government-Sponsored Actors Conduct Cyber Operations ... — https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-055a  
[9] MuddyWater - Threat Actor | FortiGuard Labs - Fortinet — https://fortiguard.fortinet.com/threat-actor/5571/muddy-water  
[10] Unmasking MuddyWater's New Malware Toolkit Driving ... - Group-IB — https://www.group-ib.com/blog/muddywater-espionage/  
[11] Purple Team Strategies Enhancing Global Security Posture Through ... — https://www.scribd.com/document/584551074/Purple-Team-Strategies-Enhancing-Global-Security-Posture-Through-Uniting-Red-and-Blue-Teams-With-Adversary-Emulation-David-Routin-Simon-Thoores-Sam  
[12] Iranian Government-Sponsored Actors Conduct Cyber Operations ... — https://www.cybercom.mil/Media/News/Article/2945592/iranian-government-sponsored-actors-conduct-cyber-operations-against-global-gov/  
[13] MuddyWater Attack Chain - demaskowanie irańskiego APT — https://cyberalert.com.pl/articles/muddywater-apt-analysis-2026.html  
[14] MuddyWater Uses DLL Side-Loading in Espionage Campaign … — https://thehackernews.com/2026/05/muddywater-uses-dll-side-loading-in.html  
[15] APT Profile - MUDDYWATER - CYFIRMA — https://www.cyfirma.com/research/apt-profile-muddywater/  
[16] 8 Ransomware Mitigation Strategies to Strengthen Your Defenses — https://www.moxfive.com/blog/8-mitigation-options-to-help-reduce-the-impact-of-a-ransomware-incident  
[17] Uncovering Vulnerabilities of LLM-Assisted Cyber Threat Intelligence — https://arxiv.org/html/2509.23573v1  
[18] MuddyWater Threat Advisory: Iranian Cyber Espionage - HawkEye — https://hawk-eye.io/wp-content/advisories/muddywater-threat-advisory.html  
[19] Ransomware Protection Strategies: Fixing 5 Network Security ... — https://zeronetworks.com/blog/ransomware-protection-strategies  
[20] Chronology of MuddyWater APT Attacks Targeting the Middle East — https://www.genians.co.kr/en/blog/threat_intelligence/muddywater-apt  
[21] Iran-Linked MuddyWater Hackers Target U.S. Networks With New … — https://thehackernews.com/2026/03/iran-linked-muddywater-hackers-target.html  
[22] Guide to Indicators of Compromise, Attack, and Behavior - ANY.RUN — https://any.run/cybersecurity-blog/iocs-iobs-ioas-explained/  
[23] Cyber Threat Feed: Latest Advisories And Intelligence — https://cybersecurityventures.com/esentire-blog/  
[24] Unpacking ClickFix: Darktrace Detection Insights — https://www.darktrace.com/de/blog/unpacking-clickfix-darktraces-detection-of-a-prolific-social-engineering-tactic  
[25] Detection: Windows DLL Search Order Hijacking Hunt with Sysmon — https://research.splunk.com/endpoint/79c7d1fc-64c7-91be-a616-ccda752efe81/  

---

## Metadata

- **Model:** bedrock/nvidia.nemotron-super-3-120b (openai-compat)
- **Stop reason:** budget
- **Duration:** 21m 35s
- **Depth reached:** 4
- **Sources read:** 25
- **Learnings:** 302
- **Verified learnings:** 182
- **Prompt tokens:** 306736
- **Completion tokens:** 104443