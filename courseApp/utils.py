"""
练习题自动分词工具模块

功能：
1. 加载 jieba 自定义词库
2. 调用 DeepSeek API 进行逐词分析 + 语法提示 + 配图关键词
3. 调用 Unsplash API 搜索并保存配图
"""

import json
import logging
import os
import re as _re
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

import jieba
import requests as http_requests
from django.conf import settings
from django.core.files.base import ContentFile

# 抑制 requests 的不安全 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 用于 API 请求的 SSL 上下文（兼容国内 CDN 老旧 TLS 配置）
_UNVERIFIED_SSL = ssl._create_unverified_context()
# 忽略服务器端异常断开（国内 CDN 常见）
_extra_opts = 0
if hasattr(ssl, 'OP_IGNORE_UNEXPECTED_EOF'):
    _extra_opts |= ssl.OP_IGNORE_UNEXPECTED_EOF
if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
    _extra_opts |= ssl.OP_LEGACY_SERVER_CONNECT
if _extra_opts:
    _UNVERIFIED_SSL.options |= _extra_opts

logger = logging.getLogger(__name__)


# 中文标点符号集合（不含空白字符）
_PUNCTUATION = set(
    '，。、？！：；""“”''「」『』（）【】《》—…·～'
    ',.;:!?\'"()[]{}<>-~@#$%^&*+/\\|`'
)
_WHITESPACE = set(' \t\n\r　')


# ---------------------------------------------------------------------------
# 1. 自定义词库
# ---------------------------------------------------------------------------

def get_available_dicts() -> list[dict]:
    """扫描 static/dicts/ 下的所有 .txt 文件，返回 [{name, label}, ...]"""
    dict_dir = Path(settings.BASE_DIR) / 'static' / 'dicts'
    files = []
    if dict_dir.exists():
        for f in sorted(dict_dir.iterdir()):
            if f.suffix == '.txt':
                files.append({
                    'name': f.name,
                    'label': f.stem,  # 去掉 .txt 后缀作为显示名
                })
    return files


def load_custom_words(dict_names: list[str]) -> list[str]:
    """
    加载指定的自定义词库文件，返回所有自定义词语列表。
    dict_names: ['hsk1.txt', 'textbook.txt']
    """
    custom_words = []
    dict_dir = Path(settings.BASE_DIR) / 'static' / 'dicts'
    if not dict_dir.exists():
        return custom_words

    for name in dict_names:
        filepath = dict_dir / name
        if not filepath.exists():
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if parts:
                        custom_words.append(parts[0])
        except Exception as e:
            logger.warning('读取词库文件 %s 失败: %s', name, e)

    return custom_words


def segment_with_dicts(text: str, dict_names: list[str]) -> list[str]:
    """
    用 jieba 分词（加载自定义词库），返回词语列表。
    自定义词库优先于 jieba 默认词典。
    """
    # 加载自定义词库到 jieba
    for name in dict_names:
        filepath = Path(settings.BASE_DIR) / 'static' / 'dicts' / name
        if filepath.exists():
            try:
                jieba.load_userdict(str(filepath))
            except Exception as e:
                logger.warning('加载词库 %s 到 jieba 失败: %s', name, e)

    # 分词
    words = list(jieba.cut(text))
    return words


# ---------------------------------------------------------------------------
# 2. DeepSeek API
# ---------------------------------------------------------------------------

