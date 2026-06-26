import json
from rdflib import Graph


SUPPORTED_FORMATS = {
    ".owl": "xml",
    ".rdf": "xml",
    ".xml": "xml",
    ".ttl": "turtle",
    ".n3": "n3",
    ".nt": "nt",
    ".jsonld": "json-ld",
    ".json": "json-ld",
}


def detect_format(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    return SUPPORTED_FORMATS.get(ext, None)


def to_rdf_xml(file_bytes: bytes, filename: str) -> str:
    """
    다양한 포맷의 온톨로지를 RDF/XML 문자열로 변환
    지원: .owl, .rdf, .xml, .ttl, .n3, .nt, .jsonld, .json
    """
    fmt = detect_format(filename)
    if fmt is None:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {filename}")

    g = Graph()

    # JSON-LD인데 일반 JSON dict 형태(python 온톨로지 출력)일 경우 처리
    if fmt == "json-ld":
        try:
            g.parse(data=file_bytes.decode("utf-8"), format="json-ld")
        except Exception:
            # json-ld 파싱 실패시 일반 json을 json-ld로 감싸서 재시도
            raw = json.loads(file_bytes.decode("utf-8"))
            if "@context" not in raw:
                raw["@context"] = {"@vocab": "http://example.org/ontology#"}
            g.parse(data=json.dumps(raw), format="json-ld")
    else:
        g.parse(data=file_bytes.decode("utf-8"), format=fmt)

    return g.serialize(format="xml")


def build_oops_request(rdf_xml: str) -> str:
    """RDF/XML을 OOPS! REST API 요청 XML로 래핑"""
    # XML 특수문자 이스케이프
    escaped = (
        rdf_xml
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OOPSRequest>
  <OntologyUrl></OntologyUrl>
  <OntologyContent>{escaped}</OntologyContent>
  <Pitfalls></Pitfalls>
</OOPSRequest>"""
