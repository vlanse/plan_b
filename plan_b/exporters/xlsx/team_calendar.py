from datetime import date
from typing import List, Dict

from plan_b.team import Team
from plan_b.plan import ProductRelease
from plan_b.date_utils import get_months_range, get_month_workdays_count
from plan_b.exporters.xlsx.utils import Pos, Region, write_row, RelPos

from plan_b.exporters.xlsx.formats import MONTH_FORMAT
from plan_b.exporters.xlsx import formats
from plan_b.exporters.xlsx.metadata import TeamAllocation, CellReference


def _create_team_capacity_table(
    sheet, start_date: date, end_date: date, team: Team, offset: Pos = Pos()
) -> Region:
    sheet.write(offset.row, offset.column, 'People', formats.green_header_format)
    column_count = write_row(
        sheet,
        RelPos(offset, 0, 1),
        cell_generator=(x.strftime(MONTH_FORMAT) for x in get_months_range(start_date, end_date)),
        cell_format=formats.green_header_format
    )

    v_offset = offset.row + 1
    for worker in team.members:
        sheet.write(v_offset, offset.column, worker.name)
        write_row(
            sheet,
            Pos(v_offset, offset.column + 1),
            cell_generator=(worker.efficiency(dt) for dt in get_months_range(start_date, end_date)),
            cell_format=formats.numeric_format
        )
        v_offset += 1

    sheet.write(offset.row + len(team.members) + 1, 0, 'Total', formats.bold_total_format)
    write_row(
        sheet,
        RelPos(offset, len(team.members) + 1, 1),
        cell_func=lambda col, _:
            f'=SUM({RelPos(offset, 1, col).to_cell()}:{RelPos(offset, len(team.members), col).to_cell()})',
        col_count=column_count,
        cell_format=formats.bold_total_format
    )

    return Region(Pos(0, 0), 2 + len(team.members), column_count)


