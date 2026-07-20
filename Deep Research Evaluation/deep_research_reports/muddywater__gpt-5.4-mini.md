# Produce a full hunt-ready dossier on actor "MuddyWater". I need everything we know: identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps. Use what a seasoned CTI analyst would want to detect, block, hunt, and investigate this entity.



## Summary

MuddyWater is an Iranian government-linked cyberespionage group widely assessed as subordinate to the Ministry of Intelligence and Security (MOIS), and it is tracked under ATT&CK as G0069 with multiple aliases including Earth Vetala, MERCURY, Static Kitten, Seedworm, TEMP.Zagros, Mango Sandstorm, TA450, and MuddyKrill. [2][1] The group has targeted government and private-sector organizations across multiple regions and sectors since at least 2017, using spear-phishing, exploitation of public-facing vulnerabilities, DLL side-loading, legitimate remote monitoring and management (RMM) software, obfuscation, credential theft, cloud staging, and multiple backdoor families to maintain access and exfiltrate data. [2][1][7][8] Across the provided material, the strongest hunt signals are not simple hashes but combinations of attribution artifacts, dual-use tooling, unusual C2 patterns, cloud/file-transfer staging, and specific malware/tool tradecraft such as ScreenConnect, SimpleHelp, Atera, Rclone, makecab.exe, go-socks5 variants, Telegram bot C2, and Starlink-based communications. [1][2] The source set does not provide a complete ATT&CK matrix, Sigma/KQL/Splunk logic, or full mitigation guidance, so this dossier emphasizes high-confidence detection, blocking, hunting, and forensic pivot points only where the sources support them. [1][5][10]

## 1) Identity, aliases, and attribution

MuddyWater is described as an Iranian cyberespionage and advanced persistent threat group widely considered part of, or subordinate to, Iran’s MOIS. [1][2][8] The actor is identified in ATT&CK as G0069. [2] Reported aliases include Earth Vetala, MERCURY, Static Kitten, Seedworm, TEMP.Zagros, Mango Sandstorm, TA450, and MuddyKrill. [2][8]

Attribution in the provided sources is strongest when it is framed as “assessed to align with MuddyWater” rather than as a definitive identification, especially in cases where tooling and infrastructure overlap with other intrusions. [10][1] The sources also note that MuddyWater’s early campaigns were difficult to attribute and were often confused with other intrusion sets, which is an important analytic caveat for retrospective cases and weak-signal sightings. [1] The use of false flags and impersonation of other threat actors is explicitly called out as an attribution and deception artifact, not a blockable IOC by itself. [1]

A separate intrusion report associates the attacker with the username `asuedulimit` used in an SSH command, but that is only an attribution artifact tied to that incident rather than a confirmed identity for the operator. [10]

## 2) Observed tradecraft and ATT&CK-aligned behavior

The provided sources do not contain a complete tactic-by-tactic ATT&CK mapping or technique IDs for MuddyWater, so the mapping below is operationally inferred from named behaviors rather than from a source-provided matrix. [1][5] The group’s long-running tradecraft centers on spear-phishing and exploitation of publicly known vulnerabilities in internet-facing servers for initial access. [1] The sources also state that Iranian threat actors use spear-phishing campaigns and honeytrap operations to gain access to accounts or sensitive information, which is relevant context for MuddyWater activity. [5]

### High-confidence behavior-to-ATT&CK mapping from the sources

| Observed behavior | ATT&CK tactic area | ATT&CK technique family | Source basis |
|---|---|---|---|
| Spear-phishing emails and impersonation of Microsoft security updates | Initial Access | Phishing / impersonation | [1][2] |
| Exploitation of public vulnerabilities in internet-facing servers | Initial Access | Exploit Public-Facing Application | [1] |
| RDP / Terminal Services login as initial access | Initial Access | Remote Services | [10] |
| SSH reverse tunneling with `ssh -R` and disabled host key checking | Command and Control / Lateral Movement support | Remote tunneling / proxying behavior | [10] |
| DLL side-loading with legitimate executables | Defense Evasion / Execution | Masquerading / DLL side-loading | [4][8][10] |
| Node.js scripts launching PowerShell for discovery | Execution / Discovery | Scripting and command interpreter use | [4] |
| Credential dumping and password theft using Mimikatz, procdump64.exe, LaZagne, Browser64 | Credential Access | Credential dumping / browser credential theft | [2] |
| HTTP and web protocols for C2, including non-standard ports 8043 and 8848 | Command and Control | Application-layer protocol / non-standard port C2 | [2] |
| Proxying through compromised websites or go-socks5 variants | Command and Control | Proxy / tunneling | [2] |
| Base64, AES, steganography, Invoke-Obfuscation | Defense Evasion | Obfuscated/encoded files and information | [2] |
| makecab.exe, Rclone, Wasabi, cloud storage staging/exfiltration | Collection / Exfiltration | Archive via utility, exfiltration to cloud | [2][5] |
| Telegram bot C2 | Command and Control | External remote service / messaging platform C2 | [1] |
| Starlink used for C2 communications | Command and Control | Alternate connectivity / commercial satellite internet | [2] |

