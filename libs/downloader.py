import os
import re
import requests
import concurrent.futures
from datetime import datetime
from collections import defaultdict


BASE_FOLDER = "mailingwork"
PAGES_FOLDER = os.path.join(BASE_FOLDER, "pages")
INDEX_FILENAME = "index.html"
DATE_FORMAT = "%d.%m.%Y"
MAX_WORKERS = 5


def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip().replace(" ", "_")


def download_file(url, dest_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {url} -> {dest_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")


def download_tasks(task_list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_file, url, dest): (url, dest) for url, dest in task_list}
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                url, dest = futures[future]
                print(f"Error downloading {url} to {dest}: {e}")


def process_entries(data):
    processed = []
    os.makedirs(PAGES_FOLDER, exist_ok=True)

    download_list = []

    for entry in data:
        if isinstance(entry.get("date"), str):
            try:
                entry["date"] = datetime.strptime(entry["date"], DATE_FORMAT)
            except ValueError as e:
                print(f"Error parsing date {entry['date']}: {e}")
                continue

        date_str = entry["date"].strftime("%Y-%m-%d")
        folder_name = sanitize_filename(f"{date_str}_{entry['name']}")
        entry_folder = os.path.join(PAGES_FOLDER, folder_name)
        os.makedirs(entry_folder, exist_ok=True)

        html_url = entry.get("html_link")
        if html_url:
            local_html_filename = "entry.html"
            local_html_path = os.path.join(entry_folder, local_html_filename)
            download_list.append((html_url, local_html_path))
        else:
            local_html_path = ""

        local_image_mappings = {}
        images = entry.get("images", [])
        for img_url in images:
            parsed = requests.utils.urlparse(img_url)
            local_img_path = parsed.path
            full_local_path = os.path.join(entry_folder, local_img_path.lstrip("/"))
            download_list.append((img_url, full_local_path))
            relative_path = "." + local_img_path
            local_image_mappings[img_url] = relative_path

        pdf_url = entry.get("pdf_link")
        local_pdf_path = ""
        if pdf_url:
            parsed_pdf = requests.utils.urlparse(pdf_url)
            pdf_filename = os.path.basename(parsed_pdf.path)
            local_pdf_path = os.path.join(entry_folder, pdf_filename)
            download_list.append((pdf_url, local_pdf_path))

        processed.append({
            "date": entry["date"],
            "name": entry["name"],
            "html_url": html_url,
            "html_path": os.path.relpath(os.path.join(entry_folder, "entry.html"), BASE_FOLDER),
            "pdf_path": os.path.relpath(local_pdf_path, BASE_FOLDER) if local_pdf_path else "",
            "entry_folder": entry_folder,
            "local_image_mappings": local_image_mappings,
        })

    download_tasks(download_list)

    for entry in processed:
        html_file = os.path.join(BASE_FOLDER, entry["html_path"])
        if os.path.exists(html_file):
            try:
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                for orig_url, rel_path in entry["local_image_mappings"].items():
                    html_content = html_content.replace(orig_url, rel_path)
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"Updated HTML links in {html_file}")
            except Exception as e:
                print(f"Error updating HTML for {html_file}: {e}")

    return processed


def generate_index(entries):
    grouped = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        year = entry["date"].year
        month = entry["date"].strftime("%B")
        grouped[year][month].append(entry)

    sorted_years = sorted(grouped.keys(), reverse=True)

    html_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>Mailingwork Archive</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px; }",
        "h1 { text-align: center; }",
        "table { width: 100%; border-collapse: collapse; margin: 20px 0; }",
        "th, td { padding: 8px 12px; border: 1px solid #ddd; }",
        "tr:nth-child(even) { background-color: #f2f2f2; }",
        "tr.header { background-color: #4CAF50; color: white; }",
        "a { color: #1a73e8; text-decoration: none; }",
        "a:hover { text-decoration: underline; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Mailingwork Archive</h1>",
        "<table>",
    ]

    for year in sorted_years:
        html_lines.append(
            f"<tr class='header'><td colspan='3'><strong style='color:#000000; font-size:14px'>{year}</strong></td></tr>")
        months = list(grouped[year].keys())
        months.sort(key=lambda m: datetime.strptime(m, "%B").month)
        for month in months:
            html_lines.append(f"<tr><td colspan='3'><strong style='font-size:13px;'>{month}</strong></td></tr>")
            month_entries = sorted(grouped[year][month], key=lambda x: x["date"], reverse=True)
            for item in month_entries:
                date_str = item["date"].strftime("%d.%m.%Y")
                html_file_link = item["html_path"]
                pdf_file_link = item["pdf_path"]
                row = (
                    f"<tr>"
                    f"<td style='font-size:10px' width='70' align='center'>{date_str}</td>"
                    f"<td><strong>{item['name']}</strong></td>"
                    f"<td style='font-size:10px' width='75' align='center'>"
                    f"<a href='{html_file_link}' target='_blank'>anzeigen</a>"
                )
                if pdf_file_link:
                    row += f" | <a href='{pdf_file_link}' target='_blank'>PDF</a>"
                row += "</td></tr>"
                html_lines.append(row)

    html_lines.extend(["</table>", "</body>", "</html>"])
    index_path = os.path.join(BASE_FOLDER, INDEX_FILENAME)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))
    print(f"Index generated at: {index_path}")


if __name__ == "__main__":
    data = [
        {"date": "24.02.2014", "name": "Karl Pilsl: Ermutigung und Termine - KW9/2014",
         "html_link": "https://login.mailingwork.de/-ea-show/3886/1019/VSCv7dKKS5/html",
         "pdf_link": "https://login.mailingwork.de/-ea-show/3886/1019/VSCv7dKKS5/pdf"},
        {"date": "17.02.2014", "name": "Karl Pilsl: Ermutigung und Termine - KW8/2014",
         "html_link": "https://login.mailingwork.de/-ea-show/3886/1017/RXL0P342Xv/html",
         "pdf_link": "https://login.mailingwork.de/-ea-show/3886/1017/RXL0P342Xv/pdf"},
        {"date": "10.02.2014", "name": "Karl Pilsl: Ermutigung und Termine - KW7/2014",
         "html_link": "https://login.mailingwork.de/-ea-show/3886/1015/hClyhjZnQn/html",
         "pdf_link": "https://login.mailingwork.de/-ea-show/3886/1015/hClyhjZnQn/pdf"},
        {"date": "12.04.2024", "name": "Mit einem starken Gott-Vertrauen mutig in die Zukunft - 1.294",
         "html_link": "https://login.mailingwork.de/-ea-show/3886/6939/lP3XKxqlSc/html",
         "pdf_link": "https://login.mailingwork.de/-ea-show/3886/6939/lP3XKxqlSc/pdf",
         "images": [
             "https://login.mailingwork.de/public/a_3886_P9hLk/webspace/tmpl_images/img_01.png",
             "https://login.mailingwork.de/public/a_3886_P9hLk/file/data/3133_u4ylogo999.jpg",
             "https://login.mailingwork.de/public/a_3886_P9hLk/file/data/3107_230522E-Mail_Header_Annett_EW3.png",
             "https://login.mailingwork.de/public/a_3886_P9hLk/file/data/3633_1294.jpg",
             "https://login.mailingwork.de/public/a_3886_P9hLk/file/data/3091_UmdenkAkademieLogo-600px.jpg"
         ]}
    ]

