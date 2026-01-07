from src.utils.company_data_utils.company_data_service import _company_data_service



def oa_get_employee_data(employee_name: str):
    return _company_data_service.get_employee(employee_name)