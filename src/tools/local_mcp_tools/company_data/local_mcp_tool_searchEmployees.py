from src.utils.company_data_utils.company_data_service import _company_data_service

def oa_search_employees(search_term: str):
    return _company_data_service.search_employees(search_term)