import os
import re
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from presidio_analyzer import AnalyzerEngine, RecognizerResult, EntityRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine, AnonymizerConfig


def normalize_stt_text(text: str) -> str:
    """
    Normalize common speech-to-text (ASR) artifacts to improve NER recall:
      - Convert verbally spoken email separators: " at " -> "@", " dot " -> "."
      - Normalize hyphen/dash/underscore words to symbols
      - Collapse whitespace
      - Keep original text separate for storage.
    """
    if not text:
        return text

    t = text
    # Pad with spaces to make replacements reliably on word boundaries
    t = f" {t} "

    replacements = [
        (r"\s+at\s+", "@"),
        (r"\s+dot\s+", "."),
        (r"\s+underscore\s+", "_"),
        (r"\s+dash\s+", "-"),
        (r"\s+hyphen\s+", "-"),
        (r"\s+plus\s+", "+"),
        (r"\s+minus\s+", "-"),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    # Remove filler words that often break NER context (optional, conservative)
    fillers = [r"\buh\b", r"\bum\b", r"\berm\b"]
    for f in fillers:
        t = re.sub(fr"\s*{f}\s*", " ", t, flags=re.IGNORECASE)

    # Collapse spaces and trim
    t = re.sub(r"\s+", " ", t).strip()
    return t


class FirstNameGazetteerRecognizer(EntityRecognizer):
    """
    Lightweight gazetteer-based recognizer to improve first-name and simple full-name recall
    in noisy ASR output where capitalization/punctuation may be degraded.

    This recognizer complements spaCy PERSON by:
      - Matching single tokens that are common first names
      - Matching simple bigrams of names (e.g., "john smith")
      - Matching context patterns ("my name is john", "i am sarah", "this is mike")
    """

    def __init__(self, first_names: Optional[List[str]] = None):
        super().__init__(supported_entities=["PERSON"], supported_language="en")
        fallback = [
            # small, illustrative list; extend via external file for production
            "john", "michael", "mike", "sarah", "sara", "david", "jennifer", "jenny", "emily",
            "james", "robert", "linda", "barbara", "william", "elizabeth", "joseph", "patricia",
            "thomas", "josh", "alex", "alexander", "alexandra", "chris", "christopher", "christine",
            "andrew", "anna", "daniel", "dan", "mark", "matt", "matthew", "laura", "lauren", "rachel",
            "steven", "steve", "jon", "jonathan", "natalie", "sam", "samantha", "tyler", "amy", "olivia",
        ]
        names = first_names or fallback
        self.first_names = {n.lower(): True for n in names}

        # context patterns to capture names following intros
        self._ctx_patterns = [
            re.compile(r"\b(?:my name is|i am|i'm|this is|it is|it's)\s+([A-Za-z][A-Za-z\-']{1,})(?:\s+([A-Za-z][A-Za-z\-']{1,}))?\b", re.IGNORECASE),
        ]

    def load_external_names(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    self.first_names[name.lower()] = True

    def analyze(  # type: ignore[override]
        self, text: str, entities: List[str], nlp_artifacts=None
    ) -> List[RecognizerResult]:
        if not text or "PERSON" not in entities:
            return []
        results: List[RecognizerResult] = []

        # 1) Context-introduced names
        for rx in self._ctx_patterns:
            for m in rx.finditer(text):
                start1, end1 = m.start(1), m.end(1)
                score = 0.75 if m.group(2) is None else 0.85
                results.append(RecognizerResult(entity_type="PERSON", start=start1, end=end1, score=score))
                if m.group(2):
                    start2, end2 = m.start(2), m.end(2)
                    results.append(RecognizerResult(entity_type="PERSON", start=start2, end=end2, score=0.85))

        # 2) Gazetteer single-token names + simple bigrams
        tokens: List[Tuple[str, int, int]] = [
            (m.group(0), m.start(), m.end()) for m in re.finditer(r"[A-Za-z][A-Za-z\-']+", text)
        ]
        for i, (tok, s, e) in enumerate(tokens):
            if tok.lower() in self.first_names:
                # modest score to let spaCy override if confident
                results.append(RecognizerResult(entity_type="PERSON", start=s, end=e, score=0.60))
                # try bigram with next token if it looks like a surname-ish token
                if i + 1 < len(tokens):
                    ntok, ns, ne = tokens[i + 1]
                    # basic heuristic to avoid joining with short/stop tokens
                    if len(ntok) >= 2 and ntok.isalpha():
                        # cover common lower/upper cases in ASR
                        results.append(RecognizerResult(entity_type="PERSON", start=s, end=ne, score=0.70))

        return results


@dataclass
class SanitizationResult:
    anonymized_text: str
    entities_found: List[Dict[str, Any]]
    entity_counts: Dict[str, int]
    mode: str
    hipaa_mode: bool
    normalized_text: str


class EnhancedPIISanitizer:
    DEFAULT_ENTITIES = [
        "PERSON",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "LOCATION",
        "IP_ADDRESS",
        "CREDIT_CARD",
        "IBAN_CODE",
        "US_SSN",
        "DATE_TIME",
        "NRP",
        "ORGANIZATION",
        "URL",
        "DOMAIN_NAME",
    ]

    HIPAA_SAFE_HARBOR_ENTITIES = [
        "PERSON",
        "LOCATION",
        "DATE_TIME",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "IP_ADDRESS",
        "URL",
        "DOMAIN_NAME",
        "US_SSN",
        "CREDIT_CARD",
        "NRP",
        "ORGANIZATION",
    ]

    def __init__(
        self,
        language: str = "en",
        entities: Optional[List[str]] = None,
        mode: str = "mask",
        mask_char: str = "*",
        hipaa_mode: bool = True,
        encrypt_key: Optional[str] = None,
    ) -> None:
        self.language = language
        self.entities = entities if entities else (self.HIPAA_SAFE_HARBOR_ENTITIES if hipaa_mode else self.DEFAULT_ENTITIES)
        self.mode = mode
        self.hipaa_mode = hipaa_mode

        # Build NLP engine (spaCy) and analyzer
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": "en_core_web_lg"}],
        })
        nlp_engine = provider.create_engine()
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

        # Add custom name recognizer to improve PERSON recall
        first_names_file = os.getenv("PII_FIRST_NAMES_FILE")  # optional large list, one name per line
        gaz = FirstNameGazetteerRecognizer()
        if first_names_file:
            gaz.load_external_names(first_names_file)
        self.analyzer.registry.add_recognizer(gaz)

        # Anonymizer
        self.anonymizer = AnonymizerEngine()
        self.anonymizers_config: Dict[str, AnonymizerConfig] = {}
        if mode == "mask":
            base = AnonymizerConfig("mask", {"masking_char": mask_char, "chars_to_mask": 1000, "from_end": False})
        elif mode == "redact":
            base = AnonymizerConfig("redact", {})
        elif mode == "hash":
            base = AnonymizerConfig("hash", {"hash_type": "sha256"})
        elif mode == "encrypt":
            key = encrypt_key or os.getenv("PII_FERNET_KEY")
            if not key:
                # fall back to hash if not configured
                base = AnonymizerConfig("hash", {"hash_type": "sha256"})
            else:
                base = AnonymizerConfig("encrypt", {"key": key})
        else:
            base = AnonymizerConfig("mask", {"masking_char": mask_char, "chars_to_mask": 1000, "from_end": False})

        self.anonymizers_config["DEFAULT"] = base
        for et in self.entities:
            self.anonymizers_config[et] = base

    def analyze(self, text: str) -> List[RecognizerResult]:
        if not text:
            return []
        normalized = normalize_stt_text(text)
        return self.analyzer.analyze(text=normalized, entities=self.entities, language=self.language)

    def anonymize(self, text: str, results: Optional[List[RecognizerResult]] = None) -> Tuple[str, str]:
        """
        Returns (anonymized_text, normalized_text_used)
        """
        normalized = normalize_stt_text(text)
        results = results if results is not None else self.analyzer.analyze(
            text=normalized, entities=self.entities, language=self.language
        )
        out = self.anonymizer.anonymize(
            text=normalized,
            analyzer_results=results,
            anonymizers_config=self.anonymizers_config,
        ).text
        return out, normalized

    def sanitize_text(self, text: str) -> SanitizationResult:
        results = self.analyze(text)
        anonymized, normalized = self.anonymize(text, results)
        entities_found = [
            {"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
            for r in results
        ]
        counts: Dict[str, int] = {}
        for r in results:
            counts[r.entity_type] = counts.get(r.entity_type, 0) + 1

        return SanitizationResult(
            anonymized_text=anonymized,
            entities_found=entities_found,
            entity_counts=counts,
            mode=self.mode,
            hipaa_mode=self.hipaa_mode,
            normalized_text=normalized,
        )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Enhanced NER-based PII sanitization for ASR transcripts")
    parser.add_argument("--mode", choices=["mask", "redact", "hash", "encrypt"], default="mask")
    parser.add_argument("--hipaa", action="store_true")
    parser.add_argument("--json", action="store_true", help="treat stdin as JSON string value under key 'text'")
    args = parser.parse_args()

    sanitizer = EnhancedPIISanitizer(mode=args.mode, hipaa_mode=args.hipaa)

    data = sys.stdin.read()
    if args.json:
        try:
            payload = json.loads(data)
            text = payload.get("text", "")
        except Exception:
            print("{}", end="")
            sys.exit(0)
    else:
        text = data

    res = sanitizer.sanitize_text(text)
    print(json.dumps({
        "anonymized_text": res.anonymized_text,
        "entity_counts": res.entity_counts,
        "mode": res.mode,
        "hipaa_mode": res.hipaa_mode,
        "normalized_text": res.normalized_text,
    }, ensure_ascii=False))