def call_deepseek(
    chinese: str,
    pinyin: str,
    english: str,
    custom_words: list[str] | None = None,
) -> dict:
    """
    调用 DeepSeek API，返回：
    {
        "word_analysis": [...],
        "grammar_hint": "...",
        "image_keywords": "..."
    }
    """
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')

    if not api_key:
        return {'error': 'DeepSeek API Key 未配置，请在 settings.py 中设置 DEEPSEEK_API_KEY'}

    # 构建自定义词语提示
    custom_words_hint = ''
    if custom_words:
        custom_words_hint = (
            '以下词语应作为整体，不要拆分（已在自定义词库中定义）：\n'
            + '、'.join(custom_words) + '\n\n'
        )

    prompt = f"""你是一个专业的中文教学助手。请分析下面这句中文，返回严格的 JSON 格式结果。

中文句子：{chinese}
拼音：{pinyin}
英文翻译：{english}

{custom_words_hint}请按以下 JSON 格式返回（只返回 JSON，不要包含其他任何内容）：

{{
  "word_analysis": [
    {{
      "word": "词语",
      "pinyin": "该词语的拼音",
      "english": "英文释义",
      "pos": "词性，如：动词/名词/形容词/副词/介词/助词/代词/数量词/连词/叹词/拟声词/成语/固定短语/前缀/后缀/时间名词/处所名词/方位名词/时间副词/程度副词/范围副词/语气副词/情态副词/介词结构/动词+了/动词+着/动词+过/能愿动词/趋向动词/判断动词",
      "grammar": "语法成分，如：主语/谓语/宾语/定语/状语/补语/中心语/兼语/同位语/插入语/独立语/介词结构/时间状语/地点状语/定语标记/程度补语/结果补语/趋向补语/可能补语/时量补语/动量补语/谓语(完成态)/谓语(进行态)/谓语(经验态)/谓语(短时态)/谓语(尝试态)"
    }}
  ],
  "grammar_hint": "用中文写一段语法提示，解释本句的关键语法点（如句型结构、虚词用法、特殊句式等），适合中级汉语学习者理解，100-200字",
  "image_keywords": "用于搜索配图的关键词，用英文，空格分隔，3-5个词，要能准确反映句子场景"
}}"""

    url = base_url.rstrip('/') + '/chat/completions'
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个中文教学助手，只输出 JSON。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.1,
        'max_tokens': 4096,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )

    # 重试机制：网络波动时自动重试一次
    max_retries = 2
    body = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode('utf-8'))
            break
        except (TimeoutError, urllib.error.URLError) as e:
            if attempt < max_retries - 1:
                logger.warning('DeepSeek API 调用超时，第 %d 次重试...', attempt + 1)
                continue
            logger.error('DeepSeek API 调用失败(重试耗尽): %s', e)
            return {'error': f'DeepSeek API 调用失败(网络超时): {e}'}
        except Exception as e:
            logger.error('DeepSeek API 调用失败: %s', e)
            return {'error': f'DeepSeek API 调用失败: {e}'}
    if body is None:
        return {'error': 'DeepSeek API 调用失败: 无法获取响应'}

    # 解析返回结果
    try:
        content = body['choices'][0]['message']['content']
        # 提取 JSON（可能被 markdown 包裹）
        content = content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[-1]
            content = content.rsplit('```', 1)[0]
        content = content.strip()
        result = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error('DeepSeek 返回解析失败: %s | 原始返回: %s', e, body)
        return {'error': f'DeepSeek 返回解析失败: {e}'}

    # 兼容字段名
    if 'word_analysis' not in result:
        result['word_analysis'] = []
    for item in result['word_analysis']:
        if 'meaning' in item and 'english' not in item:
            item['english'] = item.pop('meaning')

    # 如果 DeepSeek 未返回 image_keywords，用中文句子关键词兜底
    if not result.get('image_keywords'):
        # 提取关键实词（去掉的/了/在/是等虚词）
        words = jieba.lcut(chinese)
        stop_words = {'的','了','在','是','我','你','他','她','它','们','这','那','哪','什么','怎么','也','都','就','和','与','或','但','是','不','很','太','更','最','把','被','让','给','对','向','从','到','去','来','上','下','里','外','前','后','能','会','要','想','可以','应该','已经','正在','着','过','吧','吗','呢','啊'}
        fallback_words = [w for w in words if len(w) >= 2 and w not in stop_words][:3]
        if fallback_words:
            result['image_keywords'] = ' '.join(fallback_words)
            logger.info('DeepSeek 未返回 image_keywords，使用句子关键词兜底: %s', result['image_keywords'])
        else:
            # 直接用完整句子作为搜索词
            result['image_keywords'] = chinese[:50]
            logger.info('DeepSeek 未返回 image_keywords，使用完整句子兜底: %s', result['image_keywords'])

    return result


