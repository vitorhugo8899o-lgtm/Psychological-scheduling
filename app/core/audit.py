import logging
import sys

audit_logger = logging.getLogger('audit')

if not audit_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter('%(asctime)s AUDIT %(message)s'))
    audit_logger.addHandler(_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False


def audit(action: str, actor_id: int, **fields) -> None:
    details = ' '.join(f'{key}={value}' for key, value in fields.items())
    audit_logger.info('action=%s actor=%s %s', action, actor_id, details)
