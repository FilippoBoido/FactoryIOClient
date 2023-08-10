import dataclasses
import os

from tabulate import tabulate


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


def get_list_from_file_object(file_obj):
    return file_obj.read().strip().split('\n')


def get_list_from_file(path_to_file):
    if os.path.isfile(path_to_file):
        with open(path_to_file, 'r') as file_obj:
            return get_list_from_file_object(file_obj)


def add_to_file(path_to_file, str_to_add):
    if os.path.isfile(path_to_file):
        with open(path_to_file, 'r') as file:
            list_from_file = get_list_from_file_object(file)
        if str_to_add not in list_from_file:
            with open(path_to_file, 'a') as file:
                file.write(str_to_add + '\n')
    else:
        with open(path_to_file, 'w') as file:
            file.write(str_to_add + '\n')


def remove_from_file(path_to_file, str_to_remove):
    if os.path.isfile(path_to_file):
        with open(path_to_file, 'r') as file:
            list_from_file: list = get_list_from_file_object(file)
            if str_to_remove in list_from_file:
                list_from_file.remove(str_to_remove)
            rebuilt_list = []
            if list_from_file:
                for symbol_str in list_from_file:
                    rebuilt_list.append(symbol_str + '\n')
        with open(path_to_file, 'w') as file:
            for symbol_str in rebuilt_list:
                file.write(symbol_str)
