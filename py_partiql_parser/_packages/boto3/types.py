# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# https://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

# Taken from boto3==1.28.63
# We need some serialization/deserialization when parsing DynamoDB queries
# But there's no point in importing boto3 just for that, as this logic is fairly simple

from decimal import (
    Clamped,
    Context,
    Decimal,
    Inexact,
    Overflow,
    Rounded,
    Underflow,
)
from collections.abc import Mapping, Set
from typing import Any, Dict, List


STRING = "S"
NUMBER = "N"
BINARY = "B"
STRING_SET = "SS"
NUMBER_SET = "NS"
BINARY_SET = "BS"
NULL = "NULL"
BOOLEAN = "BOOL"
MAP = "M"
LIST = "L"

DYNAMODB_CONTEXT = Context(
    Emin=-128,
    Emax=126,
    prec=38,
    traps=[Clamped, Overflow, Inexact, Rounded, Underflow],
)


BINARY_TYPES = (bytearray, bytes)


class Binary:
    """A class for representing Binary in dynamodb

    Especially for Python 2, use this class to explicitly specify
    binary data for item in DynamoDB. It is essentially a wrapper around
    binary. Unicode and Python 3 string types are not allowed.
    """

    def __init__(self, value: Any):
        if not isinstance(value, BINARY_TYPES):
            types = ", ".join([str(t) for t in BINARY_TYPES])
            raise TypeError(f"Value must be of the following types: {types}")
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Binary):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f"Binary({self.value!r})"

    def __str__(self) -> Any:
        return self.value

    def __bytes__(self) -> Any:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)


