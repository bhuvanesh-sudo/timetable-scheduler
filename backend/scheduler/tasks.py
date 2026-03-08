from celery import shared_task
from .algorithm import generate_schedule
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_schedule_async(schedule_id):
    """
    Asynchronous task to run the timetable generation algorithm.
    """
    logger.info(f"Starting async schedule generation for schedule ID {schedule_id}")
    
    try:
        success, message = generate_schedule(schedule_id)
        if success:
            logger.info(f"Schedule {schedule_id} generated successfully: {message}")
        else:
            logger.error(f"Failed to generate schedule {schedule_id}: {message}")
            
        return {'success': success, 'message': message}
    except Exception as e:
        logger.exception(f"Exception during async schedule generation for {schedule_id}: {e}")
        return {'success': False, 'message': str(e)}
