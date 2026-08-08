import json
from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.safestring import mark_safe
from .models import CourseCategory, Course, Chapter, Lesson, LearningContent, Exercise, UserCourseEnrollment, UserLessonProgress
from .utils import get_available_dicts


# ---- 练习题的自定义表单 ----
class ExerciseAdminForm(forms.ModelForm):
    """将 question 的 JSON 拆分为三个普通文本字段"""

    chinese = forms.CharField(
        label='中文句子', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'style': 'width:500px;font-size:14px;'}),
        help_text='输入中文句子，如：今天天气很好。'
    )
    pinyin = forms.CharField(
        label='拼音', required=False,
        widget=forms.TextInput(attrs={'style': 'width:500px;font-size:14px;'}),
        help_text='带声调的拼音，如：jīntiān tiānqì hěn hǎo。'
    )
    english = forms.CharField(
        label='英文翻译', required=False,
        widget=forms.TextInput(attrs={'style': 'width:500px;font-size:14px;'}),
        help_text='英文翻译，如：The weather is nice today。'
    )

    selected_dicts = forms.MultipleChoiceField(
        label='启用自定义词库',
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=''
    )

    _pending_keywords = forms.CharField(
        required=False, widget=forms.HiddenInput,
        label=''
    )

    _auto_image_btn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'display:none;'}),
        label='自动配图'
    )

    class Meta:
        model = Exercise
        fields = '__all__'

    class Media:
        css = {'all': ['admin/css/word_analysis.css', 'plugins/sweetalert/sweetalert2.min.css', 'plugins/font-awesome-7pro/css/all.css']}
        js = ['plugins/sweetalert/sweetalert2.min.js']
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 question JSON 中提取数据填入独立字段
        if self.instance.pk and self.instance.sentences:
            try:
                q = json.loads(self.instance.sentences)
                self.fields['chinese'].initial = q.get('chinese', '')
                self.fields['pinyin'].initial = q.get('pinyin', '')
                self.fields['english'].initial = q.get('english', '')
            except (json.JSONDecodeError, TypeError):
                pass
        # 填充自定义词库选项
        dict_files = get_available_dicts()
        if dict_files:
            self.fields['selected_dicts'].choices = [
                (d['name'], d['label']) for d in dict_files
            ]
            dict_help = '勾选要启用的词库文件，分词时优先匹配自定义词库中的词语'
        else:
            self.fields['selected_dicts'].choices = []
            dict_help = '暂无词库文件，请将 .txt 文件放入 static/dicts/ 目录'
        # 追加词库上传 + 自动分词配图按钮
        self.fields['selected_dicts'].help_text = mark_safe(dict_help
          # ---- 上传词库区域 ----
          + '<div class="d-flex gap-2 align-items-center flex-wrap mt-2">'
          + '<input type="file" id="_dictFileInput" accept=".txt" class="d-none">'
          + '<input type="text" id="_dictFileName" class="form-control form-control-md" readonly placeholder="未选择文件" style="width:200px;flex:none;display:inline-block;">'
          + '<button type="button" id="_btnBrowseDict" class="btn btn-outline-secondary btn-md"><i class="fas fa-folder-open"></i> 浏览</button>'
          + '<button type="button" id="_btnUploadDict" class="btn btn-success btn-md"><i class="fas fa-upload"></i> 上传</button>'
          + '</div>'
          # ---- 自动分词按钮 ----
          + '<div class="d-flex gap-2 align-items-center flex-wrap mt-2">'
          + '<button type="button" id="_btnAutoSegment" class="btn btn-primary btn-md"><i class="fas fa-cogs"></i> 自动分词</button>'
          + '<span id="_autoStatus" class="text-muted" style="font-size:16px;"></span>'
          + '</div>'
          + '<script>'
          + '(function(){'
          # ---- 强制左对齐 ----
          + "var p=document.querySelector('.form-row.field-selected_dicts>div');if(p){p.style.marginLeft='0';p.style.paddingLeft='0';}"
          + "var hl=document.querySelector('.form-row.field-selected_dicts .help');if(hl){hl.style.marginLeft='0';hl.style.paddingLeft='0';}"
          # ---- 上传词库功能 ----
          + "var fi=document.getElementById('_dictFileInput');"
          + "var ft=document.getElementById('_dictFileName');"
          + "var fb=document.getElementById('_btnBrowseDict');"
          + "var fu=document.getElementById('_btnUploadDict');"
          + "if(fb){fb.onclick=function(){fi.click();};}"
          + "if(fi){fi.onchange=function(){if(fi.files&&fi.files[0])ft.value=fi.files[0].name;else ft.value='';};}"
          + "if(fu){fu.onclick=function(){"
          + "if(!fi||!fi.files||!fi.files[0]){Swal.fire({icon:'warning',title:'请选择文件',text:'请先点击浏览选择要上传的 .txt 词库文件',confirmButtonColor:'#20c997'});return;}"
          + "var fd=new FormData();fd.append('file',fi.files[0]);"
          + "var csrf=document.querySelector('[name=csrfmiddlewaretoken]');"
          + "var token=csrf?csrf.value:'';"
          + "fu.disabled=true;fu.innerHTML='<i class=\"fas fa-spinner fa-spin\"></i> 上传中...';"
          + "fetch('/admin/courseApp/exercise/upload_dict/',{method:'POST',headers:{'X-CSRFToken':token},body:fd})"
          + ".then(function(r){return r.json();}).then(function(d){"
          + "if(d.success){"
          + "Swal.fire({icon:'success',title:'上传成功',text:'词库文件「'+d.filename+'」已上传到服务器',confirmButtonColor:'#20c997'}).then(function(){fetch('/admin/courseApp/exercise/list_dicts/').then(function(r){return r.json();}).then(function(fd){var ul=document.getElementById('id_selected_dicts');if(ul&&fd.dicts){ul.innerHTML=fd.dicts.map(function(x){return '<li><label><input type=\"checkbox\" name=\"selected_dicts\" value=\"'+x.name+'\"> '+x.label+'</label></li>';}).join('');}});});"
          + "}else{"
          + "Swal.fire({icon:'error',title:'上传失败',text:d.error||'未知错误',confirmButtonColor:'#20c997'});"
          + "fu.disabled=false;fu.innerHTML='<i class=\"fas fa-upload\"></i> 上传';"
          + "}"
          + "}).catch(function(e){"
          + "Swal.fire({icon:'error',title:'网络错误',text:'请求失败: '+e,confirmButtonColor:'#20c997'});"
          + "fu.disabled=false;fu.innerHTML='<i class=\"fas fa-upload\"></i> 上传';"
          + "});"
          + "};}"
          # ---- 自动分词配图按钮 ----
          + "var btn=document.getElementById('_btnAutoSegment');"
          + "if(!btn||btn._as)return;btn._as=1;"
          + "var CB='#20c997';"
          + "btn.onclick=function(){"
          + "var chinese=document.getElementById('id_chinese');"
          + "var pinyin=document.getElementById('id_pinyin');"
          + "var english=document.getElementById('id_english');"
          + "if(!chinese||!pinyin||!english){Swal.fire({icon:'error',title:'页面错误',text:'表单字段未加载完成',confirmButtonColor:CB});return;}"
          + "var cv=chinese.value.trim(),pv=pinyin.value.trim(),ev=english.value.trim();"
          + "if(!cv||!pv||!ev){Swal.fire({icon:'warning',title:'内容不完整',text:'请先完整填写中文句子、拼音和英文翻译三项内容',confirmButtonColor:CB});return;}"
          + "var dicts=[];document.querySelectorAll('[name=\"selected_dicts\"]:checked').forEach(function(cb){dicts.push(cb.value);});"
          + "var st=document.getElementById('_autoStatus');"
          + "if(!btn._started){btn._started=1;"
          + "btn.disabled=true;btn.innerHTML='<i class=\"fas fa-spinner fa-spin\"></i> 分析中...';"
          + "var step=1;var colors=['#2563eb','#f59e0b','#ef4444','#8b5cf6'];"
          + "function setSt(t){if(st){st.innerHTML='<span style=\"color:'+colors[(step-1)%4]+';\">⏳</span> '+t;}}"
          + "setSt('连接服务器...');step=2;"
          + "var t1=setTimeout(function(){setSt('DeepSeek AI 分析中（约10-30秒）...');step=3;},3000);"
          + "var t2=setTimeout(function(){setSt('AI 分析较慢，请耐心等待...');step=4;},15000);"
          + "var t3=setTimeout(function(){setSt('仍在处理中，后台正在努力...');step=5;},35000);"
          + "var csrf=document.querySelector('[name=csrfmiddlewaretoken]');"
          + "var token=csrf?csrf.value:'';"
          + "if(!token){var m=document.querySelector('input[name=csrfmiddlewaretoken]');if(m)token=m.value;}"
          + "var exId=window.location.pathname.match(/\\/exercise\\/(\\d+)\\//);"
          + "var exerciseId=exId?exId[1]:null;"
          + "fetch('/admin/courseApp/exercise/auto_analyze/',{"
          + "method:'POST',"
          + "headers:{'Content-Type':'application/json','X-CSRFToken':token},"
          + "body:JSON.stringify({chinese:cv,pinyin:pv,english:ev,dicts:dicts,exercise_id:exerciseId,engine:(function(){var r=document.querySelector('input[name=_imgEngine]:checked');return r?r.value:'baidu';})()})"
          + "}).then(function(r){clearTimeout(t1);clearTimeout(t2);clearTimeout(t3);return r.json();}).then(function(d){"
          + "if(d.error){Swal.fire({icon:'error',title:'分析失败',text:d.error,confirmButtonColor:CB});btn.disabled=false;btn.innerHTML='<i class=\"fas fa-cogs\"></i> 自动分词';if(st)st.textContent='';delete btn._started;return;}"
          + "if(st)st.innerHTML='<span style=\"color:#20c997;\">✅</span> 分析完成，正在填入数据...';"
          + "if(d.word_analysis){fillWordAnalysis(d.word_analysis);}"
          + "var gh=document.getElementById('id_grammar_hint');if(gh&&d.grammar_hint)gh.value=d.grammar_hint;"
          + "if(d.keywords&&d.keywords.length){var k1=document.getElementById('_imgKw1');var k2=document.getElementById('_imgKw2');var k3=document.getElementById('_imgKw3');if(k1)k1.value=d.keywords[0]||'';if(k2)k2.value=d.keywords[1]||'';if(k3)k3.value=d.keywords[2]||'';}"
          + "Swal.fire({icon:'success',title:'分析完成',text:'逐词分析、语法提示已填入，配图请点击多媒体区域的【自动配图】',confirmButtonColor:CB});"
          + "btn.disabled=false;btn.innerHTML='<i class=\"fas fa-cogs\"></i> 自动分词';delete btn._started;"
          + "}).catch(function(e){clearTimeout(t1);clearTimeout(t2);clearTimeout(t3);Swal.fire({icon:'error',title:'请求失败',text:'网络错误，请重试。详情: '+String(e),confirmButtonColor:CB});btn.disabled=false;btn.innerHTML='<i class=\"fas fa-cogs\"></i> 自动分词';if(st)st.textContent='';delete btn._started;});"
          + "}"
          + "};"
          + "function fillWordAnalysis(data){"
          + "if(!Array.isArray(data)||!data.length)return;"
          + "var ta=document.getElementById('id_word_analysis');"
          + "if(!ta)return;"
          + "ta.value=JSON.stringify(data,null,2);"
          + "var w=document.getElementById('_waWrap');"
          + "if(!w)return;"
          + "var oldTbl=w.querySelector('table');if(oldTbl)oldTbl.remove();"
          + "var oldBtn=w.querySelector('button');if(oldBtn&&oldBtn.textContent.includes('添加'))oldBtn.remove();"
          + "var L2=[{k:'word',l:'词语'},{k:'pinyin',l:'拼音'},{k:'english',l:'英文'},{k:'pos',l:'词性'},{k:'grammar',l:'语法成分'}];"
          + "var tbl=document.createElement('table');tbl.style.cssText='border-collapse:collapse;margin-bottom:6px;width:100%;';"
          + "var hd=tbl.createTHead().insertRow();"
          + "L2.forEach(function(o){var th=document.createElement('th');th.textContent=o.l;th.style.cssText='padding:6px 8px;font-size:12px;font-weight:700;border-bottom:2px solid #ddd;text-align:left;white-space:nowrap;';hd.appendChild(th);});"
          + "var thd=document.createElement('th');thd.textContent='删';thd.style.cssText='padding:6px 8px;font-size:12px;font-weight:700;border-bottom:2px solid #ddd;width:40px;text-align:center;';hd.appendChild(thd);"
          + "var tb=tbl.createTBody();"
          + "function sync2(){var out=[];tb.querySelectorAll('tr').forEach(function(tr){var obj={};L2.forEach(function(o,i){var inp=tr.cells[i].querySelector('input');if(inp&&inp.value.trim())obj[o.k]=inp.value.trim();});if(Object.keys(obj).length)out.push(obj);});ta.value=JSON.stringify(out,null,2);}"
          + "function addRow2(it){var tr=document.createElement('tr');L2.forEach(function(o,i){var td=document.createElement('td');td.style.cssText='padding:3px 4px;vertical-align:middle;';var inp=document.createElement('input');inp.type='text';inp.placeholder=o.l;inp.value=it[o.k]||'';inp.style.cssText='width:100%;padding:4px 6px;border:1px solid #ddd;border-radius:3px;font-size:12px;box-sizing:border-box;';inp.oninput=sync2;td.appendChild(inp);tr.appendChild(td);});var td=document.createElement('td');td.style.cssText='padding:3px 4px;vertical-align:middle;text-align:center;';var db=document.createElement('button');db.type='button';db.textContent='x';db.style.cssText='border:none;background:#e74c3c;color:#fff;cursor:pointer;font-size:12px;padding:2px 10px;border-radius:4px;';db.onclick=function(){tr.remove();sync2();};td.appendChild(db);tr.appendChild(td);tb.appendChild(tr);}"
          + "data.forEach(addRow2);"
          + "var addBtn=document.createElement('button');addBtn.type='button';addBtn.textContent='+ 添加一行';"
          + "addBtn.style.cssText='padding:5px 16px;border-radius:4px;border:none;background:#20c997;color:#fff;cursor:pointer;font-size:12px;margin-top:4px;';"
          + "addBtn.onclick=function(){addRow2({});sync2();};"
          + "w.insertBefore(tbl,w.querySelector('div')||null);w.appendChild(addBtn);sync2();"
          + "}"
          + "window.fillKeywords=function(chinese,english,engine){"
          + "if(!engine){var r=document.querySelector('input[name=_imgEngine]:checked');engine=r?r.value:'baidu';}"
          + "var csrf=document.querySelector('[name=csrfmiddlewaretoken]');"
          + "var token=csrf?csrf.value:'';"
          + "if(!token){var m=document.querySelector('input[name=csrfmiddlewaretoken]');if(m)token=m.value;}"
          + "fetch('/admin/courseApp/exercise/extract_keywords/',{"
          + "method:'POST',"
          + "headers:{'Content-Type':'application/json','X-CSRFToken':token},"
          + "body:JSON.stringify({chinese:chinese,english:english,engine:engine})"
          + "}).then(function(r){return r.json();}).then(function(d){"
          + "if(d.keywords&&d.keywords.length){"
          + "var k1=document.getElementById('_imgKw1');var k2=document.getElementById('_imgKw2');var k3=document.getElementById('_imgKw3');"
          + "if(k1)k1.value=d.keywords[0]||'';if(k2)k2.value=d.keywords[1]||'';if(k3)k3.value=d.keywords[2]||'';"
          + "}"
          + "});"
          + "}"
          + '})();'
          + '</script>'
        )

        # ---- 自动配图区域（关键词输入 + 引擎选择 + 按钮）----
        self.fields['_auto_image_btn'].help_text = mark_safe(
          # ---- 关键词输入框 ----
          '<div class="row g-1 align-items-center mt-1">'
          + '<div class="col-auto"><label class="col-form-label fw-semibold">配图关键词：</label></div>'
          + '<div class="col-auto"><input type="text" id="_imgKw1" placeholder="关键词1" class="form-control" autocomplete="off" style="width:140px;"></div>'
          + '<div class="col-auto"><input type="text" id="_imgKw2" placeholder="关键词2" class="form-control" autocomplete="off" style="width:140px;"></div>'
          + '<div class="col-auto"><input type="text" id="_imgKw3" placeholder="关键词3" class="form-control" autocomplete="off" style="width:140px;"></div>'
          + '</div>'
          # ---- 引擎单选框（btn-check 胶囊按钮样式）----
          + '<div class="row g-1 align-items-center mt-1">'
          + '<div class="col-auto"><label class="col-form-label col-form-label-sm fw-semibold">配图引擎：</label></div>'
          + '<div class="col-auto"><div class="btn-group" role="group" aria-label="配图引擎">'
          + '<input type="radio" class="btn-check" name="_imgEngine" id="_imgEngUnsplash" value="unsplash" autocomplete="off"><label class="btn btn-outline-secondary" for="_imgEngUnsplash"><i class="fas fa-globe-americas"></i> Unsplash</label>'
          + '<input type="radio" class="btn-check" name="_imgEngine" id="_imgEngBaidu" value="baidu" checked autocomplete="off"><label class="btn btn-outline-secondary" for="_imgEngBaidu"><i class="fas fa-search"></i> 百度搜图</label>'
          + '<input type="radio" class="btn-check" name="_imgEngine" id="_imgEngBing" value="bing" autocomplete="off"><label class="btn btn-outline-secondary" for="_imgEngBing"><i class="fas fa-search"></i> 必应搜图</label>'
          + '<input type="radio" class="btn-check" name="_imgEngine" id="_imgEng360" value="360" autocomplete="off"><label class="btn btn-outline-secondary" for="_imgEng360"><i class="fas fa-search"></i> 360搜图</label>'
          + '</div></div>'
          + '</div>'
          # ---- 按钮区域（text-nowrap 防止换行）----
          + '<div class="d-flex gap-2 flex-wrap mt-1">'
          + '<button type="button" id="_btnRefreshKeywords" class="btn btn-outline-secondary btn-md text-nowrap"><i class="fas fa-sync-alt"></i> 刷新关键词</button>'
          + '<button type="button" id="_btnAutoImage" class="btn btn-info btn-md text-nowrap"><i class="fas fa-search"></i> 检索配图</button>'
          + '<button type="button" id="_btnSaveImage" class="btn btn-success btn-md text-nowrap d-inline-flex align-items-center gap-1" style="display:none;"><i class="fa-regular fa-floppy-disk"></i> 保存配图</button>'
          + '<button type="button" id="_btnCleanupImages" class="btn btn-outline-danger btn-md text-nowrap"><i class="fas fa-trash-alt"></i> 清理垃圾</button>'
          + '</div>'
          # ---- 追踪标签独立一行 ----
          + '<div id="_imgStatus" class="d-flex flex-wrap gap-2 align-items-center text-muted mt-1" style="font-size:16px;"></div>'
          + '<div id="_imgGallery" class="row g-2 mt-2" style="display:none;"></div>'
          + '<script>'
          + '(function(){'
          + "var ai2=document.querySelector('.form-row.field-_auto_image_btn>div');if(ai2){ai2.style.marginLeft='0';ai2.style.paddingLeft='0';}"
          + "var ai3=document.querySelector('.form-row.field-_auto_image_btn .help');if(ai3){ai3.style.marginLeft='0';ai3.style.paddingLeft='0';}"
          + "function getEngine(){var r=document.querySelector('input[name=_imgEngine]:checked');return r?r.value:'baidu';}"
          + "function getKw(){var k1=document.getElementById('_imgKw1');var k2=document.getElementById('_imgKw2');var k3=document.getElementById('_imgKw3');return[(k1?k1.value.trim():''),(k2?k2.value.trim():''),(k3?k3.value.trim():'')];}"
          + "function setKw(v1,v2,v3){var k1=document.getElementById('_imgKw1');var k2=document.getElementById('_imgKw2');var k3=document.getElementById('_imgKw3');if(k1)k1.value=v1;if(k2)k2.value=v2;if(k3)k3.value=v3;}"
          # ---- 图片预览更新函数 ----
          + "function upPreview(url){var isTemp=url.indexOf('blob:')===0||url.indexOf('data:')===0;var suffix=(!isTemp&&url.indexOf('?')<0)?'?_t='+Date.now():'';var ip=document.querySelector('.imgPreview');if(ip){ip.src=url+suffix;ip.style.display='';}}"
          # ---- 三处同步刷新：预览框 + 目前:链接 + 修改:文件输入框 ----
          + "function refreshImageInfo(url,filename){"
          + "if(url){upPreview(url);}"
          + "var link=document.querySelector('.field-image a');if(link){link.href=url||'#';link.textContent=filename||(url||'无图片');}"
          + "}"
          + "var _imgList=[],_selIdx=0,_pending={file:null,url:null};function showGallery(imgs,sel){_imgList=imgs||[];_selIdx=sel||0;var g=document.getElementById('_imgGallery');if(!g)return;if(!_imgList.length){g.style.display='none';g.innerHTML='';return;}var h='';for(var i=0;i<_imgList.length;i++){var a=i===_selIdx?' border-success':' border';h+='<div class=\"col-4 col-md-3 col-lg-2\"><div class=\"card card-sm'+a+'\" style=\"cursor:pointer;overflow:hidden\" data-i=\"'+i+'\"><img src=\"'+_imgList[i]+'\" class=\"card-img-top\" style=\"width:100%;aspect-ratio:16/9;object-fit:cover;display:block\"></div></div>';}g.innerHTML=h;g.style.display='';}"
          # ---- 页面加载时清空关键词输入框（防止浏览器缓存导致上一题的关键词残留）----
          + "var _ik1=document.getElementById('_imgKw1');var _ik2=document.getElementById('_imgKw2');var _ik3=document.getElementById('_imgKw3');if(_ik1)_ik1.value='';if(_ik2)_ik2.value='';if(_ik3)_ik3.value='';"
          + "var rk=document.getElementById('_btnRefreshKeywords');if(rk){rk.onclick=function(){"
          + "var ch=document.getElementById('id_chinese');var en=document.getElementById('id_english');var cv=(ch?ch.value.trim():'');var ev=(en?en.value.trim():'');"
          + "if(!cv){Swal.fire({icon:'warning',title:'请先填写中文句子',text:'需要中文句子来提取配图关键词',confirmButtonColor:'#20c997'});return;}"
          + "var curr=getKw();var exclude=curr.filter(Boolean);"
          + "var csrf=document.querySelector('[name=csrfmiddlewaretoken]');var token=csrf?csrf.value:'';if(!token){var m=document.querySelector('input[name=csrfmiddlewaretoken]');if(m)token=m.value;}"
          + "rk.disabled=true;rk.innerHTML='<i class=\"fas fa-spinner fa-spin\"></i> 刷新中...';"
          + "fetch('/admin/courseApp/exercise/extract_keywords/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':token},body:JSON.stringify({chinese:cv,english:ev,engine:getEngine(),exclude:exclude,is_refresh:true})})"
          + ".then(function(r){return r.json();}).then(function(d){"
          + "rk.disabled=false;rk.innerHTML='<i class=\"fas fa-sync-alt\"></i> 刷新关键词';"
          + "if(d.keywords&&d.keywords.length){setKw(d.keywords[0]||'',d.keywords[1]||'',d.keywords[2]||'');Swal.fire({icon:'success',title:'关键词已刷新',text:'新关键词: '+d.keywords.join(', '),confirmButtonColor:'#20c997',timer:1500});}"
          + "else{Swal.fire({icon:'warning',title:'刷新失败',text:d.error||'无法获取新关键词',confirmButtonColor:'#20c997'});}"
          + "});}}"
          # ---- 清理垃圾按钮 ----
          + "var cl=document.getElementById('_btnCleanupImages');if(cl){cl.onclick=function(){"
          + "cl.disabled=true;cl.innerHTML='<i class=\"fas fa-spinner fa-spin\"></i> 清理中...';"
          + "var csrf=document.querySelector('[name=csrfmiddlewaretoken]');var token=csrf?csrf.value:'';"
          + "if(!token){var m=document.querySelector('input[name=csrfmiddlewaretoken]');if(m)token=m.value;}"
          + "fetch('/admin/courseApp/exercise/cleanup_images/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':token}})"
          + ".then(function(r){return r.json();}).then(function(d){"
          + "cl.disabled=false;cl.innerHTML='<i class=\"fas fa-trash-alt\"></i> 清理垃圾';"
          + "if(d.deleted&&d.deleted.length){var msg='共清理 '+d.deleted.length+' 个垃圾文件：<br><br>'+d.deleted.map(function(f){return'<span style=\"color:#e74c3c;\">🗑️ '+f+'</span>'}).join('<br>');Swal.fire({icon:'success',title:'清理完成',html:msg,confirmButtonColor:'#20c997'});}"
          + "else{Swal.fire({icon:'info',title:'无需清理',text:'exercise_images 目录中没有垃圾图片',confirmButtonColor:'#20c997'});}"
          + "});"
          + "};}"
          + "var bi=document.getElementById('_btnAutoImage');if(!bi||bi._inited)return;bi._inited=1;"
          + "bi.onclick=function(){"
          + "var kw=getKw();var ranked=kw.filter(Boolean);"
          + "var ch=document.getElementById('id_chinese');var en=document.getElementById('id_english');var cv=(ch?ch.value.trim():'');var ev=(en?en.value.trim():'');"
          + "if(!ranked.length){Swal.fire({icon:'warning',title:'请先填写关键词',text:'配图关键词不能为空，请点击自动分词或刷新关键词',confirmButtonColor:'#20c997'});return;}"
          + "var exId=window.location.pathname.match(/\\/exercise\\/(\\d+)\\//);var exerciseId=exId?exId[1]:null;var isNew=!exerciseId;"
          + "if(isNew){var le=document.getElementById('id_lesson');if(!le||!le.value){Swal.fire({icon:'warning',title:'请先选择所属课时',text:'新建习题需要先选择所属课时',confirmButtonColor:'#20c997'});return;}}"
          + "bi.disabled=true;bi.innerHTML='<i class=\"fas fa-spinner fa-spin\"></i> 检索中...';"
          + "var st=document.getElementById('_imgStatus');if(st)st.textContent='⏳ 正在搜索配图...';"
          + "var t1=setTimeout(function(){if(st){var sb=document.createElement('span');sb.className='badge bg-light text-dark border px-2 py-1';sb.style.fontSize='14px';sb.textContent='⏳ 第1组无结果，降级中...';st.appendChild(sb);}},5000);"
          + "var t2=setTimeout(function(){if(st){var sb2=document.createElement('span');sb2.className='badge bg-light text-dark border px-2 py-1';sb2.style.fontSize='14px';sb2.textContent='⏳ 仍在努力中...';st.appendChild(sb2);}},12000);"
          + "var csrf=document.querySelector('[name=csrfmiddlewaretoken]');var token=csrf?csrf.value:'';if(!token){var m=document.querySelector('input[name=csrfmiddlewaretoken]');if(m)token=m.value;}"
          + "var payload={exercise_id:exerciseId,chinese:cv,english:ev,engine:getEngine(),kw1:ranked[0]||'',kw2:ranked[1]||'',kw3:ranked[2]||''};"
          + "if(isNew){var pi=document.getElementById('id_pinyin');var wa=document.getElementById('id_word_analysis');var gh=document.getElementById('id_grammar_hint');payload.lesson_id=document.getElementById('id_lesson').value;payload.pinyin=pi?pi.value.trim():'';payload.word_analysis=wa?wa.value:null;payload.grammar_hint=gh?gh.value:'';}"
          + "fetch('/admin/courseApp/exercise/auto_image/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':token},body:JSON.stringify(payload)})"
          + ".then(function(r){return r.json();}).then(function(d){"
          + "clearTimeout(t1);clearTimeout(t2);"
          + "var ats=d.attempts||[];"
          + "function showTimeline(idx){if(idx>=ats.length){return;}var a=ats[idx];var icon=a.found>0?'✅':'❌';var foundText=a.found>0?'找到'+a.found+'条结果':'返回0条结果';if(st){var child=document.createElement('span');child.className='badge bg-light text-dark border px-2 py-1';child.style.fontSize='14px';child.textContent=icon+' 第'+a.level+'组('+a.keywords+'): '+foundText;st.appendChild(child);}setTimeout(function(){showTimeline(idx+1);},800);}"
          + "if(d.success&&d.exercise_id){if(st)st.textContent='✅ 配图成功';window.location.href='/admin/courseApp/exercise/'+d.exercise_id+'/change/';return;}"
          + "if(d.success){bi.disabled=false;bi.innerHTML='<i class=\"fas fa-search\"></i> 检索配图';var sb=document.getElementById('_btnSaveImage');if(sb)sb.style.display='inline-flex';showTimeline(0);if(d.first_url)upPreview(d.first_url);showGallery(d.images||[],0);return;}"
          + "if(st){var eb=document.createElement('span');eb.className='badge bg-danger text-white px-2 py-1';eb.style.fontSize='14px';eb.textContent='❌ 最终失败 '+d.error;st.appendChild(eb);}showTimeline(0);setTimeout(function(){Swal.fire({icon:'error',title:'配图失败',text:d.error||'全部关键词组均无结果',confirmButtonColor:'#20c997'});},ats.length*800+500);"
          + "bi.disabled=false;bi.innerHTML='<i class=\"fas fa-search\"></i> 检索配图';"
          + "}).catch(function(e){clearTimeout(t1);clearTimeout(t2);if(st){var eb2=document.createElement('span');eb2.className='badge bg-danger text-white px-2 py-1';eb2.style.fontSize='14px';eb2.textContent='❌ 网络错误';st.appendChild(eb2);}Swal.fire({icon:'error',title:'请求失败',text:String(e),confirmButtonColor:'#20c997'});bi.disabled=false;bi.innerHTML='<i class=\"fas fa-search\"></i> 检索配图';});"
          + "};"
          # ---- 宫格图片点击选择：异步保存并刷新三处 ----
          + "document.addEventListener('click',function(e){var card=e.target.closest('[data-i]');if(!card)return;var i=parseInt(card.dataset.i);if(isNaN(i)||i>=_imgList.length)return;_selIdx=i;_pending.url=_imgList[i];_pending.file=null;refreshImageInfo(_imgList[i],'');showGallery(_imgList,i);});"
          # ---- 保存配图按钮 ----
          + "function uploadPending(){"
          + "return new Promise(function(resolve){"
          + "var exId=window.location.pathname.match(/\\/exercise\\/(\\d+)\\//);if(!exId){Swal.fire({icon:'warning',title:'请先保存习题',text:'新建习题请先点击底部保存',confirmButtonColor:'#20c997'});resolve(false);return;}"
          + "var cs=document.querySelector('[name=csrfmiddlewaretoken]');var tk=cs?cs.value:'';if(!tk){var m=document.querySelector('input[name=csrfmiddlewaretoken]');if(m)tk=m.value;}"
          + "function done(ok){if(ok){var fi=document.getElementById('id_image');if(fi)fi.value='';_pending.file=null;_pending.url=null;}resolve(ok);}"
          + "if(_pending.file){var fd=new FormData();fd.append('exercise_id',exId[1]);fd.append('file',_pending.file);fetch('/admin/courseApp/exercise/upload_image/',{method:'POST',headers:{'X-CSRFToken':tk},body:fd}).then(function(r){return r.json();}).then(function(d){if(d.success){refreshImageInfo(d.image_url,d.filename);done(true);}else{Swal.fire({icon:'error',title:'上传失败',text:d.error||'未知错误',confirmButtonColor:'#20c997'});done(false);}}).catch(function(e){Swal.fire({icon:'error',title:'网络错误',text:String(e),confirmButtonColor:'#20c997'});done(false);});return;}"
          + "if(_pending.url){fetch('/admin/courseApp/exercise/save_image_url/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':tk},body:JSON.stringify({exercise_id:exId[1],image_url:_pending.url})}).then(function(r){return r.json();}).then(function(d){if(d.success){refreshImageInfo(d.image_url,d.filename);done(true);}else{Swal.fire({icon:'error',title:'保存失败',text:d.error||'未知错误',confirmButtonColor:'#20c997'});done(false);}}).catch(function(e){Swal.fire({icon:'error',title:'网络错误',text:String(e),confirmButtonColor:'#20c997'});done(false);});return;}"
          + "done(true);"
          + "});}"
          + "var saveBtn=document.getElementById('_btnSaveImage');if(saveBtn){saveBtn.onclick=function(){"
          + "if(!_pending.file&&!_pending.url){Swal.fire({icon:'warning',title:'请先选择图片',text:'请先从宫格选择或从本地选择图片后再保存配图',confirmButtonColor:'#20c997'});return;}"
          + "saveBtn.disabled=true;saveBtn.innerHTML='<i class=\"fas fa-spinner fa-spin\"></i> 保存中...';"
          + "uploadPending().then(function(ok){saveBtn.disabled=false;saveBtn.innerHTML='<i class=\"fa-regular fa-floppy-disk\"></i> 保存配图';if(ok)Swal.fire({icon:'success',title:'保存成功',text:'图片已保存到服务器',confirmButtonColor:'#20c997',timer:1500});});"
          + "};}"
          # ---- 场景2：选择文件按钮上传图片并刷新 ----
          + "var fileInput=document.getElementById('id_image');if(fileInput){fileInput.addEventListener('change',function(){"
          + "if(!fileInput.files||!fileInput.files[0])return;"
          + "var file=fileInput.files[0];var tmpUrl=URL.createObjectURL(file);_pending.file=file;_pending.url=tmpUrl;refreshImageInfo(tmpUrl,file.name);"
          + "});}"
          # ---- 整页保存：若存在暂存图片，先上传再提交表单 ----
          + "var exForm=document.querySelector('#courseapp_exercise_form');if(!exForm)exForm=document.querySelector('.change-form form');if(exForm){exForm.addEventListener('submit',function(e){if(_pending.file||_pending.url){e.preventDefault();uploadPending().then(function(ok){if(ok){if(exForm.requestSubmit)exForm.requestSubmit(e.submitter);else exForm.submit();}});}});}"
          + '})();'
          + '</script>'
        )

        # 让原始 sentences 字段隐藏，word_analysis 显示为可编辑的 JSON 文本框
        if 'sentences' in self.fields:
            self.fields['sentences'].widget = forms.HiddenInput()
            self.fields['sentences'].required = False
        if 'word_analysis' in self.fields:
            self.fields['word_analysis'].widget = forms.Textarea(attrs={
                'rows': 6, 'style': 'width:600px;font-size:13px;font-family:monospace;',
            })
            self.fields['word_analysis'].required = False
            self.fields['word_analysis'].help_text = mark_safe(
              '<style>.form-row.field-word_analysis>div{display:flex;flex-direction:column;}.form-row.field-word_analysis label{float:none;width:auto;padding-bottom:4px;}.form-row.field-word_analysis>div>*:not(label){margin-left:0!important;padding-left:0!important;}.form-row.field-word_analysis textarea,.form-row.field-word_analysis .help{margin-left:0!important;}.form-row.field-word_analysis input,.form-row.field-word_analysis textarea,.form-row.field-word_analysis select{width:100%!important;}</style>'
              '<div id="_waWrap" style="margin:0;padding:0;width:100%;"></div>'
              '<script>'
              '(function(){'
              +"var ta=document.getElementById('id_word_analysis');"
              +"if(!ta||ta._war)return;ta._war=1;"
              +"ta.style.display='none';"
              +"var w=document.getElementById('_waWrap');if(!w)return;"
              +"var F=['word','pinyin','english','pos','grammar'];"
              +"var L=[{k:'word',l:'词语'},{k:'pinyin',l:'拼音'},{k:'english',l:'英文'},{k:'pos',l:'词性'},{k:'grammar',l:'语法成分'}];"
              +"var tbl=document.createElement('table');tbl.style.cssText='border-collapse:collapse;margin-bottom:6px;width:100%;';"
              +"var hd=tbl.createTHead().insertRow();"
              +"L.forEach(function(o){var th=document.createElement('th');th.textContent=o.l;th.style.cssText='padding:6px 8px;font-size:12px;font-weight:700;border-bottom:2px solid #ddd;text-align:left;white-space:nowrap;';hd.appendChild(th);});"
              +"var thd=document.createElement('th');thd.textContent='删';thd.style.cssText='padding:6px 8px;font-size:12px;font-weight:700;border-bottom:2px solid #ddd;width:40px;text-align:center;';hd.appendChild(thd);"
              +"var tb=tbl.createTBody();"
              +"var data=[];try{data=JSON.parse(ta.value||'[]');}catch(e){}if(!Array.isArray(data))data=[];data.forEach(function(d){if(d.meaning!==undefined){d.english=d.meaning;delete d.meaning;}});"
              +"function sync(){var out=[];tb.querySelectorAll('tr').forEach(function(tr){var obj={};L.forEach(function(o,i){var inp=tr.cells[i].querySelector('input');if(inp&&inp.value.trim())obj[o.k]=inp.value.trim();});if(Object.keys(obj).length)out.push(obj);});ta.value=JSON.stringify(out,null,2);}"
              +"function addRow(it){var tr=document.createElement('tr');L.forEach(function(o,i){var td=document.createElement('td');td.style.cssText='padding:3px 4px;vertical-align:middle;';var inp=document.createElement('input');inp.type='text';inp.placeholder=o.l;inp.value=it[o.k]||'';inp.style.cssText='width:100%;padding:4px 6px;border:1px solid #ddd;border-radius:3px;font-size:12px;box-sizing:border-box;';inp.oninput=sync;td.appendChild(inp);tr.appendChild(td);});var td=document.createElement('td');td.style.cssText='padding:3px 4px;vertical-align:middle;text-align:center;';var db=document.createElement('button');db.type='button';db.textContent='x';db.style.cssText='border:none;background:#e74c3c;color:#fff;cursor:pointer;font-size:12px;padding:2px 10px;border-radius:4px;';db.onclick=function(){tr.remove();sync();};td.appendChild(db);tr.appendChild(td);tb.appendChild(tr);}"
              +"data.forEach(addRow);if(!data.length)addRow({});"
              +"var btn=document.createElement('button');btn.type='button';btn.textContent='+ 添加一行';"
              +"btn.style.cssText='padding:5px 16px;border-radius:4px;border:none;background:#20c997;color:#fff;cursor:pointer;font-size:12px;margin-top:4px;';"
              +"btn.onclick=function(){addRow({});sync();};"
              +"w.appendChild(tbl);w.appendChild(btn);sync();"
              +'})();'
              +'</script>'
            )

    def clean(self):
        cleaned = super().clean()
        chinese = cleaned.get('chinese', '')
        pinyin = cleaned.get('pinyin', '')
        english = cleaned.get('english', '')
        # 三个字段均为空（如 list_editable 列表页仅提交 sort_order）→ 不覆盖原有 sentences
        if not any([chinese, pinyin, english]):
            cleaned.pop('sentences', None)
            return cleaned
        # 自动构造 question JSON
        q = {}
        if chinese:
            q['chinese'] = chinese
        if pinyin:
            q['pinyin'] = pinyin
        if english:
            q['english'] = english
        cleaned['sentences'] = json.dumps(q, ensure_ascii=False)
        return cleaned

    def save(self, commit=True):
        """保存时确保 sentences 字段与 chinese/pinyin/english 同步"""
        instance = super().save(commit=False)
        chinese = self.cleaned_data.get('chinese', '')
        pinyin = self.cleaned_data.get('pinyin', '')
        english = self.cleaned_data.get('english', '')
        # 三个字段均为空（list_editable 场景）→ 保留原有 sentences
        if any([chinese, pinyin, english]):
            q = {}
            if chinese: q['chinese'] = chinese
            if pinyin: q['pinyin'] = pinyin
            if english: q['english'] = english
            instance.sentences = json.dumps(q, ensure_ascii=False)
        if commit:
            instance.save()
            self._save_m2m()
        return instance


