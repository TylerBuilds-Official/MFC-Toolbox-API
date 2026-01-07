from difflib import SequenceMatcher
from src.data.company_data import COMPANY_DATA

DEPARTMENTS = {
    'executive':    ['todd weaver', 'sara weaver-lundberg', 'ken bastine', 'matt murphy'],
    'it':           ['joe sage', 'david jansson', 'ryan burtenshaw', 'tyler emery'],
    'purchasing':   ['kendall bastine', 'todd mathison', 'janet underwood'],
    'project_mgmt': ['blake reed', 'joe lenoue', 'conrad schmidt', 'evan weaver'],
    'estimating':   ['adam lee', 'cody kilby'],
    'admin':        ['angie parker', 'kasi chapman', 'beth mathison'],
    'safety':       ['erik white'],
    'sales':        ['doug danner']
}

DEPARTMENT_ALIASES = {
    'exec':         'executive',
    'leadership':   'executive',
    'management':   'executive',
    'tech':         'it',
    'technology':   'it',
    'dev':          'it',
    'development':  'it',
    'pm':           'project_mgmt',
    'project':      'project_mgmt',
    'projects':     'project_mgmt',
    'estimators':   'estimating',
    'precon':       'estimating',
    'office':       'admin',
    'administration': 'admin',
    'finance':      'admin',
    'accounting':   'admin',
    'hse':          'safety',
    'environmental': 'safety',
}


