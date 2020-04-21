"""Extract data from junit output XML files"""
from glob import glob
from xml.dom import minidom


class Junit:
    """The junit class extracts data from junit output XML files"""
    def __init__(self, path):
        self.path = path

    def get_totals(self):
        """Get the totals for all tests at the parsed junit output XML files

        Returns a dictionary with the elements: failures, errors, skipped, tests, time.
        All integers except time, that is a real.
        """
        found = False
        res = {'failures': 0, 'errors': 0, 'skipped': 0, 'tests': 0, 'time': 0}
        for tfile in glob(self.path):
            found = True
            testsuites = minidom.parse(tfile).getElementsByTagName('testsuite')
            for testsuite in testsuites:
                res['failures'] += int(testsuite.attributes['failures'].value)
                res['errors'] += int(testsuite.attributes['errors'].value)
                res['skipped'] += int(testsuite.attributes['skipped'].value)
                res['tests'] += int(testsuite.attributes['tests'].value)
                res['time'] += float(testsuite.attributes['time'].value)
        res['passed'] = res['tests'] - res['failures'] - res['errors'] - res['skipped']
        if found:
            return res
        return None

    def get_failures(self, number=-1):
        """Return a list of failure messages for failed tests.

        Keyword arguments:
        number: The maximum number of messages to return, -1 for all messages
        """
        failures = []
        for tfile in glob(self.path):
            j_failures = minidom.parse(tfile).getElementsByTagName('failure')
            if number == -1:
                number = len(failures)
            for j_failure in j_failures:
                if len(failures) <= number:
                    failures.append(j_failure.attributes['message'].value)
                else:
                    break
        return failures