# ---------------------------------------------------------------------------
# 2.5 标点注入（DeepSeek 结果后处理）
# 已废弃：改用下方 segment_and_annotate（jieba 分词 + DeepSeek 填分析）
# ---------------------------------------------------------------------------

def _jieba_split_punct(chinese_text: str) -> list[str]:
    """
    用 jieba 分词并将标点符号分离为独立 token。
    返回的列表顺序与原句一一对应。
    """
    raw = jieba.lcut(chinese_text)
    tokens: list[str] = []
    for token in raw:
        if token in _WHITESPACE:
            continue
        if len(token) == 1 and token in _PUNCTUATION:
            tokens.append(token)
        else:
            buf = ''
            for ch in token:
                if ch in _PUNCTUATION:
                    if buf:
                        tokens.append(buf)
                        buf = ''
                    tokens.append(ch)
                elif ch in _WHITESPACE:
                    if buf:
                        tokens.append(buf)
                        buf = ''
                else:
                    buf += ch
            if buf:
                tokens.append(buf)
    return tokens


def segment_and_annotate(
    chinese: str,
    pinyin: str,
    english: str,
    dict_names: list[str] | None = None,
) -> dict:
    """
    新版自动分词流程：
    1. jieba 完成完整分词（含标点，自定义词库优先）
    2. DeepSeek 对每个实词填入拼音/英文/词性/语法成分

    返回 {word_analysis, grammar_hint, image_keywords}
    """
    # ---- Step 1: 加载自定义词库 ----
    for name in (dict_names or []):
        fp = Path(settings.BASE_DIR) / 'static' / 'dicts' / name
        if fp.exists():
            try:
                jieba.load_userdict(str(fp))
            except Exception as e:
                logger.warning('加载词库 %s 失败: %s', name, e)

    # ---- Step 2: jieba 分词，分离标点 ----
    all_tokens = _jieba_split_punct(chinese)
    content_words = [t for t in all_tokens if not (len(t) == 1 and t in _PUNCTUATION)]
    is_punct_list = [len(t) == 1 and t in _PUNCTUATION for t in all_tokens]

    # 备用：image_keywords 从 content_words 提取
    stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们',
                  '这', '那', '哪', '什么', '怎么', '也', '都', '就', '和', '与',
                  '或', '但', '是', '不', '很', '太', '更', '最', '把', '被',
                  '让', '给', '对', '向', '从', '到', '去', '来', '上', '下',
                  '里', '外', '前', '后', '能', '会', '要', '想', '可以', '应该',
                  '已经', '正在', '着', '过', '吧', '吗', '呢', '啊'}
    fallback_kw = [w for w in content_words if len(w) >= 2 and w not in stop_words]

    # ---- Step 3: 调用 DeepSeek 对实词列表做标注 ----
    if not content_words:
        # 没有实词（纯标点句子），直接返回
        word_analysis = [{'word': t} for t in all_tokens]
        return {
            'word_analysis': word_analysis,
            'grammar_hint': '',
            'image_keywords': '',
        }

    annotations, grammar_hint, image_kw = _annotate_words(
        chinese, content_words, pinyin, english
    )

    # ---- Step 4: 合并分词 + 标注结果 ----
    word_analysis = []
    wi = 0
    for token, punct in zip(all_tokens, is_punct_list):
        if punct:
            word_analysis.append({'word': token, 'pinyin': '', 'english': '', 'pos': '', 'grammar': ''})
        else:
            item: dict = {'word': token}
            if wi < len(annotations):
                item.update(annotations[wi])
                wi += 1
            word_analysis.append(item)

    # image_keywords：优先用 DeepSeek 返回的英文关键词，其次用英文翻译作为搜索词，最后用中文
    image_keywords = ''
    if image_kw:
        image_keywords = image_kw
    elif english:
        # 用英文翻译的前 60 个字符作为搜索词（英文搜索命中率远高于中文）
        image_keywords = english.strip()[:60]
    elif fallback_kw:
        image_keywords = ' '.join(fallback_kw[:3])

    return {
        'word_analysis': word_analysis,
        'grammar_hint': grammar_hint or '',
        'image_keywords': image_keywords,
    }


