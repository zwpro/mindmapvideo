import type {
  AnimationStyle,
  Ratio,
  Resolution,
  ThemeStyle,
  VideoConfig,
} from '@/types'

export const DEFAULT_VIDEO_CONFIG: VideoConfig = {
  animationStyle: 'unfold',
  resolution: '1080p',
  ratio: '16:9',
  nodeDuration: 4,
  voice: { id: 'voice-aurora', speed: 1, volume: 0.9 },
  bgm: { id: 'bgm-ambient', volume: 0.4 },
  theme: 'tech',
}

export const ANIMATION_STYLES: Array<{
  id: AnimationStyle
  name: string
  description: string
  emoji: string
}> = [
  {
    id: 'unfold',
    name: '逐级展开',
    description: '从根节点开始，按层级依次展开，节奏稳健，适合教学讲解。',
    emoji: '🌿',
  },
  {
    id: 'roam',
    name: '路径漫游',
    description: '镜头沿着节点路径漫游，强调脉络感，适合知识叙事。',
    emoji: '🛣️',
  },
  {
    id: 'focus',
    name: '聚焦放大',
    description: '逐节点聚焦放大并缩回，适合突出核心要点。',
    emoji: '🔍',
  },
  {
    id: 'overview',
    name: '全局总览',
    description: '先整体概览再细节穿插，适合复杂结构总览。',
    emoji: '🛰️',
  },
]

export const RESOLUTIONS: Array<{ id: Resolution; label: string; hint: string }> = [
  { id: '720p', label: '720P', hint: '1280×720 · 流畅' },
  { id: '1080p', label: '1080P', hint: '1920×1080 · 推荐' },
  { id: '2k', label: '2K', hint: '2560×1440 · 高清' },
  { id: '4k', label: '4K', hint: '3840×2160 · 极致' },
]

export const RATIOS: Array<{ id: Ratio; label: string; hint: string }> = [
  { id: '16:9', label: '16 : 9', hint: '横屏 · 知识科普' },
  { id: '9:16', label: '9 : 16', hint: '竖屏 · 短视频' },
  { id: '1:1', label: '1 : 1', hint: '方屏 · 社交流' },
]

export const VOICES: Array<{
  id: string
  name: string
  gender: '女' | '男'
  description: string
  color: string
}> = [
  {
    id: 'voice-aurora',
    name: '极光',
    gender: '女',
    description: '清亮温暖，适合科普讲解',
    color: '#7CFFCB',
  },
  {
    id: 'voice-orion',
    name: '猎户',
    gender: '男',
    description: '低沉沉稳，适合商业训练',
    color: '#60A5FA',
  },
  {
    id: 'voice-luna',
    name: '夜灯',
    gender: '女',
    description: '柔和细腻，适合人文叙事',
    color: '#F472B6',
  },
  {
    id: 'voice-atlas',
    name: '巨匠',
    gender: '男',
    description: '激昂自信，适合产品演示',
    color: '#FF8A4C',
  },
]

export const BGM_OPTIONS: Array<{ id: string; name: string; mood: string }> = [
  { id: 'bgm-ambient', name: '星轨环绕', mood: '舒缓 · 钢琴' },
  { id: 'bgm-future', name: '未来引擎', mood: '科技 · 电子' },
  { id: 'bgm-minimal', name: '极简午后', mood: '清新 · 木吉他' },
  { id: 'bgm-epic', name: '史诗叙事', mood: '宏大 · 交响' },
  { id: 'bgm-none', name: '不使用 BGM', mood: '纯净人声' },
]

export const THEME_STYLES: Array<{
  id: ThemeStyle
  name: string
  description: string
  primary: string
  accent: string
}> = [
  {
    id: 'minimal',
    name: '极简白',
    description: '高对比黑白灰，专业内敛',
    primary: '#0B1A2A',
    accent: '#7CFFCB',
  },
  {
    id: 'tech',
    name: '科技墨蓝',
    description: '深墨蓝 + 电光青，未来科技感',
    primary: '#0B1A2A',
    accent: '#7CFFCB',
  },
  {
    id: 'academic',
    name: '学院米黄',
    description: '米黄底色 + 衬线字体，沉稳学术',
    primary: '#3B2F1F',
    accent: '#C97D3F',
  },
  {
    id: 'cartoon',
    name: '卡通糖果',
    description: '高饱和糖果色，活泼亲和',
    primary: '#5B3FBF',
    accent: '#FFC857',
  },
  {
    id: 'business',
    name: '商务深紫',
    description: '深紫 + 香槟金，正式品质',
    primary: '#1F1B3A',
    accent: '#D4AF37',
  },
]

export const POPULAR_TOPICS = [
  '人工智能发展史',
  'Python 入门学习路线',
  '区块链基础原理',
  '光合作用全过程',
  '欧洲文艺复兴',
  '宇宙的起源',
  'SEO 优化指南',
  '一节课讲透 Transformer',
]
