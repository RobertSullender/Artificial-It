# Security Policy

## 🔒 Supported Versions

We provide security updates for the following releases:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## 🚨 Reporting a Vulnerability

We take the security of Artificial-It seriously. If you believe you have found a security vulnerability, please report it to us as described here.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### How to Report

1. **Email:** Send details to our security contact via GitHub Issues (marked as [SECURITY])
   - Alternatively, email directly at: security@github.com/RobertSullender
2. **Include the following information:**
   - Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
   - Full paths of source file(s) related to the vulnerability
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Initial Response:** We will respond within 48 hours to acknowledge receipt of your report.
- **Timeline:** We aim to resolve and disclose security issues within 90 days of initial discovery, unless otherwise agreed upon.
- **Confidentiality:** The vulnerability will be kept confidential until a fix is deployed or you receive written consent from us to make it public.

### Bug Bounty Program (Optional)

We currently offer bug bounties for valid vulnerabilities:
- **Critical** (remote code execution, data breach): $500-$2000
- **High** (privilege escalation, authentication bypass): $300-$1000
- **Medium** (XSS, CSRF, information disclosure): $100-$500

See our [Contributing Guidelines](CONTRIBUTING.md) for more details.

### Preferred Languages

We prefer all communications and reports to be written in English.

## 🔐 Security Best Practices

### For Users

1. Always download the latest version from GitHub
2. Keep dependencies up to date
3. Use strong passwords for your GPU/cloud instances
4. Do not share private keys or credentials in your repository
5. Review downloaded models' licenses and requirements

### For Contributors

1. Follow secure coding practices
2. Review all third-party libraries for vulnerabilities
3. Test changes thoroughly before submitting PRs
4. Report any suspicious activity to maintainers
5. Never commit sensitive data (API keys, passwords)

## 📜 License Notice

This project is licensed under MIT license, which includes:
- Permission to use and modify code freely
- No warranty or liability provisions
- User responsibility for third-party model compliance

See [LICENSE](./LICENSE) for full terms.

---

**Thank you for helping keep Artificial-It secure!** 🙏