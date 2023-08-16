import dataclasses
import os
from multiprocessing import Process
from pathlib import Path

from typing import Optional, Callable, Dict, List, Any

import keyboard
import tailer
from tabulate import tabulate

from implementations.tc.data_classes import Paths
from implementations.tc.tc_types import validate_rpc_definitions, RPCDefinition, RPCMethod
from utilities.file import get_list_from_file, get_json


def do_tail(file_path):
    for line in tailer.follow(open(file_path), 0.1):
        print(line)


def payload_to_dataclass(payload: list, dataclass_arg):
    dataclass_list = []
    for elem in payload:
        try:
            dataclass_list.append(dataclass_arg(**elem))
        except TypeError:
            fields = [elem.__getattribute__(field.name) for field in dataclasses.fields(dataclass_arg)]
            dataclass_list.append(dataclass_arg(*fields))
    return dataclass_list


def fill_table(elem_list: list, dataclass_arg) -> str:
    table_data = [[field.name.capitalize() for field in dataclasses.fields(dataclass_arg)]]

    for elem in elem_list:
        table_data.append([value for value in dataclasses.asdict(elem).values()])
    return tabulate(table_data, headers='firstrow')


def show_notifications(file_path):
    if not os.path.isfile(file_path):
        file_path = Path(file_path)
        file_path.touch()

    process = Process(target=do_tail, daemon=True, args=(file_path,))
    process.start()
    print("Press esc to stop showing notifications.")
    keyboard.wait("esc")
    process.terminate()


def symbol_hint_callback(paths: Paths) -> Callable[[], dict[Any, None]]:
    def symbol_hint():
        hints = get_list_from_file(paths.symbol_hints_file_path)
        if hints:
            return dict([(entry, None) for entry in hints])

    return symbol_hint


def rpc_hint_callback(paths: Paths) -> Callable[[], dict[str, list[RPCMethod]]]:
    def rpc_hint():
        rpc_definitions_list = get_json(paths.rpc_definitions_file_path)
        if rpc_definitions_list:
            rpc_definitions: list[RPCDefinition] = validate_rpc_definitions(rpc_definitions_list, silent=True)
            if rpc_definitions:
                return dict(
                    [(entry.symbol_path, dict([(method.name, None) for method in entry.methods])) for entry in rpc_definitions])

    return rpc_hint
