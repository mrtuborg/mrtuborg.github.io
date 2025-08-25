#!/usr/bin/env python3
"""
Digital Garden Link Checker and Fixer

This script scans all markdown files in your digital garden to:
1. Find broken internal links
2. Suggest fixes for common link issues
3. Generate a report of link health
4. Optionally fix links automatically

Usage:
    python link_checker.py                    # Check links only
    python link_checker.py --fix             # Check and fix links
    python link_checker.py --report          # Generate detailed report
    python link_checker.py --interactive     # Interactive fixing mode
"""

import os
import re
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import unquote
import difflib

class DigitalGardenLinkChecker:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.markdown_files: Dict[str, Path] = {}
        self.all_links: Dict[str, List[Dict]] = {}
        self.broken_links: List[Dict] = []
        self.draft_links: List[Dict] = []
        self.suggestions: Dict[str, List[str]] = {}
        
        # Common link patterns
        self.wiki_link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        self.markdown_link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
        self.relative_link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)')
        
        print(f"🌱 Initializing Digital Garden Link Checker")
        print(f"📁 Root directory: {self.root_dir}")
        
    def scan_files(self):
        """Scan all markdown files in the digital garden."""
        print("\n🔍 Scanning markdown files...")
        
        for md_file in self.root_dir.rglob("*.md"):
            # Skip hidden files and directories
            if any(part.startswith('.') for part in md_file.parts):
                continue
                
            relative_path = md_file.relative_to(self.root_dir)
            
            # Create multiple possible reference formats
            self.markdown_files[str(relative_path)] = md_file
            self.markdown_files[str(relative_path.with_suffix(''))] = md_file
            self.markdown_files[md_file.name] = md_file
            self.markdown_files[md_file.stem] = md_file
            
        print(f"📄 Found {len(set(self.markdown_files.values()))} markdown files")
        
    def extract_links(self):
        """Extract all links from markdown files."""
        print("\n🔗 Extracting links...")
        
        processed_files = set()
        for file_key, file_path in self.markdown_files.items():
            if file_path in processed_files:
                continue  # Skip duplicates
            processed_files.add(file_path)
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                links = []
                
                # Extract wiki-style links [[Link]]
                for match in self.wiki_link_pattern.finditer(content):
                    link_text = match.group(1)
                    links.append({
                        'type': 'wiki',
                        'text': link_text,
                        'target': link_text,
                        'line': content[:match.start()].count('\n') + 1,
                        'match': match
                    })
                
                # Extract markdown links [text](url)
                for match in self.markdown_link_pattern.finditer(content):
                    link_text = match.group(1)
                    link_url = match.group(2)
                    
                    # Skip external links
                    if link_url.startswith(('http://', 'https://', 'mailto:', '#')):
                        continue
                        
                    links.append({
                        'type': 'markdown',
                        'text': link_text,
                        'target': link_url,
                        'line': content[:match.start()].count('\n') + 1,
                        'match': match
                    })
                
                if links:
                    self.all_links[str(file_path.relative_to(self.root_dir))] = links
                    
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
                
        total_links = sum(len(links) for links in self.all_links.values())
        print(f"🔗 Found {total_links} internal links")
        
    def check_links(self):
        """Check all links for validity and draft status."""
        print("\n🔍 Checking link validity...")
        
        for source_file, links in self.all_links.items():
            source_path = self.root_dir / source_file
            
            for link in links:
                target = link['target']
                is_broken = False
                is_draft = False
                suggestions = []
                target_file_path = None
                
                if link['type'] == 'wiki':
                    # Check wiki-style links [[Target]]
                    possible_targets = [
                        target,
                        target + '.md',
                        target.replace(' ', '-').lower(),
                        target.replace(' ', '-').lower() + '.md',
                        target.replace(' ', '%20'),
                        target.replace(' ', '%20') + '.md'
                    ]
                    
                    found = False
                    for possible_target in possible_targets:
                        if possible_target in self.markdown_files:
                            found = True
                            target_file_path = self.markdown_files[possible_target]
                            break
                            
                    if not found:
                        is_broken = True
                        suggestions = self._find_similar_files(target)
                        
                elif link['type'] == 'markdown':
                    # Check markdown links [text](target)
                    target_path = None
                    
                    if target.startswith('/'):
                        # Absolute path from root
                        target_path = self.root_dir / target.lstrip('/')
                    else:
                        # Relative path from current file
                        target_path = source_path.parent / target
                        
                    # Decode URL encoding
                    target_path = Path(unquote(str(target_path)))
                    
                    if not target_path.exists():
                        is_broken = True
                        suggestions = self._find_similar_files(target_path.name)
                    else:
                        target_file_path = target_path
                        
                # Check if target file is a draft (only if link is not broken)
                if not is_broken and target_file_path:
                    is_draft = self._is_draft_file(target_file_path)
                    
                if is_broken:
                    self.broken_links.append({
                        'source_file': source_file,
                        'link': link,
                        'suggestions': suggestions
                    })
                elif is_draft and target_file_path:
                    self.draft_links.append({
                        'source_file': source_file,
                        'link': link,
                        'target_file': str(target_file_path.relative_to(self.root_dir))
                    })
                    
        print(f"❌ Found {len(self.broken_links)} broken links")
        print(f"⚠️  Found {len(self.draft_links)} links to draft content")
        
    def _find_similar_files(self, target: str) -> List[str]:
        """Find similar file names for suggestions."""
        target_clean = target.replace('.md', '').replace('%20', ' ').lower()
        
        suggestions = []
        all_files = list(set(self.markdown_files.keys()))
        
        # Find close matches
        close_matches = difflib.get_close_matches(
            target_clean, 
            [f.replace('.md', '').lower() for f in all_files], 
            n=3, 
            cutoff=0.6
        )
        
        for match in close_matches:
            # Find the original filename
            for file_key in all_files:
                if file_key.replace('.md', '').lower() == match:
                    suggestions.append(file_key)
                    break
                    
        return suggestions[:3]  # Limit to top 3 suggestions
        
    def _is_draft_file(self, file_path: Path) -> bool:
        """Check if a file is marked as draft."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for draft: true in frontmatter
            frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL | re.MULTILINE)
            match = frontmatter_pattern.match(content)
            
            if match:
                frontmatter = match.group(1)
                # Check for draft: true or publish: false
                if re.search(r'draft:\s*true', frontmatter, re.IGNORECASE):
                    return True
                if re.search(r'publish:\s*false', frontmatter, re.IGNORECASE):
                    return True
                    
            # Check if file is in drafts/ directory
            if 'drafts/' in str(file_path) or '/drafts/' in str(file_path):
                return True
                
        except Exception as e:
            print(f"⚠️  Error checking draft status for {file_path}: {e}")
            
        return False
        
    def generate_report(self) -> str:
        """Generate a detailed report of link health."""
        report = []
        report.append("# Digital Garden Link Health Report")
        report.append(f"Generated: {Path.cwd()}")
        report.append("")
        
        # Summary
        total_files = len(set(self.markdown_files.values()))
        total_links = sum(len(links) for links in self.all_links.values())
        broken_count = len(self.broken_links)
        draft_count = len(self.draft_links)
        health_percentage = ((total_links - broken_count) / total_links * 100) if total_links > 0 else 100
        
        report.append("## Summary")
        report.append(f"- **Total Files**: {total_files}")
        report.append(f"- **Total Links**: {total_links}")
        report.append(f"- **Broken Links**: {broken_count}")
        report.append(f"- **Draft Links**: {draft_count}")
        report.append(f"- **Link Health**: {health_percentage:.1f}%")
        report.append("")
        
        if broken_count == 0 and draft_count == 0:
            report.append("🎉 **All links are working perfectly and no draft links found!**")
            return "\n".join(report)
        elif broken_count == 0:
            report.append("✅ **All links are working!**")
            if draft_count > 0:
                report.append(f"⚠️  **Warning: {draft_count} links point to draft content**")
            report.append("")
            
        # Broken links by file
        report.append("## Broken Links by File")
        
        broken_by_file = {}
        for broken in self.broken_links:
            source = broken['source_file']
            if source not in broken_by_file:
                broken_by_file[source] = []
            broken_by_file[source].append(broken)
            
        for source_file, broken_links in broken_by_file.items():
            report.append(f"### {source_file}")
            
            for broken in broken_links:
                link = broken['link']
                report.append(f"- **Line {link['line']}**: `{link['target']}`")
                
                if broken['suggestions']:
                    report.append("  - **Suggestions**:")
                    for suggestion in broken['suggestions']:
                        report.append(f"    - `{suggestion}`")
                else:
                    report.append("  - **No similar files found**")
                report.append("")
        
        # Draft links warnings
        if self.draft_links:
            report.append("## ⚠️ Links to Draft Content")
            report.append("")
            report.append("The following links point to draft content that may not be ready for public viewing:")
            report.append("")
            
            draft_by_file = {}
            for draft in self.draft_links:
                source = draft['source_file']
                if source not in draft_by_file:
                    draft_by_file[source] = []
                draft_by_file[source].append(draft)
                
            for source_file, draft_links in draft_by_file.items():
                report.append(f"### {source_file}")
                
                for draft in draft_links:
                    link = draft['link']
                    target_file = draft['target_file']
                    report.append(f"- **Line {link['line']}**: `{link['target']}` → `{target_file}`")
                    report.append(f"  - **Warning**: This link points to draft content")
                report.append("")
                
        # Quick fixes
        report.append("## Quick Fix Commands")
        report.append("```bash")
        report.append("# Run with --fix to automatically fix obvious issues")
        report.append("python link_checker.py --fix")
        report.append("")
        report.append("# Run in interactive mode to review each fix")
        report.append("python link_checker.py --interactive")
        report.append("```")
        
        return "\n".join(report)
        
    def fix_links(self, interactive: bool = False) -> int:
        """Fix broken links automatically or interactively."""
        if not self.broken_links:
            print("✅ No broken links to fix!")
            return 0
            
        fixes_applied = 0
        
        print(f"\n🔧 {'Interactive' if interactive else 'Automatic'} link fixing mode")
        
        for broken in self.broken_links:
            source_file = broken['source_file']
            link = broken['link']
            suggestions = broken['suggestions']
            
            if not suggestions:
                print(f"❌ No suggestions for: {link['target']} in {source_file}")
                continue
                
            best_suggestion = suggestions[0]
            
            if interactive:
                print(f"\n📄 File: {source_file}")
                print(f"🔗 Broken link: {link['target']} (line {link['line']})")
                print("💡 Suggestions:")
                for i, suggestion in enumerate(suggestions):
                    print(f"  {i+1}. {suggestion}")
                    
                choice = input("Choose fix (1-{}, s=skip, q=quit): ".format(len(suggestions)))
                
                if choice.lower() == 'q':
                    break
                elif choice.lower() == 's':
                    continue
                elif choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                    best_suggestion = suggestions[int(choice) - 1]
                else:
                    continue
                    
            # Apply the fix
            if self._apply_fix(source_file, link, best_suggestion):
                fixes_applied += 1
                print(f"✅ Fixed: {link['target']} → {best_suggestion}")
            else:
                print(f"❌ Failed to fix: {link['target']}")
                
        print(f"\n🎉 Applied {fixes_applied} fixes")
        return fixes_applied
        
    def _apply_fix(self, source_file: str, link: Dict, new_target: str) -> bool:
        """Apply a single link fix to a file."""
        try:
            file_path = self.root_dir / source_file
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Create the replacement based on link type
            if link['type'] == 'wiki':
                old_pattern = f"[[{link['target']}]]"
                new_pattern = f"[[{new_target}]]"
            else:  # markdown
                old_pattern = f"[{link['text']}]({link['target']})"
                new_pattern = f"[{link['text']}]({new_target})"
                
            # Replace the specific occurrence
            new_content = content.replace(old_pattern, new_pattern, 1)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
                
        except Exception as e:
            print(f"Error fixing link in {source_file}: {e}")
            
        return False
        
    def run_check(self, fix: bool = False, interactive: bool = False, report_file: Optional[str] = None):
        """Run the complete link checking process."""
        self.scan_files()
        self.extract_links()
        self.check_links()
        
        # Generate and display report
        report = self.generate_report()
        print("\n" + "="*60)
        print(report)
        
        if report_file:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Report saved to: {report_file}")
            
        # Apply fixes if requested
        if fix or interactive:
            self.fix_links(interactive=interactive)
            
            # Re-check after fixes
            if self.broken_links:
                print("\n🔄 Re-checking links after fixes...")
                self.broken_links = []
                self.check_links()
                
                if self.broken_links:
                    print(f"⚠️  {len(self.broken_links)} links still need manual attention")
                else:
                    print("🎉 All links are now working!")

def main():
    parser = argparse.ArgumentParser(
        description="Check and fix links in your digital garden",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python link_checker.py                    # Check links only
  python link_checker.py --fix             # Check and fix links automatically
  python link_checker.py --interactive     # Interactive fixing mode
  python link_checker.py --report health.md # Save report to file
  python link_checker.py --dir /path/to/garden # Check different directory
        """
    )
    
    parser.add_argument(
        '--fix', 
        action='store_true',
        help='Automatically fix broken links where possible'
    )
    
    parser.add_argument(
        '--interactive', 
        action='store_true',
        help='Interactive mode - review each fix before applying'
    )
    
    parser.add_argument(
        '--report', 
        type=str,
        help='Save detailed report to specified file'
    )
    
    parser.add_argument(
        '--dir', 
        type=str, 
        default='.',
        help='Directory to scan (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Initialize and run checker
    checker = DigitalGardenLinkChecker(args.dir)
    checker.run_check(
        fix=args.fix,
        interactive=args.interactive,
        report_file=args.report
    )

if __name__ == "__main__":
    main()
