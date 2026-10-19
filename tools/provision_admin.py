"""Sadece proje sahibinin makinesinde bir kez çalıştırılır; EXE'ye dahil edilmez."""
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from watcher.access import dpapi, vault_directory


def main():
    directory = vault_directory()
    directory.mkdir(parents=True, exist_ok=True)
    metadata = directory/'owner.json'
    if metadata.exists():
        public = json.loads(metadata.read_text('utf-8'))['public_key']
    else:
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes_raw().hex()
        (directory/'owner-bootstrap.dpapi').write_bytes(dpapi(key.private_bytes_raw()))
        metadata.write_text(json.dumps({'public_key': public}), encoding='utf-8')
    target = Path(__file__).resolve().parents[1]/'watcher'/'admin_public_key.py'
    target.write_text('"""Yalnızca doğrulama anahtarı; özel anahtar bu depoda bulunmaz."""\n'
                      + f'PUBLIC_KEY_HEX = {public!r}\n', encoding='utf-8')
    print('Yönetici ilk kurulum anahtarı yalnızca mevcut Windows kullanıcısı için hazırlandı.')
    print('Uygulamadaki Yönetici girişi düğmesinden ilk parolanızı belirleyin.')


if __name__ == '__main__':
    main()