def _annotate_words(
    chinese: str,
    content_words: list[str],
    pinyin: str,
    english: str,
) -> tuple[list[dict], str, str]:
    """
    调用 DeepSeek，为给定的实词列表填入分析数据，同时获取语法提示和配图关键词。

    返回 (annotations, grammar_hint, image_keywords)
    annotations 长度与 content_words 相同，每项含 {pinyin, english, pos, grammar}。
    API 失败时返回 ([{}...], '', '')。
    """
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')

    if not api_key:
        logger.error('DeepSeek API Key 未配置')
        return ([{} for _ in content_words], '', '')

    prompt = (
        f'你是一个专业的中文教学助手。请分析下面这句中文，返回严格的 JSON 对象。\n\n'
        f'中文句子：{chinese}\n'
        f'拼音：{pinyin}\n'
        f'英文翻译：{english}\n\n'
        f'词语列表（已分好词，按顺序排列，请逐词分析）：\n'
        + '\n'.join(f'  {i+1}. {w}' for i, w in enumerate(content_words))
        + '\n\n'
        f'返回 JSON 格式如下（只输出 JSON，不要其他内容）：\n'
        f'{{\n'
        f'  "annotations": [\n'
        f'    {{"pinyin": "拼音", "english": "英文释义", "pos": "词性", "grammar": "语法成分"}},\n'
        f'    ... 长度必须与词语列表完全一致\n'
        f'  ],\n'
        f'  "grammar_hint": "用中文写一段语法提示，解释本句的关键语法点，适合中级汉语学习者理解，100-200字",\n'
        f'  "image_keywords": "用于搜索配图的关键词，用英文空格分隔，3-5个词，要能准确反映句子场景"\n'
        f'}}\n\n'
        f'词性可选：动词/名词/形容词/副词/介词/助词/代词/数量词/连词/叹词/拟声词/成语/固定短语/时间名词/处所名词/时间副词/程度副词/范围副词/语气副词/情态副词/介词结构/能愿动词/趋向动词/判断动词\n'
        f'语法成分可选：主语/谓语/宾语/定语/状语/补语/中心语/兼语/同位语/插入语/独立语/介词结构/时间状语/地点状语/定语标记/程度补语/结果补语/趋向补语/可能补语/时量补语/动量补语'
    )

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个中文教学助手，只输出 JSON。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.1,
        'max_tokens': 4096,
    }

    body = _call_deepseek_api(api_key, base_url, payload)
    if body is None:
        return ([{} for _ in content_words], '', '')

    try:
        content = body['choices'][0]['message']['content'].strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
        result = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error('DeepSeek 返回解析失败: %s', e)
        return ([{} for _ in content_words], '', '')

    annotations = result.get('annotations', result if isinstance(result, list) else [])
    if isinstance(annotations, list) and len(annotations) > 0 and isinstance(annotations[0], dict):
        # 补齐/截断
        while len(annotations) < len(content_words):
            annotations.append({})
        annotations = annotations[:len(content_words)]
        for item in annotations:
            if 'meaning' in item and 'english' not in item:
                item['english'] = item.pop('meaning')
    else:
        annotations = [{} for _ in content_words]

    grammar_hint = result.get('grammar_hint', '') if isinstance(result, dict) else ''
    image_keywords = result.get('image_keywords', '') if isinstance(result, dict) else ''

    return (annotations, grammar_hint or '', image_keywords or '')


