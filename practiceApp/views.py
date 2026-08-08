import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from courseApp.models import Lesson, Exercise
from .models import PracticeSession, PracticeRecord


def _build_exercise_list(lesson):
    """构建课时内全部练习的序列化列表（各模式共用同一套数据）"""
    return [
        {
            'id': ex.id,
            'chinese': extract_chinese_field(ex.sentences),
            'pinyin': extract_pinyin_field(ex.sentences),
            'english': extract_english_field(ex.sentences),
            'question_raw': ex.sentences,
            'answer': extract_chinese_field(ex.sentences),
            'word_analysis': ex.word_analysis or [],
            'grammar_hint': ex.grammar_hint or '',
            'image_url': ex.image.url if ex.image else '',
            'audio_url': ex.audio_url or '',
        }
        for ex in lesson.exercises.all().order_by('sort_order')
    ]


def practice(request, lesson_id):
    """练习页面 - 从数据库读取真实题目"""
    lesson = get_object_or_404(Lesson.objects.select_related('chapter__course'), id=lesson_id)

    # 准备所有题目（四种模式共用同一套数据）
    all_exercises = _build_exercise_list(lesson)
    MODE_KEYS = ['typing', 'speaking', 'translate', 'listening']
    exercises_by_mode = {mode: all_exercises for mode in MODE_KEYS}

    course_obj = lesson.chapter.course
    chapters = course_obj.chapters.all()
    current_chapter_index = list(chapters).index(lesson.chapter) + 1 if lesson.chapter in chapters else 0
    total_chapters = chapters.count()
    total_lessons = sum(ch.lessons.count() for ch in chapters)
    initial_mode = request.GET.get('mode', 'listening')
    if initial_mode == 'typing':
        template_name = 'typing_mode.html'
    elif initial_mode == 'translate':
        template_name = 'translate_mode.html'
    elif initial_mode == 'speaking':
        template_name = 'speaking_mode.html'
    else:
        template_name = 'listening_mode.html'

    return render(request, template_name, {
        'lesson': lesson,
        'exercises_by_mode_json': json.dumps(exercises_by_mode, ensure_ascii=False),
        'exercises_count': sum(len(v) for v in exercises_by_mode.values()),
        'chapter': lesson.chapter,
        'course': course_obj,
        'current_chapter_index': current_chapter_index,
        'total_chapters': total_chapters,
        'total_lessons': total_lessons,
        'initial_mode': initial_mode,
        'active_menu': 'course-menu',
        'collapse_menu': 'collapse-std',
    })


def sorting_practice(request, lesson_id):
    """拆句重组练习页面"""
    lesson = get_object_or_404(Lesson.objects.select_related('chapter__course'), id=lesson_id)
    all_exercises = _build_exercise_list(lesson)
    exercises_by_mode = {'sorting': all_exercises}

    course_obj = lesson.chapter.course
    chapters = list(course_obj.chapters.all())

    return render(request, 'sorting_mode.html', {
        'lesson': lesson,
        'exercises_by_mode_json': json.dumps(exercises_by_mode, ensure_ascii=False),
        'exercises_count': len(all_exercises),
        'chapter': lesson.chapter,
        'course': course_obj,
        'current_chapter_index': chapters.index(lesson.chapter) + 1 if lesson.chapter in chapters else 0,
        'total_chapters': len(chapters),
        'total_lessons': sum(ch.lessons.count() for ch in chapters),
        'active_menu': 'course-menu',
        'collapse_menu': 'collapse-std',
    })