class CompanyDataService:
    """
    Service for accessing MetalsFab company data.
    Provides targeted lookups optimized for AI tool consumption.

    For changes adjust COMPANY_DATA

    """

    def __init__(self):
        self._employees  = COMPANY_DATA['office_employees']
        self._mfc_info   = COMPANY_DATA['mfc_general_info']
        self._mmm_info   = COMPANY_DATA['master_machining_manufacturing']

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _fuzzy_match_name(self, query: str, threshold: float = 0.6) -> str | None:
        """Find best matching employee name using fuzzy matching."""
        query_lower = query.lower().strip()

        # Exact match first
        if query_lower in self._employees:
            return query_lower

        # Check if query matches first name, last name, or partial
        best_match  = None
        best_score  = 0.0

        for name in self._employees.keys():
            # Direct substring check (handles "blake" -> "blake reed")
            if query_lower in name or name in query_lower:
                return name

            # Fuzzy match
            score = SequenceMatcher(None, query_lower, name).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = name

        return best_match

    @staticmethod
    def _resolve_department(dept: str) -> str | None:
        """Resolve department name or alias to canonical department key."""
        dept_lower = dept.lower().strip()

        if dept_lower in DEPARTMENTS:
            return dept_lower

        return DEPARTMENT_ALIASES.get(dept_lower)

    @staticmethod
    def _format_employee(name: str, data: dict, include_name: bool = True) -> dict:
        """Format employee data for consistent output."""
        result = {}
        if include_name:
            result['name'] = name.title()

        result.update({
            'position':  data.get('position'),
            'email':     data.get('email'),
            'extension': data.get('extension'),
            'cell':      data.get('cell')
        })
        return result

    # =========================================================================
    # Targeted Lookups (Low Token Cost)
    # =========================================================================

    def get_employee(self, employee_name: str) -> dict | None:
        """
        Look up a single employee by name (supports fuzzy matching).

        Args:
            employee_name: Full or partial employee name

        Returns:
            Employee dict with name, position, email, extension, cell
            or None if no match found
        """
        matched_name = self._fuzzy_match_name(employee_name)
        if not matched_name:
            return None

        return self._format_employee(matched_name, self._employees[matched_name])

    def get_employee_email(self, name: str) -> str | None:
        """
        Quick email lookup for a specific employee.

        Args:
            name: Full or partial employee name

        Returns:
            Email address string or None if not found
        """
        matched_name = self._fuzzy_match_name(name)
        if not matched_name:
            return None

        return self._employees[matched_name].get('email')

    def get_employee_phone(self, name: str) -> dict | None:
        """
        Get phone contact info for a specific employee.

        Args:
            name: Full or partial employee name

        Returns:
            Dict with 'extension' and 'cell' keys, or None if not found
        """
        matched_name = self._fuzzy_match_name(name)
        if not matched_name:
            return None

        emp = self._employees[matched_name]
        return {
            'name':      matched_name.title(),
            'extension': emp.get('extension'),
            'cell':      emp.get('cell')
        }

    # =========================================================================
    # Filtered Lists (Medium Token Cost)
    # =========================================================================

    def get_employees_by_department(self, department: str) -> list[dict] | None:
        """
        Get all employees in a specific department.

        Args:
            department: Department name or alias
                        Valid: executive, it, purchasing, project_mgmt,
                               estimating, admin, safety, sales
                        Aliases: exec, leadership, tech, dev, pm, projects,
                                 office, finance, hse, etc.

        Returns:
            List of employee dicts or None if department not found
        """
        resolved_dept = self._resolve_department(department)
        if not resolved_dept:
            return None

        employee_names = DEPARTMENTS.get(resolved_dept, [])
        return [
            self._format_employee(name, self._employees[name])
            for name in employee_names
            if name in self._employees
        ]

    def get_project_managers(self) -> list[dict]:
        """
        Get all project managers (common query shortcut).

        Returns:
            List of PM employee dicts
        """
        return self.get_employees_by_department('project_mgmt')

    def get_it_team(self) -> list[dict]:
        """
        Get all IT/Development team members.

        Returns:
            List of IT employee dicts
        """
        return self.get_employees_by_department('it')

    def search_employees(self, query: str) -> list[dict]:
        """
        Search employees by name, position, or email.

        Args:
            query: Search term to match against employee data

        Returns:
            List of matching employee dicts (may be empty)
        """
        query_lower = query.lower().strip()
        results = []

        for name, data in self._employees.items():
            # Search across multiple fields
            searchable = f"{name} {data.get('position', '')} {data.get('email', '')}".lower()

            if query_lower in searchable:
                results.append(self._format_employee(name, data))

        return results

    # =========================================================================
    # Summaries (AI-Friendly Formats)
    # =========================================================================

    def get_employee_directory_summary(self) -> str:
        """
        Get a compact, scannable employee directory.
        Optimized for low token count while maintaining readability.

        Returns:
            Formatted string with all employees, one per line
        """
        lines = []
        for name, data in self._employees.items():
            ext = f"ext {data['extension']}" if data.get('extension') else "no ext"
            lines.append(f"- {name.title()} ({data['position']}) - {ext}")

        return "\n".join(lines)

    @staticmethod
    def get_department_summary() -> str:
        """
        Get a summary of departments and their members.

        Returns:
            Formatted string showing department structure
        """
        lines = []
        for dept, members in DEPARTMENTS.items():
            member_names = ", ".join(name.title() for name in members)
            lines.append(f"{dept.upper()}: {member_names}")

        return "\n".join(lines)

    def list_employee_names(self) -> list[str]:
        """
        Get just the list of employee names.
        Useful for disambiguation when multiple matches possible.

        Returns:
            List of employee names in title case
        """
        return [name.title() for name in self._employees.keys()]

    @staticmethod
    def list_departments() -> list[str]:
        """
        Get list of valid department names.

        Returns:
            List of canonical department keys
        """
        return list(DEPARTMENTS.keys())

    # =========================================================================
    # Business Info
    # =========================================================================

    def get_company_info(self, entity: str = 'mfc') -> dict | None:
        """
        Get company information for MFC or Master Machining.

        Args:
            entity: 'mfc' or 'mmm' (Master Machining Manufacturing)

        Returns:
            Dict with address, phone, fax, website, description
        """
        entity_lower = entity.lower().strip()

        if entity_lower in ('mfc', 'metalsfab', 'metals fab', 'metals fabrication'):
            return {'entity': 'Metals Fabrication Company', **self._mfc_info}

        if entity_lower in ('mmm', 'master machining', 'master machining manufacturing', 'machine shop'):
            return {'entity': 'Master Machining Manufacturing', **self._mmm_info}

        return None

    def get_contact_info(self) -> dict:
        """
        Get basic MFC contact information.
        Use for directions, 'where is the office', phone number questions.

        Returns:
            Dict with address, phone, fax, website
        """
        return {
            'address': self._mfc_info['address'],
            'phone':   self._mfc_info['phone'],
            'fax':     self._mfc_info['fax'],
            'website': self._mfc_info['website']
        }

    @staticmethod
    def get_all_company_data() -> dict:
        """
        Get complete company data dump.
        Use sparingly - prefer targeted methods for most queries.

        Returns:
            Full COMPANY_DATA dictionary
        """
        return COMPANY_DATA


# Singleton instance for easy importing
_company_data_service = CompanyDataService()
