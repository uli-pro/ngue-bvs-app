# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Certificate Consistency Manager für NGÜ Bibelvers-Sponsoring App
Verwaltet Konsistenz zwischen Datenbank und Dateisystem für Certificate PDFs
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import current_app
from models import db, Certificate, Donation
from pdf_service import PDFGeneratorService, ValidationError


class CertificateConsistencyManager:
    """Verwaltet Konsistenz zwischen Datenbank und Dateisystem"""
    
    def __init__(self, pdf_service: PDFGeneratorService):
        self.pdf_service = pdf_service
        self.base_path = None
    
    @property
    def storage_path(self):
        """Lazy-loading des Storage-Pfads"""
        if self.base_path is None:
            self.base_path = current_app.config.get('CERTIFICATE_STORAGE_PATH')
        return self.base_path
    
    def verify_consistency(self) -> Dict[str, Any]:
        """Vollständige Konsistenz-Prüfung"""
        results = {
            'total_certificates': 0,
            'consistent': 0,
            'missing_files': [],
            'orphaned_files': [],
            'invalid_paths': [],
            'errors': []
        }
        
        # Alle Certificates prüfen
        certificates = Certificate.query.all()
        results['total_certificates'] = len(certificates)
        
        for cert in certificates:
            try:
                if not cert.validate_file_path():
                    results['invalid_paths'].append({
                        'id': cert.id,
                        'path': cert.file_path,
                        'reason': 'Invalid path format'
                    })
                elif not cert.exists_on_disk:
                    results['missing_files'].append({
                        'id': cert.id,
                        'path': cert.file_path,
                        'donation_id': cert.donation_id,
                        'certificate_type': cert.certificate_type
                    })
                else:
                    results['consistent'] += 1
                    
            except Exception as e:
                results['errors'].append({
                    'certificate_id': cert.id,
                    'error': str(e)
                })
        
        # Orphaned Files finden
        results['orphaned_files'] = self._find_orphaned_files()
        
        return results
    
    def _find_orphaned_files(self) -> List[Dict[str, Any]]:
        """Findet PDF-Dateien ohne entsprechenden Certificate-Record"""
        if not os.path.exists(self.storage_path):
            return []
        
        orphaned = []
        all_db_paths = set(cert.file_path for cert in Certificate.query.all() if cert.file_path)
        
        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    
                    if file_path not in all_db_paths:
                        try:
                            file_stat = os.stat(file_path)
                            orphaned.append({
                                'path': file_path,
                                'size': file_stat.st_size,
                                'modified': datetime.fromtimestamp(file_stat.st_mtime)
                            })
                        except OSError as e:
                            # Datei existiert nicht mehr oder keine Berechtigung
                            pass
        
        return orphaned
    
    def repair_missing_files(self, missing_files: List[Dict]) -> Dict[str, Any]:
        """Regeneriert fehlende PDF-Dateien"""
        results = {
            'repaired': 0,
            'failed': [],
            'errors': []
        }
        
        for missing in missing_files:
            try:
                cert_id = missing['id']
                certificate = Certificate.query.get(cert_id)
                
                if not certificate:
                    results['failed'].append(cert_id)
                    results['errors'].append({
                        'certificate_id': cert_id,
                        'error': 'Certificate record not found'
                    })
                    continue
                
                # PDF neu generieren
                donation = certificate.donation
                if not donation:
                    results['failed'].append(cert_id)
                    results['errors'].append({
                        'certificate_id': cert_id,
                        'error': 'Associated donation not found'
                    })
                    continue
                
                # Session ID aus Pfad extrahieren
                session_id = self._extract_session_from_path(certificate.file_path)
                
                # Neues Certificate generieren (das alte wird überschrieben)
                if certificate.certificate_type == 'tax_receipt':
                    new_cert = self.pdf_service.generate_tax_receipt_atomic(
                        donation.id,
                        session_id
                    )
                else:
                    new_cert = self.pdf_service.generate_certificate_atomic(
                        donation.id,
                        certificate.certificate_type,
                        session_id
                    )
                
                results['repaired'] += 1
                
            except Exception as e:
                results['failed'].append(missing.get('id', 'unknown'))
                results['errors'].append({
                    'certificate_id': missing.get('id', 'unknown'),
                    'error': str(e)
                })
        
        return results
    
    def _extract_session_from_path(self, file_path: str) -> Optional[str]:
        """Extrahiert Session-ID aus Dateipfad"""
        # Pattern: .../session_xyz123/...
        match = re.search(r'/session_([^/]+)/', file_path)
        return match.group(1) if match else None
    
    def cleanup_orphaned_files(self, max_age_days: int = 7) -> int:
        """Löscht verwaiste Dateien älter als max_age_days"""
        orphaned = self._find_orphaned_files()
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for orphan in orphaned:
            if orphan['modified'] < cutoff_date:
                try:
                    os.remove(orphan['path'])
                    deleted_count += 1
                except OSError:
                    pass
        
        return deleted_count
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Sammelt Statistiken über Certificate-Storage"""
        if not os.path.exists(self.storage_path):
            return {
                'storage_exists': False,
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0
            }
        
        total_size = 0
        file_count = 0
        file_types = {}
        
        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size
                        file_count += 1
                        
                        # Typ aus Filename extrahieren
                        if '_personal_certificate_' in file:
                            file_types['personal_certificate'] = file_types.get('personal_certificate', 0) + 1
                        elif '_tax_receipt_' in file:
                            file_types['tax_receipt'] = file_types.get('tax_receipt', 0) + 1
                        else:
                            file_types['unknown'] = file_types.get('unknown', 0) + 1
                            
                    except OSError:
                        pass
        
        return {
            'storage_exists': True,
            'total_files': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_types': file_types
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Kompletter Gesundheitscheck des Certificate-Systems"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow(),
            'issues': []
        }
        
        try:
            # Storage-Pfad prüfen
            if not os.path.exists(self.storage_path):
                health['issues'].append('Storage path does not exist')
                health['status'] = 'unhealthy'
            elif not os.access(self.storage_path, os.W_OK):
                health['issues'].append('Storage path not writable')
                health['status'] = 'unhealthy'
            
            # Konsistenz-Check
            consistency = self.verify_consistency()
            if consistency['missing_files']:
                health['issues'].append(f"{len(consistency['missing_files'])} missing files")
                if len(consistency['missing_files']) > 10:
                    health['status'] = 'unhealthy'
                else:
                    health['status'] = 'degraded'
            
            if consistency['orphaned_files']:
                health['issues'].append(f"{len(consistency['orphaned_files'])} orphaned files")
                if health['status'] == 'healthy':
                    health['status'] = 'degraded'
            
            if consistency['invalid_paths']:
                health['issues'].append(f"{len(consistency['invalid_paths'])} invalid paths")
                health['status'] = 'unhealthy'
            
            # Storage-Statistiken hinzufügen
            health['storage_stats'] = self.get_storage_statistics()
            health['consistency_summary'] = {
                'total_certificates': consistency['total_certificates'],
                'consistent_files': consistency['consistent'],
                'missing_files': len(consistency['missing_files']),
                'orphaned_files': len(consistency['orphaned_files']),
                'invalid_paths': len(consistency['invalid_paths'])
            }
            
        except Exception as e:
            health['status'] = 'error'
            health['issues'].append(f'Health check failed: {str(e)}')
        
        return health