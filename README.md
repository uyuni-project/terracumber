# Terracumber

When [Terraform](https://www.terraform.io/) meets [Cucumber](https://cucumber.io/).

This is exactly what [Uyuni](https://www.uyuni-project.org/) and [SUSE Manager](https://www.suse.com/products/suse-manager/) are using for part of the testing. We create an environment with terraform (sumaform) and then we run tests with Cucumber. Alternatively, terracumber can be also used to run Salt tests with [Salt Shaker](https://github.com/openSUSE/salt-test).

Until [SUSE's Hackweek 18](https://hackweek.suse.com/projects/terracumber-python-replacement-for-sumaform-test-runner) we were using a set of bash scripts, completely ad-hoc and hard to maintain and extend, and that is how Terracumber was born.

## Does this only work with sumaform?

No. It should work with any other environment as long as:

1. It is created with terraform.
2. The terraform has an structure similar to [sumaform](https://github.com/uyuni-project/sumaform), with several backends, and and output 'root' that contains the 'hostname' in the same way sumaform does.
3. The cucumber run produces one or more of the following outputs **[1]**:
   * Files:
     - `output*.html`
     - `output*.json` 
     - `spacewalk-debug.tar.bz2`
   * Directories:
     - `screenshots`
     - `cucumber_report`
     - `logs`
     - `results_junit`
4. The Salt Shaker run produces one or more of the following outputs **[1]**:
   * Directories:
     - `results_junit`

**[1]** We hope to make this configurable in the future.

## How should I use it?

### Software requirements

- Python 3
- [pyhcl](https://pypi.org/project/pyhcl/) module installed
- [paramiko](https://www.paramiko.org/) module installed
- [pygit2](https://www.pygit2.org/) module installed
- Terraform

`paramiko` is usually part of the base system packages. `pyhcl` and `pygit2` are packaged in the [Uyuni utils](https://download.opensuse.org/repositories/systemsmanagement:/Uyuni:/Utils/) repository.

Terraform must be configured as needed to run the terraform templates you are going to use.

### Quickstart

See [EXAMPLE.md](EXAMPLE.md) for a quick intro about the calls to `terracumber-cli`

## Advanced usage

### Create/adjust your .tf file

You will need to create at least one `.tf` file to use it to launch your environment, as well as configuring everything else (such as what command to run for the test suite).

Keep in mind:

1. There are some mandatory variables for the `.tf` file (see one of the [examples](examples/)
2. You can add extra variables to your `.tf` file, so you can use it when creating the environment. Those variables will need to be exported before running `terracumber-cli` as `TF_VAR_`, as explained at the [terraform doc](https://learn.hashicorp.com/terraform/getting-started/variables.html#from-environment-variables). Our example adds SCC credentials to pass them to Uyuni/SUSE Manager, and GitHub credentials to use them to clone the GitHub cucumber repository **[1]**

**[1]** To clone your terraform repository, it is allowed to use `TF_VAR_GIT_USER` and `TF_VAR_GIT_PASSWORD` instead of `--gituser` and `--gitpassword`, in case you do not want the credentials visible at the list of processes. If you use both the environment and the variables, then the parameters will be used to clone the terraform repository, and the variables to clone the cucumber repository at the controller.

### Create email templates

You need to create two email templates, one to be used when the environment fails to be created, the other to be used after cucumber is able to run.

The email templates are plain text files with some variables to be replaced by `terracumber-cli`:

* `$urlprefix` - Directly from your `.tf` file, from variable `URL_PREFIX`
* `$timestamp` - Either the environment variable `BUILD_NUMBER` provided by Jenkins, or a timestamp in format `%Y-%m-%d-%H-%M-%S` otherwise (corresponding to the time and date when `terracumber-cli` started.
* `$tests` - Total number of tests executed by cucumber
* `$passed` - Number of tests executed by cucumber without failures or errors
* `$failures` - Number of tests executed by cucumber with failures
* `$errors` - Number of tests executed by cucumber with errors
* `$skipped` - Number of tests skipped by cucumber
* `$failures_log` - A list of failed tests, the number of failures is determined by `terracumber-cli` `--nlines` parameter

## Bonus: clean old results

The script `clean-old-results` can be used to get rid of undesired old results (use `-h` to get help)

## How to contribute

It is easy: 
- Make sure you have Git commit signing enabled. If you are not doing it already, check out the [GitHub documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification).
- Make sure unit tests are passing
  To run them:
  ```bash
  python3 -m unittest
  ```
  For now the unit tests only cover the module.
- Then just Pull Request with your contribution.


