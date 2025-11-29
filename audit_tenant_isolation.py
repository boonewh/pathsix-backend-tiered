"""
Tenant Isolation Audit Script

This script scans all route files to verify that every database query
includes proper tenant_id filtering to maintain multi-tenant isolation.

Run this script periodically to ensure no queries bypass tenant boundaries.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Entities that MUST be filtered by tenant_id
TENANT_ENTITIES = [
    'Client', 'Lead', 'Project', 'Interaction', 'Contact',
    'ActivityLog', 'File', 'Account', 'UserPreference'
]

# Queries on these entities don't need tenant filtering
TENANT_AGNOSTIC_ENTITIES = ['User', 'Role', 'Tenant']

# Known safe patterns (queries that are already filtered by relationship)
SAFE_PATTERNS = [
    r'session\.query\(User\)\.get\(',  # Direct ID lookup
    r'\.scalar_subquery\(\)',  # Subqueries used in filters
    r'\.joinedload\(',  # Eager loading relationships
    r'\.selectinload\(',  # Eager loading relationships
]


def find_queries_in_file(filepath: str) -> List[Dict]:
    """Extract all database queries from a Python file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    queries = []
    query_pattern = r'session\.query\((\w+)\)'
    
    for i, line in enumerate(lines, 1):
        matches = re.finditer(query_pattern, line)
        for match in matches:
            entity = match.group(1)
            queries.append({
                'file': filepath,
                'line': i,
                'entity': entity,
                'code': line.strip(),
                'full_context': '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
            })
    
    return queries


def is_safe_query(query: Dict) -> Tuple[bool, str]:
    """
    Determine if a query is safe (doesn't need explicit tenant filtering).
    
    Returns:
        (is_safe, reason)
    """
    entity = query['entity']
    code = query['code']
    context = query['full_context']
    
    # Check if entity is tenant-agnostic
    if entity in TENANT_AGNOSTIC_ENTITIES:
        return True, f"{entity} is tenant-agnostic"
    
    # Check if entity doesn't require tenant filtering
    if entity not in TENANT_ENTITIES:
        return True, f"{entity} not in tenant entities list"
    
    # Check for explicit tenant_id filter
    if 'tenant_id' in context:
        return True, "tenant_id filter found in context"
    
    # Check for safe patterns
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, code):
            return True, f"Matches safe pattern: {pattern}"
    
    # Check if it's a relationship query (filtered by parent)
    if re.search(r'\.\w+\s*=\s*session\.query', context):
        return True, "Appears to be a relationship assignment"
    
    return False, "No tenant filtering detected"


def audit_routes_directory():
    """Audit all route files for tenant isolation."""
    routes_dir = Path(__file__).parent / 'app' / 'routes'
    
    all_queries = []
    for py_file in routes_dir.glob('*.py'):
        if py_file.name.startswith('__'):
            continue
        queries = find_queries_in_file(str(py_file))
        all_queries.extend(queries)
    
    print(f"🔍 Audit: Tenant Isolation Check")
    print(f"=" * 80)
    print(f"Scanning {len(all_queries)} database queries...\n")
    
    violations = []
    warnings = []
    safe_count = 0
    
    for query in all_queries:
        is_safe, reason = is_safe_query(query)
        
        if not is_safe:
            # Check if it's a known special case
            if query['entity'] == 'User' and 'filter_by(email=' in query['code']:
                warnings.append((query, "User lookup by email (auth context)"))
            elif query['entity'] == 'Role':
                warnings.append((query, "Role lookup (global entity)"))
            else:
                violations.append((query, reason))
        else:
            safe_count += 1
    
    # Report violations
    if violations:
        print(f"❌ VIOLATIONS FOUND ({len(violations)}):")
        print(f"-" * 80)
        for query, reason in violations:
            print(f"\nFile: {query['file']}")
            print(f"Line: {query['line']}")
            print(f"Entity: {query['entity']}")
            print(f"Reason: {reason}")
            print(f"Code: {query['code']}")
            print()
    
    # Report warnings
    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        print(f"-" * 80)
        for query, note in warnings:
            print(f"\nFile: {query['file']}")
            print(f"Line: {query['line']}")
            print(f"Note: {note}")
            print(f"Code: {query['code']}")
            print()
    
    # Summary
    print(f"=" * 80)
    print(f"✅ Safe queries: {safe_count}")
    print(f"⚠️  Warnings: {len(warnings)}")
    print(f"❌ Violations: {len(violations)}")
    print()
    
    if violations:
        print("🚨 ACTION REQUIRED: Fix the violations above to ensure tenant isolation.")
        return False
    elif warnings:
        print("✓ No critical violations, but review warnings above.")
        return True
    else:
        print("🎉 All queries properly enforce tenant isolation!")
        return True


if __name__ == '__main__':
    success = audit_routes_directory()
    exit(0 if success else 1)
