import argparse
import ctypes
import os
from pathlib import Path
import sys
import traceback

from watcher.core import Store,Engine,default_dir


def main():
    parser=argparse.ArgumentParser(description='KPSS İlan Yakalayıcı')
    parser.add_argument('--background',action='store_true')
    parser.add_argument('--data-dir',type=Path,default=default_dir())
    parser.add_argument('--once',action='store_true',help='Tek kontrol döngüsü (geliştirici testi)')
    parser.add_argument('--no-autostart',action='store_true')
    args=parser.parse_args()
    if args.once:
        engine=Engine(Store(args.data_dir),print if sys.stdout else None)
        engine.cycle()
        return
    mutex,event=None,None
    if os.name=='nt':
        kernel=ctypes.windll.kernel32
        kernel.CreateMutexW.restype=ctypes.c_void_p
        kernel.CreateEventW.restype=ctypes.c_void_p
        kernel.SetEvent.argtypes=[ctypes.c_void_p]
        kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
        mutex=kernel.CreateMutexW(None,False,'Local\\KPSSIlanYakalayiciV1')
        already=kernel.GetLastError()==183
        event=kernel.CreateEventW(None,False,False,'Local\\KPSSIlanYakalayiciGosterV1')
        if already:
            kernel.SetEvent(event)
            return
    from watcher.desktop import Desktop
    app=Desktop(args.data_dir,args.background,not args.no_autostart)
    app.show_event=event
    app.mainloop()


if __name__=='__main__':
    try:
        main()
    except Exception:
        error=traceback.format_exc()
        path=default_dir()
        path.mkdir(parents=True,exist_ok=True)
        (path/'baslatma-hatasi.log').write_text(error,encoding='utf-8')
        if os.name=='nt':
            ctypes.windll.user32.MessageBoxW(None,f'Uygulama başlatılamadı. Ayrıntılar:\n{path / "baslatma-hatasi.log"}', 'KPSS İlan Yakalayıcı',16)
        else:
            raise
