# Expense Tracker

Un rastreador de gastos personal que procesa automáticamente notificaciones bancarias recibidas por correo electrónico (Gmail) y registra transacciones en una base de datos SQLite.

Actualmente soporta:

- **Hey Banco** (compras con tarjeta, pagos de tarjeta, transferencias SPEI entrantes/salientes)
- **Nu** (Nubank México) – transferencias SPEI salientes (en desarrollo)
- **RappiCard** – notificaciones de compras, transferencias y pagos

## Soporte futuro para más bancos

El proyecto está diseñado para ser fácilmente extensible. Los próximos bancos que se planea agregar son:

- **PayPal** – alertas de compras y pagos enviados
- **Banorte** – transferencias, compras con tarjeta

## Características

- Conexión segura a Gmail vía OAuth 2.0
- Búsqueda global de correos de los bancos soportados
- Parsers específicos por banco
- Guardado automático de cuerpos de email en disco (`data/`) para depuración y desarrollo de parsers
- Base de datos SQLite con:
  - Tabla para almacenar transacciones realizadas
  - Tablas preparadas para categorías y subcategorías (próxima funcionalidad)
- Logging detallado
- Arquitectura limpia y extensible
