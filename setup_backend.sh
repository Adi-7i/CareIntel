#!/usr/bin/env bash
# Install the locked backend environment, then initialize its configured database.
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

skip_migrations=false
case "${1:-}" in
    "") ;;
    --skip-migrations) skip_migrations=true ;;
    -h|--help)
        echo "Usage: ./setup_backend.sh [--skip-migrations]"
        echo "Installs uv/Python 3.12, locked dependencies and libmagic; prepares .env."
        echo "By default, checks external services and applies Alembic migrations."
        echo "Use --skip-migrations to install before configuring external services."
        exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
esac
if (( $# > 1 )); then
    echo "Too many arguments. See ./setup_backend.sh --help" >&2
    exit 2
fi
trap 'echo "Setup failed. Fix the error above and rerun ./setup_backend.sh." >&2' ERR

# Keep downloaded tools and caches in the repository; never edit shell profiles.
export UV_CACHE_DIR="$PWD/.tools/uv-cache"
export UV_PYTHON_INSTALL_DIR="$PWD/.tools/python"
export UV_PYTHON_BIN_DIR="$PWD/.tools/bin"
export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
mkdir -p .tools/bin
if [[ -x .tools/bin/uv ]]; then
    uv_bin="$PWD/.tools/bin/uv"
elif command -v uv >/dev/null 2>&1; then
    uv_bin="$(command -v uv)"
else
    command -v curl >/dev/null 2>&1 || {
        echo "Install curl with your OS package manager, then rerun setup." >&2
        exit 1
    }
    echo "Installing uv locally from the official Astral installer..."
    curl --fail --silent --show-error --location --connect-timeout 15 --max-time 120 \
        https://astral.sh/uv/install.sh --output .tools/install-uv.sh
    UV_UNMANAGED_INSTALL="$PWD/.tools/bin" sh .tools/install-uv.sh
    uv_bin="$PWD/.tools/bin/uv"
fi

echo "Creating .venv with Python 3.12 and installing uv.lock dependencies..."
"$uv_bin" sync --python 3.12 --all-extras --frozen

if ! .venv/bin/python -c 'import magic; magic.from_buffer(b"CareIntel", mime=True)' \
    >/dev/null 2>&1; then
    echo "Installing the system libmagic library (administrator access may be needed)..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y libmagic1
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y file-libs
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm file
    elif command -v brew >/dev/null 2>&1; then
        brew install libmagic
    else
        echo "Install libmagic using your OS package manager, then rerun setup." >&2
        exit 1
    fi
fi
.venv/bin/python -c 'import magic; magic.from_buffer(b"CareIntel", mime=True)'
.venv/bin/python scripts/backend_runtime.py prepare-env

if [[ "$skip_migrations" == true ]]; then
    echo "Dependencies installed. Database migrations and service checks were skipped."
    echo "Configure .env, then rerun ./setup_backend.sh before starting the backend."
else
    .venv/bin/python scripts/backend_runtime.py check --before-migrations
    echo "Applying pending database migrations..."
    .venv/bin/alembic upgrade head
    .venv/bin/alembic current
    .venv/bin/python scripts/backend_runtime.py check
    echo "Backend setup complete. Run ./start.sh"
fi
