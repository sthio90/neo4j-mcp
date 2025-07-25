#!/usr/bin/env python3
"""
Validation script for the Neo4j MCP Server Demo
Checks the implementation for common issues without requiring a running server.
"""

import os
import json
import re
from pathlib import Path
import sys

def check_file_exists(filepath):
    """Check if a file exists and is readable."""
    path = Path(filepath)
    if not path.exists():
        return False, f"File not found: {filepath}"
    if not path.is_file():
        return False, f"Not a file: {filepath}"
    if not os.access(path, os.R_OK):
        return False, f"File not readable: {filepath}"
    return True, "OK"

def validate_html():
    """Validate the HTML file structure and content."""
    html_path = Path(__file__).parent / "index.html"
    exists, msg = check_file_exists(html_path)
    if not exists:
        return False, msg
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    # Check for required elements
    required_elements = [
        '<script src="mcp-client.js"',
        '<link rel="stylesheet" href="styles.css"',
        'id="connect-btn"',
        'id="server-url"',
        'id="results"',
        'onclick="getPatientInfo()"',
        'onclick="searchNotes()"',
        'onclick="listDiagnoses()"',
        'onclick="naturalQuery()"'
    ]
    
    missing = []
    for element in required_elements:
        if element not in content:
            missing.append(element)
    
    if missing:
        return False, f"Missing HTML elements: {', '.join(missing)}"
    
    # Check for all 8 tabs
    tabs = ['patient', 'search-notes', 'diagnoses', 'medications', 
            'procedures', 'lab-events', 'natural-query', 'schema']
    for tab in tabs:
        if f'id="{tab}-tab"' not in content:
            return False, f"Missing tab: {tab}"
    
    return True, "HTML structure looks good"

def validate_javascript():
    """Validate the JavaScript file."""
    js_path = Path(__file__).parent / "mcp-client.js"
    exists, msg = check_file_exists(js_path)
    if not exists:
        return False, msg
    
    with open(js_path, 'r') as f:
        content = f.read()
    
    # Check for required functions
    required_functions = [
        'class MCPClient',
        'async connect()',
        'async callTool(',
        'async getPatientInfo()',
        'async searchNotes()',
        'async listDiagnoses()',
        'async naturalQuery()',
        'displayResults(',
        'showTab('
    ]
    
    missing = []
    for func in required_functions:
        if func not in content:
            missing.append(func)
    
    if missing:
        return False, f"Missing JavaScript functions: {', '.join(missing)}"
    
    # Check for all tool implementations
    tools = ['ehr_patient', 'ehr_search_notes', 'ehr_list_diagnoses', 
             'ehr_list_medications', 'ehr_list_procedures', 'ehr_list_lab_events',
             'ehr_natural_query', 'ehr_get_schema']
    
    for tool in tools:
        if f"'{tool}'" not in content and f'"{tool}"' not in content:
            return False, f"Missing tool implementation: {tool}"
    
    return True, "JavaScript implementation looks complete"

def validate_css():
    """Validate the CSS file."""
    css_path = Path(__file__).parent / "styles.css"
    exists, msg = check_file_exists(css_path)
    if not exists:
        return False, msg
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for key styles
    required_styles = [
        '.container',
        '.tab-button',
        '.tab-content',
        '.results',
        '.loading',
        '.status-indicator',
        '.primary-btn'
    ]
    
    missing = []
    for style in required_styles:
        if style not in content:
            missing.append(style)
    
    if missing:
        return False, f"Missing CSS styles: {', '.join(missing)}"
    
    return True, "CSS styles look complete"

def validate_server_script():
    """Validate the HTTP server script."""
    server_path = Path(__file__).parent / "run_http_server.py"
    exists, msg = check_file_exists(server_path)
    if not exists:
        return False, msg
    
    with open(server_path, 'r') as f:
        content = f.read()
    
    # Check for required imports and functionality
    required_elements = [
        'from mcp',
        'from src.mcp_server_neo4j_ehr import create_server',
        'http_server',
        'cors_headers',
        'Access-Control-Allow-Origin',
        'port = 8080'
    ]
    
    missing = []
    for element in required_elements:
        if element not in content:
            missing.append(element)
    
    if missing:
        return False, f"Missing server elements: {', '.join(missing)}"
    
    # Check if executable
    if not os.access(server_path, os.X_OK):
        return False, "Server script is not executable (run: chmod +x run_http_server.py)"
    
    return True, "Server script looks good"

def validate_readme():
    """Validate the README file."""
    readme_path = Path(__file__).parent / "README.md"
    exists, msg = check_file_exists(readme_path)
    if not exists:
        return False, msg
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        '## Overview',
        '## Prerequisites',
        '## Quick Start',
        '## Using the Demo',
        '## Troubleshooting'
    ]
    
    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)
    
    if missing:
        return False, f"Missing README sections: {', '.join(missing)}"
    
    return True, "README documentation looks complete"

def check_javascript_syntax():
    """Basic JavaScript syntax validation."""
    js_path = Path(__file__).parent / "mcp-client.js"
    with open(js_path, 'r') as f:
        content = f.read()
    
    # Count braces and brackets
    open_braces = content.count('{')
    close_braces = content.count('}')
    open_brackets = content.count('[')
    close_brackets = content.count(']')
    open_parens = content.count('(')
    close_parens = content.count(')')
    
    issues = []
    if open_braces != close_braces:
        issues.append(f"Brace mismatch: {open_braces} open, {close_braces} close")
    if open_brackets != close_brackets:
        issues.append(f"Bracket mismatch: {open_brackets} open, {close_brackets} close")
    if open_parens != close_parens:
        issues.append(f"Parenthesis mismatch: {open_parens} open, {close_parens} close")
    
    if issues:
        return False, f"Syntax issues: {'; '.join(issues)}"
    
    return True, "Basic syntax checks passed"

def main():
    """Run all validation checks."""
    print("🔍 Validating Neo4j MCP Server Demo Implementation\n")
    
    checks = [
        ("HTML File", validate_html),
        ("JavaScript File", validate_javascript),
        ("CSS File", validate_css),
        ("Server Script", validate_server_script),
        ("README File", validate_readme),
        ("JavaScript Syntax", check_javascript_syntax)
    ]
    
    all_passed = True
    results = []
    
    for name, check_func in checks:
        try:
            passed, message = check_func()
            results.append((name, passed, message))
            if not passed:
                all_passed = False
        except Exception as e:
            results.append((name, False, f"Error: {str(e)}"))
            all_passed = False
    
    # Display results
    print("Validation Results:")
    print("-" * 50)
    
    for name, passed, message in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}: {message}")
    
    print("-" * 50)
    
    if all_passed:
        print("\n✅ All validation checks passed!")
        print("\nNext steps:")
        print("1. Set up your .env file with Neo4j credentials")
        print("2. Run: cd demo && python run_http_server.py")
        print("3. Open demo/index.html in your browser")
        print("4. Click Connect and start testing!")
    else:
        print("\n❌ Some validation checks failed.")
        print("Please fix the issues above before running the demo.")
        sys.exit(1)

if __name__ == "__main__":
    main()