def writing_practice(request, lesson_id):
    """写字练习页面"""
    lesson = get_object_or_404(Lesson.objects.select_related('chapter__course'), id=lesson_id)
    all_exercises = _build_exercise_list(lesson)
    exercises_by_mode = {'writing': all_exercises}

    course_obj = lesson.chapter.course
    chapters = list(course_obj.chapters.all())

    return render(request, 'writing_mode.html', {
        'lesson': lesson,
        'exercises_by_mode_json': json.dumps(exercises_by_mode, ensure_ascii=False),
        'exercises_count': len(all_exercises),
        'chapter': lesson.chapter,
        'course': course_obj,
        'current_chapter_index': chapters.index(lesson.chapter) + 1 if lesson.chapter in chapters else 0,
        'total_chapters': len(chapters),
        'total_lessons': sum(ch.lessons.count() for ch in chapters),
        'active_menu': 'course-menu',
        'collapse_menu': 'collapse-std',
    })


def extract_chinese_field(question):
    """从题目JSON中提取中文文本"""
    try:
        q = json.loads(question)
        return q.get('chinese', q.get('text', question))
    except (json.JSONDecodeError, TypeError):
        return question


def extract_pinyin_field(question):
    """从题目JSON中提取拼音"""
    try:
        q = json.loads(question)
        return q.get('pinyin', '')
    except (json.JSONDecodeError, TypeError):
        return ''


def extract_english_field(question):
    """从题目JSON中提取英文"""
    try:
        q = json.loads(question)
        return q.get('english', q.get('translation', ''))
    except (json.JSONDecodeError, TypeError):
        return ''


@require_POST
def start_session(request):
    """开始新练习会话"""
    data = json.loads(request.body)
    lesson = get_object_or_404(Lesson, id=data.get('lesson_id'))
    mode = data.get('mode', 'typing')
    exercises = data.get('exercises', [])
    user = request.user if request.user.is_authenticated else None

    session = PracticeSession.objects.create(
        user=user,
        lesson=lesson,
        mode=mode,
        total_questions=len(exercises),
        exercise_snapshot=exercises,
    )
    return JsonResponse({'session_id': session.id, 'total_questions': session.total_questions})


@require_POST
def submit_answer(request):
    """提交单题答案"""
    data = json.loads(request.body)
    session = get_object_or_404(PracticeSession, id=data.get('session_id'))
    question_index = data.get('question_index', 0)
    user_answer = data.get('user_answer', '')
    exercises = session.exercise_snapshot if isinstance(session.exercise_snapshot, list) else []

    q_data = exercises[question_index] if question_index < len(exercises) else {}
    correct_answer = q_data.get('answer', '')
    is_correct = user_answer.strip() == correct_answer.strip()

    PracticeRecord.objects.create(
        session=session,
        question_index=question_index,
        question_data=q_data,
        user_answer=user_answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        score=100 if is_correct else 0,
    )

    if is_correct:
        session.correct_count += 1
    else:
        session.wrong_count += 1
    total_done = session.correct_count + session.wrong_count
    session.score = int(session.correct_count / max(total_done, 1) * 100) if total_done > 0 else 0
    session.save()

    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': correct_answer,
        'score': session.score,
        'total': session.total_questions,
        'correct_count': session.correct_count,
        'wrong_count': session.wrong_count,
    })


