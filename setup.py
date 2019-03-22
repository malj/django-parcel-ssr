import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='django-parcel-ssr',
    version='0.2.1',
    author='Luka Maljic',
    author_email='luka@maljic.com',
    description='Django server side rendering, powered by Parcel bundler',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/malj/django-parcel-ssr',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'django',
        'requests_unixsocket'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
