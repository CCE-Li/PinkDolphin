<template>
  <section class="space-y-6">
    <div class="guide-hero panel">
      <div class="hero-orb hero-orb-a"></div>
      <div class="hero-orb hero-orb-b"></div>
      <div class="hero-orb hero-orb-c"></div>
      <div class="panel-body relative z-[1]">
        <div class="max-w-3xl">
          <!-- <p class="page-eyebrow">Usage Guide</p>
          <h1 class="page-title">使用指南</h1> -->
          <p class="page-subtitle">
            这页不是只讲概念，而是告诉你这个系统该怎么用，尤其是六层分析器如何协同工作，以及你看一封邮件时应该先看哪里、再看哪里。
          </p>
        </div>

        <div class="mt-6 flex flex-wrap items-center gap-3">
          <div class="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-white/85 px-4 py-2 text-sm text-slate-600">
            <span class="h-2.5 w-2.5 rounded-full bg-sky-500 shadow-[0_0_0_6px_rgba(0,113,227,0.12)]"></span>
            分析器协同为主线
          </div>
          <div class="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-sm text-white">
            当前模块
            <span class="font-semibold">{{ activeStage.title }}</span>
          </div>
          <button
            class="btn-secondary"
            type="button"
            @click="isAutoPlaying ? replayAnimation() : resumeAnimation()"
          >
            {{ isAutoPlaying ? '重新播放' : '继续播放' }}
          </button>
          <button
            v-if="!isAutoPlaying"
            class="btn-secondary"
            type="button"
            @click="replayAnimation"
          >
            从头播放
          </button>
        </div>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.4fr,0.6fr]">
      <div class="panel overflow-hidden">
        <div class="panel-header">
          <div>
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">分析器协同演示</h2>
            <p class="mt-2 text-sm text-slate-500">一封邮件进入系统后，不是只跑一次规则，而是按顺序经过解析、多个分析器和风险决策。</p>
          </div>
          <div class="rounded-full bg-sky-50 px-4 py-2 text-sm font-medium text-sky-700">
            Step {{ activeStageIndex + 1 }} / {{ analyzerStages.length }}
          </div>
        </div>
        <div class="panel-body">
          <div class="playback-shell">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {{ isAutoPlaying ? '自动轮播中 / 点击卡片可暂停' : '已暂停 / 点击卡片可查看细节' }}
              </div>
              <div class="text-sm text-slate-500">
                当前定位在第 {{ activeStageIndex + 1 }} 步
                <span v-if="!isAutoPlaying"> · 已暂停自动轮播</span>
              </div>
            </div>
            <div class="playback-bar mt-4">
              <div class="playback-fill" :style="{ width: `${progressPercent}%` }"></div>
            </div>
            <div class="guide-bead-track mt-4" aria-hidden="true">
              <template v-for="(stage, index) in analyzerStages" :key="stage.id">
                <div
                  class="guide-bead-group"
                  :class="{
                    'is-active': index === activeStageIndex,
                    'is-past': index < activeStageIndex,
                  }"
                  :title="stage.title"
                >
                  <div class="guide-bead">
                    <span>{{ index + 1 }}</span>
                  </div>
                </div>
                <div
                  v-if="index < analyzerStages.length - 1"
                  class="guide-arrow"
                  :class="{ 'is-active': index < activeStageIndex }"
                >
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </template>
            </div>
          </div>

          <div class="flow-grid mt-5">
            <button
              v-for="(stage, index) in analyzerStages"
              :key="stage.id"
              type="button"
              class="flow-node"
              :class="{
                'is-active': index === activeStageIndex,
                'is-past': index < activeStageIndex,
              }"
              @click="setStage(index)"
            >
              <div class="flow-node-route" aria-hidden="true">
                <div class="flow-index">{{ index + 1 }}</div>
                <div class="flow-node-line"></div>
                <div v-if="index < analyzerStages.length - 1" class="flow-node-arrows">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div v-else class="flow-node-target"></div>
              </div>
              <div class="mt-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">{{ stage.eyebrow }}</div>
              <div class="mt-3 text-base font-semibold tracking-[-0.03em] text-slate-950">{{ stage.title }}</div>
              <div class="mt-2 text-sm leading-6 text-slate-600">{{ stage.summary }}</div>
              <div class="mt-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">{{ stage.output }}</div>
            </button>
          </div>

          <div class="mt-6 grid gap-4 lg:grid-cols-[1.12fr,0.88fr]">
            <div class="rounded-[28px] border border-slate-200 bg-white px-6 py-5">
              <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">{{ activeStage.eyebrow }}</div>
              <h3 class="mt-3 text-2xl font-semibold tracking-[-0.04em] text-slate-950">{{ activeStage.title }}</h3>
              <p class="mt-3 text-sm leading-7 text-slate-600">{{ activeStage.description }}</p>

              <div class="mt-5">
                <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">你应该看什么</div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="item in activeStage.lookFor"
                    :key="item"
                    class="rounded-full border border-sky-100 bg-sky-50 px-3 py-2 text-xs font-semibold tracking-[0.08em] text-sky-700"
                  >
                    {{ item }}
                  </span>
                </div>
              </div>

              <div class="mt-6 rounded-[24px] bg-slate-50 px-5 py-4">
                <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">模块作用</div>
                <p class="mt-3 text-sm leading-7 text-slate-600">{{ activeStage.role }}</p>
              </div>
            </div>

            <div class="rounded-[28px] border border-slate-200 bg-[linear-gradient(180deg,#f8fbff_0%,#eef6ff_100%)] px-6 py-5">
              <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">协同关系</div>

              <div class="mt-4 space-y-3">
                <div class="rounded-[22px] border border-white/90 bg-white/75 px-4 py-4">
                  <div class="text-sm font-semibold text-slate-950">和哪些模块一起看</div>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span
                      v-for="item in activeStage.cooperatesWith"
                      :key="item"
                      class="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold tracking-[0.08em] text-slate-600"
                    >
                      {{ item }}
                    </span>
                  </div>
                </div>

                <div class="rounded-[22px] border border-white/90 bg-white/75 px-4 py-4">
                  <div class="text-sm font-semibold text-slate-950">什么时候重点依赖它</div>
                  <div class="mt-3 space-y-2">
                    <div v-for="item in activeStage.whenUseful" :key="item" class="flex items-start gap-3">
                      <span class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-sky-500"></span>
                      <span class="text-sm leading-6 text-slate-600">{{ item }}</span>
                    </div>
                  </div>
                </div>

                <div class="rounded-[22px] border border-white/90 bg-white/75 px-4 py-4">
                  <div class="text-sm font-semibold text-slate-950">什么时候可能跳过</div>
                  <div class="mt-3 space-y-2">
                    <div v-for="item in activeStage.skipWhen" :key="item" class="flex items-start gap-3">
                      <span class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-slate-400"></span>
                      <span class="text-sm leading-6 text-slate-600">{{ item }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="panel guide-side-panel">
          <div class="panel-header">
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">上手顺序</h2>
          </div>
          <div class="panel-body space-y-3">
            <div v-for="step in guideSteps" :key="step.title" class="rounded-[24px] border border-slate-200 bg-white px-5 py-4">
              <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">{{ step.step }}</div>
              <div class="mt-2 text-sm font-semibold text-slate-950">{{ step.title }}</div>
              <div class="mt-2 text-sm leading-6 text-slate-500">{{ step.description }}</div>
            </div>
          </div>
        </div>

        <div class="panel guide-side-panel">
          <div class="panel-header">
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">读取建议</h2>
          </div>
          <div class="panel-body space-y-3">
            <div v-for="tip in readingTips" :key="tip.title" class="rounded-[24px] border border-slate-200 bg-white px-5 py-4">
              <div class="text-sm font-semibold text-slate-950">{{ tip.title }}</div>
              <div class="mt-2 text-sm leading-6 text-slate-500">{{ tip.description }}</div>
            </div>
          </div>
        </div>

        <div class="panel guide-side-panel">
          <div class="panel-header">
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">为什么会跳过扫描</h2>
          </div>
          <div class="panel-body">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="analyzer in analyzers"
                :key="analyzer.id"
                class="analyzer-chip"
                :class="{ 'is-active': activeStage.analyzers.includes(analyzer.id) }"
              >
                {{ analyzer.label }}
              </span>
            </div>
            <p class="mt-4 text-sm leading-7 text-slate-500">
              URL、附件、LLM 等深度扫描会受到隐私白名单和策略开关影响。看到某个分析器没有参与，不代表系统坏了，也可能是当前策略主动让它跳过。
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid gap-6 lg:grid-cols-3">
      <div v-for="card in guideCards" :key="card.title" class="panel overflow-hidden">
        <div class="panel-body relative">
          <div class="guide-card-wave"></div>
          <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">{{ card.eyebrow }}</div>
          <h2 class="mt-3 text-2xl font-semibold tracking-[-0.04em] text-slate-950">{{ card.title }}</h2>
          <p class="mt-3 text-sm leading-7 text-slate-600">{{ card.description }}</p>

          <div class="mt-5 guide-bars" aria-hidden="true">
            <span v-for="bar in 6" :key="bar" :style="{ animationDelay: `${bar * 120}ms` }"></span>
          </div>

          <div class="mt-6 space-y-3">
            <div v-for="bullet in card.bullets" :key="bullet" class="flex items-start gap-3 rounded-[20px] bg-slate-50 px-4 py-3">
              <span class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-sky-500"></span>
              <span class="text-sm leading-6 text-slate-600">{{ bullet }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
  <BackToTopButton />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import BackToTopButton from '@/components/BackToTopButton.vue'

type AnalyzerGuideStage = {
  id: string
  eyebrow: string
  title: string
  summary: string
  description: string
  output: string
  role: string
  lookFor: string[]
  cooperatesWith: string[]
  whenUseful: string[]
  skipWhen: string[]
  analyzers: string[]
}

const analyzerStages: AnalyzerGuideStage[] = [
  {
    id: 'parse',
    eyebrow: 'Preflight',
    title: '邮件解析',
    summary: '系统先拆开标题、正文、头部、附件、链接和收发件人，为后面所有分析器准备输入。',
    description: '如果基础解析不完整，后面的分析器就没有干净输入，所以这是整条链路的起点。',
    output: '结构化邮件对象',
    role: '把原始邮件拆成统一结构，后续的 Header Auth、URL、Attachment、Behavior、LLM 都依赖这一步的解析结果。',
    lookFor: ['主题', '发件人', '正文', '链接', '附件', '头部字段'],
    cooperatesWith: ['Header Auth', 'Content Rule', 'URL Intel', 'Attachment', 'Behavior', 'LLM'],
    whenUseful: ['原始邮件格式复杂时', '需要确认附件和链接是否被正确提取时'],
    skipWhen: ['不会被策略跳过，它是整条分析链的前置步骤'],
    analyzers: [],
  },
  {
    id: 'header_auth',
    eyebrow: 'Analyzer 01',
    title: 'Header Auth',
    summary: '优先看 SPF、DKIM、DMARC 和 Authentication-Results，判断来源可信度。',
    description: '这是最适合先读的一层，因为它最接近邮件来源本身，能快速判断“这封邮件是不是从声称的地方发出来的”。',
    output: '来源可信度证据',
    role: '当 Header Auth 弱或失败时，后面的内容规则、URL、LLM 命中会更值得警惕；当它很强时，后面出现轻微异常也更容易被解释。',
    lookFor: ['SPF 结果', 'DKIM 结果', 'DMARC 结果', 'Authentication-Results'],
    cooperatesWith: ['Content Rule', 'Behavior', 'Risk Decision'],
    whenUseful: ['仿冒品牌邮件', '伪造发件人场景', '需要先判断来源可信度时'],
    skipWhen: ['通常不跳过，它属于低成本基础分析'],
    analyzers: ['header_auth'],
  },
  {
    id: 'content_rule',
    eyebrow: 'Analyzer 02',
    title: 'Content Rule',
    summary: '检查标题和正文里的关键词、自定义规则和已知风险模式。',
    description: '这层最适合解释“为什么系统觉得这封邮件可疑”，因为它能把异常词、语义片段和命中规则直接暴露出来。',
    output: '规则命中与文本证据',
    role: '它和 Header Auth 组合时可以区分“来源可疑 + 内容诱导”与“来源正常 + 普通营销文案”的差异。',
    lookFor: ['主题关键词', '正文诱导语', '规则命中名称', '紧急操作语气'],
    cooperatesWith: ['Header Auth', 'URL Intel', 'LLM'],
    whenUseful: ['账号验证、紧急付款、密码重置等诱导话术', '需要快速解释风险来源时'],
    skipWhen: ['通常不跳过，除非上游没有可解析文本'],
    analyzers: ['content_rule'],
  },
  {
    id: 'url',
    eyebrow: 'Analyzer 03',
    title: 'URL Intel',
    summary: '提取正文中的链接，看域名、URL 结构和情报扫描结果。',
    description: '很多高风险邮件正文看起来正常，但 URL 才是真正的恶意载荷入口，所以这层经常决定风险级别能否被拉高。',
    output: '链接风险证据',
    role: '它经常和 Content Rule、LLM 互相验证。文本可能说得很温和，但链接如果跳转到陌生域名，整体风险会明显抬升。',
    lookFor: ['陌生域名', '短链跳转', '品牌域名拼写变体', '可疑 URL 路径'],
    cooperatesWith: ['Content Rule', 'LLM', 'Risk Decision'],
    whenUseful: ['正文里出现点击、登录、验证、下载链接时', '用户担心钓鱼落点时'],
    skipWhen: ['命中隐私白名单且 URL 扫描被配置跳过时'],
    analyzers: ['url'],
  },
  {
    id: 'attachment',
    eyebrow: 'Analyzer 04',
    title: 'Attachment',
    summary: '分析附件类型、名称和扫描结果，识别危险载荷或伪装文档。',
    description: '附件层不一定每封都有，但一旦有压缩包、宏文档、可执行内容，它的权重就会迅速上升。',
    output: '附件风险证据',
    role: '它和 Content Rule 经常是配套关系。正文如果在催你“打开附件”“查看发票”，附件扫描就尤其关键。',
    lookFor: ['压缩包', '可执行文件', '宏文档', '异常扩展名', '扫描命中'],
    cooperatesWith: ['Content Rule', 'LLM', 'Risk Decision'],
    whenUseful: ['邮件带发票、合同、压缩包或 Office 文档时', '怀疑是木马投递时'],
    skipWhen: ['命中隐私白名单且附件扫描被配置跳过时', '邮件本身没有附件时'],
    analyzers: ['attachment'],
  },
  {
    id: 'behavior',
    eyebrow: 'Analyzer 05',
    title: 'Behavior',
    summary: '用历史通信关系看这是不是一条“突然出现的陌生互动”。',
    description: '这层不靠文本本身，而是看关系和上下文。很多鱼叉式钓鱼内容写得很像真的，但行为轨迹并不自然。',
    output: '历史行为偏差信号',
    role: 'Behavior 特别适合和 Header Auth 联动。来源也许通过了认证，但如果历史上从没发过这种内容，依然值得警惕。',
    lookFor: ['是否首次联系', '历史联系人关系', '突然新增收件人', '与过去主题不一致'],
    cooperatesWith: ['Header Auth', 'Content Rule', 'Risk Decision'],
    whenUseful: ['内部协作型钓鱼', '伪装成熟人或供应商时', '需要判断这封邮件“像不像平时的来往”时'],
    skipWhen: ['历史数据不足时，这层信号会偏弱，但通常不会直接跳过'],
    analyzers: ['behavior'],
  },
  {
    id: 'llm',
    eyebrow: 'Analyzer 06',
    title: 'LLM',
    summary: '把前面难以规则化的信息交给语义分析，补足文本理解能力。',
    description: 'LLM 不是替代前面的分析器，而是把前面零散的证据串起来，判断语气、诱导方式和整体钓鱼意图。',
    output: '语义风险判断',
    role: '它最适合做“综合判断”。当 Header Auth、规则、URL、Attachment 都各有一点异常时，LLM 能帮助把这些弱信号拼成完整风险图。',
    lookFor: ['账号诱导', '操作施压', '仿冒语气', '整体语义不自然'],
    cooperatesWith: ['Content Rule', 'URL Intel', 'Attachment', 'Risk Decision'],
    whenUseful: ['传统规则解释不充分时', '需要综合弱信号时', '文本伪装比较自然时'],
    skipWhen: ['命中隐私白名单且 LLM 扫描被配置跳过时', '系统配置关闭 LLM 分析时'],
    analyzers: ['llm'],
  },
  {
    id: 'decision',
    eyebrow: 'Decision Layer',
    title: '风险决策',
    summary: '最后把多个分析器的证据合并成风险等级、分数和建议动作。',
    description: '真正有价值的不是某一个分析器命中，而是多层证据在这里被统一解释，变成可以直接处置的结果。',
    output: '风险等级 + 建议动作',
    role: '这一层决定你在页面上最终看到什么，也决定 incident、审计日志、处置动作和后续复核工作如何展开。',
    lookFor: ['最终风险等级', '总分', '建议动作', '关键证据汇总'],
    cooperatesWith: ['全部分析器'],
    whenUseful: ['需要快速做处置决策时', '想知道为什么系统判 high / critical 时'],
    skipWhen: ['不会跳过，它是所有分析结果的汇总层'],
    analyzers: [],
  },
]

const analyzers = [
  { id: 'header_auth', label: 'Header Auth' },
  { id: 'content_rule', label: 'Content Rule' },
  { id: 'url', label: 'URL Intel' },
  { id: 'attachment', label: 'Attachment' },
  { id: 'behavior', label: 'Behavior' },
  { id: 'llm', label: 'LLM' },
]

const guideSteps = [
  {
    step: '01',
    title: '先接入邮箱，再看是否同步正常',
    description: '第一步不是马上看风险，而是确认邮箱账户、文件夹和同步游标都正常工作，确保系统看得到真实新增邮件。',
  },
  {
    step: '02',
    title: '打开邮件详情，先看最终风险等级',
    description: '先用 high / critical / medium 判断优先级，再决定是否继续看更细的分析证据。',
  },
  {
    step: '03',
    title: '按照“来源 -> 内容 -> 链接/附件 -> 行为 -> 语义”顺序读',
    description: '这比随机翻日志更高效，也更容易快速定位是哪一层把风险抬高了。',
  },
  {
    step: '04',
    title: '最后再看问题日志和审计记录',
    description: '当你怀疑某次扫描失败、某个分析器没跑、或系统结果不符合预期时，再去看问题日志最合适。',
  },
]

const readingTips = [
  {
    title: '先看 Header Auth，再决定是否信任后续内容',
    description: '如果来源认证异常，后续出现轻微异常就更危险；如果来源认证很强，后续异常就需要更谨慎解释。',
  },
  {
    title: '正文正常不代表安全，URL 和附件经常是落点',
    description: '很多钓鱼正文写得很克制，但真正危险的部分在链接或附件里，所以不要只看正文。',
  },
  {
    title: 'Behavior 用来识别“看起来像真的，但关系不自然”',
    description: '特别是内部熟人仿冒、供应商仿冒、首次联系等场景，行为层通常比文本层更关键。',
  },
  {
    title: 'LLM 适合做综合判断，不要单独神化它',
    description: 'LLM 最有价值的地方是把多层弱信号组织成解释，而不是替代规则、URL 或附件扫描。',
  },
]

const guideCards = [
  {
    eyebrow: 'Daily Workflow',
    title: '平时怎么用',
    description: '把这个系统当成“先筛优先级，再看证据链”的工作台，而不是单个检测器。',
    bullets: [
      '先看最近高风险邮件和邮箱状态，再进入具体邮件详情。',
      '遇到 high / critical 时，优先看来源、URL、附件三层是否同时异常。',
      '处理完后再看处置记录和审计记录，确认闭环已经形成。',
    ],
  },
  {
    eyebrow: 'False Positive',
    title: '误报怎么排查',
    description: '当你觉得系统判得太高，不要只盯一个分数，而是倒着看证据来自哪几层。',
    bullets: [
      '先确认 Header Auth 是否正常，再看规则和行为层是不是误触发。',
      '如果 URL / 附件 / LLM 被策略跳过，要先确认这是策略行为还是系统异常。',
      '最后去问题日志确认是否有扫描失败、超时或降级。',
    ],
  },
  {
    eyebrow: 'Triage',
    title: '高风险怎么处理',
    description: '系统的价值不只在识别，还在于把后续动作组织成可执行的处置流程。',
    bullets: [
      '先看系统建议动作，再决定是否隔离、标记或人工复核。',
      '如果多层分析器同时异常，不要只依赖单个解释，应按综合风险处理。',
      '处置后保留审计和问题日志，便于后续复盘与调优。',
    ],
  },
]

const activeStageIndex = ref(0)
const isAutoPlaying = ref(true)
const activeStage = computed(() => analyzerStages[activeStageIndex.value])
const progressPercent = computed(() => ((activeStageIndex.value + 1) / analyzerStages.length) * 100)

let animationTimer: number | null = null

function setStage(index: number): void {
  activeStageIndex.value = index
  pauseAnimationLoop()
}

function replayAnimation(): void {
  activeStageIndex.value = 0
  startAnimationLoop()
}

function resumeAnimation(): void {
  startAnimationLoop()
}

function startAnimationLoop(): void {
  stopAnimationLoop()
  isAutoPlaying.value = true
  animationTimer = window.setInterval(() => {
    activeStageIndex.value = (activeStageIndex.value + 1) % analyzerStages.length
  }, 1900)
}

function pauseAnimationLoop(): void {
  stopAnimationLoop()
  isAutoPlaying.value = false
}

function stopAnimationLoop(): void {
  if (animationTimer !== null) {
    window.clearInterval(animationTimer)
    animationTimer = null
  }
}

onMounted(() => {
  startAnimationLoop()
})

onBeforeUnmount(() => {
  stopAnimationLoop()
})
</script>

<style scoped>
.guide-hero {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 15% 20%, rgba(14, 165, 233, 0.2), transparent 24%),
    radial-gradient(circle at 85% 18%, rgba(59, 130, 246, 0.18), transparent 30%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(238, 246, 255, 0.92) 100%);
}

.guide-hero::after {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 113, 227, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 113, 227, 0.05) 1px, transparent 1px);
  background-size: 28px 28px;
  content: "";
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.75), transparent);
  pointer-events: none;
}

