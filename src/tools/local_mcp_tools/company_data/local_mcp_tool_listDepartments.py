from src.utils.company_data_utils.company_data_service import _company_data_service


def oa_list_departments():
    return _company_data_service.list_departments()
