from django.conf import settings
from django.db.models import Count, Case, When, IntegerField, Q, F
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from huey import crontab
from huey.contrib.djhuey import periodic_task, db_task, db_periodic_task
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import logging
from mailsnake import MailSnake
from random import shuffle

from danceschool.core.models import Series, Event, EmailTemplate, Customer, DanceTypeLevel
from danceschool.core.constants import getConstant
from danceschool.core.mixins import EmailRecipientMixin
from danceschool.vouchers.models import Voucher


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


@db_periodic_task(crontab(hour='13',minute='30'))
def emailRecentNewStudents():
    '''
    This program identifies all new students who have recently completed
    Lindy 1 classes (or other beginner classes) and sends them a custom
    email giving them a discount.
    '''
    enabled = getConstant('promotions__enableLindy1PromotionEmail')
    if not enabled:
        return

    logger.info('Sending Lindy 1 completion promotional emails.')

    # These levels are used to determine the classes to which the vouchers apply.
    try:
        lindy1Level = DanceTypeLevel.objects.get(danceType__name='Lindy Hop',name='Level 1')
    except:
        logger.error('Lindy 1 Dance type not found -- vouchers could not be created.')
        return

    # This is the email template used to send the promotional email
    template = EmailTemplate.objects.get(id=getConstant('promotions__lindy1TemplateID'))

    # This dict holds the basic voucher details that will be filled in.
    # Change these param
    vouchers = {
        'Lindy_1': {
            'name': 'Swing 1',
            'amount': 35,
            'prefix': 'SWING1_RETAKE_',
            'category': getConstant('vouchers__emailPromoCategory'),
            'expirationDate': timezone.now() + relativedelta(months=6),
            'danceTypeLevel': lindy1Level,
        },
        'Lindy_2': {
            'name': 'Swing 2',
            'amount': 15,
            'prefix': 'SWING2_CONTINUE_',
            'category': getConstant('vouchers__emailPromoCategory'),
            'expirationDate': timezone.now() + relativedelta(months=3),
        }
    }

    # Identify the recent series whose students to contact.
    # - Ended in the last 30 days
    # - Is Lindy Hop
    # - Is of level 1
    recent_series = Series.objects.filter(
        endTime__lte=timezone.now(),
        endTime__gte=timezone.now() - timedelta(days=30),
        classDescription__danceTypeLevel=lindy1Level,
    )

    if recent_series.count() == 0:
        logger.info('No eligible recent series found.  Aborting.')
        return

    # Identify the students to contact.
    # - in the applicable series
    # - Didn't take a beginner Lindy course other than in one of the applicable Lindy 1 series
    # - Haven't already received the promotion
    possible_customers = Customer.objects.annotate(
        thislindyonecount=Count(Case(When(Q(eventregistration__event__series__classDescription__danceTypeLevel=lindy1Level) & Q(eventregistration__event__series__in=recent_series),then=1),output_field=IntegerField())),
        alllindyonecount=Count(Case(When(eventregistration__event__series__classDescription__danceTypeLevel=lindy1Level, then=1),output_field=IntegerField())),
    ).annotate(
        otherlindyonecount=F('alllindyonecount') - F('thislindyonecount')
    ).filter(
        thislindyonecount__gt=0,
        otherlindyonecount=0,
    ).select_related('user').distinct()

    uncontacted_customers = [x for x in possible_customers if not isinstance(x.data, dict) or not x.data.get('lindy1PromoEmailSent')]

    if len(uncontacted_customers) == 0:
        logger.info('No eligible customers found.  Aborting.')
        return

    # The list of upcoming series includes Swing 1, Swing 2, and anything
    # labeled "All Levels"
    upcoming_series = Series.objects.filter(
        startTime__gte=timezone.now(),
        registrationOpen=True,
        status__in=[Event.RegStatus.enabled, Event.RegStatus.heldOpen],
        classDescription__danceTypeLevel__name__in=[
            'Level 1','Level 2','All Levels','Solo jazz - Level 1',
        ],
    ).order_by('startTime')

    for customer in uncontacted_customers:
        logger.debug('Preparing to send promotional email to customer %s.' % customer.id)

        for voucherKey,voucherInfo in vouchers.items():
            newVoucher = Voucher.create_new_code(
                prefix=voucherInfo.get('prefix'),
                name=_('Student Retention %s Discount for %s' % (voucherInfo['name'],customer.fullName)),
                category=voucherInfo['category'],
                originalAmount=voucherInfo['amount'],
                singleUse=True,
                forFirstTimeCustomersOnly=False,
                expirationDate=voucherInfo['expirationDate'],
            )
            voucherInfo['code'] = newVoucher.voucherId

            if voucherInfo.get('danceTypeLevel'):
                newVoucher.dancetypevoucher_set.create(danceTypeLevel=voucherInfo['danceTypeLevel'])

        # The email will be signed by the instructors of the series that ended
        instructors = customer.eventregistration_set.filter(
            event__series__classDescription__danceTypeLevel=lindy1Level,
        ).order_by('event__endTime').first().event.teachers
        shuffle(instructors)

        # For convenience, do this here rather than in the template
        teacher_first_names = ', '.join([x.firstName for x in instructors])

        if not template.defaultFromAddress or not template.content:
            logger.warning('Cannot send email to customer %s because template is not yet configured.' % customer.id)
        else:
            emailMixin = EmailRecipientMixin()

            emailMixin.email_recipient(
                template.subject,
                template.content,
                html_message=template.html_content,
                send_html=True,
                from_address=template.defaultFromAddress,
                from_name=template.defaultFromName,
                cc=template.defaultCC,
                to=customer.email,
                vouchers=vouchers,
                instructors=instructors,
                teacher_first_names=teacher_first_names,
                upcoming_series=upcoming_series,
                recipient_name=customer.fullName,
            )

        if not customer.data or not isinstance(customer.data,dict):
            customer.data = {}
        customer.data['lindy1PromoEmailSent'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save out the customer to mark that the email was sent.
        customer.save()
        logger.info('Sent Lindy 1 Completion promotional email to customer %s' % customer.id)

    logger.info('Sending of Lindy 1 Completion promotion emails complete.')
