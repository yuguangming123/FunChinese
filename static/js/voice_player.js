/**
 * 汉语语音播放器（含频谱可视化）
 * 使用阿里云 Qwen3-TTS 后端服务
 */
var VoicePlayer = {
  speaking: false,
  autoPlay: true,
  currentAudio: null,
  ttsUrl: '/practiceApp/api/tts/',
  audioContext: null,
  analyser: null,
  sourceNode: null,
  canvasAnimId: null,

  speak: function(text, opts) {
    if (!text) return;
    opts = opts || {};
    this.stop();

    var self = this;
    var selectedVoice = localStorage.getItem('qwen3_voice') || 'Cherry';
    // 兼容旧版本音色名称（CosyVoice → Qwen3）
    var oldVoices = ['longanyang','longanhuan','longhuhu_v3','longfei_v3','longpaopao_v3','longjielidou_v3','longxian_v3','longling_v3','longshanshan_v3','longniuniu_v3','longjiaxin_v3','longjiayi_v3','longanyue_v3','longlaotie_v3','longshange_v3','longanmin_v3','loongabby','loongandy'];
    if (oldVoices.indexOf(selectedVoice) >= 0) {
        selectedVoice = 'Cherry';
        localStorage.setItem('qwen3_voice', 'Cherry');
    }
    var selectedSpeed = localStorage.getItem('qwen3_speed') || '1.0';
    var selectedVolume = localStorage.getItem('qwen3_volume') || '0.8';
    var selectedEmotion = localStorage.getItem('qwen3_emotion') || '';
    var repeatCount = parseInt(localStorage.getItem('qwen3_repeat') || '1');
    var repeatInterval = parseFloat(localStorage.getItem('qwen3_interval') || '1.0');
    var playCount = 0;

    function playOnce() {
        var url = self.ttsUrl + '?text=' + encodeURIComponent(text) + '&voice=' + selectedVoice + '&speed=' + selectedSpeed + '&volume=' + selectedVolume + '&emotion=' + encodeURIComponent(selectedEmotion);
        var audio = new Audio(url);
        self.currentAudio = audio;
        self.speaking = true;

        if (playCount === 0 && typeof opts.onStart === 'function') opts.onStart();

        audio.onended = function() {
            playCount++;
            if (playCount < repeatCount) {
                setTimeout(function() { playOnce(); }, repeatInterval * 1000);
            } else {
                self.speaking = false;
                self.currentAudio = null;
                if (typeof opts.onEnd === 'function') opts.onEnd();
            }
        };
        audio.onerror = function() {
            self.speaking = false;
            self.currentAudio = null;
        };
        audio.play().catch(function(e) {
            self.speaking = false;
        });
    }

    playOnce();
  },

  stop: function() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    this.speaking = false;
    if (this.canvasAnimId) {
      cancelAnimationFrame(this.canvasAnimId);
      this.canvasAnimId = null;
    }
  },

  toggleAutoPlay: function() {
    this.autoPlay = !this.autoPlay;
    return this.autoPlay;
  },

  _initAudioAnalyser: function(audio) {
    try {
      if (!this.audioContext) {
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioContext();
      }
      // 断开旧的连接
      if (this.sourceNode) {
        try { this.sourceNode.disconnect(); } catch(e) {}
      }
      // 创建 analyser
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 128;

      // 创建媒体源并连接
      this.sourceNode = this.audioContext.createMediaElementSource(audio);
      this.sourceNode.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
    } catch(e) {
      // 浏览器不支持 AudioContext，静默降级
    }
  },

  // 启动频谱绘制
  startSpectrum: function(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var self = this;
    var cwidth = canvas.width;
    var cheight = canvas.height;
    var meterWidth = 6;
    var gap = 2;
    var meterNum = Math.floor(cwidth / (meterWidth + gap));

    function draw() {
      if (!self.speaking || !self.analyser) {
        // 静止状态
        ctx.clearRect(0, 0, cwidth, cheight);
        self.canvasAnimId = requestAnimationFrame(draw);
        return;
      }
      var array = new Uint8Array(self.analyser.frequencyBinCount);
      self.analyser.getByteFrequencyData(array);
      ctx.clearRect(0, 0, cwidth, cheight);

      var step = Math.round(array.length / meterNum);
      for (var i = 0; i < meterNum; i++) {
        var value = array[i * step] || 0;
        var h = Math.min(value / 256 * cheight * 1.5, cheight);
        var x = i * (meterWidth + gap);
        // 渐变绿
        var ratio = h / cheight;
        var r = Math.round(32 + (1 - ratio) * 200);
        var g = Math.round(201 + (1 - ratio) * 50);
        var b = Math.round(151);
        ctx.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
        ctx.fillRect(x, cheight - h, meterWidth, h);
      }
      self.canvasAnimId = requestAnimationFrame(draw);
    }
    draw();
  },

  // 停止频谱绘制
  stopSpectrum: function() {
    if (this.canvasAnimId) {
      cancelAnimationFrame(this.canvasAnimId);
      this.canvasAnimId = null;
    }
  }
};
