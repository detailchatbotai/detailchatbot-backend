python3 -m venv .venv

source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "[INFO] .venv is set up and all packages are installed. Activate with: source .venv/bin/activate"