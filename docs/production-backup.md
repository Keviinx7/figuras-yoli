# Respaldos y recuperación — Yoli Figuras de Fomix

Politica de respaldos para la base de datos local y sus auxiliares. **Nada de
esto sustituye las copias fuera del equipo.** Este documento es el manual
operativo, no la ejecución de un respaldo.

## Qué hay que respaldar

1. `instance/tienda.db` — catálogo 173 productos + datos comerciales
   (materiales, recetas, cálculos, cotizaciones, facturas, usuarios, auditoría).
2. `app/static/img/products/` — las 173 fotografías verificadas.
3. `docs/catalogo-productos.pdf` — el PDF autenticado (SHA-256 fijado).
4. La clave de sesión externa en producción (`SECRET_KEY` del entorno del
   servidor); sin ella, el panel no arranca en production.

No se respaldan nunca: `instance/.session_key` (clave de desarrollo), el `.env`,
ni bases temporales de pruebas dentro de `instance/`.

## Respaldos automáticos en el servidor

- Editor actual de la app: `backup-db` produce una copia coherente y verificada
  (`PRAGMA integrity_check`) en `instance/backups/` (o en `BACKUP_DIR` si está
  configurado), con `chmod 600`.
- Programar una copia externa diaria fuera del filesystem del proyecto, por
  ejemplo `restic`, `rclone` o `borg` dirigida a otra máquina/volumen. La cita
  con `backup-db` + copia externa es la práctica recomendada antes de cualquier
  operación de mantenimiento.
- Con PostgreSQL (fase futura), el respaldo nominal es `pg_dump`/`pg_basebackup`;
  `backup-db` queda restringido a la SQLite local.

## Recuperación

1. Detener el servidor (systemd: `systemctl stop yoli`).
2. Verificar la copia: abrirla de solo lectura con `sqlite3` y
   `PRAGMA integrity_check` → `ok`.
3. Probar la copia como una base separada (`DATABASE_URL` apuntando a la copia)
   y revisar que el catálogo y los documentos aparecen.
4. Conservar la base actual antes de sustituirla (renombrar, no borrar).
5. Sustituir `instance/tienda.db` por la copia verificada y arrancar.
6. Comprobar `/health`, una cotización de prueba y el tablero.

**No usar `init-db` ni reimportar el catálogo como procedimiento de
recuperación**: crearían una estructura sin datos o duplicarían registros.

## Retención

- Conservar al menos 4 respaldos diarios rotativos y 12 semanales.
- Cada respaldo debe quedar fuera del mismo disco donde vive la base.
- Nunca guardar respaldos dentro del directorio público servido por Nginx.