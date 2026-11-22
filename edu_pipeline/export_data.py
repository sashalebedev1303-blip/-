# Экспорт агрегатов в JSON и XML + безопасный разбор внешнего ответа (Этап 5)
# Агрегаты берутся из edu.db через queries.py (Этап 4); оба файла читаются
# обратно и сверяются. Внешний ответ проверяется ДО json.loads.
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from create_db import connect, DB_PATH
import queries

RESULTS = Path(__file__).with_name("results")
REPORT_JSON = RESULTS / "report.json"
REPORT_XML = RESULTS / "report.xml"
EXTERNAL_HTML = Path(__file__).with_name("data") / "final" / "api_response_error.html"

# Обязательные поля внешнего ответа (сценарий "отсутствует обязательное поле")
REQUIRED_EXTERNAL = {"course_code", "cnt"}


def build_report(con):
    """Собирает внутреннюю структуру отчёта из аналитических запросов."""
    return {
        "by_status": queries.status_counts(con),
        "by_course": queries.course_counts(con),
        "by_avg_duration": queries.avg_duration_by_course(con),
        "by_revenue": queries.revenue_by_course(con),
    }


def export_json(report, path):
    """Пишет отчёт в JSON: кириллица без экранирования, отступы для человека."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def export_xml(report, path):
    """Пишет тот же отчёт в XML: разделы, внутри них строки <row>."""
    root = ET.Element("report")
    for section, rows in report.items():
        node = ET.SubElement(root, section)
        for item in rows:
            row_el = ET.SubElement(node, "row")
            for key, value in item.items():
                ET.SubElement(row_el, key).text = str(value)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def read_json(path):
    """Читает report.json обратно во внутреннюю структуру."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_xml(path):
    """Читает report.xml обратно во внутреннюю структуру (значения - строки)."""
    root = ET.parse(path).getroot()
    report = {}
    for section in root:
        report[section.tag] = [{c.tag: c.text for c in row} for row in section.findall("row")]
    return report


def same_structure(json_report, xml_report):
    """Сверяет обе выгрузки: разделы, число строк и значения после приведения типов."""
    if set(json_report) != set(xml_report):
        return False
    for section, rows in json_report.items():
        xml_rows = xml_report[section]
        if len(rows) != len(xml_rows):
            return False
        for a, b in zip(rows, xml_rows):
            for key, value in a.items():
                if str(value) != b[key]:
                    return False
    return True


def safe_parse_external(text, required=REQUIRED_EXTERNAL):
    """Разбирает внешний ответ, проверяя его ДО json.loads.

    Возвращает {"data": ...} или {"error": код, ...детали}. Пустой ответ,
    не-JSON и отсутствующие обязательные поля не приводят к исключению.
    """
    if not text or not text.strip():
        return {"error": "empty_response"}
    s = text.lstrip()
    if not (s.startswith("{") or s.startswith("[")):
        return {"error": "not_json", "preview": text.strip()[:80]}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": "invalid_json", "detail": str(e)}
    if not isinstance(data, dict):
        return {"error": "not_dict", "detail": f"получен {type(data).__name__}"}
    missing = sorted(set(required) - set(data))
    if missing:
        return {"error": "missing_fields", "detail": ",".join(missing)}
    return {"data": data}


def main():
    """Экспортирует агрегаты, сверяет выгрузки, демонстрирует разбор внешних ответов."""
    con = connect(DB_PATH)
    try:
        report = build_report(con)
    finally:
        con.close()

    export_json(report, REPORT_JSON)
    export_xml(report, REPORT_XML)

    back_json = read_json(REPORT_JSON)
    back_xml = read_xml(REPORT_XML)
    total_rows = sum(len(rows) for rows in report.values())
    print("internal:", total_rows)
    print("json back:", sum(len(r) for r in back_json.values()))
    print("xml  back:", sum(len(r) for r in back_xml.values()))
    print("структуры совпадают:", same_structure(back_json, back_xml))

    html = EXTERNAL_HTML.read_text(encoding="utf-8-sig")
    print("html  →", safe_parse_external(html))
    print("empty →", safe_parse_external(""))
    print("valid →", safe_parse_external('{"course_code": "PY-100", "cnt": 4}'))
    print("bad   →", safe_parse_external('{"course_code": '))
    print("field →", safe_parse_external('{"course_code": "PY-100"}'))


if __name__ == "__main__":
    main()
