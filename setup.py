from setuptools import setup, find_packages
setup(name = 'blips',
      version = '0.0',
      description = 'Small Events',
      author = 'Brett Viren',
      author_email = 'brett.viren@gmail.com',
      license = 'GPLv2',
      url = 'http://github.com/brettviren/blips',
      packages = find_packages(),
      install_requires=open("requirements.txt").readlines(),
      entry_points = {
          'console_scripts': [
              ]
      }
)

