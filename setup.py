from distutils.core import setup

setup(
    name='Terracumber',
    author='Julio González Gil',
    author_email='jgonzalez@suse.com',
    scripts=['terracumber-cli'],
    url='https://github.com/uyuni-project/terracumber',
    description='When Terraform meets Cucumber.',
    long_description=open('README.md').read(),
    install_requires=[
        "pyhcl",
        "paramiko",
        "pygit2",
    ],
)
