from flask import Blueprint
from app.services.commercial import staff_only, register_errors

bp = Blueprint('requests_admin', __name__, url_prefix='/admin/pedidos')
bp.before_request(staff_only)
register_errors(bp)

from . import routes  # noqa: E402