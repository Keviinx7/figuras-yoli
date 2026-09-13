from flask import Blueprint
from app.extensions import db

bp = Blueprint('portal', __name__)


@bp.errorhandler(ValueError)
def invalid(error):
    db.session.rollback()
    from flask import render_template
    return render_template('public/error.html', eyebrow='REVISEMOS LOS DETALLES',
                           title='No pudimos completar la solicitud',
                           message=str(error), button_label='Volver a tu cuenta →',
                           button_endpoint='portal.panel'), 400


from . import routes  # noqa: E402  (register routes at the end).