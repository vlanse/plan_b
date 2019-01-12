from datetime import date
from typing import Dict, List
from xlsxwriter import Workbook

from plan_b.team import Team
from plan_b.plan import Project
from plan_b.exporters.xlsx.formats import init_formats
from plan_b.exporters.xlsx.metadata import save_metadata, TeamAllocation
from plan_b.exporters.xlsx.project import fill_project_worksheet
from plan_b.exporters.xlsx.team_calendar import fill_calendar_plan_worksheet, apply_plan_edits_to_team_calendar
from plan_b.exporters.xlsx.utils import write_row, Region, Pos, RelPos, merge_dicts


def export_plan(
    projects: List[Project],
    teams: List[Team],
    start_date: date,
    end_date: date,
    production_calendar: dict,
    output_file: str,
    team_allocations: Dict[str, TeamAllocation]
):
    workbook = Workbook(output_file)
    init_formats(workbook)

    sheets_by_team = {}
    for team in teams:
        sheets_by_team[team] = workbook.add_worksheet(team.name)

    sheets_by_project = {}
    for project in projects:
        sheets_by_project[project] = workbook.add_worksheet(project.name)

    total_cells_by_team = {}
    for project, sheet in sheets_by_project.items():
        total_cells_by_team = merge_dicts(
            total_cells_by_team,
            fill_project_worksheet(sheet, project, teams)
        )

    team_allocation_regions: Dict[Team, Dict[str, Region]] = {}
    for team, sheet in sheets_by_team.items():
        team_allocation_regions[team] = fill_calendar_plan_worksheet(
            sheet,
            start_date,
            end_date,
            team,
            production_calendar,
            projects,
            total_cells_by_team[team]
        )

        if team_allocations:
            apply_plan_edits_to_team_calendar(
                sheet, team_allocations[team.name], team_allocation_regions[team]
            )

    sheet = workbook.add_worksheet('Meta')
    save_metadata(sheet, start_date, end_date, team_allocation_regions)

    workbook.close()
