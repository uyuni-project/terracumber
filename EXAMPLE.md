These examples will assume you will be using libvirt, and a `main.tf` file `examples/main.tf-jenkins` that will launch an Uyuni environment, the Uyuni testsuite and emulate mails as sent for reports served from Jenkins.

Not all the parameters included on the examples ar mandatory, but some are added for clarity.

Check the help if you want to make the CLI calls shorter by using default values.

# Running step by step

First of all, create a copy of the `main.tf` example for Jenkins:

```bash
cp examples/main.tf-jenkins examples/main.tf-jenkins.mycopy
```

As you are going to run this locally, without using a bridge, and with a libvirt network, run this:

```bash
sed -i -e 's/use_avahi    = false/use_avahi    = true/' examples/main.tf-jenkins.mycopy
```

Also adjust to email to receive the reports. You should use an address local to your machine (`yourusername@localhost`)
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

Create an folder for the outputs (not required if ìt already exists):
```bash
mkdir /tmp/sumaform_outputs
```

Clone or update the repository with the terraform code (sumaform in our case):
```
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --gitrepo https://github.com/uyuni-project/sumaform.git --gitfolder /tmp/sumaform --gitref master --runstep gitsync
```

Create the terraform environment:
```
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/sumaform.log  --gitfolder /tmp/sumaform --init --runstep provision
```

Run an Uyuni testsuite step (iterate for more steps if needed):
```
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep cucumber --cucumber-cmd "TERRAFORM=/usr/bin/terraform TERRAFORM_PLUGINS=/usr/bin; export PRODUCT=Uyuni; cd /root/spacewalk/testsuite; rake cucumber:core"
```

When you are done with the tests, get the results:
```
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep getresults
```

And, finally, send an email (optional):
```
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/testsuite.log --gitfolder /tmp/sumaform --runstep mail

```

If you want to start again, run the `gitsync` step if you want to fetch changes, and then run the `provision` step without `--init` and providing a list of resources to be tained (the example includes instances and their disks):
```
./terracumber-cli --tf examples/main.tf-jenkins.mycopy --outputdir /tmp/sumaform_outputs --logfile /tmp/sumaform/sumaform.log  --gitfolder /tmp/sumaform  --runstep provision --taint '.*(domain|main_disk).*'
```
