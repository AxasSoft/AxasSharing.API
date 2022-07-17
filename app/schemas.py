""""
JSON Schema Draft 7 и схемы для валидации данных
Подробнее о JSON Schema на https://json-schema.org/understanding-json-schema/index.html

"""
from typing import Dict, List, Any, Optional, Union


def _const(value: Any) -> Dict[str, Any]:
    """
    :param value: значение

    Постоянное значение JSON Schema Draft 7
    """

    return {
        "const": value
    }


def _enum(*args: Any) -> Dict[str, Any]:
    """
    :param *args:
    :param args: Члены перечисления

    Перечисление JSON Schema Draft 7
    """
    return {
        "enum": list(args)
    }


def _null():
    """
    Тип null JSON Schema Draft 7
    """

    return {
        "type": "null"
    }


def _nullable(constraint: Dict[str, str]) -> Dict[str, str]:
    """

    :param constraint: ограничение, к которому применяется модификатор
    :return: новое ограничение

    Модификатор типа, добавляющий `null`, как возможный вариант типа
    """

    type_ = constraint.get('type')
    if type_ is None:
        new_type = "null"
    elif isinstance(type_, str):
        new_type = [type_, "null"]
    else:
        new_type = [*type_, "null"]

    constraint.update({'type': new_type})
    return constraint


def _bool() -> Dict[str, str]:
    """
    Логический тип JSON Schema Draft 7
    """

    return {
        "type": "boolean"
    }


