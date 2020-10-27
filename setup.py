import setuptools

import santepublique

setuptools.setup(
        name="santepublique",
        version=santepublique.__version__,
        author="Jérôme JACQ",
        author_email="jacqjero@gmail.com",
        include_package_data=True,
        packages=setuptools.find_packages(),
        install_requires=['numpy','pandas']
)       
