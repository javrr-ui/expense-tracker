# Expense Tracker

Un rastreador de gastos personal que procesa automáticamente notificaciones bancarias recibidas por correo electrónico (Gmail) y registra transacciones en una base de datos SQLite.

Actualmente soporta:

- **Hey Banco** (compras con tarjeta, pagos de tarjeta, transferencias SPEI entrantes/salientes)
- **Nu** (Nubank México) – transferencias SPEI salientes (en desarrollo)
- **RappiCard** – notificaciones de compras, transferencias y pagos
- **Banorte** – transferencias SPEI salientes
- **Mercado pago** - transferencias SPEI salientes
- **DiDi** – pagos de DiDi Préstamos (y depósitos cuando el correo trae el monto)
- **Banamex** – compras con tarjeta y depósitos SPEI (`notificaciones@banamex.com`)

## Soporte futuro para más bancos

El proyecto está diseñado para ser fácilmente extensible. Los próximos bancos que se planea agregar son:

- **American Express** - Compras y pago de tarjeta

## Características

- Conexión segura a Gmail vía OAuth 2.0
- Búsqueda global de correos de los bancos soportados
- Parsers específicos por banco (incluye DiDi)
- Cuentas (crédito, préstamo, cheques, monedero) con saldo por snapshot + deltas
- Estados de cuenta PDF (Nu primero; subida manual y adjuntos de Gmail)
- Alta manual de transacciones, notas, tags, reembolsable
- Categorías, reglas automáticas y presupuesto vs real
- Recordatorios de pago (vencido / pronto / programado)
- API JSON compartida por la web y un futuro cliente móvil

## Interfaz Gráfica (Frontend)

Se incluye una interfaz web construida con **React + TypeScript + Tailwind CSS**.

### Ejecutar el proyecto

```bash
# Terminal 1 - Backend
fastapi dev api.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

La interfaz permite ver, filtrar y buscar transacciones, además de disparar manualmente la sincronización con Gmail.