@require_GET
@csrf_exempt
def tts(request):
    """文本转语音 - 直接调用阿里云 Qwen3-TTS REST API（替代 dashscope SDK）"""
    text = request.GET.get('text', '').strip()
    voice = request.GET.get('voice', 'Cherry')
    speech_rate = float(request.GET.get('speed', '1.0'))
    volume = int(float(request.GET.get('volume', '0.8')) * 100)
    emotion = request.GET.get('emotion', '')
    speech_rate = max(0.5, min(2.0, speech_rate))
    volume = max(0, min(100, volume))
    if not text:
        return JsonResponse({'error': 'no text'}, status=400)

    try:
        import requests as http_requests
        api_key = settings.DASHSCOPE_API_KEY
        base_url = getattr(settings, 'DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/api/v1')

        model = settings.QWEN3_TTS_MODEL
        if emotion and emotion != '无':
            model = settings.QWEN3_TTS_INSTRUCT_MODEL
        payload = {
            'model': model,
            'input': {'text': text},
            'parameters': {
                'voice': voice,
                'speech_rate': speech_rate,
                'volume': volume,
            }
        }
        if emotion and emotion != '无':
            payload['parameters']['instructions'] = f'请用{emotion}的语气朗读'

        endpoint = base_url.rstrip('/') + '/services/aigc/multimodal-generation/generation'
        resp = http_requests.post(
            endpoint,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        audio_url = result['output']['audio']['url']
        audio_resp = http_requests.get(audio_url, timeout=30)
        return HttpResponse(audio_resp.content, content_type='audio/wav')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def complete_session(request):
    """完成练习会话"""
    data = json.loads(request.body)
    session = get_object_or_404(PracticeSession, id=data.get('session_id'))
    session.status = 'completed'
    session.completed_at = timezone.now()
    session.save()
    return JsonResponse({'status': 'ok', 'score': session.score})


@require_POST
@csrf_exempt
def evaluate_speech(request):
    """口语评测：录音 → 讯飞语音评测"""
    try:
        raw_body = request.body
        try:
            data = json.loads(raw_body)
        except UnicodeDecodeError:
            # 部分终端（如 Windows Git Bash 或 curl）发送 GBK 编码的 JSON
            data = json.loads(raw_body.decode('gbk'))
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的 JSON 数据'}, status=400)
    except Exception:
        return JsonResponse({'error': '无效的请求数据'}, status=400)

    audio_base64 = data.get('audio')
    ref_text = data.get('text', '')
    words = data.get('words', [])
    energy = data.get('energy', 0)
    duration = data.get('duration', 0)

    if not audio_base64 or not ref_text:
        return JsonResponse({'error': '缺少音频或参考文本'}, status=400)

    result = _try_xunfei_eval(audio_base64, ref_text, words, energy, duration)
    return JsonResponse(result)


def _try_xunfei_eval(audio_base64, ref_text, words, energy, duration):
    """口语评测：录音 -> 腾讯云智聆（SOE），含 PCM 转换"""
    import json, base64 as b64, subprocess, tempfile, os, re as _re

    # Check Tencent Cloud SOE credentials
    secret_id = getattr(settings, 'TENCENT_SOE_SECRET_ID', '')
    secret_key = getattr(settings, 'TENCENT_SOE_SECRET_KEY', '')
    soe_app_id = getattr(settings, 'TENCENT_SOE_APP_ID', '')
    soe_region = getattr(settings, 'TENCENT_SOE_REGION', 'ap-guangzhou')

    if not secret_id or not secret_key or not soe_app_id:
        result = _mock_evaluation(words, ref_text, energy, duration)
        result['error_detail'] = '\u672a\u914d\u7f6e\u817e\u8baf\u4e91\u667a\u8046 API \u51ed\u8bc1'
        return result

    try:
        # 1. webm -> 16kHz PCM (same as before)
        raw_bytes = b64.b64decode(audio_base64)
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
            f.write(raw_bytes)
            webm_path = f.name
        pcm_path = webm_path + '.pcm'
        ff = subprocess.run(
            ['ffmpeg', '-y', '-i', webm_path, '-ar', '16000', '-ac', '1',
             '-sample_fmt', 's16', '-f', 's16le', pcm_path],
            capture_output=True, timeout=30)
        if ff.returncode != 0 or not os.path.exists(pcm_path):
            try: os.unlink(webm_path)
            except: pass
            return _mock_evaluation(words, ref_text, energy, duration)
        with open(pcm_path, 'rb') as f:
            pcm_data = f.read()
        try: os.unlink(webm_path); os.unlink(pcm_path)
        except: pass

        # 2. Detect language: Chinese or English
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in ref_text)
        server_type = 1 if has_chinese else 0  # 1=Chinese, 0=English

        # 3. Call Tencent Cloud SOE (TransmitOralProcessWithInit - one-shot mode)
        from tencentcloud.common import credential as tc_cred
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.soe.v20180724 import soe_client, models
        import uuid

        cred = tc_cred.Credential(secret_id, secret_key)
        client = soe_client.SoeClient(cred, soe_region)

        req = models.TransmitOralProcessWithInitRequest()
        req.SessionId = str(uuid.uuid4())
        req.SoeAppId = soe_app_id
        req.RefText = ref_text
        req.WorkMode = 1                  # one-shot
        req.EvalMode = 0                  # word mode
        req.ScoreCoeff = 2.0              # default coefficient
        req.ServerType = server_type
        req.TextMode = 0                  # plain text
        req.VoiceFileType = 4             # PCM
        req.VoiceEncodeType = 1           # raw
        req.UserVoiceData = b64.b64encode(pcm_data).decode('ascii')
        req.SeqId = 1
        req.IsEnd = 1
        req.SentenceInfoEnabled = 1

        resp = client.TransmitOralProcessWithInit(req)

        # 4. Parse response
        total = max(0, min(100, int(round(resp.SuggestedScore or 0))))
        accuracy = max(0, min(100, int(round(resp.PronAccuracy or 0))))
        fluency = max(0, min(100, int(round(resp.PronFluency or 0))))
        completion = max(0, min(100, int(round(resp.PronCompletion or 0))))

        # Volume score from energy
        if energy < 0.005:
            _vol = max(20, int(energy * 4000 + 10))
        elif energy < 0.02:
            _vol = int(40 + energy * 1500)
        elif energy < 0.06:
            _vol = int(60 + energy * 400)
        elif energy < 0.15:
            _vol = int(75 + energy * 120)
        else:
            _vol = min(98, 88 + energy * 20)
        volume_score = max(20, min(98, _vol))

        # Word-level scores: match API results with input word_analysis
        api_words = {}
        if resp.Words:
            for w in resp.Words:
                key = w.ReferenceWord or w.Word or ''
                if key:
                    api_words[key] = {
                        'score': max(0, min(100, int(round(w.PronAccuracy or 0)))),
                        'match_tag': w.MatchTag,
                    }

        word_scores = []
        for w in words:
            wt = w.get('word', '')
            if wt in api_words:
                word_scores.append({'word': wt, 'score': api_words[wt]['score']})
            else:
                # Word not found in API response -> user didnt say it
                word_scores.append({'word': wt, 'score': 0})

        # Grade
        if total >= 90: grade = '\u4f18\u79c0'
        elif total >= 80: grade = '\u826f\u597d'
        elif total >= 70: grade = '\u4e00\u822c'
        elif total >= 60: grade = '\u8f83\u5dee'
        else: grade = '\u9700\u6539\u8fdb'

        return {
            'mock': False,
            'overall_score': total,
            'accuracy_score': accuracy,
            'fluency_score': fluency,
            'integrity_score': completion,
            'volume_score': volume_score,
            'word_scores': word_scores,
            'grade': grade,
            'dimensions': {
                'accuracy': {'label': '\u53d1\u97f3\u51c6\u786e\u5ea6', 'desc': '\u8bc4\u4f30\u53d1\u97f3\u662f\u5426\u6e05\u6670\u3001\u6807\u51c6', 'weight': '35%', 'score': accuracy},
                'fluency': {'label': '\u6d41\u5229\u5ea6', 'desc': '\u8bc4\u4f30\u8bf4\u8bdd\u7684\u8282\u594f\u662f\u5426\u81ea\u7136\u6d41\u7545', 'weight': '30%', 'score': fluency},
                'integrity': {'label': '\u5b8c\u6574\u5ea6', 'desc': '\u8bc4\u4f30\u662f\u5426\u5b8c\u6574\u6717\u8bfb\u4e86\u6240\u6709\u5185\u5bb9', 'weight': '20%', 'score': completion},
                'volume': {'label': '\u97f3\u91cf', 'desc': '\u8bc4\u4f30\u97f3\u91cf\u662f\u5426\u5145\u8db3\u3001\u7a33\u5b9a', 'weight': '15%', 'score': volume_score},
            },
        }

    except TencentCloudSDKException as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'\u667a\u8046\u8bc4\u6d4b\u5931\u8d25: {e}')
        result = _mock_evaluation(words, ref_text, energy, duration)
        result['error_detail'] = f'\u817e\u8baf\u4e91\u667a\u8046\u8bc4\u6d4b\u5931\u8d25: {str(e)[:200]}'
        return result

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'\u667a\u8046\u8bc4\u6d4b\u5f02\u5e38: {e}')
        result = _mock_evaluation(words, ref_text, energy, duration)
        result['error_detail'] = f'\u817e\u8baf\u4e91\u667a\u8046\u8bc4\u6d4b\u5931\u8d25: {str(e)[:200]}'
        return result