.hero-orb {
  position: absolute;
  border-radius: 999px;
  opacity: 0.72;
  filter: blur(6px);
  pointer-events: none;
}

.hero-orb-a {
  top: 38px;
  right: 132px;
  height: 84px;
  width: 84px;
  background: rgba(0, 113, 227, 0.18);
  animation: drift 8s ease-in-out infinite;
}

.hero-orb-b {
  right: 40px;
  top: 132px;
  height: 120px;
  width: 120px;
  background: rgba(14, 165, 233, 0.16);
  animation: drift 10s ease-in-out infinite reverse;
}

.hero-orb-c {
  bottom: 28px;
  right: 210px;
  height: 54px;
  width: 54px;
  background: rgba(59, 130, 246, 0.18);
  animation: drift 7s ease-in-out infinite;
}

.playback-shell {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(248, 251, 255, 0.92) 0%, rgba(255, 255, 255, 0.92) 100%);
  padding: 16px 18px;
}

.playback-bar {
  position: relative;
  overflow: hidden;
  height: 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
}

.playback-bar::after {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(90deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  content: "";
}

.playback-fill {
  position: relative;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #38bdf8 0%, #0ea5e9 45%, #0071e3 100%);
  box-shadow: 0 8px 20px rgba(0, 113, 227, 0.2);
  transition: width 520ms cubic-bezier(0.22, 1, 0.36, 1);
}

.playback-fill::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.55), transparent);
  background-size: 180px 100%;
  animation: trackGlow 2.2s linear infinite;
  content: "";
}