# ---- 练习题管理 ----
@admin.register(Exercise)
class ExerciseAdmin(ModelAdmin):
    form = ExerciseAdminForm
    list_display = ['sort_order', 'short_chinese', 'lesson', 'id', 'has_image', 'has_audio']
    list_display_links = ['short_chinese']
    list_filter = ['lesson__chapter__course']
    search_fields = ['sentences']
    list_editable = ['sort_order']
    readonly_fields = ['image_preview']

    fieldsets = [
        ('基本信息', {'fields': ['lesson', 'sort_order']}),
        ('句子内容', {'fields': ['chinese', 'pinyin', 'english']}),
        ('自定义词库', {'fields': ['selected_dicts'], 'classes': ['wide'], 'description': '勾选要启用的自定义分词词库，自动分词时将优先匹配'}),
        ('多媒体资源', {'fields': ['image', 'image_preview', 'audio_url', '_auto_image_btn'], 'classes': ['wide']}),
        ('语法提示', {'fields': ['grammar_hint']}),
        ('逐词分析', {'fields': ['word_analysis'], 'classes': ['wide']}),
    ]

    def save_model(self, request, obj, form, change):
        """保存时确保 sentences 字段与 chinese/pinyin/english 同步"""
        chinese = form.cleaned_data.get('chinese', '')
        pinyin = form.cleaned_data.get('pinyin', '')
        english = form.cleaned_data.get('english', '')
        # 三个字段均为空（list_editable 场景）→ 保留原有 sentences
        if any([chinese, pinyin, english]):
            q = {}
            if chinese: q['chinese'] = chinese
            if pinyin: q['pinyin'] = pinyin
            if english: q['english'] = english
            obj.sentences = json.dumps(q, ensure_ascii=False)
        obj.save()

    def short_chinese(self, obj):
        try:
            q = json.loads(obj.sentences)
            return q.get('chinese', '')[:40]
        except (json.JSONDecodeError, TypeError):
            return str(obj.sentences)[:40]
    short_chinese.short_description = '中文句子'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = '图片'

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img class="imgPreview" src="{obj.image.url}" style="max-width:300px;max-height:180px;border-radius:8px;border:1px solid #ddd;object-fit:cover;">')
        return mark_safe('<img class="imgPreview" src="" style="display:none;max-width:300px;max-height:180px;border-radius:8px;border:1px solid #ddd;object-fit:cover;"><span>— 无图片 —</span>')
    image_preview.short_description = '图片预览'

    def has_audio(self, obj):
        return bool(obj.audio_url)
    has_audio.boolean = True
    has_audio.short_description = '音频'


