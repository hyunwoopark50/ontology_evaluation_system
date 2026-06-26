import os
import re
import requests
from flask import Flask, render_template, request, jsonify
from app.utils.converter import to_rdf_xml, build_oops_request, detect_format

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

OOPS_URL = os.environ.get("OOPS_URL", "http://oops:8080/oops/rest")


def parse_oops_response(rdf_text: str) -> list[dict]:
    """OOPS! RDF Turtle 응답을 파싱해서 pitfall 리스트로 변환"""
    pitfalls = []
    blocks = re.split(r"\n\s*\n", rdf_text.strip())
    for block in blocks:
        if "oops:pitfall" not in block:
            continue
        p = {}
        for line in block.splitlines():
            line = line.strip().rstrip(";.")
            if "oops:hasCode" in line:
                m = re.search(r'"(.+?)"', line)
                if m:
                    p["code"] = m.group(1)
            elif "oops:hasName" in line:
                m = re.search(r'"(.+?)"', line)
                if m:
                    p["name"] = m.group(1)
            elif "oops:hasDescription" in line:
                m = re.search(r'"(.+?)"', line)
                if m:
                    p["description"] = m.group(1)
            elif "oops:hasImportanceLevel" in line:
                m = re.search(r'"(.+?)"', line)
                if m:
                    p["importance"] = m.group(1)
            elif "oops:hasNumberAffectedElements" in line:
                m = re.search(r"(\d+)", line)
                if m:
                    p["affected"] = int(m.group(1))
        if p.get("code"):
            pitfalls.append(p)

    # 중요도 순 정렬
    order = {"CRITICAL": 0, "IMPORTANT": 1, "MINOR": 2}
    pitfalls.sort(key=lambda x: order.get(x.get("importance", "MINOR"), 2))
    return pitfalls


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/evaluate", methods=["POST"])
def evaluate():
    onto_file = request.files.get("ontology")
    pdf_file = request.files.get("pdf")

    if not onto_file:
        return jsonify({"error": "온톨로지 파일이 필요합니다."}), 400

    filename = onto_file.filename
    fmt = detect_format(filename)
    if fmt is None:
        return jsonify({"error": f"지원하지 않는 파일 형식: {filename}"}), 400

    # 1. RDF/XML 변환
    try:
        rdf_xml = to_rdf_xml(onto_file.read(), filename)
    except Exception as e:
        return jsonify({"error": f"온톨로지 변환 실패: {str(e)}"}), 400

    # 2. OOPS! 호출
    oops_result = {"pitfalls": [], "error": None, "raw": ""}
    try:
        oops_req = build_oops_request(rdf_xml)
        resp = requests.post(
            OOPS_URL,
            data=oops_req.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
            timeout=60,
        )
        if resp.ok and "oops:pitfall" in resp.text:
            oops_result["pitfalls"] = parse_oops_response(resp.text)
            oops_result["raw"] = resp.text
        else:
            oops_result["error"] = f"OOPS! 응답 오류 (HTTP {resp.status_code})"
            oops_result["raw"] = resp.text
    except requests.exceptions.ConnectionError:
        oops_result["error"] = "OOPS! 서버에 연결할 수 없습니다."
    except Exception as e:
        oops_result["error"] = f"OOPS! 호출 실패: {str(e)}"

    # 3. 통계
    pitfalls = oops_result["pitfalls"]
    stats = {
        "total": len(pitfalls),
        "critical": sum(1 for p in pitfalls if p.get("importance") == "CRITICAL"),
        "important": sum(1 for p in pitfalls if p.get("importance") == "IMPORTANT"),
        "minor": sum(1 for p in pitfalls if p.get("importance") == "MINOR"),
    }

    return jsonify({
        "filename": filename,
        "format": fmt,
        "stats": stats,
        "pitfalls": pitfalls,
        "oops_error": oops_result["error"],
        "pdf_uploaded": pdf_file is not None and pdf_file.filename != "",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
