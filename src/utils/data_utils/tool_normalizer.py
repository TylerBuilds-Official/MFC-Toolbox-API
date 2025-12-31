"""
Normalizes raw MCP tool output into a standard tabular format.

Each tool may return data in different shapes. This service converts
them all to a consistent {columns, rows, row_count} structure for
visualization.
"""
from typing import Any
from src.utils.data_utils.data_result import NormalizedResult


class ToolNormalizer:
    """
    Normalizes raw tool output to tabular format.
    
    Usage:
        normalizer = ToolNormalizer()
        result = normalizer.normalize("get_all_job_info", raw_data)
    """

    def normalize(self, tool_name: str, raw_result: Any) -> NormalizedResult:
        """
        Routes to appropriate normalizer based on tool name.
        
        Args:
            tool_name: The MCP tool identifier
            raw_result: Raw output from the tool
            
        Returns:
            NormalizedResult with columns, rows, row_count
        """
        # Route to specific normalizers
        normalizer_map = {
            "get_all_job_info": self._normalize_job_list,
            "get_job_info": self._normalize_single_job,
        }
        
        normalizer = normalizer_map.get(tool_name)
        
        if normalizer:
            try:
                return normalizer(raw_result)
            except Exception as e:
                # If specific normalizer fails, try generic
                print(f"[ToolNormalizer] Specific normalizer failed for {tool_name}: {e}")
                return self._normalize_generic(raw_result)
        
        # Fallback to generic normalizer
        return self._normalize_generic(raw_result)

    def _normalize_job_list(self, raw_result: dict) -> NormalizedResult:
        """
        Normalizes get_all_job_info output.
        
        Input shape: {job_number: {field: value, ...}, ...}
        Output: Tabular with job fields as columns
        """
        if not raw_result or isinstance(raw_result, dict) and "message" in raw_result:
            return NormalizedResult.empty()
        
        # Collect all unique keys across all jobs for columns
        all_keys = set()
        for job_data in raw_result.values():
            if isinstance(job_data, dict):
                all_keys.update(job_data.keys())
        
        # Define preferred column order (common fields first)
        preferred_order = [
            'JobNumber', 'JobName', 'Contractor', 'Location', 
            'StartDate', 'TotalItems', 'TotalWeight'
        ]
        
        # Build column list: preferred first, then alphabetical remainder
        columns = [k for k in preferred_order if k in all_keys]
        remaining = sorted(all_keys - set(columns))
        columns.extend(remaining)
        
        # Build rows
        rows = []
        for job_number, job_data in raw_result.items():
            if isinstance(job_data, dict):
                row = [job_data.get(col) for col in columns]
                rows.append(row)
        
        return NormalizedResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            meta={"source_tool": "get_all_job_info"}
        )

    def _normalize_single_job(self, raw_result: dict) -> NormalizedResult:
        """
        Normalizes get_job_info output (single job detail).
        
        Input shape: {field: value, ...}
        Output: Two-column table (Field, Value) for detail view
        """
        if not raw_result or isinstance(raw_result, dict) and "message" in raw_result:
            return NormalizedResult.empty()
        
        # For single job, create Field/Value pairs
        columns = ["Field", "Value"]
        rows = []
        
        # Define preferred field order
        preferred_order = [
            'JobNumber', 'JobName', 'Contractor', 'ContractorContact',
            'Location', 'StartDate', 'TotalItems', 'TotalWeight'
        ]
        
        # Add preferred fields first
        added_keys = set()
        for key in preferred_order:
            if key in raw_result:
                rows.append([key, raw_result[key]])
                added_keys.add(key)
        
        # Add remaining fields alphabetically
        for key in sorted(raw_result.keys()):
            if key not in added_keys:
                rows.append([key, raw_result[key]])
        
        return NormalizedResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            meta={"source_tool": "get_job_info", "view_type": "detail"}
        )

    def _normalize_generic(self, raw_result: Any) -> NormalizedResult:
        """
        Generic normalizer for unknown tool output shapes.
        
        Handles common patterns:
        - List of dicts → table with dict keys as columns
        - Dict of dicts → table with nested dict keys as columns
        - Single dict → Field/Value pairs
        - List of primitives → single column table
        """
        if raw_result is None:
            return NormalizedResult.empty()
        
        # Handle error responses
        if isinstance(raw_result, dict) and "message" in raw_result and len(raw_result) == 1:
            return NormalizedResult(
                columns=["Message"],
                rows=[[raw_result["message"]]],
                row_count=1,
                meta={"type": "message"}
            )
        
        # List of dicts (most common for tabular data)
        if isinstance(raw_result, list) and raw_result and isinstance(raw_result[0], dict):
            # Collect all keys
            all_keys = set()
            for item in raw_result:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            columns = sorted(all_keys)
            rows = []
            for item in raw_result:
                if isinstance(item, dict):
                    rows.append([item.get(col) for col in columns])
            
            return NormalizedResult(
                columns=columns,
                rows=rows,
                row_count=len(rows)
            )
        
        # Dict of dicts (keyed collection)
        if isinstance(raw_result, dict) and raw_result:
            first_value = next(iter(raw_result.values()))
            if isinstance(first_value, dict):
                # Similar to job list handling
                all_keys = set()
                for item in raw_result.values():
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                
                columns = sorted(all_keys)
                rows = []
                for item in raw_result.values():
                    if isinstance(item, dict):
                        rows.append([item.get(col) for col in columns])
                
                return NormalizedResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows)
                )
            
            # Single flat dict → Field/Value
            columns = ["Field", "Value"]
            rows = [[k, v] for k, v in raw_result.items()]
            return NormalizedResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                meta={"view_type": "detail"}
            )
        
        # List of primitives
        if isinstance(raw_result, list):
            columns = ["Value"]
            rows = [[item] for item in raw_result]
            return NormalizedResult(
                columns=columns,
                rows=rows,
                row_count=len(rows)
            )
        
        # Single primitive value
        return NormalizedResult(
            columns=["Value"],
            rows=[[raw_result]],
            row_count=1
        )
