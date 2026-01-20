import sqlite3
import datetime
import hashlib
# Güvenlik modülü yoksa basit bir dummy sınıf kullanır, varsa onu import eder.
try:
    from utils.security import SecurityManager
except ImportError:
    class SecurityManager:
        def hash_password(self, pwd): return hashlib.sha256(pwd.encode()).hexdigest()
        def verify_password(self, stored, provided): return stored == self.hash_password(provided)
        def encrypt_data(self, data): return data # Şifreleme yoksa düz döner
        def decrypt_data(self, data): return data

class DatabaseManager:
    def __init__(self, db_name="krats.db"):
        self.db_name = db_name
        self.security = SecurityManager() # Güvenlik yöneticisi başlatıldı
        self.conn = None
        self.connect()
        self.init_db()
        self._migrate_db() # Yeni sütunları güvenle ekler

    def connect(self):
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def _get_conn(self):
        # Her işlem için taze bağlantı (Thread-safe olması için)
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        # --- TABLOLAR ---
        
        # 1. AYARLAR
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        
        # 2. KULLANICILAR (Specialty Sütunu ile)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                role TEXT,
                commission_rate INTEGER DEFAULT 0,
                specialty TEXT DEFAULT 'Genel'
            )
        """)

        # 3. HASTALAR
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT, tc_no TEXT UNIQUE, full_name TEXT,
                phone TEXT, birth_date TEXT, gender TEXT, address TEXT,
                status TEXT DEFAULT 'Yeni', source TEXT DEFAULT 'Diğer', email TEXT
            )
        """)

        # 4. RANDEVULAR
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, doctor_id INTEGER,
                appointment_date TEXT, status TEXT, notes TEXT, reminder_sent INTEGER DEFAULT 0,
                active_user_id INTEGER,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            )
        """)
        
        # 5. FİNANS
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, category TEXT,
                amount REAL, description TEXT, date TEXT
            )
        """)
        
        # 6. STOK
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, unit TEXT,
                quantity INTEGER, threshold INTEGER DEFAULT 10
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, user_id INTEGER,
                patient_id INTEGER, quantity INTEGER, date TEXT
            )
        """)
        
        # 7. MESAJLAR
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER,
                message TEXT, timestamp TEXT
            )
        """)
        
        # 8. DOSYALAR
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, 
                file_name TEXT, file_path TEXT, file_type TEXT, upload_date TEXT
            )
        """)
        
        # 9. TIBBİ KAYITLAR
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, doctor_id INTEGER,
                anamnez TEXT, diagnosis TEXT, treatment TEXT, prescription TEXT, date TEXT
            )
        """)
        
        # 10. LOGLAR
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action_type TEXT,
                description TEXT, timestamp TEXT
            )
        """)

        # Varsayılan Admin Hesabı
        self.cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not self.cursor.fetchone():
            hashed_pw = self.security.hash_password("admin")
            self.cursor.execute("INSERT INTO users (username, password, full_name, role, specialty) VALUES (?, ?, ?, ?, ?)",
                           ("admin", hashed_pw, "Sistem Yöneticisi", "admin", "Genel"))

        self.conn.commit()
        # Bağlantıyı açık tutmuyoruz, metotlar kendi açacak
        # self.conn.close() 

    def _migrate_db(self):
        """Veritabanı yapısını günceller (Eski DB'ye yeni sütun ekleme)"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            # Users tablosuna specialty ekle
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN specialty TEXT DEFAULT 'Genel'")
                conn.commit()
            except: pass # Zaten varsa hata verir, geç
            conn.close()
        except Exception as e:
            print(f"Migration Error: {e}")

    # --- HELPER METODLAR ---
    def _encrypt(self, text): return self.security.encrypt_data(str(text)) if text else ""
    def _decrypt(self, text): return self.security.decrypt_data(str(text)) if text else ""

    def _fetch_all(self, sql, params=()):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"DB Fetch Error: {e}")
            return []
        finally:
            conn.close()

    def _execute(self, sql, params=()):
        conn = self._get_conn()
        try:
            conn.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Exec Error: {e}")
            return False
        finally:
            conn.close()

    # --- AYARLAR ---
    def get_setting(self, key):
        res = self._fetch_all("SELECT value FROM settings WHERE key=?", (key,))
        return res[0][0] if res else None

    def set_setting(self, key, value):
        return self._execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def is_module_active(self, key):
        val = self.get_setting(key)
        return val == "1"
    
    def get_notification_settings(self):
        return []

    def get_system_status(self):
        try:
            from utils.license_manager import LicenseManager
            license_key = self.get_setting("license_key")
            current_user_count = self.get_user_count()
            lm = LicenseManager()
            is_valid, msg, limit, expiry = lm.validate_license(license_key)
            return {
                "valid": is_valid, "message": msg if license_key else "Lisans Yok.",
                "limit": limit if is_valid else 0, "current": current_user_count,
                "expiry": expiry if expiry else "-"
            }
        except:
            return {"valid": True, "message": "Lisans Modülü Yok", "limit": 99, "current": 0, "expiry": "Sınırsız"}

    # --- KULLANICI İŞLEMLERİ ---
    def get_user_count(self):
        res = self._fetch_all("SELECT COUNT(*) FROM users")
        return res[0][0] if res else 0

    def check_login(self, username, password):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        # user[2] password sütunu
        if user and self.security.verify_password(user[2], password): return user
        return None

    def add_user_secure(self, username, password, full_name, role, commission_rate=0, specialty="Genel"):
        # Lisans kontrolü
        status = self.get_system_status()
        if status["limit"] > 0 and status["current"] >= status["limit"]: return False, "Kota Dolu!"
        
        check = self._fetch_all("SELECT id FROM users WHERE username=?", (username,))
        if check: return False, "Kullanıcı adı alınmış."

        try:
            hashed = self.security.hash_password(password)
            self._execute("INSERT INTO users (username, password, full_name, role, commission_rate, specialty) VALUES (?, ?, ?, ?, ?, ?)", 
                          (username, hashed, full_name, role, commission_rate, specialty))
            return True, "Kayıt Başarılı."
        except Exception as e: return False, str(e)

    def get_all_users(self): return self._fetch_all("SELECT id, username, full_name, role, commission_rate, specialty FROM users")
    
    def get_users_except(self, uid): 
        # Chat sayfası için
        return self._fetch_all("SELECT id, username, full_name, role FROM users WHERE id != ?", (uid,))

    def get_user_specialty(self, user_id):
        res = self._fetch_all("SELECT specialty FROM users WHERE id=?", (user_id,))
        return res[0][0] if res else "Genel"

    # --- HASTA İŞLEMLERİ ---
    def get_patient_count(self):
        res = self._fetch_all("SELECT COUNT(*) FROM patients")
        return res[0][0] if res else 0

    def get_active_patients(self):
        rows = self._fetch_all("SELECT * FROM patients WHERE status != 'Arşiv' ORDER BY id DESC")
        return self._decrypt_patients(rows)

    def get_archived_patients(self):
        rows = self._fetch_all("SELECT * FROM patients WHERE status = 'Arşiv' ORDER BY id DESC")
        return self._decrypt_patients(rows)

    def _decrypt_patients(self, rows):
        decrypted = []
        for r in rows:
            try:
                # r yapısı: id, tc, name, phone, bdate, gender, address, status, source, email
                decrypted.append((
                    r[0], self._decrypt(r[1]), self._decrypt(r[2]), self._decrypt(r[3]), 
                    r[4], r[5], self._decrypt(r[6]), r[7], r[8], r[9]
                ))
            except: decrypted.append(r)
        return decrypted

    def add_patient(self, tc, name, phone, bdate, gender, address, email=None, source="Diğer"):
        return self._execute("INSERT INTO patients (tc_no, full_name, phone, birth_date, gender, address, email, source, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Yeni')", 
                             (self._encrypt(tc), self._encrypt(name), self._encrypt(phone), bdate, gender, self._encrypt(address), email, source))

    def get_patient_by_id(self, pid):
        rows = self._fetch_all("SELECT * FROM patients WHERE id=?", (pid,))
        if rows:
            r = rows[0]
            return (r[0], self._decrypt(r[1]), self._decrypt(r[2]), self._decrypt(r[3]), r[4], r[5], self._decrypt(r[6]), r[7], r[8], r[9])
        return None
        
    def archive_patient(self, pid): return self._execute("UPDATE patients SET status = 'Arşiv' WHERE id = ?", (pid,))
    def restore_patient(self, pid): return self._execute("UPDATE patients SET status = 'Yeni' WHERE id = ?", (pid,))

    # --- RANDEVU İŞLEMLERİ ---
    def add_appointment(self, patient_id, doctor_id, date_str, notes, active_user_id=None):
        return self._execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes, active_user_id) VALUES (?, ?, ?, ?, ?, ?)",
                             (patient_id, doctor_id, date_str, "Bekliyor", self._encrypt(notes), active_user_id))

    def get_todays_appointments(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        rows = self._fetch_all("""
            SELECT a.id, p.full_name, a.appointment_date, a.status, a.notes 
            FROM appointments a JOIN patients p ON a.patient_id = p.id 
            WHERE a.appointment_date LIKE ? ORDER BY a.appointment_date ASC
        """, (f"{today}%",))
        final = []
        for r in rows: final.append((r[0], self._decrypt(r[1]), r[2], r[3], self._decrypt(r[4])))
        return final

    # --- BİLDİRİM & LOG ---
    def get_pending_reminders(self):
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        rows = self._fetch_all("SELECT a.id, p.full_name, p.phone, p.email, a.appointment_date FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.appointment_date LIKE ? AND a.reminder_sent = 0", (f"{tomorrow}%",))
        final = []
        for r in rows: final.append((r[0], self._decrypt(r[1]), self._decrypt(r[2]), r[3], r[4]))
        return final
    
    def mark_reminder_sent(self, app_id): return self._execute("UPDATE appointments SET reminder_sent = 1 WHERE id = ?", (app_id,))

    # --- FİNANS & STOK ---
    def add_transaction(self, t_type, cat, amount, desc, date):
        return self._execute("INSERT INTO transactions (type, category, amount, description, date) VALUES (?, ?, ?, ?, ?)", (t_type, cat, amount, desc, str(date)))
    def get_transactions(self): return self._fetch_all("SELECT * FROM transactions ORDER BY date DESC")
    def delete_transaction(self, tid): return self._execute("DELETE FROM transactions WHERE id=?", (tid,))
    
    def get_inventory(self): return self._fetch_all("SELECT * FROM products")
    def add_product(self, name, unit, qty, threshold): return self._execute("INSERT INTO products (name, unit, quantity, threshold) VALUES (?, ?, ?, ?)", (name, unit, qty, threshold))
    def delete_product(self, pid): return self._execute("DELETE FROM products WHERE id=?", (pid,))
    
    # --- SOHBET ---
    def send_message(self, sender, receiver, msg):
        return self._execute("INSERT INTO messages (sender_id, receiver_id, message, timestamp) VALUES (?, ?, ?, ?)", (sender, receiver, msg, str(datetime.datetime.now())))
    def get_chat_history(self, u1, u2):
        return self._fetch_all("SELECT sender_id, message, timestamp FROM messages WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?) ORDER BY timestamp ASC", (u1, u2, u2, u1))
    
    # --- MEDİKAL KAYITLAR ---
    def add_patient_file(self, pid, name, path, ftype):
        return self._execute("INSERT INTO patient_files (patient_id, file_name, file_path, file_type, upload_date) VALUES (?, ?, ?, ?, ?)", (pid, name, path, ftype, str(datetime.datetime.now())))
    def get_patient_files(self, pid): return self._fetch_all("SELECT * FROM patient_files WHERE patient_id=?", (pid,))
    
    def add_medical_record(self, pid, did, anamnez, diag, treat, presc, *args):
        return self._execute("INSERT INTO medical_records (patient_id, doctor_id, anamnez, diagnosis, treatment, prescription, date) VALUES (?, ?, ?, ?, ?, ?, ?)", (pid, did, anamnez, diag, treat, presc, str(datetime.datetime.now())))
    
    def get_patient_sources(self):
        # CRM Grafiği İçin
        rows = self.get_active_patients()
        sources = {}
        for p in rows:
            src = p[8] if len(p)>8 else "Diğer"
            sources[src] = sources.get(src, 0) + 1
        return list(sources.items())