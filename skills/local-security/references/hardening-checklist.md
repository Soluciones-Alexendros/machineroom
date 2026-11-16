# Hardening Checklist

## Overview

Systematic hardening checklist for Linux hosts. Run after install and quarterly.

## Categories

### 1. Access Control

| Check | Command | Expected |
|-------|---------|----------|
| Root SSH disabled | `sshd -T | grep permitrootlogin` | `permitrootlogin no` |
| Password auth disabled | `sshd -T | grep passwordauthentication` | `passwordauthentication no` |
| Max auth tries | `sshd -T | grep maxauthtries` | `maxauthtries 3` |
| Login grace time | `sshd -T | grep logingracetime` | `logingracetime 30` |
| Allow users/groups | `sshd -T | grep allowusers` | Configured |
| Fail2ban active | `systemctl status fail2ban` | active |

### 2. Kernel Parameters (sysctl)

| Parameter | Value | File |
|-----------|-------|------|
| `net.ipv4.ip_forward` | 0 | `/etc/sysctl.d/99-hardening.conf` |
| `net.ipv4.conf.all.send_redirects` | 0 | |
| `net.ipv4.conf.default.send_redirects` | 0 | |
| `net.ipv4.conf.all.accept_redirects` | 0 | |
| `net.ipv4.conf.default.accept_redirects` | 0 | |
| `net.ipv4.conf.all.secure_redirects` | 0 | |
| `net.ipv4.conf.default.secure_redirects` | 0 | |
| `net.ipv4.icmp_echo_ignore_broadcasts` | 1 | |
| `net.ipv4.icmp_ignore_bogus_error_responses` | 1 | |
| `net.ipv4.tcp_syncookies` | 1 | |
| `net.ipv6.conf.all.forwarding` | 0 | |
| `kernel.dmesg_restrict` | 1 | |
| `kernel.kptr_restrict` | 2 | |
| `kernel.yama.ptrace_scope` | 1 | |
| `fs.suid_dumpable` | 0 | |
| `vm.mmap_rnd_bits` | 32 | |
| `vm.mmap_rnd_compat_bits` | 16 | |

Apply: `sysctl --system`

### 3. Filesystem

| Check | Command | Expected |
|-------|---------|----------|
| /tmp noexec,nodev,nosuid | `findmnt /tmp` | Options include noexec,nodev,nosuid |
| /var/tmp noexec,nodev,nosuid | `findmnt /var/tmp` | Options include noexec,nodev,nosuid |
| /dev/shm noexec,nodev,nosuid | `findmnt /dev/shm` | Options include noexec,nodev,nosuid |
| Home encryption | `lsblk -f` | LUKS on /home |
| Swap encryption | `swapon -s` | Encrypted swap |

### 4. Services

| Service | Action |
|---------|--------|
| avahi-daemon | Disable if not needed |
| cups | Disable if not printing |
| bluetooth | Disable if not needed |
| ModemManager | Disable if no modem |
| NetworkManager-wait-online | Disable if slow boot |

### 5. Auditing

| Check | Command |
|-------|---------|
| auditd installed | `pacman -Q audit` |
| Audit rules loaded | `auditctl -l` |
| Key events logged | `ausearch -k <key>` |

### 6. User Accounts

| Check | Command |
|-------|---------|
| No empty passwords | `awk -F: '($2 == "") {print $1}' /etc/shadow` |
| UID 0 only root | `awk -F: '($3 == 0) {print $1}' /etc/passwd` |
| Password aging | `chage -l <user>` |
| Lock inactive users | `usermod -L <user>` |

### 7. Logging

| Check | Expected |
|-------|----------|
| journald persistent | `Storage=persistent` in `/etc/systemd/journald.conf` |
| Log rotation | `/etc/logrotate.d/*` configured |
| Remote logging | Optional: forward to SIEM |

### 8. Updates

| Check | Command |
|-------|---------|
| Auto-updates enabled | `systemctl status pacman-updates.timer` (Arch) |
| Kernel live patching | `kernel.patches` or `kpatch` |
| Unattended upgrades | `unattended-upgrades` (Debian) |

## Automation

```bash
# Run all checks
./scripts/audit_full.sh --profile hardening

# Generate report
./scripts/report_render.py --input audit.json --output hardening.html
```

## References

- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [Arch Linux Hardening](https://wiki.archlinux.org/title/Security)
- [systemd Security](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)
- [Lynis Auditing](https://cisofy.com/lynis/)