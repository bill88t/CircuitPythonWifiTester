from storage import disable_usb_drive

try:
    from supervisor import disable_autoreload
except ImportError:
    from supervisor import runtime

    def disable_autoreload():
        runtime.autoreload = False


try:
    from supervisor import status_bar

    status_bar.console = False
    del status_bar
except ImportError:
    pass
try:
    disable_usb_drive()
except RuntimeError:
    pass
disable_autoreload()
del disable_autoreload, disable_usb_drive
try:
    del runtime
except:
    pass
