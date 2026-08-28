# WORKAROUND (this machine): pandas' C extension (pandas._libs.tslibs) crashes with a
# native stack overflow when first imported deep inside the sentence_transformers
# import chain (Python 3.12, pandas 3.0.3, Windows). Importing pandas early, at a
# shallow stack depth, avoids the crash. Import src.common before sentence_transformers.
import pandas  # noqa: F401