class TypeSerializer:
    """This class serializes Python data types to DynamoDB types."""

    def serialize(self, value: Any) -> Dict[str, Any]:
        """The method to serialize the Python data types.

        :param value: A python value to be serialized to DynamoDB. Here are
            the various conversions:

            Python                                  DynamoDB
            ------                                  --------
            None                                    {'NULL': True}
            True/False                              {'BOOL': True/False}
            int/Decimal                             {'N': str(value)}
            string                                  {'S': string}
            Binary/bytearray/bytes (py3 only)       {'B': bytes}
            set([int/Decimal])                      {'NS': [str(value)]}
            set([string])                           {'SS': [string])
            set([Binary/bytearray/bytes])           {'BS': [bytes]}
            list                                    {'L': list}
            dict                                    {'M': dict}

            For types that involve numbers, it is recommended that ``Decimal``
            objects are used to be able to round-trip the Python type.
            For types that involve binary, it is recommended that ``Binary``
            objects are used to be able to round-trip the Python type.

        :rtype: dict
        :returns: A dictionary that represents a dynamoDB data type. These
            dictionaries can be directly passed to botocore methods.
        """
        dynamodb_type = self._get_dynamodb_type(value)
        serializer = getattr(self, f"_serialize_{dynamodb_type}".lower())
        return {dynamodb_type: serializer(value)}

    def _get_dynamodb_type(self, value: Any) -> str:
        dynamodb_type = None

        if self._is_null(value):
            dynamodb_type = NULL

        elif self._is_boolean(value):
            dynamodb_type = BOOLEAN

        elif self._is_number(value):
            dynamodb_type = NUMBER

        elif self._is_string(value):
            dynamodb_type = STRING

        elif self._is_binary(value):
            dynamodb_type = BINARY

        elif self._is_type_set(value, self._is_number):
            dynamodb_type = NUMBER_SET

        elif self._is_type_set(value, self._is_string):
            dynamodb_type = STRING_SET

        elif self._is_type_set(value, self._is_binary):
            dynamodb_type = BINARY_SET

        elif self._is_map(value):
            dynamodb_type = MAP

        elif self._is_listlike(value):
            dynamodb_type = LIST

        else:
            msg = f'Unsupported type "{type(value)}" for value "{value}"'
            raise TypeError(msg)

        return dynamodb_type

    def _is_null(self, value: Any) -> bool:
        if value is None:
            return True
        return False

    def _is_boolean(self, value: Any) -> bool:
        if isinstance(value, bool):
            return True
        return False

    def _is_number(self, value: Any) -> bool:
        if isinstance(value, (int, Decimal)):
            return True
        elif isinstance(value, float):
            raise TypeError("Float types are not supported. Use Decimal types instead.")
        return False

    def _is_string(self, value: Any) -> bool:
        if isinstance(value, str):
            return True
        return False

    def _is_binary(self, value: Any) -> bool:
        if isinstance(value, (Binary, bytearray, bytes)):
            return True
        return False

    def _is_set(self, value: Any) -> bool:
        if isinstance(value, Set):
            return True
        return False

    def _is_type_set(self, value: Any, type_validator: Any) -> bool:
        if self._is_set(value):
            if False not in map(type_validator, value):
                return True
        return False

    def _is_map(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            return True
        return False

    def _is_listlike(self, value: Any) -> bool:
        if isinstance(value, (list, tuple)):
            return True
        return False

    def _serialize_null(self, value: Any) -> bool:
        return True

    def _serialize_bool(self, value: bool) -> bool:
        return value

    def _serialize_n(self, value: Any) -> str:
        number = str(DYNAMODB_CONTEXT.create_decimal(value))
        if number in ["Infinity", "NaN"]:
            raise TypeError("Infinity and NaN not supported")
        return number

    def _serialize_s(self, value: Any) -> Any:
        return value

    def _serialize_b(self, value: Any) -> Any:
        if isinstance(value, Binary):
            value = value.value
        return value

    def _serialize_ss(self, value: Any) -> List[bool]:
        return [self._serialize_s(s) for s in value]

    def _serialize_ns(self, value: Any) -> List[str]:
        return [self._serialize_n(n) for n in value]

    def _serialize_bs(self, value: Any) -> List[Any]:
        return [self._serialize_b(b) for b in value]

    def _serialize_l(self, value: Any) -> Any:
        return [self.serialize(v) for v in value]

    def _serialize_m(self, value: Any) -> Any:
        return {k: self.serialize(v) for k, v in value.items()}


class TypeDeserializer:
    """This class deserializes DynamoDB types to Python types."""

    def deserialize(self, value: Any) -> Any:
        """The method to deserialize the DynamoDB data types.

        :param value: A DynamoDB value to be deserialized to a pythonic value.
            Here are the various conversions:

            DynamoDB                                Python
            --------                                ------
            {'NULL': True}                          None
            {'BOOL': True/False}                    True/False
            {'N': str(value)}                       Decimal(str(value))
            {'S': string}                           string
            {'B': bytes}                            Binary(bytes)
            {'NS': [str(value)]}                    set([Decimal(str(value))])
            {'SS': [string]}                        set([string])
            {'BS': [bytes]}                         set([bytes])
            {'L': list}                             list
            {'M': dict}                             dict

        :returns: The pythonic value of the DynamoDB type.
        """

        if not value:
            raise TypeError(
                "Value must be a nonempty dictionary whose key "
                "is a valid dynamodb type."
            )
        dynamodb_type = list(value.keys())[0]
        try:
            deserializer = getattr(self, f"_deserialize_{dynamodb_type}".lower())
        except AttributeError:
            raise TypeError(f"Dynamodb type {dynamodb_type} is not supported")
        return deserializer(value[dynamodb_type])

    def _deserialize_null(self, value: Any) -> None:
        return None

    def _deserialize_bool(self, value: bool) -> bool:
        return value

    def _deserialize_n(self, value: Any) -> Any:
        return DYNAMODB_CONTEXT.create_decimal(value)

    def _deserialize_s(self, value: Any) -> Any:
        return value

    def _deserialize_b(self, value: Any) -> Binary:
        return Binary(value)

    def _deserialize_ns(self, value: Any) -> Any:
        return set(map(self._deserialize_n, value))

    def _deserialize_ss(self, value: Any) -> Any:
        return set(map(self._deserialize_s, value))

    def _deserialize_bs(self, value: Any) -> Any:
        return set(map(self._deserialize_b, value))

    def _deserialize_l(self, value: Any) -> Any:
        return [self.deserialize(v) for v in value]

    def _deserialize_m(self, value: Any) -> Any:
        return {k: self.deserialize(v) for k, v in value.items()}
