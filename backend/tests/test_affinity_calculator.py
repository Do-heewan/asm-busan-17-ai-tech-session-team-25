from app.services.affinity_calculator import compute_delta, _keyword_score

# ---------------------------------------------------------------------------
# 감정 가중치 변경 확인
# ---------------------------------------------------------------------------

def test_smile_weight_is_2():
    """smile 가중치가 2여야 한다 (기존 3에서 변경)."""
    assert compute_delta("", "smile") == 2


def test_surprise_weight_is_1():
    """surprise 가중치가 1이어야 한다 (기존 2에서 변경)."""
    assert compute_delta("", "surprise") == 1


def test_idle_weight_unchanged():
    """idle 가중치는 0 유지."""
    assert compute_delta("", "idle") == 0


def test_sad_weight_unchanged():
    """sad 가중치는 -3 유지."""
    assert compute_delta("", "sad") == -3


# ---------------------------------------------------------------------------
# 신규 부정 키워드 확인
# ---------------------------------------------------------------------------

def test_keyword_molla():
    """'몰라' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("몰라") == -3


def test_keyword_amuguna():
    """'아무거나' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("아무거나") == -3


def test_keyword_sangkwan_eopseo():
    """'상관없어' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("상관없어") == -3


def test_keyword_dwaesseo():
    """'됐어' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("됐어") == -3


def test_keyword_bbaejwo():
    """'빼줘' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("빼줘") == -3


def test_keyword_pass():
    """'패스' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("패스") == -3


def test_keyword_pigonhae():
    """'피곤해' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("피곤해") == -3


def test_keyword_jollyeo():
    """'졸려' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("졸려") == -3


# ---------------------------------------------------------------------------
# 복합: 긍정 키워드 + smile 감정
# ---------------------------------------------------------------------------

def test_positive_keyword_with_smile():
    """'좋아 고마워' + smile: 키워드(+4 cap) + emotion(+2) = 6."""
    assert compute_delta("좋아 고마워", "smile") == 6


# ---------------------------------------------------------------------------
# 복합: 부정 키워드 + idle 감정
# ---------------------------------------------------------------------------

def test_negative_keyword_molla_with_idle():
    """'몰라' + idle: 키워드(-3) + emotion(0) = -3."""
    assert compute_delta("몰라", "idle") == -3


# ---------------------------------------------------------------------------
# system_prompts OUTPUT_FORMAT 감정 정의 확인
# ---------------------------------------------------------------------------
from app.prompts.system_prompts import OUTPUT_FORMAT

def test_output_format_idle_is_default():
    """OUTPUT_FORMAT에 idle이 기본값임이 명시되어야 한다."""
    assert "기본값" in OUTPUT_FORMAT


def test_output_format_surprise_excludes_excitement():
    """OUTPUT_FORMAT에서 surprise가 설렘을 포함하지 않아야 한다."""
    assert "설렘" not in OUTPUT_FORMAT


def test_output_format_sad_includes_disengagement_cue():
    """OUTPUT_FORMAT에서 sad가 무관심 반응에 대한 안내를 포함해야 한다."""
    assert "무관심" in OUTPUT_FORMAT
