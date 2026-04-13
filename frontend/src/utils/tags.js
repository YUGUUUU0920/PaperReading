const THEME_META = {
  大模型: { tone: "model", description: "训练策略、能力边界、推理效率与系统设计。" },
  多模态: { tone: "multimodal", description: "让文本、图像、视频与语音在同一模型里协同理解。" },
  RAG: { tone: "retrieval", description: "检索增强、知识注入与外部记忆的最新实践。" },
  智能体: { tone: "agent", description: "任务分解、工具调用与行动闭环的系统能力。" },
  推理: { tone: "reasoning", description: "数学、逻辑、程序与长链推断能力的提升。" },
  强化学习: { tone: "control", description: "决策、探索、奖励建模与策略优化。" },
  扩散模型: { tone: "generative", description: "生成、编辑、采样与高保真建模。" },
  图学习: { tone: "graph", description: "图结构表示、关系推断与结构化学习。" },
  机器人: { tone: "control", description: "具身控制、策略学习与真实环境决策。" },
  代码生成: { tone: "reasoning", description: "编程代理、代码合成与自动修复。" },
  对齐: { tone: "retrieval", description: "安全、偏好学习、价值对齐与行为约束。" },
  计算机视觉: { tone: "multimodal", description: "感知、理解与视觉表示学习。" },
  自然语言处理: { tone: "model", description: "语言理解、生成与文本任务基础能力。" },
  视频理解: { tone: "multimodal", description: "时空建模、视频问答与长视频推断。" },
  语音音频: { tone: "multimodal", description: "语音理解、音频生成与跨模态听觉建模。" },
  时间序列: { tone: "graph", description: "预测、异常检测与时序模式发现。" },
  世界模型: { tone: "generative", description: "环境建模、预测规划与长期模拟。" },
  推荐系统: { tone: "graph", description: "排序、召回与用户行为建模。" },
  联邦学习: { tone: "systems", description: "分布式协作训练与跨端隐私保护。" },
  医疗AI: { tone: "data", description: "医学数据建模、临床推断与健康场景应用。" },
  隐私安全: { tone: "systems", description: "模型安全、隐私防护与可靠性设计。" },
  数据集: { tone: "data", description: "新数据资源、构建流程与数据质量设计。" },
  基准评测: { tone: "data", description: "公开 benchmark、评估协议与能力对比。" },
  评测分析: { tone: "data", description: "诊断、误差拆解与系统性评估方法。" },
  人工智能: { tone: "default", description: "跨方向研究与综合方法线索。" },
};

const SIGNAL_TONES = {
  开源了代码: "resource",
  开源模型: "resource",
  开放获取: "resource",
  "含 OpenReview": "resource",
  引用量高: "impact",
  高被引: "impact",
  新晋热门: "impact",
  影响力强: "impact",
  口头报告: "track",
  聚光论文: "track",
  补充收录: "track",
};

export const FEATURED_THEMES = ["大模型", "多模态", "RAG", "智能体", "推理", "强化学习", "扩散模型", "图学习"];
export const THEME_ORDER = Object.keys(THEME_META);
export const THEME_GROUPS = [
  {
    title: "模型与推理",
    description: "围绕模型能力、推理质量与任务规划的主题入口。",
    themes: ["大模型", "推理", "智能体", "代码生成", "对齐", "自然语言处理"],
  },
  {
    title: "多模态与感知",
    description: "覆盖视觉、视频、语音与跨模态理解的核心方向。",
    themes: ["多模态", "计算机视觉", "视频理解", "语音音频", "扩散模型"],
  },
  {
    title: "决策与世界建模",
    description: "更偏向行动、控制、环境理解与长期规划。",
    themes: ["强化学习", "机器人", "世界模型", "时间序列", "推荐系统"],
  },
  {
    title: "数据、系统与评测",
    description: "关注检索、数据构建、评测协议与系统可靠性。",
    themes: ["RAG", "图学习", "联邦学习", "隐私安全", "数据集", "基准评测", "评测分析", "医疗AI"],
  },
];

export function getTagTone(tag) {
  return THEME_META[tag]?.tone || SIGNAL_TONES[tag] || "default";
}

export function getThemeMeta(theme) {
  return THEME_META[theme] || THEME_META.人工智能;
}

export function pickPrimaryTheme(tags = []) {
  for (const theme of THEME_ORDER) {
    if (tags.includes(theme)) return theme;
  }
  return "人工智能";
}

export function toTagId(tag) {
  return encodeURIComponent(tag).replaceAll("%", "");
}
