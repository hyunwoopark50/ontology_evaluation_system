import os
import requests
from flask import Flask, render_template, request, jsonify
from app.utils.converter import to_rdf_xml, build_oops_request, detect_format
from app.pitfall_catalog import PITFALL_CATALOG

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

OOPS_URL = os.environ.get("OOPS_URL", "http://oops:8080/oops/rest")


def parse_oops_json(data: dict) -> list[dict]:
    pitfalls = []
    for code_key, elements in data.get("pitfalls", {}).items():
        if not elements:
            continue
        first = elements[0]
        info = first.get("info", {})
        importance = info.get("importance", "MINOR")
        title_en = info.get("title", code_key)
        desc_en = info.get("description", "")
        affected_elements = [r.get("uri", "") for e in elements for r in e.get("resources", []) if r.get("uri")]

        catalog = PITFALL_CATALOG.get(code_key, {})

        pitfalls.append({
            "code":              code_key,
            "name_en":           title_en,
            "name_ko":           catalog.get("title", title_en),
            "description_en":    desc_en,
            "description_ko":    catalog.get("description", desc_en),
            "fix":               catalog.get("fix", ""),
            "importance":        importance,
            "affected":          len(elements),
            "affected_elements": affected_elements[:8],
        })

    order = {"CRITICAL": 0, "IMPORTANT": 1, "MINOR": 2}
    pitfalls.sort(key=lambda x: order.get(x["importance"], 2))
    return pitfalls


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/evaluate", methods=["POST"])
def evaluate():
    onto_file = request.files.get("ontology")
    pdf_file  = request.files.get("pdf")

    if not onto_file:
        return jsonify({"error": "온톨로지 파일이 필요합니다."}), 400

    filename = onto_file.filename
    fmt = detect_format(filename)
    if fmt is None:
        return jsonify({"error": f"지원하지 않는 파일 형식: {filename}"}), 400

    try:
        rdf_xml = to_rdf_xml(onto_file.read(), filename)
    except Exception as e:
        return jsonify({"error": f"온톨로지 변환 실패: {str(e)}"}), 400

    oops_error = None
    pitfalls   = []
    try:
        oops_req = build_oops_request(rdf_xml)
        resp = requests.post(
            OOPS_URL,
            data=oops_req,
            headers={"Content-Type": "application/xml"},
            timeout=120,
        )
        if resp.ok:
            pitfalls = parse_oops_json(resp.json())
        else:
            oops_error = f"OOPS! HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        oops_error = "OOPS! 서버에 연결할 수 없습니다."
    except Exception as e:
        oops_error = f"OOPS! 오류: {str(e)}"

    stats = {
        "total":     len(pitfalls),
        "critical":  sum(1 for p in pitfalls if p["importance"] == "CRITICAL"),
        "important": sum(1 for p in pitfalls if p["importance"] == "IMPORTANT"),
        "minor":     sum(1 for p in pitfalls if p["importance"] == "MINOR"),
    }

    return jsonify({
        "filename":     filename,
        "format":       fmt,
        "stats":        stats,
        "pitfalls":     pitfalls,
        "oops_error":   oops_error,
        "pdf_uploaded": pdf_file is not None and pdf_file.filename != "",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
