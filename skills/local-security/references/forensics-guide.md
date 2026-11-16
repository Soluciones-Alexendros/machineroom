# Forensics Guide

## Overview

Light forensic record management for Linux hosts. Evidence preservation, log analysis, and incident timeline.

## Principles

1. **Preserve first** — Never modify original evidence
2. **Document everything** — Chain of custody
3. **Use read-only tools** — Mount `/` ro, use `dd` for images
4. **Timestamp everything** — UTC, ISO 8601

## Evidence Collection

### System State Snapshot

```bash
# Create forensic snapshot directory
SNAPSHOT_DIR="/forensics/$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$SNAPSHOT_DIR"

# Process list
ps auxww > "$SNAPSHOT_DIR/processes.txt"
pstree -p > "$SNAPSHOT_DIR/pstree.txt"

# Network connections
ss -tunap > "$SNAPSHOT_DIR/netstat.txt"
netstat -tunap > "$SNAPSHOT_DIR/netstat-legacy.txt"

# Open files
lsof -n > "$SNAPSHOT_DIR/lsof.txt"

# Loaded modules
lsmod > "$SNAPSHOT_DIR/lsmod.txt"

# Kernel messages
dmesg -T > "$SNAPSHOT_DIR/dmesg.txt"

# Systemd state
systemctl list-units --all > "$SNAPSHOT_DIR/systemd-units.txt"
systemctl list-unit-files > "$SNAPSHOT_DIR/systemd-unit-files.txt"
```

### Disk Image (Read-Only)

```bash
# Identify target
lsblk -f

# Create image (use write blocker hardware if available)
dd if=/dev/nvme0n1 of=/forensics/disk-$(date -u +%Y%m%d).img bs=4M status=progress conv=noerror,sync

# Verify hash
sha256sum /forensics/disk-$(date -u +%Y%m%d).img > /forensics/disk-$(date -u +%Y%m%d).img.sha256
```

### Memory Dump (Advanced)

```bash
# Requires LiME kernel module or avml
# avml (AWS)
wget https://github.com/microsoft/avml/releases/latest/download/avml
chmod +x avml
./avml /forensics/memory-$(date -u +%Y%m%d).lime
```

## Log Analysis

### Auth Logs

```bash
# Failed logins
grep "Failed password" /var/log/auth.log | tail -20

# Successful logins
grep "Accepted password" /var/log/auth.log | tail -20

# Sudo usage
grep "sudo:" /var/log/auth.log | tail -20

# SSH key auth
grep "Accepted publickey" /var/log/auth.log
```

### Systemd Journal

```bash
# All logs since boot
journalctl -b

# Last hour
journalctl --since "1 hour ago"

# Specific unit
journalctl -u sshd --since "24 hours ago"

# Priority filter
journalctl -p 3 -b  # errors and above

# Export
journalctl -b --output=json > /forensics/journal-$(date -u +%Y%m%d).json
```

### Auditd Logs

```bash
# Search by key
ausearch -k ssh -ts today

# Search by UID
ausearch -ui 1000 --start today

# Summary
aureport --summary -ts today
aureport --auth -ts today
aureport --file -ts today
```

### Package Manager Logs

```bash
# pacman (Arch)
grep -E "installed|upgraded|removed" /var/log/pacman.log | tail -20

# apt (Debian)
grep -E "install|upgrade|remove" /var/log/apt/history.log

# dnf (RHEL/Fedora)
dnf history list
dnf history info <id>
```

## Timeline Construction

```bash
# Combine timestamps from multiple sources
cat /var/log/auth.log /var/log/syslog /var/log/kern.log | \
  grep -E "$(date +%Y-%m-%d)" | \
  sort > /forensics/timeline-$(date +%Y%m%d).txt

# Using journalctl for unified timeline
journalctl --since "2024-01-15 00:00:00" --until "2024-01-16 00:00:00" \
  --output=short-iso > /forensics/timeline-20240115.txt
```

## Common Indicators

| Indicator | Log Source | Query |
|-----------|------------|-------|
| Brute force | auth.log | `grep "Failed password" | wc -l` |
| Privilege escalation | auth.log, audit | `grep "sudo.*COMMAND" /var/log/auth.log` |
| Persistence | systemd, cron | `systemctl list-unit-files --state=enabled` |
| Data exfil | network, lsof | `ss -tunap | grep ESTAB` |
| Rootkit | chkrootkit, rkhunter | `chkrootkit; rkhunter --check` |

## Automation

```bash
#!/bin/bash
# forensics-collect.sh
set -euo pipefail

OUT="/forensics/$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"

# Collect
collect_system_state "$OUT"
collect_logs "$OUT"
collect_network "$OUT"

# Package
tar -czf "$OUT.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"

echo "Forensic package: $OUT.tar.gz"
```

## Chain of Custody

```markdown
# Evidence Log

| Item | Hash (SHA256) | Collected By | Date (UTC) | Storage Location |
|------|---------------|--------------|------------|------------------|
| disk.img | a1b2c3... | admin | 2024-01-15 14:30:00 | /forensics/disk.img |
| memory.lime | d4e5f6... | admin | 2024-01-15 14:35:00 | /forensics/memory.lime |
| auth.log | 789abc... | admin | 2024-01-15 14:40:00 | /forensics/logs/auth.log |
```

## Tools

| Tool | Purpose |
|------|---------|
| `auditd` | Kernel-level audit |
| `systemd-journald` | Structured logging |
| `chkrootkit` / `rkhunter` | Rootkit scanning |
| `lynis` | Security auditing |
| `avml` | Memory acquisition |
| `volatility3` | Memory analysis |
| `autopsy` / `sleuthkit` | Disk forensics |

## References

- [DFIR Guide](https://dfir.training/)
- [Linux Forensics](https://linuxforensics.info/)
- [Auditd Documentation](https://linux.die.net/man/8/auditd)
- [Systemd Journal](https://www.freedesktop.org/software/systemd/man/journalctl.html)
- [Volatility3](https://github.com/volatilityfoundation/volatility3)