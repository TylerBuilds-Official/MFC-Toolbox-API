from src.utils.company_data_utils.company_data_service import _company_data_service



def oa_get_company_info(entity: str = 'mfc'):
    return _company_data_service.get_company_info(entity)