def _str(
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    :param min_length: минимальная длина строки
    :param max_length: максимальная длина строки
    :param pattern: паттерн, которому должна соответствовать строка

    Строка JSON Schema Draft 7
    """

    str_constraint = {
        "type": "string",
    }

    optional_constraints = {
        "minLength": min_length,
        "maxLength": max_length,
        "pattern": pattern
    }

    for name, val in optional_constraints.items():
        if val is not None:
            str_constraint[name] = val

    return str_constraint


def _int(
        minimum: Optional[int] = None,
        exclusive_minimum: Optional[bool] = None,
        maximum: Optional[int] = None,
        exclusive_maximum: Optional[bool] = None,
        multiple_of: Optional[int] = None
) -> Dict[str, Any]:
    """
    :param minimum: Минимальное значение, допустимое для числа
    :param exclusive_minimum: Исключительный ли минимум
    :param maximum: Максимальное значение, допустимое для числа
    :param exclusive_maximum: Исключительный ли максимум
    :param multiple_of: если передано, число должно делиться на этот параметр

    Целочисленный тип тип JSON Schema Draft 7

    """

    int_constrain = {
        "type": "integer"
    }
    if minimum is not None:
        int_constrain.update(
            {
                "minimum": minimum
            }
        )
        if exclusive_minimum is not None:
            int_constrain.update(
                {
                    "exclusiveMinimum": exclusive_minimum
                }
            )
    if maximum is not None:
        int_constrain.update(
            {
                "maximum": maximum
            }
        )
        if exclusive_maximum is not None:
            int_constrain.update(
                {
                    "exclusiveMaximum": exclusive_maximum
                }
            )
    if multiple_of is not None:
        int_constrain.update(
            {
                "multipleOf": multiple_of
            }
        )
    return int_constrain


def _number(
        minimum: Optional[float] = None,
        exclusive_minimum: Optional[bool] = None,
        maximum: Optional[float] = None,
        exclusive_maximum: Optional[bool] = None,
        multiple_of: Optional[float] = None
) -> Dict[str, Any]:
    """
    :param minimum: Минимальное значение, допустимое для числа
    :param exclusive_minimum: Исключительный ли минимум
    :param maximum: Максимальное значение, допустимое для числа
    :param exclusive_maximum: Исключительный ли максимум
    :param multiple_of: если передано, число должно делиться на этот параметр

    Числовой тип тип JSON Schema Draft 7

    """

    number_constrain = {
        "type": "number"
    }
    if minimum is not None:
        number_constrain.update(
            {
                "minimum": minimum
            }
        )
        if exclusive_minimum is not None:
            number_constrain.update(
                {
                    "exclusiveMinimum": exclusive_minimum
                }
            )
    if maximum is not None:
        number_constrain.update(
            {
                "maximum": maximum
            }
        )
        if exclusive_maximum is not None:
            number_constrain.update(
                {
                    "exclusiveMaximum": exclusive_maximum
                }
            )
    if multiple_of is not None:
        number_constrain.update(
            {
                "multipleOf": multiple_of
            }
        )
    return number_constrain


def _array(
        items: Union[Dict, List[Dict], None] = None,
        min_length: int = 0,
        max_length: Optional[int] = None,
        unique: bool = False,
        additional_items: bool = False
) -> Dict[str, Any]:
    """
    :param items: Описание элементов списка
    :param min_length: минимальная длина списка
    :param max_length: максимальная длина списка
    :param unique: должен ли список содержать только уникальные элементы
    :param additional_items: разрешены ли дополнительные элементы в списке

    Списочный тип JSON Schema Draft 7

    """

    array_constraint = {
        "type": "array",
        "minItems": min_length,
        "uniqueItems": unique,
        "additionalItems": additional_items
    }

    optional_constraints = {
        'items': items,
        'maxItems': max_length
    }

    for name, val in optional_constraints.items():
        if val is not None:
            array_constraint[name] = val

    return array_constraint


def _obj(
        required_properties: Optional[Dict[str, Any]] = None,
        optional_properties: Optional[Dict[str, Any]] = None,
        additional_property: Union[bool, Dict[str, Any]] = False,
        min_properties: Optional[int] = None,
        max_properties: Optional[int] = None,
        property_names: Optional[Dict[str, Dict[str, Any]]] = None,
        pattern_properties: Optional[Dict[str, Dict[str, Any]]] = None,
        dependencies: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    :param required_properties: обязательные свойства
    :param optional_properties: необязательные свойства
    :param additional_property: спецификатор дополнительных полей
    :param min_properties: минимальное количество свойств у объекта
    :param max_properties: максимальное количество свойств у объекта
    :param property_names: спецификатор для имён свойств
    :param pattern_properties: спецификатор правил, зависимых от регулярного выражения.

    Объектный тип тип JSON Schema Draft 7
    """

    properties = dict()
    if required_properties is not None:
        properties = required_properties.copy()
    if optional_properties is not None:
        properties.update(optional_properties)

    obj_constraint = {
        "type": "object",
        "properties": properties,
        "required": list(required_properties.keys()) if required_properties is not None else [],
        "additionalProperties": additional_property
    }

    optional_constraints = {
        'minProperties': min_properties,
        'maxProperties': max_properties,
        'propertyNames': property_names,
        'patternProperties': pattern_properties,
        'dependencies': dependencies
    }

    for name, val in optional_constraints.items():
        if val is not None:
            obj_constraint[name] = val

    return obj_constraint


# Project constraint helpers

def _file(mimetype: Union[str, List[str]] = '*/*'):
    """

    :param mimetype: тип файла. См. mimetype
    :return: Файловый тип Custom JSON Schema

    Возвращает описания файла для JSON Schema - подобной схеме специфичной для данного проекта.
    Должен использоваться только для схем, используемых для проверки файлов
    """
    return {
        'mimetype': mimetype
    }


def _integer_as_string() -> Dict[str, Any]:
    """
    Целочисленный тип, переданный строкой

    """

    return _str(
        pattern='^\\d+$'
    )


def _integer_as_string_or_empty() -> Dict[str, Any]:
    """
    Целочисленный тип, переданный строкой (Возможно пустой)

    """

    return _str(
        pattern='^\\d*$'
    )


def _tel():
    return _str(
        pattern=r'\d{0,16}'
    )


def _email():
    return _str(
        pattern='.+@.+\\..+'
    )


def with_tel():
    return _obj(
        required_properties={
            'tel': _str()
        }
    )


def siw_tel():
    return _obj(
        required_properties={
            'tel': _str(),
            'code': _str(pattern=r'\d{4}'),
        },
    )


def editing_device():
    return _obj(
        required_properties={
            'device': _str(),
            'enable_notifications': _bool()
        },
        optional_properties={
            'has_subscription': _bool()
        }
    )


def editing_bool_mark():
    return _obj(
        required_properties={
            'value': _bool()
        }
    )


def edit_profile():
    return _obj(
        optional_properties={
            field: _nullable(_str())
            for field in [
                'name',
                'name',
                'passport_issued',
                'issue_date',
                'department_code',
                'passport_series',
                'passport_num',
                'surname',
                'patronymic',
                'gender',
                'birthdate',
                'birthplace',
            ]
        }
    )


def edit_profile_avatar():
    return _obj(
        required_properties={
            'image': _file('image/*')
        }
    )


def create_flat():
    return _obj(
        required_properties={
            'room_count': _int(minimum=0, maximum=4),
            'has_balcony': _bool(),
            'has_loggia': _bool(),
            'address': _str(),
            'lat': _number(),
            'lon': _number(),
            'area': _number(),
            'price_short': _nullable(_int()),
            'price_long': _nullable(_int()),
            'children': _bool(),
            'animals':_bool(),
            'washing_machine': _bool(),
            'fridge': _bool(),
            'tv': _bool(),
            'dishwasher':_bool(),
            'air_conditioner': _bool(),
            'smoking': _bool(),
            'noise':_bool(),
            'party':_bool(),
            'title':_str(),
            'guest_count':_int(),
            'bed_count':_int(),
            'restroom_count':_int()
        }
    )


def edit_flat():
    return _obj(
        optional_properties={
            'room_count': _int(minimum=0, maximum=4),
            'has_balcony': _bool(),
            'has_loggia': _bool(),
            'address': _str(),
            'lat': _number(),
            'lon': _number(),
            'area': _number(),
            'price_short': _nullable(_int()),
            'price_long': _nullable(_int()),
            'children': _bool(),
            'animals':_bool(),
            'washing_machine': _bool(),
            'fridge': _bool(),
            'tv': _bool(),
            'dishwasher':_bool(),
            'air_conditioner': _bool(),
            'smoking': _bool(),
            'noise':_bool(),
            'party':_bool(),
            'title':_str(),
            'guest_count':_int(),
            'bed_count':_int(),
            'restroom_count':_int()
        }
    )


def search():
    return _obj(
        optional_properties={
            'search': _str(),
            'has_balcony':_enum('0','1','2'),
            'has_loggia':_enum('0','1','2'),
            'children':_enum('0','1','2'),
            'animals':_enum('0','1','2'),
            'washing_machine':_enum('0','1','2'),
            'fridge':_enum('0','1','2'),
            'tv':_enum('0','1','2'),
            'dishwasher':_enum('0','1','2'),
            'air_conditioner':_enum('0','1','2'),
            'smoking':_enum('0','1','2'),
            'noise':_enum('0','1','2'),
            'party':_enum('0','1','2'),
        }
    )


def create_rent():
    return _obj(
        required_properties={
            'start_at': _int(),
            'end_at': _int()
        }
    )

