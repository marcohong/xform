from setuptools import setup

setup(
    name='xform',
    version='0.3.1',
    description='Binding form data validation framework.',
    author='Maco',
    author_email='macohong@hotmail.com',
    zip_safe=False,
    license='MIT License',
    url='https://github.com/marcohong/xform',
    keywords=['Form validation', 'Data Binding',
              'Tornado web', 'aiohttp web', 'Sanic web'],
    packages=['xform', 'xform/adapters'],
    python_requires='>=3.6',
    install_requires=['multidict', 'attrs'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: Implementation :: CPython",
        'Operating System :: OS Independent',
        'Framework :: AsyncIO',
    ]
)