def _mock_evaluation(words, ref_text, energy=0, duration=0):
    """
    Backend speech evaluation using audio features (energy, duration).
    
    Scoring dimensions:
    1. accuracy_score  (35%) - pronunciation clarity based on RMS energy
    2. fluency_score   (30%) - speaking pace based on duration/char count
    3. integrity_score (20%) - completeness based on duration vs expected
    4. volume_score    (15%) - volume adequacy based on energy level
    
    Overall = accuracy*0.35 + fluency*0.30 + integrity*0.20 + volume*0.15
    """
    import re as _re, math, random
    random.seed(42)  # deterministic per session

    # Count Chinese characters in the reference text
    chinese_chars = len(_re.findall("[\u4e00-\u9fff]", ref_text))
    if not chinese_chars:
        chinese_chars = max(1, len(words))

    # === 1. ACCURACY SCORE (35%) ===
    if energy < 0.005:
        acc = max(15, energy * 3000 + 10)
    elif energy < 0.02:
        acc = 35 + energy * 1000
    elif energy < 0.06:
        acc = 60 + energy * 400
    elif energy < 0.15:
        acc = 75 + energy * 100
    else:
        acc = min(98, 85 + energy * 30)
    acc = max(15, min(98, acc))

    # Penalize if duration is too short (user didn't finish reading)
    if duration > 0 and chinese_chars > 0:
        min_expected = chinese_chars * 0.15
        if duration < min_expected:
            ratio = duration / min_expected
            acc = acc * (0.5 + 0.5 * min(1, ratio))

    accuracy_score = int(round(acc))

    # === 2. FLUENCY SCORE (30%) ===
    if duration <= 0 or chinese_chars == 0:
        fluency_score = 80
    else:
        pace = duration / chinese_chars
        if pace < 0.10:
            fluency_score = max(30, int(35 + pace * 200))
        elif pace < 0.18:
            fluency_score = int(45 + (pace - 0.10) * 300)
        elif pace < 0.25:
            fluency_score = int(68 + (pace - 0.18) * 250)
        elif pace < 0.40:
            fluency_score = int(88 + (pace - 0.25) * 60)
        elif pace < 0.55:
            fluency_score = int(95 - (pace - 0.40) * 50)
        elif pace < 0.80:
            fluency_score = int(80 - (pace - 0.55) * 80)
        else:
            fluency_score = max(35, int(60 - (pace - 0.80) * 40))
        fluency_score = max(30, min(98, fluency_score))

    # === 3. INTEGRITY SCORE (20%) ===
    if duration <= 0 or chinese_chars == 0:
        integrity_score = 80
    else:
        expected = chinese_chars * 0.35 + 0.5
        ratio = duration / expected

        if ratio < 0.25:
            integrity_score = max(15, int(ratio * 100))
        elif ratio < 0.50:
            integrity_score = int(25 + (ratio - 0.25) * 120)
        elif ratio < 0.75:
            integrity_score = int(55 + (ratio - 0.50) * 100)
        elif ratio < 1.25:
            integrity_score = int(80 + (ratio - 0.75) * 50)
        elif ratio < 1.80:
            integrity_score = int(105 - (ratio - 1.25) * 30)
        else:
            integrity_score = max(40, int(85 - (ratio - 1.80) * 25))

        if energy < 0.01:
            integrity_score = int(integrity_score * 0.6)
        elif energy < 0.03:
            integrity_score = int(integrity_score * 0.85)
        integrity_score = max(15, min(98, integrity_score))

    # === 4. VOLUME SCORE (15%) ===
    if energy < 0.005:
        vol = max(20, int(energy * 4000 + 10))
    elif energy < 0.02:
        vol = int(40 + energy * 1500)
    elif energy < 0.06:
        vol = int(60 + energy * 400)
    elif energy < 0.15:
        vol = int(75 + energy * 120)
    else:
        vol = min(98, 88 + energy * 20)
    volume_score = max(20, min(98, vol))

    # === OVERALL (weighted average) ===
    overall = accuracy_score * 0.35 + fluency_score * 0.30 + integrity_score * 0.20 + volume_score * 0.15
    overall = int(round(overall))

    # === PER-WORD SCORES ===
    word_scores = []
    if words:
        wc = len(words)
        for i, w in enumerate(words):
            word_text = w.get("word", "")
            word_len = len(word_text)

            # Position: middle words score slightly higher
            if wc > 1:
                pos_ratio = i / (wc - 1)
                pos_factor = 1 - 0.10 * abs(pos_ratio - 0.5)
            else:
                pos_factor = 1.0

            # Length bonus for multi-character words
            length_bonus = min(4, word_len * 1.2)

            # fluency and integrity modulate consistency
            f_mod = fluency_score / 100.0
            i_mod = integrity_score / 100.0
            combine = 0.6 + 0.4 * ((f_mod + i_mod) / 2)

            # Natural variance per word
            variance = random.uniform(-3, 3)

            ws = accuracy_score * pos_factor * combine + length_bonus + variance
            ws = max(20, min(100, int(round(ws))))
            word_scores.append({"word": word_text, "score": ws})

    # === GRADE ===
    if overall >= 90:
        grade = "\u4f18\u79c0"
    elif overall >= 80:
        grade = "\u826f\u597d"
    elif overall >= 70:
        grade = "\u4e00\u822c"
    elif overall >= 60:
        grade = "\u8f83\u5dee"
    else:
        grade = "\u9700\u6539\u8fdb"

    return {
        "mock": True,
        "overall_score": overall,
        "accuracy_score": accuracy_score,
        "fluency_score": fluency_score,
        "integrity_score": integrity_score,
        "volume_score": volume_score,
        "word_scores": word_scores,
        "grade": grade,
        "dimensions": {
            "accuracy": {"label": "\u53d1\u97f3\u51c6\u786e\u5ea6", "desc": "\u8bc4\u4f30\u53d1\u97f3\u662f\u5426\u6e05\u6670\u3001\u6807\u51c6", "weight": "35%", "score": accuracy_score},
            "fluency": {"label": "\u6d41\u5229\u5ea6", "desc": "\u8bc4\u4f30\u8bf4\u8bdd\u7684\u8282\u594f\u662f\u5426\u81ea\u7136\u6d41\u7545", "weight": "30%", "score": fluency_score},
            "integrity": {"label": "\u5b8c\u6574\u5ea6", "desc": "\u8bc4\u4f30\u662f\u5426\u5b8c\u6574\u6717\u8bfb\u4e86\u6240\u6709\u5185\u5bb9", "weight": "20%", "score": integrity_score},
            "volume": {"label": "\u97f3\u91cf", "desc": "\u8bc4\u4f30\u97f3\u91cf\u662f\u5426\u5145\u8db3\u3001\u7a33\u5b9a", "weight": "15%", "score": volume_score},
        },
    }
