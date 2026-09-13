#!/bin/zsh
# Point this repository at your GitHub account and push it.
#
#   ./publish.sh <your-github-username>
#   ./publish.sh <your-github-username> <repo-name>     (if you called it something else)
#
# Create the empty repository on github.com first -- see GITHUB.md. Run this once; after that, updating
# is the ordinary three lines at the bottom of GITHUB.md.
set -e
USER="$1"; REPO="${2:-laurel-corpus}"
if [ -z "$USER" ]; then echo "usage: ./publish.sh <your-github-username> [repo-name]"; exit 1; fi
cd "$(dirname "$0")"

# CITATION.cff ships with a placeholder because the address is not known until the repository exists.
# Anyone citing this dataset reads that line, so it has to be right before the first push.
if grep -q 'REPLACE-ME' CITATION.cff; then
  sed -i '' "s|https://github.com/REPLACE-ME/laurel-corpus|https://github.com/$USER/$REPO|" CITATION.cff
  git add CITATION.cff
  git commit -q -m "Point the citation at the published repository"
  echo "== CITATION.cff now points at github.com/$USER/$REPO"
fi

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER/$REPO.git"
echo "== pushing about 40 MB; GitHub will ask for your username and a personal access token"
git push -u origin main
echo
echo "Live at https://github.com/$USER/$REPO"