def _call_deepseek_api(api_key: str, base_url: str, payload: dict) -> dict | None:
    """调用 DeepSeek API 返回原始响应体，失败返回 None。"""
    url = base_url.rstrip('/') + '/chat/completions'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (TimeoutError, urllib.error.URLError) as e:
            if attempt == 0:
                logger.warning('DeepSeek API 超时，重试...')
                continue
            logger.error('DeepSeek API 失败: %s', e)
            return None
        except Exception as e:
            logger.error('DeepSeek API 异常: %s', e)
            return None
    return None
# ---------------------------------------------------------------------------

def search_images_only(keywords: str, engine: str = 'baidu') -> tuple[bool, str, list]:
    """
    仅搜索图片并返回 URL 列表（不保存到磁盘）。

    引擎可选：unsplash / baidu / bing / 360
    默认 baidu。

    返回 (是否成功, 错误信息, 图片URL列表)。
    """
    if not keywords:
        return (False, '关键词为空', [])

    engine_map = {
        'unsplash': _search_only_unsplash,
        'baidu': _search_only_baidu,
        'bing': _search_only_bing,
        '360': _search_only_360,
    }
    searcher = engine_map.get(engine)
    if not searcher:
        return (False, f'未知配图引擎: {engine}', [])

    logger.info('配图引擎(仅搜索): %s, 关键词: %s', engine, keywords)
    return searcher(keywords)


def _search_unsplash(keywords: str, exercise) -> tuple[bool, str, int]:
    """用 Unsplash 搜索并保存图片。返回 (成功, 错误, 结果数)。"""
    api_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', '')
    if not api_key:
        return (False, 'UNSPLASH_ACCESS_KEY 未配置', 0)

    try:
        query = urllib.parse.quote(keywords)
        search_url = (
            f'https://api.unsplash.com/search/photos'
            f'?query={query}&per_page=1&orientation=landscape'
        )
        req = urllib.request.Request(
            search_url,
            headers={'Authorization': f'Client-ID {api_key}'},
        )
        with urllib.request.urlopen(req, timeout=30, context=_UNVERIFIED_SSL) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        all_results = data.get('results', [])
        found = len(all_results)
        if not all_results:
            return (False, f'Unsplash 搜索无结果', found)

        img_url = all_results[0]['urls']['regular']
        dl_ok, dl_err = _download_and_save(img_url, keywords, exercise, 'Unsplash')
        return (dl_ok, dl_err, found)

    except Exception as e:
        return (False, f'Unsplash 请求失败: {e}', 0)


def _search_only_unsplash(keywords: str) -> tuple[bool, str, list]:
    """Unsplash 搜索（仅返回 URL 列表，不保存）。"""
    api_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', '')
    if not api_key:
        return (False, 'UNSPLASH_ACCESS_KEY 未配置', [])
    try:
        query = urllib.parse.quote(keywords)
        req = urllib.request.Request(
            f'https://api.unsplash.com/search/photos?query={query}&per_page=9&orientation=landscape',
            headers={'Authorization': f'Client-ID {api_key}'},
        )
        with urllib.request.urlopen(req, timeout=30, context=_UNVERIFIED_SSL) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        urls = [r['urls']['regular'] for r in data.get('results', []) if r.get('urls')]
        return (True, '', urls) if urls else (False, 'Unsplash 搜索无结果', [])
    except Exception as e:
        return (False, f'Unsplash 请求失败: {e}', [])


