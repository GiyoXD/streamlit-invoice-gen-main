"""
HeaderLayoutUpdater - Updates header spans AND column positions.

This module provides functionality to update both colspan/rowspan values and 
column positions for headers based on Excel analysis data and col_id mappings.
"""

from typing import Dict, Any, List
import logging


class HeaderLayoutUpdaterError(Exception):
    """Custom exception for HeaderLayoutUpdater errors."""
    pass


class HeaderLayoutUpdater:
    """Updates header spans AND column positions based on Excel analysis data and col_id mappings."""
    
    def __init__(self, excel_analysis_data=None):
        """Initialize HeaderLayoutUpdater."""
        self.logger = logging.getLogger(__name__)
        self.excel_analysis_data = excel_analysis_data
        
        # Define span rules based on col_id patterns (fallback for when analysis data is not available)
        # These can be configured based on your Excel layouts
        self.span_rules = {
            # Quantity columns often span multiple sub-columns
            'col_qty_sf': {'colspan': 1, 'rowspan': 1},  # Default for most cases
            'col_qty_pcs': {'colspan': 1, 'rowspan': 1},
            'col_qty': {'colspan': 2, 'rowspan': 1},  # When quantity spans both PCS and SF
            
            # Description columns that might span multiple columns
            'col_desc': {'colspan': 1, 'rowspan': 1},  # Default
            
            # Headers that might span multiple rows in complex layouts
            'col_static': {'colspan': 1, 'rowspan': 2},  # Mark & No often spans 2 rows
            'col_pallet': {'colspan': 1, 'rowspan': 2},
            'col_po': {'colspan': 1, 'rowspan': 2},
            'col_item': {'colspan': 1, 'rowspan': 2},
            'col_net': {'colspan': 1, 'rowspan': 2},
            'col_gross': {'colspan': 1, 'rowspan': 2},
            'col_cbm': {'colspan': 1, 'rowspan': 2},
            
            # Standard columns
            'col_no': {'colspan': 1, 'rowspan': 1},
            'col_unit_price': {'colspan': 1, 'rowspan': 1},
            'col_amount': {'colspan': 1, 'rowspan': 1},
        }
        
    def _analyze_spans_from_excel_data(self, sheet_name: str) -> Dict[str, Dict[str, int]]:
        """
        Analyze actual spans from Excel analysis data.
        
        Args:
            sheet_name: Name of the sheet to analyze
            
        Returns:
            Dictionary mapping header text to span data
        """
        if not self.excel_analysis_data:
            print(f"⚠️  [HEADER_SPAN_UPDATER] {sheet_name}: No Excel analysis data available, using fallback rules")
            return {}
        
        try:
            # Find the sheet data
            sheet_data = None
            for sheet in self.excel_analysis_data.get('sheets', []):
                if sheet.get('sheet_name') == sheet_name:
                    sheet_data = sheet
                    break
            
            if not sheet_data:
                print(f"⚠️  [HEADER_SPAN_UPDATER] {sheet_name}: Sheet not found in analysis data")
                return {}
            
            header_positions = sheet_data.get('header_positions', [])
            print(f"🔍 [HEADER_SPAN_UPDATER] {sheet_name}: Found {len(header_positions)} headers in Excel analysis")
            
            # Group headers by row to detect multi-row structures
            headers_by_row = {}
            for header in header_positions:
                row = header.get('row')
                if row not in headers_by_row:
                    headers_by_row[row] = []
                headers_by_row[row].append(header)
            
            spans = {}
            
            # Detect spans based on header structure
            for row, row_headers in headers_by_row.items():
                print(f"🔍 [HEADER_SPAN_UPDATER] {sheet_name}: Row {row} has {len(row_headers)} headers")
                
                # Sort headers by column position for gap analysis
                sorted_headers = sorted(row_headers, key=lambda h: h.get('column', 0))
                
                for i, header in enumerate(sorted_headers):
                    keyword = header.get('keyword', '')
                    column = header.get('column', 0)
                    
                    # Default spans
                    colspan = 1
                    rowspan = 1
                    
                    # Check for column gaps that indicate spanning
                    if i < len(sorted_headers) - 1:
                        next_header = sorted_headers[i + 1]
                        next_column = next_header.get('column', 0)
                        column_gap = next_column - column
                        
                        if column_gap > 1:
                            # This header spans multiple columns
                            colspan = column_gap
                            print(f"🔧 [HEADER_SPAN_UPDATER] {sheet_name}: Detected '{keyword}' spans {colspan} columns (gap to next header)")
                    else:
                        # This is the last header in the row - check if it should span multiple columns
                        # For certain patterns, the last header might span remaining columns
                        if 'amount' in keyword.lower() and len(sorted_headers) <= 4:
                            # Amount headers in simple layouts often span multiple columns
                            # Estimate span based on common patterns
                            if sheet_name.lower() == 'contract':
                                # In contracts, Amount often spans 2-3 columns for subtotals
                                colspan = 2
                                print(f"🔧 [HEADER_SPAN_UPDATER] {sheet_name}: Detected '{keyword}' spans {colspan} columns (last header pattern)")
                    
                    # Check if this header spans multiple columns by looking for sub-headers
                    if keyword.lower() == 'quantity':
                        # Look for PCS/SF sub-headers in the next row
                        next_row = row + 1
                        if next_row in headers_by_row:
                            sub_headers = [h for h in headers_by_row[next_row] 
                                         if h.get('column', 0) >= column]
                            if len(sub_headers) >= 2:
                                # Check if we have PCS and SF
                                sub_texts = [h.get('keyword', '').upper() for h in sub_headers[:2]]
                                if 'PCS' in sub_texts and 'SF' in sub_texts:
                                    colspan = 2
                                    print(f"🔧 [HEADER_SPAN_UPDATER] {sheet_name}: Detected '{keyword}' spans 2 columns (PCS+SF)")
                    
                    # Check if this header spans multiple rows
                    # Headers that don't have sub-headers typically span multiple rows
                    if row in headers_by_row and (row + 1) in headers_by_row:
                        next_row_headers = headers_by_row[row + 1]
                        # If there's no corresponding header in the next row at this column, this spans rows
                        has_sub_header = any(h.get('column') == column for h in next_row_headers)
                        if not has_sub_header and keyword.lower() not in ['quantity']:
                            rowspan = 2
                            print(f"🔧 [HEADER_SPAN_UPDATER] {sheet_name}: Detected '{keyword}' spans 2 rows (no sub-header)")
                    
                    spans[keyword] = {'colspan': colspan, 'rowspan': rowspan}
                    
            print(f"📊 [HEADER_LAYOUT_UPDATER] {sheet_name}: Detected spans: {spans}")
            return spans
            
        except Exception as e:
            print(f"❌ [HEADER_LAYOUT_UPDATER] {sheet_name}: Error analyzing Excel data: {str(e)}")
            return {}
    
    def _analyze_positions_from_excel_data(self, sheet_name: str) -> Dict[str, Dict[str, int]]:
        """
        Analyze Excel data to extract header column positions.
        
        Args:
            sheet_name: Name of the sheet to analyze
            
        Returns:
            Dictionary mapping header text to position info: {'header_text': {'col': 0, 'row': 0}}
        """
        try:
            if not self.excel_analysis_data or 'sheets' not in self.excel_analysis_data:
                print(f"⚠️  [HEADER_LAYOUT_UPDATER] {sheet_name}: No Excel analysis data available for position detection")
                return {}
            
            # Find the matching sheet in the analysis data
            sheet_data = None
            for sheet in self.excel_analysis_data['sheets']:
                if sheet['sheet_name'].lower() == sheet_name.lower():
                    sheet_data = sheet
                    break
            
            if not sheet_data or 'header_positions' not in sheet_data:
                print(f"⚠️  [HEADER_LAYOUT_UPDATER] {sheet_name}: No header positions found in Excel analysis data")
                return {}
            
            positions = {}
            
            for header_pos in sheet_data['header_positions']:
                keyword = header_pos.get('keyword', '').strip()
                column = header_pos.get('column', 0)
                row = header_pos.get('row', 0)
                
                if keyword and column >= 0:
                    # Convert from 1-based Excel column to 0-based config column
                    positions[keyword] = {
                        'col': column - 1,  # Convert to 0-based
                        'row': row
                    }
                    
            print(f"📊 [HEADER_LAYOUT_UPDATER] {sheet_name}: Detected positions: {positions}")
            return positions
            
        except Exception as e:
            print(f"❌ [HEADER_LAYOUT_UPDATER] {sheet_name}: Error analyzing Excel position data: {str(e)}")
            return {}
        
    def update_header_layout(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update header spans AND column positions in the configuration.
        
        Args:
            config: Configuration to update
            
        Returns:
            Updated configuration with span data and column positions
        """
        try:
            print("🔍 [HEADER_LAYOUT_UPDATER] Starting header layout updates (spans + positions)...")
            updated_config = config.copy()
            
            # Process each sheet in the configuration
            for sheet_key, sheet_config in updated_config.items():
                if not isinstance(sheet_config, dict):
                    continue
                
                # Look for data_mapping section
                if sheet_key == 'data_mapping':
                    print(f"🔍 [HEADER_SPAN_UPDATER] Found data_mapping section")
                    for sheet_name, sheet_data in sheet_config.items():
                        if isinstance(sheet_data, dict) and 'header_to_write' in sheet_data:
                            print(f"🔍 [HEADER_SPAN_UPDATER] Processing sheet: {sheet_name}")
                            self._update_sheet_headers(sheet_data['header_to_write'], sheet_name)
                
                # Also check direct sheet configurations
                elif 'header_to_write' in sheet_config:
                    print(f"🔍 [HEADER_SPAN_UPDATER] Processing direct sheet: {sheet_key}")
                    self._update_sheet_headers(sheet_config['header_to_write'], sheet_key)
            
            print("✅ [HEADER_SPAN_UPDATER] Header spans updated successfully")
            self.logger.info("Header spans updated successfully")
            return updated_config
            
        except Exception as e:
            print(f"❌ [HEADER_SPAN_UPDATER] Failed to update header spans: {str(e)}")
            raise HeaderLayoutUpdaterError(f"Failed to update header spans: {str(e)}") from e
    
    def _update_sheet_headers(self, header_to_write: List[Dict[str, Any]], sheet_name: str) -> None:
        """
        Update headers for a specific sheet - BOTH spans AND positions.
        
        Args:
            header_to_write: List of header dictionaries to update
            sheet_name: Name of the sheet for logging
        """
        if not isinstance(header_to_write, list):
            print(f"⚠️  [HEADER_LAYOUT_UPDATER] {sheet_name}: header_to_write is not a list: {type(header_to_write)}")
            return
        
        print(f"📝 [HEADER_LAYOUT_UPDATER] {sheet_name}: Processing {len(header_to_write)} headers for layout updates")
        
        # Step 1: Update spans (colspan/rowspan) from Excel analysis data
        excel_spans = self._analyze_spans_from_excel_data(sheet_name)
        
        # Step 2: Update column positions from Excel analysis data  
        excel_positions = self._analyze_positions_from_excel_data(sheet_name)
        
        # Special handling for Packing list with quantity spans
        is_packing_list = 'packing' in sheet_name.lower()
        
        updated_count = 0
        for i, header in enumerate(header_to_write):
            if not isinstance(header, dict):
                continue
            
            col_id = header.get('id')
            header_text = header.get('text', '')
            
            if not col_id:
                print(f"⚠️  [HEADER_SPAN_UPDATER] {sheet_name}: Header {i} has no 'id': {header}")
                continue
            
            # Try to get span from Excel analysis first
            span_rule = None
            
            # Match by header text from Excel analysis for SPANS
            for excel_keyword, excel_span in excel_spans.items():
                if self._text_matches(header_text, excel_keyword):
                    span_rule = excel_span
                    print(f"🎯 [HEADER_LAYOUT_UPDATER] {sheet_name}: Matched '{header_text}' with Excel span '{excel_keyword}' → {excel_span}")
                    break
            
            # Fall back to hardcoded rules if no Excel match
            if span_rule is None:
                span_rule = self.span_rules.get(col_id, {'colspan': 1, 'rowspan': 1})
                print(f"🔄 [HEADER_LAYOUT_UPDATER] {sheet_name}: Using fallback span rule for '{header_text}' ({col_id}) → {span_rule}")
            
            # Special case: In Packing list, quantity headers have special spans
            if is_packing_list:
                if col_id == 'col_qty_sf' and not header.get('text', '').startswith('SF'):
                    # This is the parent "Quantity" header that spans PCS and SF
                    span_rule = {'colspan': 2, 'rowspan': 1}
                elif col_id in ['col_qty_pcs', 'col_qty_sf'] and ('PCS' in header.get('text', '') or 'SF' in header.get('text', '')):
                    # These are the sub-headers under Quantity
                    span_rule = {'colspan': 1, 'rowspan': 1}
            
            # Try to get position from Excel analysis
            position_rule = None
            
            # Match by header text from Excel analysis for POSITIONS
            for excel_keyword, excel_position in excel_positions.items():
                if self._text_matches(header_text, excel_keyword):
                    position_rule = excel_position
                    print(f"📍 [HEADER_LAYOUT_UPDATER] {sheet_name}: Matched '{header_text}' with Excel position '{excel_keyword}' → col {excel_position['col']}")
                    break
            
            # Update the header with span data
            old_colspan = header.get('colspan', 1)
            old_rowspan = header.get('rowspan', 1)
            old_col = header.get('col', -1)
            
            header['colspan'] = span_rule['colspan']
            header['rowspan'] = span_rule['rowspan']
            
            # Update column position if we found one from Excel analysis
            if position_rule is not None:
                header['col'] = position_rule['col']
            
            # Track what was updated
            span_changed = old_colspan != span_rule['colspan'] or old_rowspan != span_rule['rowspan']
            position_changed = position_rule is not None and old_col != position_rule['col']
            
            if span_changed or position_changed:
                updated_count += 1
                text_preview = header.get('text', 'N/A')[:20] + '...' if len(header.get('text', '')) > 20 else header.get('text', 'N/A')
                span_info = f"colspan:{span_rule['colspan']}, rowspan:{span_rule['rowspan']}"
                col_info = f", col:{header.get('col', 'unchanged')}" if position_changed else ""
                print(f"🔧 [HEADER_LAYOUT_UPDATER] {sheet_name}: Updated '{text_preview}' ({col_id}) → {span_info}{col_info}")
            else:
                text_preview = header.get('text', 'N/A')[:15] + '...' if len(header.get('text', '')) > 15 else header.get('text', 'N/A')
                print(f"   [HEADER_LAYOUT_UPDATER] {sheet_name}: No change '{text_preview}' ({col_id}) → colspan:{span_rule['colspan']}, rowspan:{span_rule['rowspan']}")
        
        # Apply overlap detection and resolution after position updates
        self._resolve_column_overlaps(header_to_write, sheet_name)
        
        if updated_count > 0:
            print(f"✅ [HEADER_SPAN_UPDATER] {sheet_name}: Updated {updated_count} headers")
            self.logger.info(f"Updated {updated_count} headers in {sheet_name}")
        else:
            print(f"ℹ️  [HEADER_SPAN_UPDATER] {sheet_name}: No headers were updated")
    
    def _text_matches(self, config_text: str, excel_text: str) -> bool:
        """
        Check if configuration text matches Excel text (with some flexibility).
        
        Args:
            config_text: Text from configuration
            excel_text: Text from Excel analysis
            
        Returns:
            True if they match
        """
        # Clean both texts for comparison
        clean_config = config_text.lower().strip()
        clean_excel = excel_text.lower().strip()
        
        # Direct match
        if clean_config == clean_excel:
            return True
        
        # Remove common variations
        clean_config = clean_config.replace('&', '').replace(' ', '').replace('(', '').replace(')', '')
        clean_excel = clean_excel.replace('&', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Check if one contains the other
        if clean_config in clean_excel or clean_excel in clean_config:
            return True
        
        # Special cases - be more specific to avoid false matches
        if clean_config == 'quantity' and 'quantity' in clean_excel:
            return True
        if clean_config == 'description' and 'description' in clean_excel:
            return True
        if clean_config == 'mark' and 'mark' in clean_excel and len(clean_config) <= len(clean_excel):
            return True
        if clean_config == 'item' and 'item' in clean_excel:
            return True
        if clean_config == 'remarks' and 'remarks' in clean_excel:
            return True
        
        return False
    
    def _resolve_column_overlaps(self, header_to_write: List[Dict[str, Any]], sheet_name: str) -> None:
        """
        Detect and resolve column overlaps in header configurations.
        
        This method ensures that headers with colspan don't overlap with other headers
        by recalculating column positions sequentially when overlaps are detected.
        
        Args:
            header_to_write: List of header configuration entries
            sheet_name: Name of the sheet for logging
        """
        if not header_to_write:
            return
            
        # Group headers by row for overlap detection
        headers_by_row = {}
        for header in header_to_write:
            if not isinstance(header, dict) or 'row' not in header or 'col' not in header:
                continue
                
            row = header['row']
            if row not in headers_by_row:
                headers_by_row[row] = []
            headers_by_row[row].append(header)
        
        overlaps_detected = False
        
        # Check each row for overlaps
        for row, headers in headers_by_row.items():
            if len(headers) <= 1:
                continue
                
            # Sort headers by column position
            headers.sort(key=lambda h: h['col'])
            
            # Check for overlaps and resolve them
            for i in range(len(headers) - 1):
                current_header = headers[i]
                next_header = headers[i + 1]
                
                current_col = current_header['col']
                current_colspan = current_header.get('colspan', 1)
                current_end = current_col + current_colspan - 1
                
                next_col = next_header['col']
                
                # Check if current header overlaps with next header
                if current_end >= next_col:
                    overlaps_detected = True
                    new_next_col = current_end + 1
                    print(f"📍 [HEADER_LAYOUT_UPDATER] {sheet_name}: Overlap detected! Moving '{next_header.get('text', 'Unknown')}' from col {next_col} → col {new_next_col}")
                    next_header['col'] = new_next_col
                    
                    # Cascade the position changes to subsequent headers
                    self._cascade_position_changes(headers, i + 1, sheet_name)
        
        if overlaps_detected:
            print(f"✅ [HEADER_LAYOUT_UPDATER] {sheet_name}: All column overlaps resolved")
    
    def _cascade_position_changes(self, headers: List[Dict[str, Any]], start_index: int, sheet_name: str) -> None:
        """
        Cascade position changes to subsequent headers to maintain proper spacing.
        
        Args:
            headers: List of headers sorted by column position
            start_index: Index to start cascading from
            sheet_name: Name of the sheet for logging
        """
        for i in range(start_index, len(headers) - 1):
            current_header = headers[i]
            next_header = headers[i + 1]
            
            current_col = current_header['col']
            current_colspan = current_header.get('colspan', 1)
            current_end = current_col + current_colspan - 1
            
            next_col = next_header['col']
            
            # If the next header would overlap, move it
            if current_end >= next_col:
                new_next_col = current_end + 1
                print(f"📍 [HEADER_LAYOUT_UPDATER] {sheet_name}: Cascading move '{next_header.get('text', 'Unknown')}' from col {next_col} → col {new_next_col}")
                next_header['col'] = new_next_col
    
    def add_span_rule(self, col_id: str, colspan: int = 1, rowspan: int = 1) -> None:
        """
        Add or update a span rule for a specific col_id.
        
        Args:
            col_id: Column ID to set rules for
            colspan: Number of columns to span
            rowspan: Number of rows to span
        """
        self.span_rules[col_id] = {'colspan': colspan, 'rowspan': rowspan}
        self.logger.debug(f"Added span rule: {col_id} → colspan:{colspan}, rowspan:{rowspan}")
    
    def get_span_rules(self) -> Dict[str, Dict[str, int]]:
        """
        Get current span rules.
        
        Returns:
            Dictionary of span rules
        """
        return self.span_rules.copy()
