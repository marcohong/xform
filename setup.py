from setuptools import setup

setup(
    name='xform',
    version='0.2.1',
    description='Binding form data validation framework.',
    author='Maco',
    author_email='macohong@hotmail.com',
    zip_safe=False,
    license='MIT License',
    url='https://github.com/marcohong/xform',
    keywords=['Form data validation', 'Form Data Binding', 'Web framework'],
    packages=['xform', 'xform/adapters'],
    python_requires='>=3.6',
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
        "Programming Language :: Python :: Implementation :: CPython",
        'Operating System :: OS Independent',
        'Framework :: AsyncIO',
    ]
)