def _search_baidu(keywords: str, exercise) -> tuple[bool, str, int]:
    """百度图片搜索。返回 (成功, 错误, 结果数)。"""
    try:
        query = urllib.parse.quote(keywords)
        # 使用百度图片搜索 JSON API（acjson 接口）
        search_url = (
            f'https://image.baidu.com/search/acjson'
            f'?tn=resultjson_com&word={query}&pn=0&rn=10&ie=utf-8&oe=utf-8'
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://image.baidu.com/',
            'Accept': 'application/json, text/plain, */*',
        }
        sess = http_requests.Session()
        resp = sess.get(search_url, headers=headers, timeout=30, verify=False)
        resp.encoding = 'utf-8'

        # Baidu 可能返回 JSONP（函数包裹），也可能是纯 JSON
        text = resp.text.strip()
        if text.startswith('(') and text.endswith(')'):
            # JSONP 格式：({...})
            text = text[1:-1]
        elif text.startswith('json('):
            # JSONP 格式：json({...})
            text = text[5:-1]

        data = json.loads(text)
        result_list = data.get('data', [])
        # 过滤空项（Baidu 有时返回 [null, {...}, null]）
        valid_items = [x for x in result_list if x and isinstance(x, dict)]
        found = len(valid_items)

        img_url = ''
        for item in valid_items:
            img_url = item.get('thumbURL') or item.get('middleURL') or item.get('objURL') or ''
            if img_url:
                break

        if not img_url:
            logger.warning('百度搜索无结果: keywords=%s, total_data=%d', keywords, len(result_list))
            return (False, '百度图片搜索无结果', found)

        # objURL 可能是经过 Baidu 跳转编码的，需要解码
        if img_url.startswith('http://') or img_url.startswith('https://'):
            pass  # 已经是直接 URL
        elif img_url.startswith('//'):
            img_url = 'https:' + img_url
        else:
            # 可能是 Baidu 私有格式，尝试作为普通 URL 处理
            img_url = urllib.parse.unquote(img_url)

        dl_ok, dl_err = _download_and_save(img_url, keywords, exercise, 'Baidu')
        return (dl_ok, dl_err, found)

    except Exception as e:
        logger.error('百度图片搜索失败: keywords=%s, error=%s', keywords, e)
        return (False, f'百度图片搜索失败: {e}', 0)