.guide-bead-track {
  display: flex;
  align-items: center;
  gap: 8px;
}

.guide-bead-group {
  position: relative;
  z-index: 1;
}

.guide-bead {
  position: relative;
  display: inline-flex;
  height: 34px;
  width: 34px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  transition:
    transform 220ms ease,
    border-color 220ms ease,
    background 220ms ease,
    color 220ms ease,
    box-shadow 220ms ease;
}

.guide-bead::after {
  position: absolute;
  inset: -5px;
  border-radius: inherit;
  border: 1px solid transparent;
  content: "";
}

.guide-bead-group.is-past .guide-bead {
  border-color: rgba(14, 165, 233, 0.2);
  background: linear-gradient(180deg, rgba(224, 242, 254, 0.96) 0%, rgba(186, 230, 253, 0.92) 100%);
  color: #0369a1;
}

.guide-bead-group.is-active .guide-bead {
  transform: scale(1.08);
  border-color: rgba(0, 113, 227, 0.28);
  background: linear-gradient(180deg, #38bdf8 0%, #0071e3 100%);
  color: #fff;
  box-shadow: 0 10px 22px rgba(0, 113, 227, 0.22);
}

.guide-bead-group.is-active .guide-bead::after {
  border-color: rgba(56, 189, 248, 0.24);
  animation: beadPulse 1.6s ease-in-out infinite;
}

.guide-arrow {
  display: flex;
  flex: 1;
  min-width: 16px;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.guide-arrow span {
  height: 9px;
  width: 9px;
  border-top: 2px solid rgba(148, 163, 184, 0.45);
  border-right: 2px solid rgba(148, 163, 184, 0.45);
  transform: rotate(45deg);
  transition: border-color 220ms ease, opacity 220ms ease, transform 220ms ease;
}

.guide-arrow.is-active span {
  border-top-color: rgba(14, 165, 233, 0.88);
  border-right-color: rgba(14, 165, 233, 0.88);
  animation: arrowRush 1s ease-in-out infinite;
}

.guide-arrow.is-active span:nth-child(2) {
  animation-delay: 120ms;
}

.guide-arrow.is-active span:nth-child(3) {
  animation-delay: 240ms;
}

.flow-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr);
}

