from src.utils.company_data_utils.company_data_service import _company_data_service


def oa_get_department_summary():
    return _company_data_service.get_department_summary()