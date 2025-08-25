# 🔗 Digital Garden Link Health Checker

Automated link health monitoring and maintenance for your digital garden.

## 🌱 Overview

This repository includes an automated link health checking system that:
- **Scans all markdown files** for internal links
- **Detects broken links** and provides fix suggestions
- **Identifies draft content** links that may not be ready for public viewing
- **Runs automatically** on pull requests and weekly maintenance
- **Provides detailed reports** with actionable insights

## 🚀 Quick Start

### Local Usage

```bash
# Basic link health check
python3 link_checker.py

# Generate detailed report
python3 link_checker.py --report link_health_report.md

# Interactive fixing mode (review each fix)
python3 link_checker.py --interactive

# Automatic fixing mode (apply obvious fixes)
python3 link_checker.py --fix

# Check specific directory
python3 link_checker.py --dir content/
```

### GitHub Actions Integration

The link checker runs automatically:

- **📝 On Pull Requests**: Prevents broken links from being merged
- **🔄 On Push to Main**: Validates link health after changes
- **⏰ Weekly Schedule**: Sunday 2 AM UTC maintenance check
- **🎯 Manual Trigger**: Run on-demand with custom options

## 📊 Understanding the Report

### Health Score Indicators
- **🟢 90-100%**: Excellent link health
- **🟡 70-89%**: Good with minor issues
- **🔴 <70%**: Needs attention

### Link Types Detected
- **Wiki Links**: `[[Page Name]]`
- **Markdown Links**: `[text](url)`
- **URL-Encoded Links**: `What%20is%20Digital%20Gardening.md`
- **Directory Links**: `embedded-systems/video4linux-mipi-journey/`

### Issue Categories
- **❌ Broken Links**: Links pointing to non-existent files
- **⚠️ Draft Links**: Links pointing to draft content (not ready for public)

## 🔧 Manual Workflow Triggers

### Basic Health Check
```yaml
# In GitHub Actions tab, run "Digital Garden Link Health Check"
# Uses default settings (check entire repository)
```

### With Automatic Fixes
```yaml
# Manual trigger with inputs:
# - fix_links: true
# - target_directory: . (or specific path)
```

### Directory-Specific Check
```yaml
# Manual trigger with inputs:
# - fix_links: false
# - target_directory: content/specific-section/
```

## 📋 Workflow Features

### Pull Request Integration
- **Automatic Comments**: Link health summary on every PR
- **Status Checks**: Prevents merging if critical issues found
- **Detailed Reports**: Full link analysis attached as artifacts

### Issue Management
- **Auto-Issue Creation**: Creates issues when health drops below 50%
- **Duplicate Prevention**: Won't spam with multiple health alerts
- **Smart Labeling**: `link-health`, `automated`, `maintenance` labels

### Failure Thresholds
- **⚠️ Warning**: Health below 50% (creates issue)
- **💥 Critical**: Health below 25% (fails workflow)

## 🛠️ Configuration

### Customizing Triggers
Edit `.github/workflows/link-health-check.yaml`:

```yaml
# Change schedule (currently Sunday 2 AM UTC)
schedule:
  - cron: "0 2 * * 0"

# Modify file patterns to watch
paths:
  - "**/*.md"
  - "content/**"
  - "source/**"
```

### Adjusting Thresholds
Modify the workflow conditions:

```yaml
# Change warning threshold (default: 50%)
if: parseFloat(steps.link_check.outputs.link_health) < 50

# Change critical threshold (default: 25%)
if: parseFloat(steps.link_check.outputs.link_health) < 25
```

## 📈 Best Practices

### Regular Maintenance
1. **Review Weekly Reports**: Check automated health reports
2. **Fix High-Priority Issues**: Address broken links to main navigation
3. **Update Draft Status**: Move completed content out of drafts
4. **Use Interactive Mode**: `--interactive` for careful manual fixes

### Link Hygiene
- **Use Relative Paths**: `../other-section/page.md` instead of absolute
- **Consistent Naming**: Avoid spaces and special characters in filenames
- **Directory Structure**: Organize content logically for easier linking
- **Draft Management**: Use frontmatter `publish: false` for work-in-progress

### Automation Tips
- **Enable Auto-Fix**: For obvious issues like typos in filenames
- **Monitor Artifacts**: Download detailed reports from workflow runs
- **Set Up Notifications**: Get alerts when health drops significantly

## 🔍 Troubleshooting

### Common Issues

**"No links found"**
- Check file permissions and encoding
- Verify markdown files are in expected locations
- Ensure link patterns match your content style

**"High false positive rate"**
- Review draft detection logic
- Check URL encoding handling
- Verify relative path resolution

**"Workflow fails unexpectedly"**
- Check Python version compatibility
- Verify file system permissions
- Review GitHub Actions logs

### Debug Mode
```bash
# Run with verbose output
python3 link_checker.py --dir . --report debug_report.md

# Check specific file patterns
python3 -c "
import re
content = open('your-file.md').read()
links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
print('Found links:', links)
"
```

## 📚 Advanced Usage

### Custom Link Patterns
Modify `link_checker.py` to support additional link formats:

```python
# Add custom pattern
custom_pattern = re.compile(r'your_pattern_here')
```

### Integration with Other Tools
- **Pre-commit Hooks**: Run link checker before commits
- **CI/CD Pipelines**: Integrate with deployment workflows
- **Documentation Sites**: Validate before publishing

## 🤝 Contributing

To improve the link checker:

1. **Test Changes**: Run on sample content first
2. **Update Documentation**: Keep this README current
3. **Monitor Performance**: Ensure scalability with large repositories
4. **Add Features**: Consider new link types or validation rules

---

## 📊 Current Status

Last updated: 2025-08-26  
Link checker version: 1.0  
Supported link types: 4 (Wiki, Markdown, URL-encoded, Directory)  
Automation level: Full GitHub Actions integration  

---

*This link checker helps maintain the health and navigability of your digital garden by ensuring all internal links work correctly and draft content is properly managed.*