@media (min-width: 768px) {
  .flow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1280px) {
  .flow-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .flow-grid > :nth-child(5) {
    grid-column: 4;
    grid-row: 2;
  }

  .flow-grid > :nth-child(6) {
    grid-column: 3;
    grid-row: 2;
  }

  .flow-grid > :nth-child(7) {
    grid-column: 2;
    grid-row: 2;
  }

  .flow-grid > :nth-child(8) {
    grid-column: 1;
    grid-row: 2;
  }
}

.flow-node {
  position: relative;
  min-height: 172px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 26px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(248, 250, 252, 0.96) 100%);
  padding: 16px 16px 15px;
  text-align: left;
  transition:
    transform 220ms ease,
    border-color 220ms ease,
    box-shadow 220ms ease,
    background 220ms ease;
}

.flow-node::after {
  position: absolute;
  inset: auto -18% -62% auto;
  height: 120px;
  width: 120px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%);
  content: "";
}

.flow-node.is-past {
  border-color: rgba(14, 165, 233, 0.18);
  background: linear-gradient(180deg, rgba(250, 252, 255, 1) 0%, rgba(239, 246, 255, 0.88) 100%);
}

.flow-node.is-past .flow-node-line {
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.72), rgba(14, 165, 233, 0.42));
}

.flow-node.is-past .flow-node-arrows span {
  border-top-color: rgba(14, 165, 233, 0.76);
  border-right-color: rgba(14, 165, 233, 0.76);
}

