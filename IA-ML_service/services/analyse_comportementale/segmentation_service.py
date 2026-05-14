def segment_score(score: float) -> str:
    if score >= 60:
        return "HOT"
    if score >= 35:
        return "WARM"
    return "COLD"
