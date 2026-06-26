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
    fmt = detect_format(filename)
    if fmt is None:
        raise ValueError(f"지원하지 않는 파일 형식: {filename}")

    g = Graph()
    if fmt == "json-ld":
        try:
            g.parse(data=file_bytes.decode("utf-8"), format="json-ld")
        except Exception:
            raw = json.loads(file_bytes.decode("utf-8"))
            if "@context" not in raw:
                raw["@context"] = {"@vocab": "http://example.org/ontology#"}
            g.parse(data=json.dumps(raw), format="json-ld")
    else:
        g.parse(data=file_bytes.decode("utf-8"), format=fmt)

    return g.serialize(format="xml")


def build_oops_request(rdf_xml: str) -> bytes:
    """CDATA로 감싸서 이스케이프 없이 전송"""
    xml_str = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<OOPSRequest>\n'
        '  <OntologyUrl></OntologyUrl>\n'
        '  <OntologyContent><![CDATA[\n'
        + rdf_xml +
        '\n  ]]></OntologyContent>\n'
        '  <Pitfalls></Pitfalls>\n'
        '</OOPSRequest>'
    )
    return xml_str.encode("utf-8")
