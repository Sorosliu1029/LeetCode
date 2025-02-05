import random
from requests.sessions import Session
from .gh_generator import LEETCODE

WEBSITE_PATHS = [
    # '/api',
    "/api/htmlbanner/home/",
]


def patch_csrf_token(s: Session):
    url = LEETCODE + random.choice(WEBSITE_PATHS)
    s.get(url)
