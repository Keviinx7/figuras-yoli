import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
import click
from flask import abort, current_app, request, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from app.extensions import db
from app.models.commercial import BusinessSettings, TaxSetting, SchemaVersion, AuditEvent, User


def roles_required(*roles):
    def decorate(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_active or current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorate


def staff_only():
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    if not current_user.is_active or current_user.role not in ('admin','vendedor'):
        abort(403)
    # Serialize administrative writes BEFORE reading mutable document state.
    if request.method == 'POST':
        db.session.execute(text('BEGIN IMMEDIATE'))


def settings():
    return db.session.get(BusinessSettings,1), db.session.get(TaxSetting,1)


def record(entity, entity_id, action, detail=''):
    db.session.add(AuditEvent(user_id=current_user.id if current_user.is_authenticated else None,
                             entity=entity,entity_id=entity_id,action=action,detail=detail[:500]))


def commit():
    db.session.commit()


def register_errors(bp):
    @bp.errorhandler(ValueError)
    def invalid(error):
        db.session.rollback()
        from flask import render_template
        return render_template('admin/error.html',message=str(error)),400

    @bp.errorhandler(IntegrityError)
    def conflict(error):
        db.session.rollback()
        from flask import render_template
        return render_template('admin/error.html',message='Ya existe un registro con esos datos. Recargue antes de volver a intentar.'),409

    @bp.errorhandler(OperationalError)
    def busy(error):
        db.session.rollback()
        current_app.logger.error('No se pudo completar una operación SQLite: %s', type(error).__name__)
        from flask import render_template
        return render_template('admin/error.html',message='La base está ocupada o no está actualizada. Reintente; si continúa, revise upgrade-db.'),503


def initialize_settings():
    if not db.session.get(BusinessSettings,1): db.session.add(BusinessSettings(id=1))
    if not db.session.get(TaxSetting,1): db.session.add(TaxSetting(id=1))
    if not db.session.get(SchemaVersion,1): db.session.add(SchemaVersion(version=1))
    db.session.commit()


def register_cli(app):
    @app.cli.command('upgrade-db')
    def upgrade_db():
        """Backup SQLite, then add missing commercial tables. Never reimport products."""
        path=Path(db.engine.url.database)
        if not path.is_file(): raise click.ClickException('No existe la SQLite actual; revise la configuración.')
        folder=Path(app.instance_path)/'backups';folder.mkdir(exist_ok=True)
        backup=folder/('tienda-upgrade-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.db')
        with sqlite3.connect(path) as source, sqlite3.connect(backup) as target:
            source.backup(target)
            tables=[r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            before={t:([r[1] for r in source.execute('PRAGMA table_info("'+t+'")')],source.execute('SELECT * FROM "'+t+'" ORDER BY rowid').fetchall()) for t in tables}
        backup.chmod(0o600)
        db.create_all()
        with db.engine.begin() as connection:
            columns={row[1] for row in connection.exec_driver_sql('PRAGMA table_info(product_cost_recipes)')}
            if 'is_active' not in columns:
                connection.exec_driver_sql('ALTER TABLE product_cost_recipes ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1')
        initialize_settings()
        with sqlite3.connect(path) as connection:
            for table,(columns,rows) in before.items():
                selected=','.join('"'+column+'"' for column in columns)
                if connection.execute('SELECT '+selected+' FROM "'+table+'" ORDER BY rowid').fetchall()!=rows:
                    raise click.ClickException('Los datos previos difieren en '+table+'. Revise el backup: '+str(backup))
            if connection.execute('pragma integrity_check').fetchone()!=('ok',) or connection.execute('pragma foreign_key_check').fetchall():
                raise click.ClickException('Falló la verificación SQLite. Backup: '+str(backup))
        click.echo(f'Actualización aditiva terminada. Catálogo intacto. Backup: {backup}')

    @app.cli.command('backup-db')
    def backup_db():
        """Consistent full SQLite backup, including all commercial data."""
        path=Path(db.engine.url.database)
        if not path.is_file(): raise click.ClickException('No existe la SQLite configurada.')
        folder=Path(app.instance_path)/'backups';folder.mkdir(exist_ok=True)
        backup=folder/('tienda-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.db')
        with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as source, sqlite3.connect(backup) as target:
            source.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                raise click.ClickException('La copia no pasó integrity_check.')
        backup.chmod(0o600)
        click.echo(f'Backup verificado: {backup}')

    @app.cli.command('create-user')
    @click.option('--username',prompt=True)
    @click.option('--email',default='')
    @click.option('--role',type=click.Choice(['admin','vendedor']),default='admin')
    @click.password_option(confirmation_prompt=True)
    def create_user(username,email,role,password):
        """Create an administrative user; password is prompted without echo."""
        from app.auth.routes import validate_user
        try:
            username,email=validate_user(username,email)
            user=User(username=username,email=email or None,role=role)
            user.set_password(password)
            db.session.add(user);db.session.flush()
            db.session.add(AuditEvent(entity='user',entity_id=user.id,action='created_cli'))
            db.session.commit()
        except (ValueError,IntegrityError) as error:
            db.session.rollback();raise click.ClickException('No se creó el usuario: datos inválidos o duplicados.') from error
        click.echo(f'Usuario {username} creado con rol {role}.')
