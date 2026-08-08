"""
练习题后台管理专用视图（AJAX 端点）
"""

import json
import os
from pathlib import Path

from django.conf import settings
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from courseApp.models import Exercise, Lesson
from courseApp.utils import (
    _download_and_save,
    _extract_ranked_keywords,
    search_images_only,
    segment_and_annotate,
)

ENG_NAMES = {'unsplash':'Unsplash','baidu':'百度','bing':'必应','360':'360'}


@csrf_exempt
def auto_image_view(request):
    """自动配图接口：DeepSeek 提取关键词 → 按 3→2→1 逐步降级搜索"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '无效的 JSON 数据'}, status=400)

    exercise_id = data.get('exercise_id')
    engine = data.get('engine', 'baidu')
    chinese = data.get('chinese', '').strip()
    english = data.get('english', '').strip()

    if not chinese:
        return JsonResponse({'success': False, 'error': '缺少中文句子，无法提取关键词'})

    # ---- 1. 提取或创建 Exercise 对象 ----
    if exercise_id:
        try:
            exercise_obj = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return JsonResponse({'success': False, 'error': '习题不存在'})
        # 如果请求中没有带 chinese，从 DB 读取
        if not chinese:
            try:
                q = json.loads(exercise_obj.sentences)
                chinese = q.get('chinese', '')
                english = q.get('english', '')
            except (json.JSONDecodeError, TypeError):
                pass
        if not chinese:
            return JsonResponse({'success': False, 'error': '无法获取中文句子'})
    else:
        lesson_id = data.get('lesson_id')
        if not lesson_id:
            return JsonResponse({'success': False, 'error': '新建习题需要指定所属课时'})
        try:
            lesson_obj = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return JsonResponse({'success': False, 'error': '指定的课时不存在'})
        pinyin = data.get('pinyin', '')
        sentences_json = json.dumps(
            {'chinese': chinese, 'pinyin': pinyin, 'english': english},
            ensure_ascii=False,
        )
        max_order = Exercise.objects.filter(lesson=lesson_obj).aggregate(
            m=models.Max('sort_order')
        )['m'] or 0
        raw_wa = data.get('word_analysis')
        grammar_hint = data.get('grammar_hint', '')
        exercise_obj = Exercise.objects.create(
            lesson=lesson_obj,
            sentences=sentences_json,
            sort_order=max_order + 1,
        )
        if raw_wa:
            if isinstance(raw_wa, str):
                try:
                    exercise_obj.word_analysis = json.loads(raw_wa)
                except (json.JSONDecodeError, TypeError):
                    exercise_obj.word_analysis = []
            else:
                exercise_obj.word_analysis = raw_wa
        if grammar_hint:
            exercise_obj.grammar_hint = grammar_hint
        if raw_wa or grammar_hint:
            exercise_obj.save(update_fields=['word_analysis', 'grammar_hint'])
        exercise_id = str(exercise_obj.id)

    # ---- 2. 提取关键词（从请求中的三个输入框读取）----
    kw1 = data.get('kw1', '').strip()
    kw2 = data.get('kw2', '').strip()
    kw3 = data.get('kw3', '').strip()
    ranked_kws = [k for k in [kw1, kw2, kw3] if k]
    if not ranked_kws:
        target_lang = 'english' if engine == 'unsplash' else 'chinese'
        ranked_kws = _extract_ranked_keywords(chinese, english, target_lang)
        if not ranked_kws:
            if target_lang == 'english':
                ranked_kws = [english.strip()[:60]] if english else [chinese[:30]]
            else:
                ranked_kws = [chinese[:30]]

    # ---- 3. 逐级搜索，收集全部图片，按匹配度排序 ----
    attempts = []
    eng_name = ENG_NAMES.get(engine, engine)
    # level_urls[n] = [url1, url2, ...]
    level_urls: dict[int, list[str]] = {}
    last_error = ''

    for n in range(len(ranked_kws), 0, -1):
        kw = ' '.join(ranked_kws[:n])
        success, err_msg, img_urls = search_images_only(kw, engine)
        level_urls[n] = img_urls
        attempts.append({
            'level': n,
            'keywords': kw,
            'found': len(img_urls),
            'detail': eng_name + ('搜索无结果' if not img_urls else '找到图片'),
        })
        if not success:
            last_error = err_msg

    # 按匹配度去重排序：level 高（关键词多）的图片优先
    seen: set[str] = set()
    ranked: list[str] = []
    for level in sorted(level_urls.keys(), reverse=True):
        for url in level_urls[level]:
            if url and url not in seen:
                seen.add(url)
                ranked.append(url)

    if ranked:
        return JsonResponse({
            'success': True,
            'exercise_id': exercise_id if not data.get('exercise_id') else None,
            'first_url': ranked[0],
            'images': ranked[:27],
            'attempts': attempts,
        })

    return JsonResponse({
        'success': False,
        'error': f'配图失败，已尝试{len(ranked_kws)}组关键词。{last_error}',
        'attempts': attempts,
    })


@csrf_exempt
def save_image_url_view(request):
    """保存指定 URL 的图片到 exercise.image（保存配图按钮用）"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '仅支持 POST 请求'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '无效的 JSON 数据'}, status=400)
    exercise_id = data.get('exercise_id')
    image_url = data.get('image_url', '').strip()
    if not exercise_id or not image_url:
        return JsonResponse({'success': False, 'error': '缺少 exercise_id 或 image_url'})
    try:
        exercise_obj = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return JsonResponse({'success': False, 'error': '习题不存在'})
    success, err = _download_and_save(image_url, '', exercise_obj, 'Gallery')
    new_url = exercise_obj.image.url if success and exercise_obj.image else ''
    filename = os.path.basename(exercise_obj.image.name) if success and exercise_obj.image else ''
    return JsonResponse({'success': success, 'image_url': new_url, 'filename': filename, 'error': err})


