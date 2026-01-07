from src.utils.company_data_utils.company_data_service import _company_data_service



def oa_get_project_managers():
    return _company_data_service.get_project_managers()