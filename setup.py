import pip
from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = pip.req.parse_requirements('requirements_common.txt', session=pip.download.PipSession())
common_requirements = [str(r.req) for r in requirements]

requirements = pip.req.parse_requirements('requirements_test.txt', session=pip.download.PipSession())
test_requirements = [str(r.req) for r in requirements]

requirements = pip.req.parse_requirements('requirements_dev.txt', session=pip.download.PipSession())
dev_requirements = [str(r.req) for r in requirements]

setup(
    name='jira_linker_slack_bot',
    version='1.0.0',
    description='A SlackBot that responds to messages that contain JIRA issue keys with a message that contains details about the JIRA issues. Runs in Amazon Lambda.',
    long_description=readme,
    author='Mike Weaver',
    author_email='mike@weaverfamily.net',
    url='https://github.com/mikeweaver/jira_linker_slack_bot',
    install_requires=common_requirements,
    tests_require=test_requirements,
    extras_require={
        'dev': dev_requirements
    },
    test_suite="tests"
)