The sources also describe custom malware and tool families associated with MuddyWater, including POWERSTATS, MuddyViper, RustyWater, Out1, SHARPSTATS, Fooder, LP-Notes, PowGoop, Mori, Small Sieve, STARWHALE, Tsundere Botnet, DCHSpy, Dindoor, Fakeset, Stagecomp, Darkcomp, and others. [2][5][8] MuddyWater also uses custom malware, open-source offensive tools, dual-use utilities, and commodity malware, including ransomware, which makes static detection insufficient on its own. [7] The group has repeatedly introduced new malware variants, infrastructure configurations, and delivery mechanisms, further reducing the reliability of hash-only or single-signature detection. [7]

## 3) Infrastructure, staging, and C2 patterns

MuddyWater’s infrastructure profile in the sources is heterogeneous and intentionally fluid, with multiple transport and staging patterns rather than a single reusable backbone. [1][2][7] The group has used HTTP and other web protocols for C2, including non-standard ports 8043 and 8848. [2] These ports are additionally reported as botnet C2 ports. [2] The group has also proxied traffic through compromised websites or go-socks5 variants, which makes network-layer detections dependent on behavioral correlation rather than destination alone. [2]

The sources also show a preference for leveraging legitimate or third-party services to reduce overt maliciousness. MuddyWater has used domains, web services, and file-sharing services such as OneHub, Sync, and TeraBox to distribute tools. [2] It has used public file-transfer service `sendit[.]sh` to stage stolen data in at least one campaign. [4] It has attempted exfiltration to Wasabi cloud storage through Rclone, and a separate campaign described use of Rclone to a Wasabi bucket for software-company exfiltration. [2][5] The actor has also used commercial satellite internet, specifically Starlink, for C2 communications in late 2025 and early 2026. [2]

A notable infrastructure pattern is that MuddyWater blends malicious C2 with living-off-the-land and legitimate remote access tools. ScreenConnect, SimpleHelp, and Atera are described as used by the group and are better treated as dual-use tooling than as blocking-only indicators. [1] The group has also used nine legitimate RMM tools for persistent remote access, which is a strong pivot for enterprise hunting because it suggests attacker preference for blending into sanctioned administration workflows. [7] Another observed C2 pattern is malware communicating through a Telegram bot rather than relying solely on static file artifacts, indicating messaging-platform C2 as a recurring pattern. [1]

Incident-specific infrastructure from the sources includes attacker-controlled IP `157.20.182.49` as a connection target for a malicious DLL, and `162.0.230.185` as an IP used with SSH in one intrusion. [4][10] Those IPs are suitable for blocking or hunting in the context of those campaigns. [10][4]

## 4) Malware, tooling, and operational workflow

MuddyWater’s tooling stack combines custom backdoors, credential theft utilities, obfuscators, living-off-the-land binaries, and cloud-enabled exfiltration. [2][5][8] The source set explicitly names POWERSTATS, MuddyViper, RustyWater, Out1, SHARPSTATS, Fooder, LP-Notes, PowGoop, Mori, Small Sieve, STARWHALE, Tsundere Botnet, DCHSpy, Dindoor, Fakeset, Stagecomp, and Darkcomp as associated tooling. [2][5][8]

Small Sieve is particularly actionable: `gram_app.exe` is described as an NSIS installer that installs the `index.exe` backdoor and adds a persistence registry key, while `index.exe` is a PyInstaller-bundled Python 3.9 backdoor. [8] That gives defenders a concrete installer-to-backdoor chain to hunt across disk, process lineage, registry persistence, and unusual Python-bundled executables. [8] Dindoor is described as a previously unknown backdoor leveraging the Deno JavaScript runtime for execution, which is operationally valuable because Deno execution on endpoints is uncommon and can be hunted through process and file telemetry. [5]

A major credential-access cluster includes Mimikatz, `procdump64.exe`, LaZagne, and Browser64 for credential dumping and password theft. [2] Another important data-theft technique is ChromElevator, embedded in DLLs to siphon passwords, cookies, and payment card data from Chromium-based browsers and bypass App-Bound Encryption protections. [4] The campaign also used Node.js scripts to launch PowerShell code for discovery and information gathering, which is useful for correlating script-engine usage with downstream recon actions. [4]

MuddyWater also relies on obfuscation and packaging to hide payloads: Base64, AES, steganography, and Invoke-Obfuscation are all named in the sources. [2] The use of `makecab.exe` suggests archiving or staging of data and payloads through built-in Windows functionality. [2] The use of Rclone and cloud storage services such as Wasabi indicates common exfiltration and staging workflows that can be hunted via process, command-line, cloud API, and egress telemetry. [2][5]

