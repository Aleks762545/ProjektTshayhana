import logging
from app.config import settings
level = settings.get('logging',{}).get('level','INFO')
logging.basicConfig(level=getattr(logging, level))
logger = logging.getLogger('tea_house')
