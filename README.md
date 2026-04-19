how to build cli:

cd your project folder and run

PYINSTALLER_CONFIG_DIR="$PWD/_pyi_cfg" \
.venv_pyi311/bin/python -m PyInstaller --noconfirm --onefile \
  --name MagicTool \
  --distpath dist_universal2 \
  --workpath build_universal2 \
  --specpath spec_universal2 \
  --target-arch universal2 \
  --add-data "$PWD/mix:mix" \
  nrf_oneclick_program.py