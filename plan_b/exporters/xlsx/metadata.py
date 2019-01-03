import dateutil

from datetime import date
from openpyxl import load_workbook
from typing import List, Dict, Tuple

from plan_b.team import Team
from plan_b.date_utils import get_months_range
from plan_b.exporters.xlsx.utils import Pos, write_row, RelPos, Region


METADATA_HEADER = 'CAPACITY PLAN METADATA v0.2 - DO NOT EDIT'


class ItemAllocation:

    def __init__(self, item_name: str):
        self.name = item_name
        self.allocations: List[Tuple[date, float]] = []


class TeamAllocation:

    def __init__(self, team_name: str):
        self.team_name: str = team_name
        self.items: Dict[str, ItemAllocation] = {}


class CellReference:

    def __init__(self, pos: Pos, title: str):
        self.pos: Pos = pos
        self.title: str = title


def save_metadata(
    sheet, start_date: date, end_date: date, allocations_by_team: Dict[Team, Dict[str, Region]]
):
    offset = Pos(0, 0)
    write_row(sheet, offset, cell_generator=[METADATA_HEADER])
    write_row(
        sheet,
        RelPos(offset, 1),
        cell_generator=['Period', start_date.isoformat(), end_date.isoformat()]
    )
    write_row(sheet, RelPos(offset, 2), cell_generator=['Team calendars'])
    offset = RelPos(offset, 3)
    row = 0
    for team, allocations in allocations_by_team.items():
        write_row(sheet, RelPos(offset, row), cell_generator=['Team', team.name])
        row += 1
        for item_name, table_pos in allocations.items():
            write_row(
                sheet,
                RelPos(offset, row),
                cell_generator=[
                    'Item',
                    item_name,
                    table_pos.offset.row,
                    table_pos.offset.column,
                    table_pos.rows,
                    table_pos.columns
                ]
            )
            row += 1


def load_metadata(filename: str) -> Dict[str, TeamAllocation]:
    workbook = load_workbook(filename, read_only=True)

    metadata_sheet = workbook['Meta']

    row_idx = 0
    team_calendar_flag = False

    team_allocations = {}

    team_sheet = None
    months_range = None
    current_team = None

    for row in metadata_sheet.rows:
        if row_idx == 0:
            if row[0].value != METADATA_HEADER:
                raise ValueError('Invalid header in metadata section detected')

        if row[0].value == 'Period':
            start_date = dateutil.parser.parse(row[1].value)
            end_date = dateutil.parser.parse(row[2].value)
            months_range = list(get_months_range(start_date, end_date))

        if row[0].value == 'Team calendars':
            team_calendar_flag = True

        if team_calendar_flag:

            if row[0].value == 'Team':
                current_team = row[1].value
                team_allocations[current_team] = TeamAllocation(current_team)
                team_sheet = workbook[current_team]

            elif row[0].value == 'Item':
                current_team_allocation = team_allocations[current_team]

                item_row, item_start_column, item_column_count = row[2].value, row[3].value, row[5].value
                month_idx = 0
                item_allocation = ItemAllocation(row[1].value)

                item_cells = team_sheet[item_row + 1][item_start_column: item_start_column + item_column_count]
                for cell in item_cells:
                    item_allocation.allocations.append((months_range[month_idx], cell.value))
                    month_idx += 1

                current_team_allocation.items[item_allocation.name] = item_allocation

        row_idx += 1

    return team_allocations
