#!/usr/bin/env python3
"""
Pattern Checker - Utility to inspect and test text replacement patterns.

This script helps you:
1. View all current patterns
2. Test patterns against sample text
3. Add new patterns
4. Modify existing patterns
"""

import re
from enhanced_text_processor import EnhancedTextProcessor


def show_all_patterns():
    """Display all current patterns in a readable format."""
    processor = EnhancedTextProcessor()
    patterns = processor.get_replacement_patterns()
    
    print("=" * 80)
    print("CURRENT TEXT REPLACEMENT PATTERNS")
    print("=" * 80)
    print()
    
    for category, config in patterns.items():
        print(f"📋 {category.upper()}")
        print(f"   Replacement: '{config['replacement']}'")
        print(f"   Patterns:")
        for i, pattern in enumerate(config['patterns'], 1):
            print(f"     {i}. {pattern}")
        print()


def show_circular_pattern():
    """Display the circular pattern checking order."""
    print("=" * 80)
    print("CIRCULAR PATTERN CHECKING ORDER")
    print("=" * 80)
    print()
    print("When a label is found at position D20, adjacent cells are checked in this order:")
    print()
    
    # This matches the pattern in enhanced_text_processor.py
    circular_pattern = [
        (0, 1, 10, "right"),           # D20 -> E20 (most common)
        (0, 2, 8, "right+2"),          # D20 -> F20
        (1, 0, 7, "below"),            # D20 -> D21 
        (-1, 0, 6, "above"),           # D20 -> D19
        (1, 1, 5, "below-right"),      # D20 -> E21
        (-1, 1, 5, "above-right"),     # D20 -> E19
        (0, -1, 4, "left"),            # D20 -> C20
        (1, -1, 3, "below-left"),      # D20 -> C21
        (-1, -1, 3, "above-left"),     # D20 -> C19
        (0, 3, 2, "right+3"),          # D20 -> G20
        (2, 0, 2, "below+2"),          # D20 -> D22
        (-2, 0, 2, "above+2"),         # D20 -> D18
    ]
    
    print("Priority | From D20 | Direction    | Description")
    print("-" * 60)
    for row_offset, col_offset, priority, description in circular_pattern:
        # Calculate target position from D20 (row=20, col=4)
        target_row = 20 + row_offset
        target_col = 4 + col_offset
        target_cell = f"{chr(64 + target_col)}{target_row}"
        print(f"{priority:8d} | {target_cell:8s} | {description:12s} | Adjacent cell check")


def test_pattern(text, category=None):
    """Test if a text matches any patterns."""
    processor = EnhancedTextProcessor()
    patterns = processor.get_replacement_patterns()
    
    print(f"\n🔍 Testing text: '{text}'")
    print("-" * 50)
    
    matches = []
    
    if category:
        # Test specific category
        if category in patterns:
            config = patterns[category]
            for pattern in config['patterns']:
                regex = re.compile(pattern, re.IGNORECASE)
                if regex.search(text):
                    matches.append((category, pattern, config['replacement']))
        else:
            print(f"❌ Category '{category}' not found!")
            return
    else:
        # Test all categories
        for cat, config in patterns.items():
            for pattern in config['patterns']:
                regex = re.compile(pattern, re.IGNORECASE)
                if regex.search(text):
                    matches.append((cat, pattern, config['replacement']))
    
    if matches:
        print("✅ Matches found:")
        for cat, pattern, replacement in matches:
            print(f"  Category: {cat}")
            print(f"  Pattern:  {pattern}")
            print(f"  Replace:  {replacement}")
            print()
    else:
        print("❌ No matches found")


def interactive_pattern_tester():
    """Interactive pattern testing."""
    print("=" * 80)
    print("INTERACTIVE PATTERN TESTER")
    print("=" * 80)
    print("Enter text to test against patterns (or 'quit' to exit)")
    print()
    
    while True:
        text = input("Enter text to test: ").strip()
        
        if text.lower() in ['quit', 'exit', 'q']:
            break
        
        if not text:
            continue
            
        test_pattern(text)
        print()


def show_examples():
    """Show example texts that match each pattern."""
    print("=" * 80)
    print("PATTERN EXAMPLES")
    print("=" * 80)
    print()
    
    examples = {
        'date': [
            'Date: 2024-01-15',
            'Dated: 2024/12/31', 
            '2025-03-20'
        ],
        'date_label': [
            'Date:',
            'Invoice Date:',
            'Contract Date:'
        ],
        'contract_no': [
            'Contract No: ABC-123',
            'Contract: DEF/2024/001',
            'Cont. No: GHI-456'
        ],
        'invoice_no': [
            'Invoice No: INV-2024-001',
            'Inv. No: 12345',
            'Bill No: BILL/2024/123'
        ],
        'ref_no': [
            'Ref. No: REF-001',
            'Reference No: ABC/123',
            'Our Ref: XYZ-456'
        ],
        'etd': [
            'ETD: 2024-02-01',
            'Estimated Time of Departure: 2024/03/15',
            'Departure: 2025-01-30'
        ]
    }
    
    for category, example_list in examples.items():
        print(f"📋 {category.upper()} examples:")
        for example in example_list:
            print(f"  ✅ '{example}'")
        print()


def main():
    """Main function with menu options."""
    while True:
        print("\n" + "=" * 80)
        print("PATTERN CHECKER MENU")
        print("=" * 80)
        print("1. Show all patterns")
        print("2. Show circular pattern order")
        print("3. Test specific text")
        print("4. Interactive pattern tester")
        print("5. Show pattern examples")
        print("6. Exit")
        print()
        
        choice = input("Choose an option (1-6): ").strip()
        
        if choice == '1':
            show_all_patterns()
        elif choice == '2':
            show_circular_pattern()
        elif choice == '3':
            text = input("Enter text to test: ").strip()
            if text:
                test_pattern(text)
        elif choice == '4':
            interactive_pattern_tester()
        elif choice == '5':
            show_examples()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main() 