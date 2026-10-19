"""Yerel proje sahibinin imzaladığı tarama yetkileri ve şifreli anahtar kasası."""
import base64
import ctypes
from ctypes import wintypes
import json
import os
import hashlib
import hmac
import platform
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

from .admin_public_key import PUBLIC_KEY_HEX

NORMAL_MAX_DAYS = 7
MIN_PASSWORD_LENGTH = 8
PASSWORD_ITERATIONS = 600_000


def password_record(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PASSWORD_ITERATIONS)
    return {'algorithm': 'pbkdf2-sha256', 'iterations': PASSWORD_ITERATIONS,
            'salt': base64.b64encode(salt).decode('ascii'),
            'digest': base64.b64encode(digest).decode('ascii')}


def verify_password(password, record):
    try:
        if record['algorithm'] != 'pbkdf2-sha256' or type(record['iterations']) is not int:
            return False
        if not 100_000 <= record['iterations'] <= 2_000_000:
            return False
        salt = base64.b64decode(record['salt'], validate=True)
        expected = base64.b64decode(record['digest'], validate=True)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, record['iterations'])
        return hmac.compare_digest(actual, expected)
    except (ValueError, KeyError, TypeError):
        return False


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')


def machine_identity():
    identity = platform.node()
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography') as key:
                identity = winreg.QueryValueEx(key, 'MachineGuid')[0]
        except OSError:
            pass
    return hashlib.sha256(identity.encode('utf-8')).hexdigest()


def sign_grant(private_key, installation_id, days):
    if private_key.public_key().public_bytes_raw().hex() != PUBLIC_KEY_HEX:
        raise PermissionError('Bu anahtar proje yöneticisine ait değil.')
    payload = {'version': 1, 'installation': installation_id, 'machine': machine_identity(), 'days': days}
    return {'payload': payload, 'signature': base64.b64encode(private_key.sign(canonical(payload))).decode('ascii')}


def valid_grant(grant, installation_id, days):
    try:
        payload = grant['payload']
        if payload != {'version': 1, 'installation': installation_id, 'machine': machine_identity(), 'days': days}:
            return False
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX)).verify(
            base64.b64decode(grant['signature'], validate=True), canonical(payload))
        return True
    except Exception:
        # Bozuk veya geçersiz yetki hiçbir koşulda geniş erişim sağlamaz.
        return False


def vault_directory():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'KPSSIlanYakalayiciAdmin'


def dpapi(data, decrypt=False):
    if os.name != 'nt':
        raise OSError('İlk yönetici kurulumu Windows kullanıcı korumasını gerektirir.')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    result = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    operation = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    operation.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                          ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    operation.restype = wintypes.BOOL
    if not operation(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel = ctypes.WinDLL('kernel32')
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(ctypes.cast(result.data, ctypes.c_void_p))


class OwnerVault:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else vault_directory()
        self.pem = self.directory/'owner-private.pem'
        self.bootstrap = self.directory/'owner-bootstrap.dpapi'

    def available(self):
        try:
            metadata = json.loads((self.directory/'owner.json').read_text('utf-8'))
            return metadata['public_key'] == PUBLIC_KEY_HEX and (self.pem.exists() or self.bootstrap.exists())
        except (OSError, ValueError, KeyError):
            return False

    def needs_password(self):
        return not self.pem.exists()

    def create_password(self, password):
        if not self.available() or not self.needs_password():
            raise PermissionError('Yönetici anahtarı bu bilgisayarda hazırlanmamış veya parola zaten belirlenmiş.')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f'En az {MIN_PASSWORD_LENGTH} karakterlik bir yönetici parolası belirleyin.')
        key = Ed25519PrivateKey.from_private_bytes(dpapi(self.bootstrap.read_bytes(), decrypt=True))
        self.check_key(key)
        encrypted = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                      serialization.BestAvailableEncryption(password.encode('utf-8')))
        temporary = self.pem.with_suffix('.tmp')
        temporary.write_bytes(encrypted)
        temporary.replace(self.pem)
        # Şifreli anahtarın yeniden açıldığı doğrulanmadan ilk kurulum kaydı silinmez.
        self.unlock(password)
        self.bootstrap.unlink()
        return key

    def unlock(self, password):
        if not self.available() or not self.pem.exists():
            raise PermissionError('Yönetici anahtarı bulunamadı.')
        try:
            metadata_path = self.directory/'owner.json'
            metadata = json.loads(metadata_path.read_text('utf-8'))
            record = metadata.get('password_hash')
            if record is not None and not verify_password(password, record):
                raise ValueError('Parola doğrulanamadı.')
            key = serialization.load_pem_private_key(self.pem.read_bytes(), password=password.encode('utf-8'))
            self.check_key(key)
            if record is None:
                # Önce eski şifreli anahtar açılır; ancak doğru paroladan sonra özet kaydedilir.
                metadata['password_hash'] = password_record(password)
                temporary = metadata_path.with_suffix('.tmp')
                temporary.write_text(json.dumps(metadata), encoding='utf-8')
                temporary.replace(metadata_path)
            return key
        except (ValueError, TypeError):
            raise ValueError('Yönetici parolası yanlış veya anahtar dosyası geçersiz.') from None

    @staticmethod
    def check_key(key):
        if not isinstance(key, Ed25519PrivateKey) or key.public_key().public_bytes_raw().hex() != PUBLIC_KEY_HEX:
            raise PermissionError('Anahtar bu projenin yöneticisine ait değil.')
