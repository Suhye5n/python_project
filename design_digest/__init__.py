"""design_digest — 매일 한 번 디자인 트렌드를 모아 메일로 보고하는 앱.

사용 예::

    python -m design_digest preview     # 수집해서 HTML 리포트만 만들기
    python -m design_digest run         # 수집 + 메일 발송
"""

from .models import Article, Digest, ImageItem

__all__ = ["Article", "Digest", "ImageItem", "__version__"]

__version__ = "1.0.0"
