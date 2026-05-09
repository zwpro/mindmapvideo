<script setup lang="ts">
import { Sparkles, Github, Twitter, Send } from 'lucide-vue-next'
</script>

<template>
  <footer class="border-t border-zinc-200 bg-zinc-50/80">
    <div
      class="mx-auto grid w-full max-w-[1280px] gap-10 px-6 py-12 lg:grid-cols-4 lg:px-10"
    >
      <div class="space-y-4 lg:col-span-2">
        <div class="flex items-center gap-2">
          <span
            class="grid h-8 w-8 place-items-center rounded-md border border-electric-400/40 bg-electric-400/10"
          >
            <Sparkles class="h-4 w-4 text-electric-400" />
          </span>
          <span class="font-display text-base font-semibold tracking-tight">
            MindMap<span class="text-electric-400">Video</span>
          </span>
        </div>
        <p class="max-w-md text-sm leading-relaxed text-mist-400">
          AI 驱动的思维导图视频生成平台 ——
          输入主题，分钟级产出结构化大纲与配音动画视频，覆盖知识科普、教育培训、企业课件等场景。
        </p>
      </div>

      <div>
        <h4 class="mb-3 text-sm font-medium text-moon-50">产品</h4>
        <ul class="space-y-2 text-sm text-mist-400">
          <li><a class="hover:text-electric-400" href="#">功能介绍</a></li>
          <li><a class="hover:text-electric-400" href="#">案例展示</a></li>
          <li><a class="hover:text-electric-400" href="#">更新日志</a></li>
        </ul>
      </div>

      <div>
        <h4 class="mb-3 text-sm font-medium text-moon-50">关于</h4>
        <ul class="space-y-2 text-sm text-mist-400">
          <li><a class="hover:text-electric-400" href="#">关于我们</a></li>
          <li><a class="hover:text-electric-400" href="#">联系方式</a></li>
          <li><a class="hover:text-electric-400" href="#">隐私政策</a></li>
        </ul>
      </div>
    </div>

    <div
      class="border-t border-zinc-200"
    >
      <div
        class="mx-auto flex w-full max-w-[1280px] flex-col items-center justify-between gap-3 px-6 py-5 text-xs text-mist-500 md:flex-row lg:px-10"
      >
        <p>© {{ new Date().getFullYear() }} MindMap Video. All rights reserved.</p>
        <div class="flex items-center gap-3">
          <a class="hover:text-electric-400" href="#" aria-label="GitHub">
            <Github class="h-4 w-4" />
          </a>
          <a class="hover:text-electric-400" href="#" aria-label="Twitter">
            <Twitter class="h-4 w-4" />
          </a>
          <a class="hover:text-electric-400" href="#" aria-label="联系我们">
            <Send class="h-4 w-4" />
          </a>
        </div>
      </div>
    </div>
  </footer>
</template>
