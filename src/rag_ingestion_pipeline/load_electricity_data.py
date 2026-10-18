
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from .database import engine


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "nigeria_electricity_data.xlsx"
)


def load_electricity_data() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Excel file not found: {DATA_FILE}")

    state_df = pd.read_excel(DATA_FILE, sheet_name="State_Coverage")
    tariff_df = pd.read_excel(DATA_FILE, sheet_name="Tariffs")

    with engine.begin() as connection:
        state_df.to_sql(
            "state_coverage",
            con=connection,
            if_exists="replace",
            index=False,
        )

        tariff_df.to_sql(
            "electricity_tariffs",
            con=connection,
            if_exists="replace",
            index=False,
        )

        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_state_coverage_state "
                "ON state_coverage (\"State_or_Area\")"
            )
        )

        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_electricity_tariffs_disco "
                "ON electricity_tariffs (\"DisCo_ID\")"
            )
        )

    print(f"Loaded {len(state_df)} state coverage records.")
    print(f"Loaded {len(tariff_df)} electricity tariff records.")


if __name__ == "__main__":
    load_electricity_data()