## 5) Hunt package: IOCs, pivot points, queries, mitigations, and gaps

### IOC classification

#### Block
These are the strongest block-oriented indicators explicitly supported by the sources, but they should still be time-bounded and campaign-scoped because MuddyWater rotates infrastructure frequently. [7][1]

- `157.20.182.49` as a malicious DLL connection target. [4][10]
- `162.0.230.185` as an SSH-related IP used in one intrusion. [10]
- Support email `support@microsoftonlines[.]com` used in phishing. [2]
- Non-standard C2 ports `8043` and `8848`, when correlated with confirmed MuddyWater activity. [2]

#### Hunt
These are better used as correlation pivots than as blanket blocks because several are dual-use or campaign-specific. [1][2]

- ScreenConnect, SimpleHelp, and Atera usage on systems that should not normally run them. [1]
- Rclone, especially when paired with cloud storage access to Wasabi. [2][5]
- OneHub, Sync, and TeraBox use for tool distribution. [2]
- Telegram bot C2. [1]
- Starlink-based C2 communications. [2]
- Go-socks5 variants and proxying through compromised websites. [2]
- Node.js launching PowerShell. [4]
- Browser credential theft tooling such as Browser64, LaZagne, and Mimikatz. [2]
- Small Sieve artifacts: `gram_app.exe`, `index.exe`. [8]
- Dindoor / Deno runtime execution. [5]

#### Forensics-only
These are attribution or deception artifacts that should not be treated as standalone block indicators. [1][10]

- False flags and impersonation of other threat actors. [1]
- The username `asuedulimit` in the SSH command. [10]
- Assessed-but-not-definitive attribution to MuddyWater in incident reports. [10]
- Campaign-level linkage of Stagecomp/Darkcomp signatures to MuddyWater. [5]

### Practical hunt pivots

The best pivots in the source set are multi-artifact combinations rather than isolated indicators. [7][1] A strong example is legitimate binary abuse plus malicious DLL side-loading: Fortemedia `fmapp.exe` and SentinelOne `sentinelmemoryscanner.exe` were used as signed host binaries to load malicious DLLs. [4] Another is the `FMAPP.exe`/`FMAPP.dll` pair used in an intrusion involving C2 to `157.20.182.49`. [10][4] Yet another is RDP or SSH initial access followed by reverse tunneling and side-loading, which combines access, persistence, and C2 behaviors. [10]

Additional pivots include:
- Python-bundled backdoors and installers, especially `index.exe` from Small Sieve. [8]
- Deno runtime artifacts tied to Dindoor. [5]
- Chromium browser data theft via ChromElevator. [4]
- Cloud storage transfers to Wasabi. [2][5]
- Public file-transfer staging through `sendit[.]sh`. [4]
- Use of Microsoft-themed phishing and fake security-update lures. [2]

### Hunting queries

The sources do not provide Sigma, KQL, or Splunk logic, nor do they specify telemetry requirements for such detections. [1][5] To stay within source limits, the following are hunt patterns rather than executable query language content.

**Windows process hunt pattern**
- Legitimate signed application launching a DLL from the same directory or an unusual user-writable path, especially `fmapp.exe`, `sentinelmemoryscanner.exe`, or `gram_app.exe`. [4][10][8]
- `node.exe` spawning `powershell.exe`. [4]
- `ssh.exe` using `-R` with host key checking disabled. [10]
- `rclone.exe` with Wasabi-related endpoints or cloud bucket arguments. [2][5]

**Endpoint file hunt pattern**
- `index.exe`, `gram_app.exe`, `FMAPP.dll`, Dindoor-related Deno scripts, Fakeset, Stagecomp, Darkcomp, and other MuddyWater-linked tool names. [8][5][4]
- Python-bundled executables in unusual directories, especially when paired with persistence registry keys. [8]

**Network hunt pattern**
- Outbound traffic on ports `8043` or `8848`. [2]
- Telegram bot traffic from endpoints not expected to use messaging-platform C2. [1]
- Starlink-associated communication paths in late 2025/early 2026 campaign windows. [2]
- Egress to `157.20.182.49` or `162.0.230.185`. [4][10]
- Transfers to Wasabi or public file-sharing/file-transfer services like OneHub, Sync, TeraBox, or `sendit[.]sh`. [2][4][5]

### Mitigations

The source set provides very limited defensive guidance. One advisory explicitly recommends prioritizing patching known exploited vulnerabilities. [8] Another says to strengthen monitoring capabilities. [5] Beyond that, the sources do not provide hardening steps, response actions, or a full mitigation playbook. [1][5] Because MuddyWater frequently changes malware and infrastructure, static signature-based blocking is described as unreliable, which implies defenders should emphasize behavioral monitoring and layered detections rather than single-artifact controls. [7]