def _create_team_calendar_table(
    sheet,
    capacity_table: Region,
    start_date: date,
    end_date: date,
    production_calendar: dict,
    releases: List[ProductRelease],
    total_cells: List[CellReference]
) -> Dict[str, Region]:

    offset = RelPos(capacity_table.pos_below(), 1)

    sheet.write(offset.row, offset.column, '', formats.green_header_format)
    column_count = write_row(
        sheet,
        RelPos(offset, 0, 1),
        cell_generator=(x.strftime(MONTH_FORMAT) for x in get_months_range(start_date, end_date)),
        cell_format=formats.green_header_format
    )

    sheet.write(offset.row + 1, offset.column, 'People')
    write_row(
        sheet,
        RelPos(offset, 1, 1),
        cell_func=lambda col, _: f'={Pos(capacity_table.pos_below().row - 1, col).to_cell()}',
        col_count=column_count,
        cell_format=formats.numeric_format
    )

    sheet.write(offset.row + 2, offset.column, 'Working days')
    workdays_count = get_month_workdays_count(start_date, end_date, production_calendar)
    write_row(
        sheet,
        RelPos(offset, 2, 1),
        cell_generator=get_months_range(start_date, end_date),
        cell_func=lambda _, d: workdays_count[d],
        col_count=column_count
    )

    sheet.write(offset.row + 3, offset.column, 'Working weeks')
    write_row(
        sheet,
        RelPos(offset, 3, 1),
        cell_func=lambda col, _: f'={Pos(offset.row + 2, col).to_cell()} / 5',
        col_count=column_count
    )

    sheet.write(offset.row + 4, offset.column, 'Man * weeks')
    write_row(
        sheet,
        RelPos(offset, 4, 1),
        cell_func=lambda c, _: f'={Pos(offset.row + 1, c).to_cell()} * {Pos(offset.row + 3, c).to_cell()}',
        col_count=column_count,
        cell_format=formats.numeric_format
    )

    # TODO consider either time of the year or real vacations of people (e.g. create vacation field for worker)
    # TODO or use both at once - when real dates of vacations are not known
    sheet.write(offset.row + 5, offset.column, 'Vacations')
    calendar_table_totals_row = capacity_table.pos_below().row - 1
    write_row(
        sheet,
        RelPos(offset, 5, 1),
        cell_func=lambda c, _: f'={Pos(calendar_table_totals_row, c).to_cell()} * 5 / 12',
        col_count=column_count,
        cell_format=formats.numeric_format
    )

    sheet.write(offset.row + 6, offset.column, 'Support tasks')
    write_row(
        sheet,
        RelPos(offset, 6, 1),
        cell_func=lambda c, _: 1.5,
        col_count=column_count,
        cell_format=formats.numeric_format
    )

    sheet.write(offset.row + 7, offset.column, 'Remaining', formats.bold_total_format)
    write_row(
        sheet,
        RelPos(offset, 7, 1),
        cell_func=lambda c, _:
            f'={Pos(offset.row + 4, c).to_cell()}'
            f'-{Pos(offset.row + 5, c).to_cell()}'
            f'-{Pos(offset.row + 6, c).to_cell()}',
        col_count=column_count,
        cell_format=formats.bold_total_format
    )
    sheet.set_column(0, 0, width=15)

    # allocations region
    offset = RelPos(offset, 8)
    time_allocation_cells_by_item: Dict[str, Region] = {}

    row_count = 0
    for cell_ref in total_cells:
        allocation_pos = RelPos(offset, row_count)
        sheet.write(allocation_pos.row, allocation_pos.column, cell_ref.title)
        time_allocation_cells_by_item[cell_ref.title] = Region(allocation_pos, 1, column_count)
        row_count += 1

    # difference between total available and allocated resources
    offset = RelPos(offset, row_count)
    sheet.write(offset.row, 0, 'Difference', formats.bold_total_format)
    for i in range(1, column_count + 1):
        sheet.write(
            offset.row,
            offset.column + i,
            f'={RelPos(offset, - len(releases) - 1, i).to_cell()}'
            f'-SUM({RelPos(offset, - len(releases), i).to_cell()}:{RelPos(offset, - 1, i).to_cell()})',
            formats.bold_total_format
        )

    # summary by release rows
    offset = RelPos(offset, len(releases))
    write_row(
        sheet, offset, cell_generator=['Item', 'Needed', 'Allocated', 'Diff'], cell_format=formats.green_header_format
    )
    offset = RelPos(offset, 1)
    row_count = 0
    for cell_ref in total_cells:
        row_offset = RelPos(offset, row_count)
        allocation_pos = time_allocation_cells_by_item[cell_ref.title].offset
        write_row(
            sheet,
            row_offset,
            cell_generator=[
                cell_ref.title,
                f'={cell_ref.pos.to_cell()}',
                f'=SUM({allocation_pos.to_cell()}:{RelPos(allocation_pos, column=column_count).to_cell()})',
                f'={RelPos(row_offset, column=2).to_cell()}-{RelPos(row_offset, column=1).to_cell()}'
            ],
            cell_format=formats.numeric_format
        )
        row_count += 1

    return time_allocation_cells_by_item


def fill_calendar_plan_worksheet(
    sheet,
    start_date: date,
    end_date: date,
    team: Team,
    production_calendar: dict,
    releases: List[ProductRelease],
    total_cells: List[CellReference]
) -> Dict[str, Region]:
    capacity_table = _create_team_capacity_table(sheet, start_date, end_date, team)

    return _create_team_calendar_table(
        sheet,
        capacity_table,
        start_date,
        end_date,
        production_calendar,
        releases,
        total_cells
    )


def apply_plan_edits_to_team_calendar(
    sheet, previous_data: TeamAllocation, releases_pos: Dict[str, Region]
):
    for item_name, region in releases_pos.items():
        idx = 0
        for col in range(region.offset.column, region.offset.column + region.columns):
            sheet.write(region.offset.row, col, previous_data.items[item_name].allocations[idx][1])
            idx += 1
