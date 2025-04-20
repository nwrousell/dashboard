"""
Database Wrapper

Sources will call methods to insert into the underlying sql db, and the frontend will call methods to extract/aggregate data for visualizations.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Adapters
sqlite3.register_adapter(
    datetime, lambda dt: dt.isoformat()
)  # TODO: normalize timezone automatically
# sqlite3.register_converter("timestamp", lambda s: datetime.fromisoformat(s.decode()))
sqlite3.register_adapter(timedelta, lambda td: td.seconds)


class Database:
    def __init__(self, db_path: str = "./store.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        # self.conn.row_factory = sqlite3.Row  # optional: return rows as dict-like
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            self.conn.close()

    def create_table(self, name: str, columns: List[str]):
        assert columns[0] == "timestamp timestamp"
        for col in columns:
            assert len(col.split(" ")) == 2

        column_str = ",\n".join(columns)
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {name} (
{column_str}
)""")

    def insert(self, table: str, columns: List[str], rows: List[Tuple]):
        comma_separated_columns = ", ".join(columns)
        comma_separated_colon_columns = ", ".join(map(lambda c: ":" + c, columns))

        self.cursor.executemany(
            f"INSERT INTO {table} ({comma_separated_columns}) VALUES ({comma_separated_colon_columns})",
            rows,
        )
        print(f"inserted {len(rows)} rows into {table} table")

    def query(
        self,
        table: str,
        metric: str,
        time_periods: List[Tuple[datetime, datetime]],
        aggregation_type,
        group_by_column: Optional[str] = None,
    ):
        """
        Collects events in a given list of time periods and aggregates them using the specified aggregation method.
        Performs the aggregation in a single SQL query.

        :param table: String, name of table
        :param metric: String, column to perform aggregation over
        :param time_periods: List of tuples, each containing start and end datetimes.
        :param aggregation_type: The aggregation method ('max', 'mean', 'median', 'sum', 'min').
        :param group_by_column: The column to group by
        :return: List of results, one for each time period, containing the aggregated value.
        """

        for timeperiod in time_periods:
            timeperiod = (timeperiod[0].isoformat(), timeperiod[1].isoformat())

        aggregation_methods = {
            "max": f"MAX({metric})",
            "mean": f"AVG({metric})",
            "median": f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {metric})",
            "sum": f"SUM({metric})",
            "min": f"MIN({metric})",
        }

        if aggregation_type not in aggregation_methods:
            raise ValueError(
                f"Invalid aggregation type: {aggregation_type}. Choose from 'max', 'mean', 'median', 'sum', 'min'."
            )

        time_period_conditions = []
        for start, end in time_periods:
            group_str1 = f", {group_by_column}" if group_by_column else ""
            group_str2 = f"\tGROUP BY {group_by_column}\n" if group_by_column else ""
            time_period_conditions.append(f"""
                SELECT '{start} - {end}' AS time_period, 
                    {aggregation_methods[aggregation_type]} AS aggregated_value{group_str1}
                FROM {table}
                WHERE timestamp BETWEEN '{start}' AND '{end}'{group_str2}
            """)

        final_query = " UNION ALL ".join(time_period_conditions)
        self.cursor.execute(final_query)
        results = self.cursor.fetchall()
        if group_by_column:
            return [
                {
                    "timeperiod": result[0],
                    "value": result[1],
                    "group": result[2],
                }
                for result in results
            ]
        else:
            return [{"timeperiod": result[0], "value": result[1]} for result in results]


if __name__ == "__main__":
    pass
    # with Database() as db:
    #     print("hi")
