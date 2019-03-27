from glob import glob
from xml.dom import minidom

class Junit:
    ''' The junit class extracts data from junit output XML files.

    :param path: The path where junit XML files are.
    '''
    def __init__(self, path):
        self.path = path

    def get_totals(self):
        ''' Get the totals for all the parsed junit output XML files.
        :returns: A dictionary with the elements: failures, errors, skipped, tests, time. All integers except time, that is a real.
        :rtype: dict
        '''
        t = { 'failures': 0, 'errors': 0, 'skipped': 0, 'tests': 0, 'time': 0 }
        for f in glob(self.path):
            testsuites = minidom.parse(f).getElementsByTagName('testsuite')
            for testsuite in testsuites:
                t['failures'] += int(testsuite.attributes['failures'].value)
                t['errors'] += int(testsuite.attributes['errors'].value)
                t['skipped'] += int(testsuite.attributes['skipped'].value)
                t['tests'] += int(testsuite.attributes['tests'].value)
                t['time'] += float(testsuite.attributes['time'].value)
        t['passed'] = t['tests'] - t['failures'] - t['errors'] - t['skipped']
        return(t)

    def get_failures(self, number=-1):
        ''' Return failure messages for failed tests.
        :param number: The maximum number of messages to return, -1 for all messages
        :returns: A list with the failure messages
        :rtype: list
        '''
        failures = []
        for f in glob(self.path):
            j_failures = minidom.parse(f).getElementsByTagName('failure')
            for j_failure in j_failures:
                if len(failures) <= number:
                    failures.append(j_failure.attributes['message'].value)
                else:
                    break
        return(failures)