.flow-node.is-past .flow-node-target {
  border-color: rgba(14, 165, 233, 0.52);
  background: rgba(224, 242, 254, 0.92);
}

.flow-node.is-active {
  transform: translateY(-4px);
  border-color: rgba(0, 113, 227, 0.3);
  background: linear-gradient(180deg, rgba(255, 255, 255, 1) 0%, rgba(234, 244, 255, 0.98) 100%);
  box-shadow: 0 22px 42px rgba(0, 113, 227, 0.12);
}

.flow-node.is-active .flow-index {
  background: linear-gradient(180deg, #38bdf8 0%, #0071e3 100%);
  color: #fff;
  box-shadow: 0 10px 22px rgba(0, 113, 227, 0.16);
}

.flow-node.is-active .flow-node-line {
  background: linear-gradient(90deg, rgba(56, 189, 248, 1), rgba(0, 113, 227, 0.72));
}

.flow-node.is-active .flow-node-arrows span {
  border-top-color: rgba(0, 113, 227, 0.95);
  border-right-color: rgba(0, 113, 227, 0.95);
  animation: arrowRush 1s ease-in-out infinite;
}

.flow-node.is-active .flow-node-arrows span:nth-child(2) {
  animation-delay: 120ms;
}

.flow-node.is-active .flow-node-arrows span:nth-child(3) {
  animation-delay: 240ms;
}

.flow-node.is-active .flow-node-target {
  transform: scale(1.08);
  border-color: rgba(0, 113, 227, 0.92);
  background: rgba(224, 242, 254, 1);
  box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.08);
}

