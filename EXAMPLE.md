# Examples

These examples assume that you will be using `libvirt` and a `main.tf` file based on `examples/main.tf-jenkins` that will launch an Uyuni environment, the Uyuni test suite and emulate emails as sent for reports served from Jenkins.

Not all the parameters included on the examples ar mandatory, but some are added for clarity.

Check the help if you want to make the CLI calls shorter by using default values.

## Running step by step

First of all, create a copy of the `main.tf` example for Jenkins:

```bash
cp examples/main.tf-jenkins examples/main.tf-jenkins.mycopy
```

As you are going to run this locally, without using a bridge, and with a libvirt network, run this:

```bash
sed -i -e 's/use_avahi    = false/use_avahi    = true/' examples/main.tf-jenkins.mycopy
```

Also adjust the email to receive the reports. You should use an address local to your machine (`yourusername@localhost`)

```bash
sed -i -e 's/default = "juliogonzalez@localhost"/default = "YOUREMAIL"/' examples/main.tf-jenkins.mycopy
```

Export SCC credentials:

```bash
export TF_VAR_SCC_USER=<ID>
export TF_VAR_SCC_PASSWORD=<PASSWORD>
```

Export a variable `BUILD_TIMESTAMP` to be used by all the steps (when running on Jenkins this is not needed and `BUILD_NUMBER` provided by Jenkins can be used automatically):

```bash
export BUILD_TIMESTAMP=$(date '+%Y-%m-%d-%H-%M-%S')
```

Create a folder for the outputs (not required if ìt already exists):

```bash
mkdir /tmp/sumaform_outputs
```

Clone or update the repository with the terraform code (sumaform in our case):

```bash
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --gitrepo https://github.com/uyuni-project/sumaform.git --gitfolder /tmp/sumaform --gitref master --runstep gitsync
```

Create the terraform environment:

```bash
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/sumaform.log  --gitfolder /tmp/sumaform --init --runstep provision
```

Run an Uyuni test suite step (iterate for more steps if needed):

```bash
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep cucumber --cucumber-cmd "TERRAFORM=/usr/bin/terraform TERRAFORM_PLUGINS=/usr/bin; export PRODUCT=Uyuni; cd /root/spacewalk/testsuite; rake cucumber:core"
```

When you are done with the tests, get the results:

```bash
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep getresults
```

And, finally, send an email (optional):

```bash
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep mail

```

If you want to start again, run the `gitsync` step if you want to fetch changes, and then run the `provision` step without `--init` and providing a list of resources to be tainted (the example includes instances and their disks):

```bash
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/sumaform.log  --gitfolder /tmp/sumaform  --runstep provision --taint '.*(domain|main_disk).*'
```

## Salt Shaker executions

The same `gitsync`, `provision` steps detailed above also apply when running Salt Shaker, then you have the following steps that are only for Salt Shaker:

Run Salt Shaker unit tests:

```bash
./terracumber-cli --tf examples/main.tf-salt-shaker --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep saltshaker --saltshaker-cmd "/usr/bin/salt-test --package-flavor bundle --skiplist https://raw.githubusercontent.com/openSUSE/salt-test-skiplist/main/skipped_tests.toml unit -- --core-tests --ssh-tests --slow-tests --run-expensive --run-destructive --junitxml /root/results_junit/junit-report-unit.xml -vvv --tb=native"
```

Run Salt Shaker integration tests:

```bash
./terracumber-cli --tf examples/main.tf-salt-shaker --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep saltshaker --saltshaker-cmd "/usr/bin/salt-test --package-flavor bundle --skiplist https://raw.githubusercontent.com/openSUSE/salt-test-skiplist/main/skipped_tests.toml integration -- --core-tests --ssh-tests --slow-tests --run-expensive --run-destructive --junitxml /root/results_junit/junit-report-integration.xml -vvv --tb=native"
```

Run Salt Shaker functional tests:

```bash
./terracumber-cli --tf examples/main.tf-salt-shaker --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep saltshaker --saltshaker-cmd "/usr/bin/salt-test --package-flavor bundle --skiplist https://raw.githubusercontent.com/openSUSE/salt-test-skiplist/main/skipped_tests.toml functional -- --core-tests --ssh-tests --slow-tests --run-expensive --run-destructive --junitxml /root/results_junit/junit-report-functional.xml -vvv --tb=native"
```

**NOTE:** You can use `--package-flavor classic` when triggering the Salt Shaker in order to test using the classic Salt package instead of the Salt Bundle.

When you are done with the Salt Shaker tests, get the results:

```bash
./terracumber-cli --tf examples/main.tf-salt-shaker --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep saltshaker_getresults
```

And, finally, send an email (optional):

```bash
./terracumber-cli --tf examples/main.tf-salt-shaker --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep saltshaker_mail
```
