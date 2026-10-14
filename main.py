from __future__ import annotations

import argparse
import sys
from pathlib import Path
import customtkinter as ctk

from database.migrations import inicializar_base_de_datos
from src.ui.app import HeladeriaApp


def main() -> None:
    parser = argparse.ArgumentParser(description="HELA-POS - Sistema POS Heladería Artesanal")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Ruta personalizada a la base de datos SQLite.",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None

    inicializar_base_de_datos(db_path=db_path)

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    app = HeladeriaApp(db_path=db_path)
    app.mainloop()


if __name__ == "__main__":
    main()
