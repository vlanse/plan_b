from xlsxwriter import Workbook


MONTH_FORMAT = '%b/%Y'

GREEN_HEADER = {'bg_color': '#5E7E3F', 'font_color': 'white'}
green_header_format = None

BOLD_TOTAL = {'bold': True, 'bg_color': 'yellow', 'num_format': '0.0', 'top': 1, 'bottom': 1}
bold_total_format = None

BOLD_TOTAL_NO_BORDERS = {'bold': True, 'bg_color': 'yellow', 'num_format': '0.0'}
bold_total_no_borders_format = None

CENTERED_HEADER = {
    'align': 'center',
    'valign': 'top',
    'text_wrap': True,
    'bold': True,
    'bg_color': '#5E7E3F',
    'font_color': 'white',
}
centered_header_format = None

CENTERED_HEADER_BORDER = {
    'align': 'center',
    'valign': 'top',
    'text_wrap': True,
    'bold': True,
    'bg_color': '#5E7E3F',
    'font_color': 'white',
    'right': 1,
    'left': 1
}
centered_header_border_format = None

CENTERED_VERTICAL_TEXT_HEADER = {
    'align': 'left',
    'text_wrap': True,
    'bold': True,
    'bg_color': '#5E7E3F',
    'font_color': 'white',
    'rotation': 90,
}
centered_vertical_text_header_format = None

CENTERED_VERTICAL_TEXT_HEADER_LEFT_BORDER = {
    'align': 'left',
    'text_wrap': True,
    'bold': True,
    'bg_color': '#5E7E3F',
    'font_color': 'white',
    'rotation': 90,
    'left': 1
}
centered_vertical_text_header_left_border_format = None

CENTERED_VERTICAL_TEXT_HEADER_RIGHT_BORDER = {
    'align': 'left',
    'text_wrap': True,
    'bold': True,
    'bg_color': '#5E7E3F',
    'font_color': 'white',
    'rotation': 90,
    'right': 1
}
centered_vertical_text_header_right_border_format = None

NUMERIC = {
    'num_format': '0.0'
}
numeric_format = None

NUMERIC_BORDER_LEFT = {
    'num_format': '0.0',
    'left': 1
}
numeric_border_left_format = None

NUMERIC_BORDER_RIGHT = {
    'num_format': '0.0',
    'right': 1
}
numeric_border_right_format = None

CONF_LEVEL_HIGH = {
    'bg_color': '#CEEDD0',
    'num_format': '0.0',
}
conf_level_high_format = None

CONF_LEVEL_MED = {
    'bg_color': '#FCEAA5',
    'num_format': '0.0',
}
conf_level_med_format = None

CONF_LEVEL_LOW = {
    'bg_color': '#F7C9CF',
    'num_format': '0.0',
}
conf_level_low_format = None


__workbook = None


def init_formats(workbook: Workbook):
    global __workbook
    __workbook = workbook

    global green_header_format
    green_header_format = workbook.add_format(GREEN_HEADER)

    global bold_total_format
    bold_total_format = workbook.add_format(BOLD_TOTAL)

    global bold_total_no_borders_format
    bold_total_no_borders_format = workbook.add_format(BOLD_TOTAL_NO_BORDERS)

    global centered_header_format
    centered_header_format = workbook.add_format(CENTERED_HEADER)

    global numeric_format
    numeric_format = workbook.add_format(NUMERIC)

    global centered_vertical_text_header_format
    centered_vertical_text_header_format = workbook.add_format(CENTERED_VERTICAL_TEXT_HEADER)

    global numeric_border_left_format
    numeric_border_left_format = workbook.add_format(NUMERIC_BORDER_LEFT)

    global numeric_border_right_format
    numeric_border_right_format = workbook.add_format(NUMERIC_BORDER_RIGHT)

    global centered_header_border_format
    centered_header_border_format = workbook.add_format(CENTERED_HEADER_BORDER)

    global centered_vertical_text_header_left_border_format
    centered_vertical_text_header_left_border_format = workbook.add_format(CENTERED_VERTICAL_TEXT_HEADER_LEFT_BORDER)

    global centered_vertical_text_header_right_border_format
    centered_vertical_text_header_right_border_format = workbook.add_format(CENTERED_VERTICAL_TEXT_HEADER_RIGHT_BORDER)


def get_format(format_desc: dict):
    return __workbook.add_format(format_desc)
