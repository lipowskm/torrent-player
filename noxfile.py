import nox
from nox_poetry import Session, session

nox.options.error_on_external_run = True
nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["test"]


@session(python=["3.8", "3.9", "3.10", "3.11"])
def test(s: Session) -> None:
    s.install(".", "pytest", "pytest-cov")
    s.run(
        "python",
        "-m",
        "pytest",
        "--cov=fact",
        "--cov-report=html",
        "--cov-report=term",
        "tests",
        *s.posargs,
    )
