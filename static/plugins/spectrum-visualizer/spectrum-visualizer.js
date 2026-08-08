/** SpectrumVisualizer — 实时音频频谱可视化插件 */
;(function($, window, undefined) {
  'use strict';
  var SV = {
    version: '1.2.0', canvas: null, ctx: null, audioContext: null, analyser: null, sourceNode: null, animId: null,
    options: { style: 'bars', fftSize: 128, barWidth: 6, barGap: 2, barMinHeight: 2, color: '#20c997', smoothing: 0.7 },
    isActive: false, isPlaying: false,
    init: function(o) { if (o) $.extend(this.options, o); return this; },
    setCanvas: function(el) { if (typeof el === 'string') el = document.querySelector(el); if (!el) return this; this.canvas = el; this.ctx = el.getContext('2d'); return this; },
    connectAudio: async function(audioEl) {
      try {
        if (!this.audioContext) this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (this.audioContext.state === 'suspended') await this.audioContext.resume();
        if (this.sourceNode) try { this.sourceNode.disconnect(); } catch(e) {}
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = this.options.fftSize; this.analyser.smoothingTimeConstant = this.options.smoothing;
        this.sourceNode = this.audioContext.createMediaElementSource(audioEl);
        this.sourceNode.connect(this.analyser); this.analyser.connect(this.audioContext.destination);
      } catch(e) {}
      return this;
    },
    start: function() { if (!this.animId) { this.isActive = true; this._draw(); } return this; },
    setPlaying: function(v) { this.isPlaying = v; return this; },
    setStyle: function(s) { this.options.style = s; return this; },
    getStyle: function() { return this.options.style; },
    _clearCanvas: function() { if (this.ctx) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); },
    _draw: function() {
      var self = this;
      function draw() {
        if (!self.isActive) return; self.animId = requestAnimationFrame(draw);
        var W = self.canvas.width, H = self.canvas.height, ctx = self.ctx;
        ctx.clearRect(0, 0, W, H);
        var arr = new Uint8Array(self.analyser ? self.analyser.frequencyBinCount : 64);
        if (self.isPlaying && self.analyser) {
          self.analyser.getByteFrequencyData(arr);
        } else {
          return;
        }
        var style = self.options.style || 'bars';
        if (style === 'wave') {
          var farr = new Uint8Array(self.analyser ? self.analyser.frequencyBinCount : 64);
          if (self.analyser) self.analyser.getByteFrequencyData(farr);
          self._drawWave(ctx, W, H, farr);
        } else if (style === 'circle') {
          self._drawCircle(ctx, W, H, arr);
        } else {
          self._drawBars(ctx, W, H, arr);
        }
      }
      draw();
    },
    _drawBars: function(ctx, W, H, arr) {
      var bw = 6, gap = 2, step = bw + gap, c = Math.floor(W / step), ds = Math.max(1, Math.floor(arr.length / c));
      for (var i = 0; i < c; i++) {
        var v = arr[i * ds] || 0, h = Math.max(2, (v / 255) * H * 1.2), r = h / H;
        ctx.fillStyle = 'rgb(' + Math.round(32 + (1 - r) * 200) + ',' + Math.round(201 + (1 - r) * 50) + ',151)';
        ctx.fillRect(i * step, H - h, bw, h);
      }
    },
    _drawWave: function(ctx, W, H, arr) {
      var len = arr.length, mid = H / 2;
      // 找到最后一个非静默频段（能量 > 10）
      var last = 0;
      for (var i = 0; i < len; i++) { if (arr[i] > 10) last = i; }
      if (last < 2) return;
      // 居中偏移
      var offset = (len - (last + 1)) / 2;
      ctx.beginPath();
      ctx.moveTo(0, mid);
      for (var i = 0; i <= last; i++) {
        var v = arr[i] || 0;
        var x = ((i + offset) / len) * W;
        var y = mid - (v / 255) * H * 0.45;
        ctx.lineTo(x, y);
      }
      ctx.strokeStyle = '#20c997';
      ctx.lineWidth = 2;
      ctx.stroke();
      // 渐变填充
      ctx.lineTo(W, H);
      ctx.lineTo(0, H);
      ctx.closePath();
      var grad = ctx.createLinearGradient(0, 0, 0, H);
      grad.addColorStop(0, 'rgba(32,201,151,0.12)');
      grad.addColorStop(1, 'rgba(32,201,151,0)');
      ctx.fillStyle = grad;
      ctx.fill();
    },
    _drawCircle: function(ctx, W, H, arr) {
      var cx = W / 2, cy = H / 2, rMax = Math.min(W, H) * 0.4;
      var bands = 60, step = Math.max(1, Math.floor(arr.length / bands));
      // 外圈
      ctx.beginPath();
      for (var i = 0; i <= bands; i++) {
        var v = arr[Math.min(i * step, arr.length - 1)] || 0;
        var r = rMax * 0.3 + (v / 255) * rMax * 0.7;
        var angle = (i / bands) * Math.PI * 2 - Math.PI / 2;
        var x = cx + Math.cos(angle) * r;
        var y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = '#20c997';
      ctx.lineWidth = 2;
      ctx.stroke();
      // 放射线条
      for (var i = 0; i < bands; i += 3) {
        var v = arr[Math.min(i * step, arr.length - 1)] || 0;
        var r = rMax * 0.3 + (v / 255) * rMax * 0.7;
        var angle = (i / bands) * Math.PI * 2 - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
        ctx.strokeStyle = 'rgba(32,201,151,0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      // 内圈
      ctx.beginPath();
      ctx.arc(cx, cy, rMax * 0.3, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(32,201,151,0.15)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  };
  window.SpectrumVisualizer = SV;
})(jQuery || {}, window);
