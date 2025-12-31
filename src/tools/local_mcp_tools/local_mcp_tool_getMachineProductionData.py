from src.tools.sql_tools.get_machine_production import get_machine_production

def oa_get_machine_production(days_back: int = 30):
    return get_machine_production(days_back)