# ui/pages/backup.py

import flet as ft
from database.db_manager import DatabaseManager
from services.backup_service import BackupService
from utils.logger import get_logger

logger = get_logger(__name__)


class BackupPage:
    """ACTIVATED HIDDEN FEATURE - Backup management page"""
    
    def __init__(self, page: ft.Page, db: DatabaseManager):
        """Initialize backup page
        
        Args:
            page: Flet page instance
            db: Database manager
        """
        self.page = page
        self.db = db
        self.backup_service = BackupService(db)
        
        # UI elements
        self.backup_list = ft.Column(spacing=10)
        self.progress_bar = ft.ProgressBar(visible=False, color="teal")
        self.status_text = ft.Text("Hazır", size=12, color="grey")
        
        logger.info("BackupPage initialized (HIDDEN FEATURE ACTIVATED)")
    
    def view(self) -> ft.View:
        """Build backup view
        
        Returns:
            Backup management view
        """
        # Load existing backups
        self.load_backups()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BACKUP, color="teal", size=32),
                ft.Column([
                    ft.Text("Yedekleme Yönetimi", size=24, weight="bold"),
                    ft.Text("Veritabanı ve dosya yedekleme", size=12, color="grey")
                ], spacing=0)
            ]),
            padding=20,
            bgcolor="white",
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, "black"))
        )
        
        # Action buttons
        actions = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Yeni Yedek Oluştur",
                    icon=ft.Icons.ADD_CIRCLE,
                    bgcolor="teal",
                    color="white",
                    on_click=self.create_backup
                ),
                ft.ElevatedButton(
                    "Dosya Dahil Yedekle",
                    icon=ft.Icons.FOLDER_COPY,
                    bgcolor="blue",
                    color="white",
                    on_click=lambda e: self.create_backup(e, include_files=True)
                ),
                ft.Container(expand=True),
                self.status_text
            ]),
            padding=20,
            bgcolor="white",
            border_radius=10
        )
        
        # Progress
        progress_container = ft.Container(
            content=self.progress_bar,
            padding=ft.padding.symmetric(horizontal=20)
        )
        
        # Backup list
        backup_container = ft.Container(
            content=ft.Column([
                ft.Text("Mevcut Yedekler", size=18, weight="bold"),
                ft.Divider(),
                self.backup_list
            ]),
            padding=20,
            bgcolor="white",
            border_radius=10,
            expand=True
        )
        
        return ft.View(
            "/backup",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        actions,
                        progress_container,
                        backup_container
                    ], spacing=20, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_backups(self):
        """Load and display existing backups"""
        self.backup_list.controls.clear()
        
        try:
            backups = self.backup_service.list_backups()
            
            if not backups:
                self.backup_list.controls.append(
                    ft.Text("Henüz yedek oluşturulmamış", italic=True, color="grey")
                )
            else:
                for backup in backups:
                    self.backup_list.controls.append(
                        self._create_backup_card(backup)
                    )
        
        except Exception as e:
            logger.error(f"Failed to load backups: {e}")
            self.backup_list.controls.append(
                ft.Text(f"Hata: {e}", color="red")
            )
        
        try:
            self.backup_list.update()
        except:
            pass
    
    def _create_backup_card(self, backup: dict) -> ft.Card:
        """Create backup item card
        
        Args:
            backup: Backup info dictionary
            
        Returns:
            Backup card widget
        """
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FOLDER_ZIP, color="teal", size=40),
                    ft.Column([
                        ft.Text(backup['filename'], weight="bold"),
                        ft.Text(
                            f"{backup['created_str']} - {backup['size_mb']} MB",
                            size=12,
                            color="grey"
                        )
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.RESTORE,
                        tooltip="Geri Yükle",
                        icon_color="blue",
                        on_click=lambda e, path=backup['path']: self.restore_backup(path)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DOWNLOAD,
                        tooltip="İndir",
                        icon_color="green",
                        on_click=lambda e, path=backup['path']: self.download_backup(path)
                    )
                ]),
                padding=15
            )
        )
    
    def create_backup(self, e, include_files: bool = False):
        """Create new backup
        
        Args:
            e: Event
            include_files: Whether to include uploaded files
        """
        self.status_text.value = "Yedek oluşturuluyor..."
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Indeterminate
        self.page.update()
        
        def progress_callback(value: float):
            """Update progress bar"""
            self.progress_bar.value = value
            try:
                self.progress_bar.update()
            except:
                pass
        
        try:
            success, message = self.backup_service.create_backup(
                include_files=include_files,
                progress_callback=progress_callback
            )
            
            self.progress_bar.visible = False
            
            if success:
                self.status_text.value = "Yedek başarıyla oluşturuldu"
                self.status_text.color = "green"
                
                self.page.open(
                    ft.SnackBar(
                        ft.Text("Yedek oluşturuldu"),
                        bgcolor="green"
                    )
                )
                
                # Reload list
                self.load_backups()
            else:
                self.status_text.value = f"Hata: {message}"
                self.status_text.color = "red"
                
                self.page.open(
                    ft.SnackBar(
                        ft.Text(message),
                        bgcolor="red"
                    )
                )
        
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            self.progress_bar.visible = False
            self.status_text.value = "Hata oluştu"
            self.status_text.color = "red"
        
        self.page.update()
    
    def restore_backup(self, backup_path: str):
        """Restore from backup
        
        Args:
            backup_path: Path to backup file
        """
        # Confirmation dialog
        def confirm_restore(e):
            self.page.close(dialog)
            self._perform_restore(backup_path)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Geri Yükleme Onayı"),
            content=ft.Text(
                "Dikkat! Bu işlem mevcut veritabanını yedeğin ile değiştirecektir. "
                "Devam etmek istediğinizden emin misiniz?"
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Geri Yükle",
                    bgcolor="red",
                    color="white",
                    on_click=confirm_restore
                )
            ]
        )
        
        self.page.open(dialog)
    
    def _perform_restore(self, backup_path: str):
        """Perform backup restore
        
        Args:
            backup_path: Path to backup file
        """
        self.status_text.value = "Geri yükleniyor..."
        self.status_text.color = "blue"
        self.page.update()
        
        try:
            success, message = self.backup_service.restore_backup(backup_path)
            
            if success:
                self.status_text.value = "Geri yükleme başarılı - Lütfen uygulamayı yeniden başlatın"
                self.status_text.color = "green"
                
                self.page.open(
                    ft.SnackBar(
                        ft.Text("Geri yükleme tamamlandı. Lütfen uygulamayı yeniden başlatın."),
                        bgcolor="green"
                    )
                )
            else:
                self.status_text.value = f"Hata: {message}"
                self.status_text.color = "red"
                
                self.page.open(
                    ft.SnackBar(
                        ft.Text(message),
                        bgcolor="red"
                    )
                )
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            self.status_text.value = "Geri yükleme başarısız"
            self.status_text.color = "red"
        
        self.page.update()
    
    def download_backup(self, backup_path: str):
        """Download backup file
        
        Args:
            backup_path: Path to backup file
        """
        # In a full implementation, this would trigger a file download
        # For now, just show the path
        self.page.open(
            ft.SnackBar(
                ft.Text(f"Yedek yolu: {backup_path}"),
                bgcolor="blue"
            )
        )