.flow-index {
  display: inline-flex;
  height: 34px;
  width: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.flow-node-route {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flow-node-line {
  flex: 1;
  min-width: 18px;
  height: 2px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.22);
  transition: background-color 220ms ease;
}

.flow-node-arrows {
  display: flex;
  align-items: center;
  gap: 2px;
}

.flow-node-arrows span {
  --arrow-rotation: 45deg;
  height: 8px;
  width: 8px;
  border-top: 2px solid rgba(148, 163, 184, 0.42);
  border-right: 2px solid rgba(148, 163, 184, 0.42);
  transform: rotate(var(--arrow-rotation));
  transition: border-color 220ms ease, opacity 220ms ease, transform 220ms ease;
}

.flow-node-target {
  height: 12px;
  width: 12px;
  border: 2px solid rgba(148, 163, 184, 0.38);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  transition: border-color 220ms ease, background-color 220ms ease, transform 220ms ease;
}

@media (min-width: 1280px) {
  .flow-grid > :nth-child(4) .flow-node-arrows span {
    --arrow-rotation: 135deg;
  }

  .flow-grid > :nth-child(5) .flow-node-route,
  .flow-grid > :nth-child(6) .flow-node-route,
  .flow-grid > :nth-child(7) .flow-node-route,
  .flow-grid > :nth-child(8) .flow-node-route {
    flex-direction: row-reverse;
  }

  .flow-grid > :nth-child(5) .flow-node-arrows span,
  .flow-grid > :nth-child(6) .flow-node-arrows span,
  .flow-grid > :nth-child(7) .flow-node-arrows span {
    --arrow-rotation: 225deg;
  }
}

.guide-side-panel {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(248, 251, 255, 0.96) 100%);
}

