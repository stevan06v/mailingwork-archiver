import asyncio
import requests
from libs.data_refiner import read_json, refine_data, sort_by_date
from libs.downloader import process_entries, generate_index

if __name__ == "__main__":
   try:
      data = read_json()
      refined_data = refine_data(data)
      sorted_data = sort_by_date(refined_data)

      processed_entries = process_entries(sorted_data)
      generate_index(processed_entries)

   except Exception as e:
      print(e)