def _search_only_baidu(keywords: str) -> tuple[bool, str, list]:
    """百度搜索（仅返回 URL 列表，不保存）。"""
    try:
        query = urllib.parse.quote(keywords)
        # acjson 完整参数（带完整参数可绕过反爬拦截，简化版返回 Forbid spider access）
        search_url = (
            f'https://image.baidu.com/search/acjson'
            f'?tn=resultjson_com&ipn=rj&ct=201326592&is=0&fp=result'
            f'&queryWord={query}&cl=2&lm=-1&ie=utf-8&oe=utf-8'
            f'&adpicid=&st=-1&z=&ic=0&hd=&latest=0&copyright=0'
            f'&word={query}&s=0&se=&tab=&width=&height=&face=0'
            f'&istype=2&qc=&nc=1&fr=&simid=&pn=0&rn=10&gsm=1e'
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://image.baidu.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        sess = http_requests.Session()
        resp = sess.get(search_url, headers=headers, timeout=30, verify=False)
        resp.encoding = 'utf-8'
        text = resp.text.strip()
        if text.startswith('(') and text.endswith(')'):
            text = text[1:-1]
        elif text.startswith('json('):
            text = text[5:-1]
        data = json.loads(text)
        valid_items = [x for x in data.get('data', []) if x and isinstance(x, dict)]
        urls = []
        for item in valid_items:
            u = item.get('thumbURL') or item.get('middleURL') or item.get('objURL') or ''
            if u:
                if u.startswith('//'):
                    u = 'https:' + u
                urls.append(u)
            if len(urls) >= 9:
                break
        return (True, '', urls) if urls else (False, '百度搜索无结果', [])
    except Exception as e:
        return (False, f'百度图片搜索失败: {e}', [])


def _search_bing(keywords: str, exercise) -> tuple[bool, str, int]:
    """必应图片搜索。返回 (成功, 错误, 结果数)。"""
    try:
        query = urllib.parse.quote(keywords)
        search_url = f'https://cn.bing.com/images/search?q={query}&form=IRFLTR'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'text/html,application/xhtml+xml',
            'Referer': 'https://cn.bing.com/',
        }
        sess = http_requests.Session()
        resp = sess.get(search_url, headers=headers, timeout=30, verify=False)
        resp.encoding = 'utf-8'
        html = resp.text

        # 多重正则回退
        all_urls = []

        # 模式1: <img class="mimg" src="..." — Bing 主图标准格式
        all_urls = _re.findall(r'<img[^>]+class="mimg"[^>]+src="(https?://[^"]+)"', html)

        if not all_urls:
            # 模式2: "m":"https://..." (JSON 内联数据)
            all_urls = _re.findall(r'"m":"(https?://[^"]+)"', html)

        if not all_urls:
            # 模式3: data-src="..." (懒加载)
            all_urls = _re.findall(r'data-src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)

        if not all_urls:
            # 模式4: mediaurl 属性
            all_urls = _re.findall(r'mediaurl="(https?://[^"]+)"', html)

        if not all_urls:
            # 模式5: src="..." 且包含 jpg/png/webp
            all_urls = _re.findall(r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)

        found = len(all_urls)
        if not all_urls:
            logger.warning('必应搜索无结果: keywords=%s, html_len=%d', keywords, len(html))
            return (False, '必应搜索无结果', 0)

        img_url = all_urls[0].replace('\\', '').split('"')[0]
        dl_ok, dl_err = _download_and_save(img_url, keywords, exercise, 'Bing')
        return (dl_ok, dl_err, found)

    except Exception as e:
        logger.error('必应图片搜索失败: keywords=%s, error=%s', keywords, e)
        return (False, f'必应图片搜索失败: {e}', 0)


def _search_only_bing(keywords: str) -> tuple[bool, str, list]:
    """必应搜索（仅返回 URL 列表，不保存）。"""
    try:
        query = urllib.parse.quote(keywords)
        headers = {'User-Agent':'Mozilla/5.0','Accept-Language':'zh-CN,zh','Referer':'https://cn.bing.com/'}
        sess = http_requests.Session()
        resp = sess.get(f'https://cn.bing.com/images/search?q={query}&form=IRFLTR', headers=headers, timeout=30, verify=False)
        html = resp.text
        raw = _re.findall(r'<img[^>]+class="mimg"[^>]+src="(https?://[^"]+)"', html)
        if not raw: raw = _re.findall(r'"m":"(https?://[^"]+)"', html)
        if not raw: raw = _re.findall(r'data-src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)
        if not raw: raw = _re.findall(r'mediaurl="(https?://[^"]+)"', html)
        if not raw: raw = _re.findall(r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)
        urls = [u.replace('\\','').split('"')[0] for u in raw[:9]]
        return (True, '', urls) if urls else (False, '必应搜索无结果', [])
    except Exception as e:
        return (False, f'必应图片搜索失败: {e}', [])


def _search_360(keywords: str, exercise) -> tuple[bool, str, int]:
    """360图片搜索。返回 (成功, 错误, 结果数)。"""
    try:
        query = urllib.parse.quote(keywords)
        search_url = f'https://image.so.com/j?q={query}&pn=1&ps=1'
        req = urllib.request.Request(
            search_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Referer': 'https://image.so.com/'},
        )
        with urllib.request.urlopen(req, timeout=30, context=_UNVERIFIED_SSL) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            data = json.loads(html)

        result_list = data.get('list', [])
        found = len(result_list)
        if not result_list:
            return (False, '360图片搜索无结果', 0)

        img_url = result_list[0].get('img') or result_list[0].get('thumb') or ''
        if not img_url:
            return (False, '360图片搜索无结果', found)

        dl_ok, dl_err = _download_and_save(img_url, keywords, exercise, '360')
        return (dl_ok, dl_err, found)

    except Exception as e:
        return (False, f'360图片搜索失败: {e}', 0)


def _search_only_360(keywords: str) -> tuple[bool, str, list]:
    """360搜索（仅返回 URL 列表，不保存）。"""
    try:
        req = urllib.request.Request(
            f'https://image.so.com/j?q={urllib.parse.quote(keywords)}&pn=1&ps=9',
            headers={'User-Agent':'Mozilla/5.0','Referer':'https://image.so.com/'},
        )
        with urllib.request.urlopen(req, timeout=30, context=_UNVERIFIED_SSL) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        urls = []
        for item in data.get('list', []):
            u = item.get('img') or item.get('thumb') or ''
            if u: urls.append(u)
            if len(urls) >= 9: break
        return (True, '', urls) if urls else (False, '360搜索无结果', [])
    except Exception as e:
        return (False, f'360图片搜索失败: {e}', [])


def _download_and_save(img_url: str, keywords: str, exercise, source: str) -> tuple[bool, str]:
    """下载图片并保存到 exercise.image"""
    try:
        img_req = urllib.request.Request(
            img_url,
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        with urllib.request.urlopen(img_req, timeout=30, context=_UNVERIFIED_SSL) as resp:
            img_data = resp.read()

        ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1] or '.jpg'
        filename = f'exercise_{exercise.id}_{keywords[:20]}{ext}' if exercise.id else f'temp_{keywords[:20]}{ext}'
        exercise.image.save(filename, ContentFile(img_data), save=True)

        logger.info('图片已保存: %s (来自 %s)', filename, source)
        return (True, '')

    except Exception as e:
        return (False, f'图片下载失败: {e}')


def _extract_ranked_keywords(chinese: str, english: str, target_lang: str = 'chinese',
                              exclude: list[str] | None = None) -> list[str]:
    """
    调用 DeepSeek 从句子中提取 3 个核心关键词，按重要性从高到低排序。
    target_lang='chinese' 返回中文关键词，'english' 返回英文关键词。
    exclude: 需要避免的关键词列表（刷新时使用）。
    失败时返回空列表，由调用方自行兜底。
    """
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
    if not api_key:
        return []

    lang_hint = '用英文返回' if target_lang == 'english' else '用中文返回'
    exclude_hint = ''
    if exclude:
        exclude_hint = (
            f'\n注意：以下关键词已经使用过，请返回与它们完全不同的新关键词'
            f'（至少 2 个与以下词语不同）：{", ".join(exclude)}\n'
        )
    prompt = (
        f'你是一个专业的图片搜索助手。请从以下句子中提取 3 个最能代表句子核心内容的关键词，'
        f'按重要性从高到低排序。{lang_hint}，每词一行，不要序号，不要其他内容。'
        + exclude_hint
        + f'\n排序优先级规则（从高到低）：\n'
        f'1. 语法成分优先级：主语 > 宾语 > 谓语 > 其他成分\n'
        f'2. 语言单位优先级：词语 > 词组 > 短语\n'
        f'3. 优先选择具体、可视化的名词，避免抽象词和虚词\n\n'
        f'句子：{chinese}\n翻译：{english}'
    )
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个图片搜索关键词助手，只输出关键词。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.1,
        'max_tokens': 256,
    }
    body = _call_deepseek_api(api_key, base_url, payload)
    if body is None:
        return []

    try:
        content = body['choices'][0]['message']['content'].strip()
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        # 去掉可能的序号前缀（如 "1. 词" 或 "1、词"）
        import re as _re
        keywords = []
        for line in lines[:3]:
            line = _re.sub(r'^[\d]+[.、\)\s]*', '', line).strip()
            if line:
                keywords.append(line)
        return keywords[:3]
    except Exception:
        return []
