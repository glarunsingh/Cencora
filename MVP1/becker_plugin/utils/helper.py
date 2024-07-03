"""
Module for helper functions
"""
import logging
import os.path
import sys
import time
import datetime
import calendar
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Border, Side

import pandas as pd

from utils.logs import create_log

logger = create_log(name="Becker_Hospital", level=logging.INFO)

class helper:
    def __init__(self) -> None:
        pass

    def file_name(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        name = "BeckerHospital_" + timestamp + '.xlsx'
        return name


    def file_path(self):
        temp_dir = './temp'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        name = self.file_name()
        path = os.path.join(temp_dir, name)
        return path, name


    def convert_utc_date(self,date_str):
        dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
        date_obj = datetime.datetime.strptime(date_str, dateformat)
        formatted_date = date_obj.strftime("%A, %B %d, %Y")
        return formatted_date


    def create_dataframe(self,data):
        df = pd.DataFrame(data)
        df['news_date'] = df['news_date'].apply(self.convert_utc_date)
        df = df.rename(columns={'news_date': 'Date', "news_title": "Title", "news_url": "URL", 
                                "news_summary": "Summary",
                                "client_name":"Client",
                                "sentiment": "Sentiment"})
        df.index += 1
        return df


    def create_excel(self,df, f_path):
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
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) if col not in ['Sr NO.', 'Sentiment'] else len(
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


    def delete_file_after_delay(self,f_path):
        try:
            delay=120
            time.sleep(delay)
            if os.path.exists(f_path):
                os.remove(f_path)
                logger.info(f"File deleted after {delay} seconds: {f_path}")
            else:
                logger.warning("File not found: " + f_path)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Deleting file: {f_path}Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)


    def start_end_date(self,date):
        """
        function to return start date and end date from the input date which is of format YYYY-MM
        """
        try:
            dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
            # Split the date into year and month
            year, month = map(int, date.split('-'))

            # Start date is always the first day of the month
            start_date = datetime.datetime(year, month, 1)

            # Use calendar.monthrange() to get the number of days in the month
            _, num_days = calendar.monthrange(year, month)

            # End date is the last day of the month
            end_date = datetime.datetime(year, month, num_days)
            start_date = start_date.strftime(dateformat)
            end_date = end_date.strftime(dateformat)

            return start_date,end_date
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in converting dates. Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)

    def deduplicate_dicts(self,dict_list, keyword):
        seen = set()
        deduplicated_list = [d for d in dict_list if not (d[keyword] in seen or seen.add(d[keyword]))]
        return deduplicated_list