# ---- 其他模型注册 ----
@admin.register(CourseCategory)
class CourseCategoryAdmin(ModelAdmin):
    list_display = ['id', 'name', 'parent', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ['id', 'name', 'category', 'teacher', 'difficulty', 'is_published', 'is_free', 'price', 'heat', 'sort_order']
    list_filter = ['is_published', 'is_free', 'difficulty', 'category']
    search_fields = ['name', 'subtitle']


@admin.register(Chapter)
class ChapterAdmin(ModelAdmin):
    list_display = ['id', 'name', 'course', 'sort_order']
    list_filter = ['course']
    search_fields = ['name']


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ['id', 'name', 'chapter', 'content_type_summary', 'exercise_count', 'duration', 'is_trial', 'sort_order']
    list_filter = ['is_trial', 'chapter__course']
    search_fields = ['name']

    def content_type_summary(self, obj):
        types = obj.contents.values_list('content_type', flat=True).distinct()
        return ', '.join(types) if types else '—'
    content_type_summary.short_description = '内容类型'

    def exercise_count(self, obj):
        return obj.exercises.count()
    exercise_count.short_description = '练习题数'


@admin.register(LearningContent)
class LearningContentAdmin(ModelAdmin):
    list_display = ['id', 'lesson', 'content_type', 'title', 'sort_order']
    list_filter = ['content_type']
    fields = ['lesson', 'content_type', 'title', 'content_display', 'sort_order']
    readonly_fields = ['content_display']

    def content_display(self, obj):
        if obj.content:
            return mark_safe(f'<pre style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:12px;line-height:1.5;max-height:400px;overflow:auto;">{json.dumps(obj.content, ensure_ascii=False, indent=2)}</pre>')
        return '—'
    content_display.short_description = '内容数据（只读）'



@admin.register(UserCourseEnrollment)
class UserCourseEnrollmentAdmin(ModelAdmin):
    list_display = ['id', 'user', 'course', 'is_completed', 'progress', 'enrolled_at']
    list_filter = ['is_completed']


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(ModelAdmin):
    list_display = ['id', 'user', 'lesson', 'is_completed', 'score', 'last_studied_at']
    list_filter = ['is_completed']
