import config
import unittest

class TestUtils(unittest.TestCase):
    def test_read_config(self):
        # SCC_USER and SCC_PASSWORD do not have value on the TF
        variables = { "URL_PREFIX": "https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE",
                      "CUCUMBER_COMMAND": "export PRODUCT='Uyuni' && cd /root/spacewalk/testsuite && rake cucumber:testsuite",
                      "CUCUMBER_BRANCH": "master",
                      "CUCUMBER_RESULTS": "/root/spacewalk/testsuite",
                      "MAIL_SUBJECT": "Results Uyuni-Master $status: $tests scenarios ($failures failed, $errors errors, $skipped skipped, $passed passed)",
                      "MAIL_TEMPLATE": "templates/mail-template-jenkins.txt",
                      "MAIL_SUBJECT_ENV_FAIL": "Results Uyuni-Master: Environment setup failed",
                      "MAIL_TEMPLATE_ENV_FAIL": "templates/mail-template-jenkins-env-fail.txt",
                      "MAIL_FROM": "galaxy-ci@suse.de",
                      "MAIL_TO": "juliogonzalez@localhost",
                      "GIT_USER": "null",
                      "GIT_PASSWORD": "null" }
        self.maxDiff = None
        self.assertDictEqual(config.read_config('tests/test.tf'), variables)


if __name__ == '__main__':
    unittest.main()
