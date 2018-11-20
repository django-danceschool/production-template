from django.conf import settings
from django.utils import timezone

from huey import crontab
from huey.contrib.djhuey import periodic_task, db_task
from dateutil.relativedelta import relativedelta
import logging
from mailsnake import MailSnake


# Define logger for this file
logger = logging.getLogger(__name__)


@db_task(retries=3)
def addCustomerToMailingList(customer):
    '''
    When called, this adds the customer's email to the mailing list.
    '''
    if not hasattr(settings,'MAILCHIMP_API_KEY') or not hasattr(settings,'MAILCHIMP_LIST_ID'):
        logger.info('Did not update mailing list to add customer %s, MailChimp is not set up.' % customer.id)
        return

    logger.info('Updating mailing list in MailChimp, adding customer %s.' % customer.id)
    ms = MailSnake(settings.MAILCHIMP_API_KEY)
    listId = settings.MAILCHIMP_LIST_ID

    ms.listSubscribe(
        id=listId,
        email_address=customer.email,
        email_type='html',
        double_optin=False,
        update_existing=True,
        merge_vars={
            'FNAME': customer.first_name,
            'LNAME': customer.last_name
        })


# This is UTC time, so hour 7 is 2am
@periodic_task(crontab(hour='7',minute='0'))
def backupDatabase():
    if hasattr(settings,'BACKUP_NIGHTLY_ENABLED'):
        if settings.BACKUP_NIGHTLY_ENABLED:
            from django.core.management import call_command
            backup_file = settings.BASE_DIR + '/../../backup/web_data_' + timezone.now().strftime('%Y%m%d') + '.json'
            logger.info('Beginning JSON backup to file ' + backup_file + '.')
            with open(backup_file,'w') as f:
                try:
                    call_command('dumpdata',indent=1,format='json',natural_foreign=True,stdout=f)
                    logger.info('Backup completed.')
                except:
                    logger.error('Backup to file ' + backup_file + ' failed.')


# This is UTC time, so hour 7 is 2am
@periodic_task(crontab(hour='7',minute='10'))
def backupDatabaseSFTP():
    if hasattr(settings,'BACKUP_NIGHTLY_ENABLED') \
       and hasattr(settings,'BACKUP_SFTP_HOST') \
       and hasattr(settings,'BACKUP_SFTP_USER') \
       and hasattr(settings,'BACKUP_SFTP_PASS') \
       and hasattr(settings,'BACKUP_SFTP_PATH'):
        if settings.BACKUP_NIGHTLY_ENABLED:
            logger.info('Beginning SFTP backup of tonight\'s JSON backup file.')
            import paramiko
            transport = paramiko.Transport(settings.BACKUP_SFTP_HOST)
            transport.connect(username=settings.BACKUP_SFTP_USER, password=settings.BACKUP_SFTP_PASS)
            sftp = paramiko.SFTPClient.from_transport(transport)
            remote_path = settings.BACKUP_SFTP_PATH
            backup_path = settings.BASE_DIR + '/../../backup/'
            backup_file = 'web_data_' + timezone.now().strftime('%Y%m%d') + '.json'
            try:
                sftp.chdir(remote_path)
            except:
                sftp.mkdir(remote_path)
                sftp.chdir(remote_path)
            try:
                sftp.put(backup_path + backup_file, remote_path + backup_file)
                logger.info('Successfully uploaded backup file ' + backup_file + ' to remote server ' + settings.BACKUP_SFTP_HOST[0])
            except (IOError, OSError):
                logger.warning('Failed to upload file to remote server.')
            sftp.close()
            transport.close()
    else:
        logger.info('Backup settings not provided, no SFTP backup performed.')
