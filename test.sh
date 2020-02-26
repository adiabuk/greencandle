export PYENV_ROOT="/opt/pyenv"
PYENV_BIN=/opt/pyenv/versions/3.7.0/bin/
export PATH="$PYENV_BIN:$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install 3.7.0
pyenv global 3.7.0
pip 
