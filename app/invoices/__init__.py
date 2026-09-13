from flask import Blueprint
from app.services.commercial import staff_only,register_errors
bp=Blueprint('invoices',__name__,url_prefix='/admin/facturas')
bp.before_request(staff_only)
register_errors(bp)
from . import routes
