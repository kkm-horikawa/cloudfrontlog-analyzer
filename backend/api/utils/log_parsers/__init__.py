"""CloudFrontログパーサーモジュール。

このモジュールは、CloudFrontの様々なログフォーマット（v1/v2）を
統一的なインターフェースで解析するためのパーサークラスを提供します。

対応フォーマット:
    - W3C (v1): タブ区切りgzip形式
    - JSON (v2): JSON形式
    - Parquet (v2): Parquet形式
    - Plain (v2): CSV形式

Example:
    >>> from api.utils.log_parsers import create_parser
    >>> parser = create_parser(format_type='json')
    >>> df = parser.parse(content)

Available Classes:
    - AbstractLogParser: すべてのパーサーの基底クラス
    - W3CParser: W3C形式パーサー (v1)
    - JSONParser: JSON形式パーサー (v2)
    - ParquetParser: Parquet形式パーサー (v2)
    - PlainParser: Plain/CSV形式パーサー (v2)
"""

from .base import AbstractLogParser
from .json_parser import JSONParser
from .parquet_parser import ParquetParser
from .plain_parser import PlainParser
from .w3c_parser import W3CParser

__all__ = [
    "AbstractLogParser",
    "W3CParser",
    "JSONParser",
    "ParquetParser",
    "PlainParser",
    "create_parser",
]


def create_parser(format_type: str) -> AbstractLogParser:
    """指定されたフォーマットタイプのパーサーを作成します。

    Args:
        format_type (str): フォーマットタイプ
            'w3c', 'json', 'parquet', 'plain' のいずれか

    Returns:
        AbstractLogParser: 対応するパーサーインスタンス

    Raises:
        ValueError: 未知のフォーマットタイプの場合

    Example:
        >>> parser = create_parser('json')
        >>> isinstance(parser, JSONParser)
        True
    """
    format_type_lower = format_type.lower()

    parser_map = {
        "w3c": W3CParser,
        "json": JSONParser,
        "parquet": ParquetParser,
        "plain": PlainParser,
    }

    parser_class = parser_map.get(format_type_lower)
    if not parser_class:
        raise ValueError(
            f"Unknown format type: {format_type}. "
            f"Supported formats: {list(parser_map.keys())}"
        )

    return parser_class()
