from flask import Blueprint
from app.services.commercial import staff_only,register_errors
bp=Blueprint('customers',__name__,url_prefix='/admin/clientes')
bp.before_request(staff_only)
register_errors(bp)
from . import routes
