from dataclasses import dataclass
from typing import Optional

from signals.generic_signals import Signal, SignalDict


@dataclass
class TCSignal(Signal):
    all_symbols: bool = False
    get_symbol: bool = False
    set_symbol: bool = False
    ignore_list: bool = False
    add_to_ignore: bool = False
    remove_from_ignore: bool = False
    clear_ignore_list: bool = False
    watchlist: bool = False
    add_to_watchlist: bool = False
    remove_from_watchlist: bool = False
    clear_watchlist: bool = False
    notify: bool = False
    stop_notification: bool = False
    notification_list: bool = False
    add_to_notification_list: bool = False
    remove_from_notification_list: bool = False
    clear_notification_list: bool = False
    stop_notifications: bool = False

    nested_completer_dict: Optional[dict] = None


def symbol_hint() -> dict:
    ...


class TCSignalDict(SignalDict):
    def __init__(self):
        # Remember the ':' symbol after the name of the signal
        self._tc_signals = {
            "All symbols:": TCSignal(all_symbols=True),
            "Get symbol:": TCSignal(get_symbol=True),
            "Set symbol:": TCSignal(set_symbol=True, nested_completer_dict=symbol_hint()),
            "Ignore list:": TCSignal(ignore_list=True),
            "Add symbol to ignore list:": TCSignal(add_to_ignore=True),
            "Remove symbol from ignore list:": TCSignal(remove_from_ignore=True),
            "Clear ignore list:": TCSignal(clear_ignore_list=True),
            "Watchlist:": TCSignal(watchlist=True),
            "Add symbol to watchlist:": TCSignal(add_to_watchlist=True),
            "Remove symbol from watchlist:": TCSignal(remove_from_watchlist=True),
            "Clear watchlist:": TCSignal(clear_watchlist=True),
            "Notify:": TCSignal(notify=True),
            "Stop notification:": TCSignal(stop_notification=True),
            "Notification list:": TCSignal(notification_list=True),
            "Add to notification list:": TCSignal(add_to_notification_list=True),
            "Remove from notification list:": TCSignal(remove_from_notification_list=True),
            "Clear notification list:": TCSignal(clear_notification_list=True),
            "Stop notifications:": TCSignal(stop_notifications=True)
        }
        super().__init__(self._tc_signals)
