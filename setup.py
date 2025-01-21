from setuptools import setup, find_packages

setup(
    name="books_portal",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.100.0",
        "sqlalchemy[asyncio]>=2.0.0",
        "alembic>=1.11.0",
        "asyncpg>=0.28.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "minio>=7.1.15",
        "redis>=5.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "email-validator>=2.0.0",
    ],
    python_requires=">=3.10",
) 