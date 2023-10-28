set -o pipefail

source /opt/venv/bin/activate

for r in requirements*.txt; do
  pip install --disable-pip-version-check -r $r | { grep -v "already satisfied" || :; }
done