@csrf_exempt
def upload_image_view(request):
    """上传本地图片文件到 exercise.image（选择文件按钮用）"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '仅支持 POST 请求'}, status=405)

    exercise_id = request.POST.get('exercise_id')
    upload_file = request.FILES.get('file')
    if not exercise_id or not upload_file:
        return JsonResponse({'success': False, 'error': '缺少 exercise_id 或文件'})

    try:
        exercise_obj = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return JsonResponse({'success': False, 'error': '习题不存在'})

    try:
        exercise_obj.image.save(upload_file.name, upload_file, save=True)
        new_url = exercise_obj.image.url
        filename = os.path.basename(exercise_obj.image.name)
        return JsonResponse({'success': True, 'image_url': new_url, 'filename': filename})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'图片保存失败: {e}'})


@csrf_exempt
def auto_analyze_view(request):
    """
    自动分词接口（仅管理员可用）
    POST 参数：
        chinese: str  中文句子
        pinyin: str   拼音
        english: str  英文翻译
        dicts: list   选中的自定义词库文件名列表
    """
    if not request.user.is_staff:
        return JsonResponse({'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的 JSON 数据'}, status=400)

    chinese = data.get('chinese', '').strip()
    pinyin = data.get('pinyin', '').strip()
    english = data.get('english', '').strip()
    dict_names = data.get('dicts', [])

    if not all([chinese, pinyin, english]):
        return JsonResponse({'error': '请完整填写中文句子、拼音和英文翻译三项内容'})

    # 新版流程：jieba 分词 + DeepSeek 标注
    result = segment_and_annotate(chinese, pinyin, english, dict_names)

    if 'error' in result:
        return JsonResponse(result, status=500)

    # 提取配图关键词（直接返回，前端无需第二次 API 调用）
    engine = data.get('engine', 'baidu')
    target_lang = 'english' if engine == 'unsplash' else 'chinese'
    kws = _extract_ranked_keywords(chinese, english, target_lang)
    if not kws:
        if target_lang == 'english':
            kws = [english.strip()[:60]] if english else [chinese[:30]]
        else:
            kws = [chinese[:30]]

    return JsonResponse({
        'word_analysis': result.get('word_analysis', []),
        'grammar_hint': result.get('grammar_hint', ''),
        'image_keywords': result.get('image_keywords', ''),
        'keywords': kws,
    })


@csrf_exempt
def extract_keywords_view(request):
    """关键词提取接口：根据中文句子提取 3 个核心关键词（支持排除已有关键词）"""
    if not request.user.is_staff:
        return JsonResponse({'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的 JSON 数据'}, status=400)

    chinese = data.get('chinese', '').strip()
    english = data.get('english', '').strip()
    engine = data.get('engine', 'baidu')
    exclude = data.get('exclude', [])
    is_refresh = data.get('is_refresh', False)

    if not chinese:
        return JsonResponse({'error': '缺少中文句子'})

    target_lang = 'english' if engine == 'unsplash' else 'chinese'
    exclude_kws = exclude if is_refresh else None
    keywords = _extract_ranked_keywords(chinese, english, target_lang, exclude_kws)

    if not keywords:
        if target_lang == 'english':
            fallback = [english.strip()[:60]] if english else [chinese[:30]]
        else:
            fallback = [chinese[:30]]
        return JsonResponse({'keywords': fallback, 'fallback': True})

    return JsonResponse({'keywords': keywords, 'fallback': False})


@csrf_exempt
def cleanup_images_view(request):
    """清理 exercise_images 目录中未被任何 Exercise.image 引用的垃圾图片"""
    if not request.user.is_staff:
        return JsonResponse({'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    import os
    img_dir = settings.MEDIA_ROOT / 'exercise_images'
    if not img_dir.exists():
        return JsonResponse({'deleted': []})

    # 收集 DB 中所有 image 字段引用的文件名
    used_images = set()
    for ex in Exercise.objects.exclude(image='').iterator():
        # image.name 是相对于 MEDIA_ROOT 的路径，如 "exercise_images/xxx.jpg"
        name = ex.image.name
        if name:
            used_images.add(os.path.basename(name))

    # 扫描目录，删除未使用的文件
    deleted_files = []
    for f in sorted(img_dir.iterdir()):
        if f.is_file():
            if f.name not in used_images:
                try:
                    f.unlink()
                    deleted_files.append(f.name)
                except OSError:
                    pass

    return JsonResponse({'deleted': deleted_files})


@csrf_exempt
def upload_dict_view(request):
    """上传自定义词库文件"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': '未授权访问'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '仅支持 POST 请求'}, status=405)

    if not request.FILES.get('file'):
        return JsonResponse({'success': False, 'error': '请选择要上传的文件'})

    file = request.FILES['file']
    if not file.name.endswith('.txt'):
        return JsonResponse({'success': False, 'error': '仅支持 .txt 格式的词库文件'})

    dict_dir = Path(settings.BASE_DIR) / 'static' / 'dicts'
    dict_dir.mkdir(parents=True, exist_ok=True)
    filepath = dict_dir / file.name

    try:
        with open(filepath, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        if filepath.exists():
            return JsonResponse({'success': True, 'filename': file.name})
        else:
            return JsonResponse({'success': False, 'error': '文件写入失败，请检查目录权限'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'上传失败: {e}'})

@csrf_exempt
def list_dicts_view(request):
    """返回当前词库列表（AJAX 局部刷新用）"""
    if not request.user.is_staff:
        return JsonResponse({'error': '未授权访问'}, status=403)
    from courseApp.utils import get_available_dicts
    files = get_available_dicts()
    return JsonResponse({'dicts': files})
