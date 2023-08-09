import dataclasses
import datetime
import os
from dataclasses import dataclass
from typing import Optional

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import yes_no_dialog
from pyads import ADSError
from tabulate import tabulate

from signal_analyzers.generic_signal_analyzers import SignalAnalyzer
from utilities.functions import fill_table, payload_to_dataclass
from signals.generic_signals import Signal
import pyads

from implementations.tc.tc_signals import TCSignal


@dataclass
class Symbol:
    name: str
    comment: str
    symbol_type: str
    array_size: int
    auto_update: bool
    index_group: int
    index_offset: int
    value: None


class TCSignalAnalyzer(SignalAnalyzer):
    payload_buffer: dict = {}

    def __init__(self, ams_net_id='127.0.0.1.1.1', port=pyads.PORT_TC3PLC1):
        super().__init__()
        self._plc = pyads.Connection(ams_net_id, port)
        self._plc.open()
        self._ignore_list_path = 'ignore_ads_symbols.txt'
        self._watchlist_path = 'watchlist.txt'
        self._notification_list_path = 'notification_list.txt'
        self._notification_dict = {}

    def _get_ads_symbol(self, symbol_str):
        symbol = self._plc.get_symbol(symbol_str)
        if symbol.plc_type:
            symbol.read()

        return symbol

    def _print_out_symbol(self, symbol_str):
        symbol = self._get_ads_symbol(symbol_str)
        table_list = payload_to_dataclass([symbol], Symbol)
        table = fill_table(table_list, Symbol)
        print(table)

    @staticmethod
    def _print_out_symbols(symbols):
        dataclass_symbols = payload_to_dataclass(symbols, Symbol)
        table = fill_table(dataclass_symbols, Symbol)
        print(table)

    @staticmethod
    def _get_symbol_str(signal: Signal):
        symbol_str = signal.payload
        signal.payload = None
        return symbol_str

    @staticmethod
    def _get_list_from_file(file_obj):
        return file_obj.read().strip().split('\n')

    @staticmethod
    def _add_notification(symbol, notification_dict, callback=None):

        if symbol.name not in notification_dict:
            symbol.auto_update = True
            if not callback:
                def _notification_callback(notification_header, index_tuple):
                    timestamp_microseconds = notification_header.contents.nTimeStamp // 10
                    # Convert the timestamp to a datetime object
                    date_time = datetime.datetime(1601, 1, 1) + datetime.timedelta(
                        microseconds=timestamp_microseconds)
                    formatted_date_time = date_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                    if 'STRING' in symbol.symbol_type:
                        symbol_value = notification_dict[symbol.name].value
                        print(symbol_value)
                        byte_string = b''
                        for byte in symbol_value:
                            if byte == b'\x00':
                                break
                            byte_string += byte
                        payload = byte_string.decode('utf-8')
                    else:
                        payload = notification_dict[symbol.name].value

                    # {notification_header.contents.data}
                    output_string = (
                        f"{formatted_date_time}: Notification received for symbol {symbol.name}. "
                        f"Value changed to: {payload}\n")

                    with open('ADSNotification.txt', 'a') as notification_file:
                        notification_file.write(output_string)

                    TCSignalAnalyzer.payload_buffer[symbol.name] = notification_header

                callback = _notification_callback

            return_val = symbol.add_device_notification(callback)
            notification_dict[symbol.name] = symbol
            print(f"Notification callback for symbol {symbol.name} setup successfully {return_val}")

    def _add_to_file(self, path_to_file, str_to_add):
        if os.path.isfile(path_to_file):
            with open(path_to_file, 'r') as file:
                list_from_file = self._get_list_from_file(file)
            if str_to_add not in list_from_file:
                with open(path_to_file, 'a') as file:
                    file.write(str_to_add + '\n')
        else:
            with open(path_to_file, 'w') as file:
                file.write(str_to_add + '\n')

    def _remove_from_file(self, path_to_file, str_to_remove):
        if os.path.isfile(path_to_file):
            with open(path_to_file, 'r') as file:
                list_from_file: list = self._get_list_from_file(file)
                if str_to_remove in list_from_file:
                    list_from_file.remove(str_to_remove)
                rebuilt_list = []
                if list_from_file:
                    for symbol_str in list_from_file:
                        rebuilt_list.append(symbol_str + '\n')
            with open(path_to_file, 'w') as file:
                for symbol_str in rebuilt_list:
                    file.write(symbol_str)

    def cleanup(self):
        for notification in self._notification_dict.values():
            notification.clear_device_notifications()

    async def eval(self, signal: Signal):
        tc_signal = TCSignal(**dataclasses.asdict(signal))
        try:
            if tc_signal.all_symbols:
                ignore_symbols: Optional[list] = None
                # Get a list of symbols to ignore
                if os.path.isfile(self._ignore_list_path):
                    with open(self._ignore_list_path, 'r') as ignore_symbols_file:
                        ignore_symbols = self._get_list_from_file(ignore_symbols_file)

                symbols = self._plc.get_all_symbols()
                filtered_symbols = []
                for symbol in symbols:
                    if ignore_symbols and symbol.name in ignore_symbols:
                        continue
                    filtered_symbols.append(symbol)
                    if symbol.plc_type:
                        symbol.read()

                self._print_out_symbols(filtered_symbols)

            elif tc_signal.get_symbol:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._print_out_symbol(symbol_str)

            elif tc_signal.add_to_ignore:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._add_to_file(self._ignore_list_path, symbol_str)

            elif tc_signal.add_to_watchlist:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._add_to_file(self._watchlist_path, symbol_str)
                    self._print_out_symbol(symbol_str)

            elif tc_signal.remove_from_ignore:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._remove_from_file(self._ignore_list_path, symbol_str)

            elif tc_signal.remove_from_watchlist:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._remove_from_file(self._watchlist_path, symbol_str)

            elif tc_signal.ignore_list:
                if os.path.isfile(self._ignore_list_path):
                    with open(self._ignore_list_path, 'r') as ignore_list_file:
                        ignore_list = self._get_list_from_file(ignore_list_file)
                    tabulate_data = [[value] for value in ignore_list]
                    print(tabulate(tabulate_data, headers=['ADS Symbols in ignore list']))

            elif tc_signal.watchlist:
                if os.path.isfile(self._watchlist_path):
                    with open(self._watchlist_path, 'r') as watchlist_file:
                        watchlist = self._get_list_from_file(watchlist_file)
                    if watchlist:
                        watchlist_symbols = []
                        for watchlist_symbol in watchlist:
                            symbol = self._get_ads_symbol(watchlist_symbol)
                            watchlist_symbols.append(symbol)
                        self._print_out_symbols(watchlist_symbols)

            elif tc_signal.clear_ignore_list:
                if os.path.isfile(self._ignore_list_path):
                    result = await yes_no_dialog(
                        title='Clear Ignore list',
                        text='Are you sure you want to clear the ignore list?',
                    ).run_async()
                    if result:
                        os.remove(self._ignore_list_path)

            elif tc_signal.clear_watchlist:
                if os.path.isfile(self._watchlist_path):
                    result = await yes_no_dialog(
                        title='Clear Watchlist',
                        text='Are you sure you want to clear the Watchlist?',
                    ).run_async()
                    if result:
                        os.remove(self._watchlist_path)

            elif tc_signal.notify:
                if tc_signal.payload:
                    symbol_str = self._get_symbol_str(tc_signal)
                    target_symbol = self._get_ads_symbol(symbol_str)

                    self._add_notification(target_symbol, self._notification_dict)

            elif tc_signal.stop_notification:
                if tc_signal.payload:
                    symbol_str = self._get_symbol_str(tc_signal)
                    if symbol_str in self._notification_dict:
                        self._notification_dict[symbol_str].clear_device_notifications()
                        del self._notification_dict[symbol_str]
                        print("Done")
                    else:
                        print("Nothing to do")

            elif tc_signal.notification_list:
                if os.path.isfile(self._notification_list_path):
                    with open(self._notification_list_path, 'r') as notification_list_file:
                        notification_list = self._get_list_from_file(notification_list_file)
                    if notification_list:
                        for notification_str in notification_list:
                            symbol = self._get_ads_symbol(notification_str)
                            self._add_notification(symbol, notification_dict=self._notification_dict)

            elif tc_signal.add_to_notification_list:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._add_to_file(self._notification_list_path, symbol_str)

            elif tc_signal.remove_from_notification_list:
                if signal.payload:
                    symbol_str = self._get_symbol_str(signal)
                    self._remove_from_file(self._notification_list_path, symbol_str)

            elif tc_signal.clear_notification_list:
                if os.path.isfile(self._notification_list_path):
                    result = await yes_no_dialog(
                        title='Clear Watchlist',
                        text='Are you sure you want to clear the Watchlist?',
                    ).run_async()
                    if result:
                        os.remove(self._notification_list_path)

            elif tc_signal.stop_notifications:
                if os.path.isfile(self._notification_list_path):
                    with open(self._notification_list_path, 'r') as notification_list_file:
                        notification_list = self._get_list_from_file(notification_list_file)
                    if notification_list:
                        for notification in notification_list:
                            if notification in self._notification_dict:
                                self._notification_dict[notification].clear_device_notifications()
                                del self._notification_dict[notification]
                                print(f"Notification for {notification} symbol stopped")

        except ADSError as e:
            print_formatted_text(HTML(f'<red>ERR: {e}</red>'))
