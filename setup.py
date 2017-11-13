from setuptools import setup

KEYWORDS = ['unittest', 'testing', 'tests']
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: Implementation :: CPython',
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Testing',
]
setup(
    name='nose2-jira-plugin',
    version=open('src/nose2_contrib/jira/_version.py').readlines()[-1].split()[-1].strip('"\''),
    packages=['nose2_contrib', 'nose2_contrib.jira'],
    package_dir={'': 'src'},
    url='https://github.com/artragis/nose2-jira-plugin',
    license='MIT',
    author='François (artragis) Dambrine',
    author_email='artragis@gmail.com',
    description='A nose2 test runner plugin to deal with jira bugtracker',
    keywords=KEYWORDS,
    classifiers=CLASSIFIERS,
    install_requires=['jira==1.0.10', 'nose2>=0.6.5'],
    extras_require={
        'doc': ['sphinx-rtd-theme==0.2.4', 'sphinxcontrib-websupport==1.0.1', 'Sphinx==1.6.5',
                'sphinxcontrib-mermaid==0.3']
    }
)
