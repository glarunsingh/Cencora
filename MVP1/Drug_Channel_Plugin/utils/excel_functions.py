import logging
import os.path
import sys
import time
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Border, Side

import pandas as pd

from utils.logs import create_log

logger = create_log(name="Drug_Channel", level=logging.INFO)


class ExcelFunc:
    def __init__(self):
        pass

    def file_name(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        name = "DrugChannel_" + timestamp + '.xlsx'
        return name

    def file_path(self):
        temp_dir = './temp'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        name = self.file_name()
        path = os.path.join(temp_dir, name)
        return path, name

    def convert_utc_date(self, date_str):
        dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
        date_obj = datetime.strptime(date_str, dateformat)
        formatted_date = date_obj.strftime("%A, %B %d, %Y")
        return formatted_date

    def create_dataframe(self, data):
        df = pd.DataFrame(data)
        df['news_date'] = df['news_date'].apply(self.convert_utc_date)
        df = df.rename(
            columns={'news_date': 'Date', "news_title": "Title", "news_url": "URL", "news_summary": "Summary",
                     "sentiment": "Sentiment"})
        df.index += 1
        return df

    def create_excel(self, df, f_path):
        workbook = Workbook()
        sheet = workbook.active

        # Set headers in the first row
        headers = ['Sr NO.'] + list(df.columns)
        sheet.append(headers)

        # Set dynamic column widths and apply text wrapping
        max_width = 78
        wrap_alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        for col_idx, col in enumerate(headers, start=1):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) if col not in ['Sr NO.',
                                                                                            'Sentiment'] else len(
                col) + 1
            adjusted_width = min(max_length, max_width)
            column_letter = chr(64 + col_idx)
            sheet.column_dimensions[column_letter].width = adjusted_width

        # Add data from DataFrame to worksheet and apply text wrapping
        for row in dataframe_to_rows(df.reset_index(), index=False, header=False):
            sheet.append(row)

        # Apply text wrapping to all cells
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = wrap_alignment
                cell.border = thin_border

        # Save workbook to file
        workbook.save(f_path)

    def delete_file_after_delay(self, f_path):
        try:
            delay = 120
            time.sleep(delay)
            if os.path.exists(f_path):
                os.remove(f_path)
                logger.info(f"File deleted after {delay} seconds: {f_path}")
            else:
                logger.warning("File not found: " + f_path)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Deleting file: {f_path}Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
