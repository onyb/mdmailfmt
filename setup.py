from setuptools import setup

setup(name='mdmailfmt',
      version='0.1',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.5',
          'Topic :: Communications :: Email :: Email Clients (MUA)',
      ],
      description='Send markdown email templates',
      url='http://github.com/lajarre/mdmailfmt',
      author='Alexandre Hajjar',
      author_email='alexandre.hajjar@gmail.com',
      license='MIT',
      packages=['mdmailfmt'],
      install_requires=[
          'markdown',
      ],
      include_package_data=True,
      zip_safe=False)
