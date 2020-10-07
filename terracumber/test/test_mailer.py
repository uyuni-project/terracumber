from email.mime.text import MIMEText

import config
import junit
import mailer
import unittest
import utils

class TestMailer(unittest.TestCase):
    def setUp(self):
        self.config = config.read_config('test/resources/test.tf')
        self.from_addr = self.config['MAIL_FROM']
        self.to_addr = self.config['MAIL_TO']
        self.template_data = {}
        self.template_data['urlprefix'] = self.config['URL_PREFIX']
        self.template_data['timestamp'] = 1

    def test_fill_template(self):

        # Testsuite failures
        message_assert = MIMEText("""#################################################################
# SUMMARY
#################################################################
Build:   https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1
Console: https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/console
Results: https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1
Report:  https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1/cucumber_report/cucumber_report.html
Logs:    https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1/spacewalk-debug.tar.bz2

#################################################################
# SCENARIOS
#################################################################
Total:   66
Passed:  63
Failed:  3
Errors:  0
Skipped: 0

failed Schedule some actions on the CentOS 7 traditional client
""")
        subject_assert = "Results Uyuni-Master FAILED: 66 scenarios (3 failed, 0 errors, 0 skipped, 63 passed)"

        junit_data = junit.Junit('test/resources/junit/failures')
        self.template_data['status'] = "FAILED"
        self.template_data['failures_log'] = '\n'.join(junit_data.get_failures(1))
        self.template_data = utils.merge_two_dicts(self.template_data,junit_data.get_totals())

        template = self.config['MAIL_TEMPLATE']
        subject = self.config['MAIL_SUBJECT']

        self.maxDiff = None
        mail = mailer.Mailer(template, self.from_addr, self.to_addr, subject, self.template_data)
        self.assertEqual(mail.get_subject(), subject_assert)
        self.assertEqual(str(mail.get_message()), str(message_assert))

        # Testsuite success
        message_assert = MIMEText("""#################################################################
# SUMMARY
#################################################################
Build:   https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1
Console: https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/console
Results: https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1
Report:  https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1/cucumber_report/cucumber_report.html
Logs:    https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1/spacewalk-debug.tar.bz2

#################################################################
# SCENARIOS
#################################################################
Total:   55
Passed:  55
Failed:  0
Errors:  0
Skipped: 0


""")
        subject_assert = "Results Uyuni-Master PASSED: 55 scenarios (0 failed, 0 errors, 0 skipped, 55 passed)"

        junit_data = junit.Junit('test/resources/junit/passed')
        self.template_data['status'] = "PASSED"
        self.template_data['failures_log'] = ''
        self.template_data = utils.merge_two_dicts(self.template_data,junit_data.get_totals())

        template = self.config['MAIL_TEMPLATE']
        subject = self.config['MAIL_SUBJECT']

        self.maxDiff = None
        mail = mailer.Mailer(template, self.from_addr, self.to_addr, subject, self.template_data)
        self.assertEqual(mail.get_subject(), subject_assert)
        self.assertEqual(str(mail.get_message()), str(message_assert))

        # Environment failures
        message_assert = MIMEText("""#################################################################
# SUMMARY
#################################################################
Build:   https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1
Console: https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/console
Results: https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE/1/execution/node/4/ws/results/1

Environment failed to be created, so no spacewalk-debug tarball or cucumber results are available.
""")
        subject_assert = "Results Uyuni-Master: Environment setup failed"
        self.template_data['status'] = "FAILED"
        template = self.config['MAIL_TEMPLATE_ENV_FAIL']
        subject = self.config['MAIL_SUBJECT_ENV_FAIL']

        self.maxDiff = None
        mail = mailer.Mailer(template, self.from_addr, self.to_addr, subject, self.template_data)
        self.assertEqual(mail.get_subject(), subject_assert)
        self.assertEqual(str(mail.get_message()), str(message_assert))


if __name__ == '__main__':
    unittest.main()
