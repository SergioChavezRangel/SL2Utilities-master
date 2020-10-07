from distutils.core import setup


setup(
    name='sl2util',
    version='1.0.2',
    packages=['sl2util'],
    url='',
    license='MIT License',
    author='SergioChavez',
    author_email='l2.steel.automation@gmail.com',
    description='Steelmaking Automation Utils',
    long_description=open('README.md').read(),
    py_modules=['sl2util.logger', 'sl2util.configdatareader', 'sl2util.dbhandler', 'sl2util.utils', ]
)
