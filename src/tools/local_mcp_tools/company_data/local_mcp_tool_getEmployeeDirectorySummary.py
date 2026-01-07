from src.utils.company_data_utils.company_data_service import _company_data_service



def oa_get_employee_directory_summary():
    return _company_data_service.get_employee_directory_summary()