.analyzer-chip {
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 10px 14px;
  text-transform: uppercase;
  transition: all 180ms ease;
}

.analyzer-chip.is-active {
  border-color: rgba(0, 113, 227, 0.22);
  background: rgba(234, 244, 255, 0.95);
  color: #0071e3;
  box-shadow: inset 0 0 0 1px rgba(0, 113, 227, 0.04);
}

.guide-card-wave {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 10% 20%, rgba(0, 113, 227, 0.08), transparent 28%),
    radial-gradient(circle at 85% 15%, rgba(56, 189, 248, 0.08), transparent 24%);
  pointer-events: none;
}

.guide-bars {
  display: flex;
  align-items: end;
  gap: 8px;
  height: 84px;
}

.guide-bars span {
  flex: 1;
  min-width: 0;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.24) 0%, rgba(0, 113, 227, 0.88) 100%);
  animation: equalize 1.9s ease-in-out infinite;
  transform-origin: bottom;
}

.guide-bars span:nth-child(1) {
  height: 38%;
}

.guide-bars span:nth-child(2) {
  height: 70%;
}

.guide-bars span:nth-child(3) {
  height: 52%;
}

.guide-bars span:nth-child(4) {
  height: 82%;
}

.guide-bars span:nth-child(5) {
  height: 46%;
}

.guide-bars span:nth-child(6) {
  height: 62%;
}

@keyframes drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(0, -12px, 0) scale(1.06);
  }
}

@keyframes trackGlow {
  from {
    background-position: -180px 0;
  }
  to {
    background-position: calc(100% + 180px) 0;
  }
}

@keyframes equalize {
  0%,
  100% {
    transform: scaleY(0.74);
    opacity: 0.72;
  }
  50% {
    transform: scaleY(1.08);
    opacity: 1;
  }
}

@keyframes beadPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.4;
  }
  50% {
    transform: scale(1.12);
    opacity: 0.75;
  }
}

@keyframes arrowRush {
  0%,
  100% {
    opacity: 0.32;
    transform: rotate(var(--arrow-rotation, 45deg)) translate(-1px, 1px);
  }
  50% {
    opacity: 1;
    transform: rotate(var(--arrow-rotation, 45deg)) translate(1px, -1px);
  }
}

@media (max-width: 1024px) {
  .hero-orb {
    display: none;
  }

  .guide-bead-track {
    gap: 5px;
  }

  .guide-arrow {
    min-width: 10px;
  }

  .guide-arrow span {
    height: 7px;
    width: 7px;
  }
}
</style>
