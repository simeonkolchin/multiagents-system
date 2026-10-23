from app.services.transcript import format_episodes, parse_transcript


def test_parses_all_episodes(episodes):
    assert len(episodes) == 11
    assert episodes[0].speaker == "interviewer"
    assert episodes[1].speaker == "candidate"
    assert episodes[0].t == "00:30"


def test_roles_detected(episodes):
    candidate_lines = [e for e in episodes if e.speaker == "candidate"]
    interviewer_lines = [e for e in episodes if e.speaker == "interviewer"]
    assert len(candidate_lines) == 6
    assert len(interviewer_lines) == 5


def test_roundtrip_format_parse(episodes):
    text = format_episodes(episodes)
    reparsed = parse_transcript(text)
    assert len(reparsed) == len(episodes)
    assert reparsed[1].speaker == "candidate"
