import sys
from io import StringIO
from datetime import timedelta
from django.db import models
from django.utils import timezone


class SystemMonitorManager(models.Manager):

    def cron_script_run(self, item_name, run_interval, max_exec_time):
        obj, created = self.get_or_create(name=item_name, defaults={
            'item_type': SystemMonitor.CRON_SCRIPT,
            'run_interval': run_interval,
            'max_exec_time': max_exec_time,
        })
        obj.started_at = timezone.now()
        obj.finished_at = None
        obj.run_interval = run_interval
        obj.max_exec_time = max_exec_time
        obj.save()
        return obj


class SystemMonitor(models.Model):

    objects = SystemMonitorManager()

    class Meta:
        db_table = 'core_systemmonitor'

    CRON_SCRIPT = 0

    RESULT_NONE = 0
    RESULT_OK = 1
    RESULT_ERROR = 2

    name = models.CharField(max_length=255, unique=True)
    item_type = models.IntegerField(choices=[(CRON_SCRIPT, 'CRON_SCRIPT')])
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    last_finish_at = models.DateTimeField(null=True)
    run_interval = models.IntegerField()
    max_exec_time = models.IntegerField()
    last_run_result = models.IntegerField(choices=[
        (RESULT_NONE, 'NONE'),
        (RESULT_OK, 'OK'),
        (RESULT_ERROR, 'ERROR'),
    ], default=RESULT_NONE)

    stdout = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)

    def finish(self):
        self.finished_at = timezone.now()
        self.last_finish_at = self.finished_at

    def time_running(self):
        t2 = self.finished_at
        if not t2:
            t2 = timezone.now()
        return t2 - self.started_at

    def runs_too_long(self):
        diff = self.time_running()
        if diff > timedelta(seconds=self.max_exec_time):
            return True
        else:
            return False


class BotLog(models.Model):

    # objects = SystemMonitorManager()

    class Meta:
        db_table = 'core_bot_log'

    name = models.CharField(max_length=255, unique=True)

    created_at = models.DateTimeField(null=True)

    error = models.TextField(null=True, blank=True)


def cron_script_run(item_name, run_interval, max_exec_time):
    def _cron_script_run(fn):
        def decor(*args, **kwargs):
            old_stdout = sys.stdout
            stdout_string = StringIO()
            sys.stdout = stdout_string

            obj = SystemMonitor.objects.cron_script_run(item_name, run_interval, max_exec_time)
            try:
                result = fn(*args, **kwargs)
                obj.last_run_result = SystemMonitor.RESULT_OK
                obj.finish()
                obj.stderr = None
                obj.stdout = None

                return result
            except Exception as e:
                obj.stderr = e
                obj.last_run_result = SystemMonitor.RESULT_ERROR
            finally:
                result_string = stdout_string.getvalue()

                obj.stdout = result_string
                obj.save()

                sys.stdout = old_stdout
                sys.stdout.write(result_string)

        return decor
    return _cron_script_run


def cron_log_error(item_name, run_interval, max_exec_time):
    def _cron_log_error(fn):
        def decor(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as e:
                obj = BotLog.objects.create(
                    name=item_name,
                    error=e,
                    created_at=timezone.now(),
                )
        return decor
    return _cron_log_error
