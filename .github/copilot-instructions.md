# KRATS - Copilot Development Guide

## Architecture Overview

**KRATS** is a Turkish clinic management system built with Flet (Flutter for Python), SQLite, and custom security modules. It's organized into three core layers:

1. **UI Layer** (`pages/`): Page-based architecture using Flet's component system
2. **Data Layer** (`database/db_manager.py`): SQLite with encryption and lazy loading patterns
3. **Service Layer** (`utils/`): Security, licensing, localization, notifications, and integrations

## Critical Patterns

### Page Implementation Pattern
All pages follow this structure:
```python
class [PageName]Page:
    def __init__(self, page: ft.Page, db, optional_params):
        self.page = page
        self.db = db
        # Cache data to avoid repeated queries
        self.data_cache = []
    
    def view(self) -> ft.View:
        # Build UI components
        # Load data via self.load_data()
        return ft.View("/route", controls=[...])
```

Pages are stateless - rebuild UI on every route change. Caching is done within the page instance for performance. See [pages/patient_list.py](pages/patient_list.py#L1) and [pages/doctor_home.py](pages/doctor_home.py#L1) for patterns.

### Routing & Session Management
- Routes handled in [main.py](main.py#L125) via `TemplateRoute` for parameterized routes
- Session data stored in `page.session` (survives within app lifecycle)
- Auth check: `page.session.get("user_id")` and role via `page.session.get("role")`
- **Auto-logout**: Inactivity timeout (5 minutes) via daemon thread - [main.py](main.py#L102)

### Database Patterns
- **Initialization**: Single `DatabaseManager` instance per app in [main.py](main.py#L90)
- **Helper methods**: Use `_fetch_all()` and `_execute()` for SQL operations
- **Encryption**: Patient phone/TC fields encrypted automatically via `_encrypt()` and `_decrypt()`
- **No direct SQL calls** in pages - all access through `DatabaseManager` methods
- **Settings table** stores config: theme, license status, country code

### Security & Compliance
- **Password hashing**: SHA256 (see [security_manager.py](utils/security_manager.py#L40))
- **Data encryption**: Fernet-based for PII (patient phone, TC numbers)
- **KVKK compliance**: Auto-logout after 5 minutes inactivity (Turkish GDPR equivalent)
- **Secret key management**: Loaded from `secret.key` file or `CLINIC_APP_SECRET_KEY` env var
- **Audit logs**: All critical actions logged to `audit_logs` table

### Localization & Multi-Country Support
- Country config in [utils/localization.py](utils/localization.py#L1) defines modules and currencies
- Turkish ("TR"), US/Global ("US"), German ("DE") support
- UI text mixed Turkish/English - normalize new additions to existing language patterns

### Component Organization (Flet/Flutter specifics)
- Dark mode support: Check `self.page.theme_mode == ft.ThemeMode.DARK`
- Theme color: Retrieved via `db.get_setting("theme_color")` (defaults to "teal")
- Layout: Use `ft.Row`, `ft.Column` with `expand=True` for responsive design
- Data tables: Use `ft.DataTable` with `heading_row_color` for active/archive distinction
- Background services: Daemon threads for 3D server, notifications, inactivity check

## Key Services & Integrations

| Service | Purpose | Key Methods |
|---------|---------|-------------|
| `DatabaseManager` | SQLite ORM-like wrapper | `get_all_patients()`, `add_patient()`, `get_todays_appointments()` |
| `SecurityManager` | Encryption & password hashing | `hash_password()`, `verify_password()`, `encrypt_data()`, `decrypt_data()` |
| `LicenseManager` | License validation | `is_valid()`, `check_expiry()` |
| `NotificationService` | SMS/WhatsApp/Email | Starts as daemon thread if available |
| `BackupManager` | Database backups | Auto-backup on startup |

## Running & Development

**Start app**: 
```bash
python3 /Users/aligucuk/Desktop/KRATS/main.py
```

**Background services** spawned automatically:
- 3D server on port 8000 (GLB model serving)
- Notification service (if `notification_service.py` exists)
- Inactivity monitor thread

**Database reset**: Run `setup_db.py` or `reset_db.py` for clean state

## Common Tasks

### Add a New Page
1. Create `pages/new_feature.py` with class `NewFeaturePage()`
2. Add import in [main.py](main.py#L10)
3. Add route in `route_change()` function - [main.py](main.py#L135)
4. Use session data for auth: `if not page.session.get("user_id"): page.go("/login")`

### Fetch & Display Patient Data
```python
patients = self.db.get_all_patients()  # Returns list of tuples
for patient in patients:
    tc_no, name, phone = patient[1], patient[2], patient[3]  # Phone is encrypted
    phone_decrypted = self.db.decrypt_data(phone)  # Decrypt before display
```

### Handle Async Operations in Flet
Use `page.run_task()` for thread-safe UI updates from background operations - see inactivity check in [main.py](main.py#L120)

## Known Quirks & Gotchas

- **Performance**: `db.get_all_patients()` uses `len()` not `COUNT(*)` - OK for small clinics but refactor for scaling
- **Optional modules**: Pages like `MedicalDetailPage`, `ChatPage`, `TVDisplayPage` fail gracefully if missing (try/except imports in [main.py](main.py#L23))
- **TC number uniqueness**: Must be validated before patient creation (database enforces UNIQUE constraint)
- **Flet threading**: Never call UI methods directly from threads - always use `page.run_task()`
- **Dark mode**: Not all pages fully styled for dark mode yet - theme color check in [doctor_home.py](pages/doctor_home.py#L45)

## File Organization Reference
- `pages/` - UI pages (one per major feature)
- `database/` - Data access layer
- `utils/` - Cross-cutting concerns (security, licensing, notifications)
- `assets/` - 3D models (GLB) and HTML templates
- `backups/` - Auto-generated database backups
