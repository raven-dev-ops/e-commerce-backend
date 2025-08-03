# products/utils.py

import logging
from .tasks import send_low_stock_email

logger = logging.getLogger(__name__)


def send_low_stock_notification(product_name, product_id, current_stock):
    """
    Sends an email notification to administrators about low stock levels.
    """
    try:
        send_low_stock_email.delay(product_name, product_id, current_stock)
        logger.info("Low stock notification task queued for product: %s", product_name)
    except Exception as e:
        logger.error(
            "Error queueing low stock notification for product %s: %s",
            product_name,
            e,
        )