### Intelligence gaps

The biggest gap is that the sources do not provide a full ATT&CK mapping or technique IDs for the actor, so analytic coverage must be built from observed behaviors rather than a source-native matrix. [1][5] Another gap is detection engineering content: no Sigma, KQL, or Splunk rules are supplied, and no telemetry requirements are enumerated. [1][5] The sources also do not describe mitigations or response procedures in operational detail. [1][5] Attribution uncertainty remains a notable issue because early MuddyWater campaigns were often confused with other intrusion sets, and the provided material also includes cases where “aligned with MuddyWater” is the strongest available language rather than definitive attribution. [1][10] Finally, some campaign details remain unresolved, including whether the Rclone exfiltration attempt succeeded and the exact initial access vector in the South Korean electronics manufacturer intrusion. [5][4]

## Key Findings

- MuddyWater is a long-running Iranian APT associated with MOIS and tracked as G0069 with multiple aliases. [2][1][8]
- The actor’s most reliable detection surfaces are not single hashes but compound behaviors: phishing, side-loading, RMM abuse, cloud staging, obfuscation, and non-standard C2. [1][2][7]
- Legitimate binaries and dual-use tools are central to the group’s tradecraft, including ScreenConnect, SimpleHelp, Atera, Rclone, Node.js, PowerShell, and SSH tunneling. [1][2][4][10]
- Strong hunt pivots include `157.20.182.49`, `162.0.230.185`, ports `8043` and `8848`, `fmapp.exe`/`FMAPP.dll`, `sentinelmemoryscanner.exe`, `gram_app.exe`, `index.exe`, Deno-based Dindoor activity, and cloud/file-transfer staging. [4][10][8][5][2]
- The sources support blocking only a narrow set of campaign-specific indicators; most other artifacts are better treated as hunt and forensic pivots because MuddyWater reuses dual-use tools and rotates infrastructure. [1][7][2]
- Defensive guidance in the source set is thin, but patching known exploited vulnerabilities and improving monitoring are the only explicit recommendations provided. [8][5]

## Gaps

- unverified claims removed
- No source provides a full ATT&CK technique ID mapping or complete tactic-by-tactic matrix for MuddyWater. [1][5]
- No Sigma, KQL, or Splunk detection content is provided. [1][5]
- No telemetry-source requirements are specified for endpoint, network, identity, or cloud detections. [1][5]
- No detailed mitigations, hardening checklist, or incident-response playbook is included. [1][5]
- Some attribution remains uncertain because early activity was confused with other intrusion sets, and some reporting uses “assessed to align with” rather than definitive attribution. [1][10]
- Several campaign details are incomplete, including the success of at least one Rclone exfiltration attempt and the initial access vector in one intrusion. [5][4]
- The sources do not provide comprehensive IOCs such as hashes, full domain lists, certificate fingerprints, or broader infrastructure clusters beyond the named examples. [1][2][4][5]

---

## Sources

[1] MuddyWater (hacker group) - Wikipedia — https://en.wikipedia.org/wiki/MuddyWater_(hacker_group)  
[2] MuddyWater, Earth Vetala, MERCURY, Static Kitten, Seedworm, … — https://attack.mitre.org/groups/G0069/  
[3] MuddyWater — https://executivegov.com/tag/muddywater/  
[4] MuddyWater Uses DLL Side-Loading in Espionage Campaign … — https://thehackernews.com/2026/05/muddywater-uses-dll-side-loading-in.html  
[5] Iran-Linked MuddyWater Hackers Target U.S. Networks With New … — https://thehackernews.com/2026/03/iran-linked-muddywater-hackers-target.html  
[6] Muddy Water Kava - Authentic Kava in St. Petersburg, FL - (727) 520 … — https://www.mwkava.com/  
[7] MuddyWater APT Group | Iranian Cyber Espionage Profile — https://www.group-ib.com/masked-actors/muddywater/  
[8] Iranian Government-Sponsored Actors Conduct Cyber Operations — https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-055a  
[9] Muddy Water Kava, Saint Petersburg - Restaurantji — https://www.restaurantji.com/fl/saint-petersburg/muddy-water-kava-/  
[10] Unmasking an Attack Chain of MuddyWater | Huntress — https://www.huntress.com/blog/muddywater-attack-chain  

---

## Metadata

- **Model:** openai/gpt-5.4-mini (openai-compat)
- **Stop reason:** maxDepth
- **Duration:** 2m 36s
- **Depth reached:** 4
- **Sources read:** 10
- **Learnings:** 157
- **Verified learnings:** 75
- **Prompt tokens:** 61062
- **Completion tokens:** 17672