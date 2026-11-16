# Resume and interview notes / 简历与面试草稿

仅使用与当前阶段相符的版本；当前尚未完成可浏览地图/5案/本人独立复核，不能写成最终成果。AI代码不等于本人编程技能。不得宣称通过OneForma认证或存在雇佣关系。

## 当前可用，但先由本人核实贡献

**中文：** 老太沟地图与搜索质量评估案例（个人作品集，进行中）：基于云南大理田野背景，与AI协作建立来源可追溯的地点记录及评估草稿，分别讨论实体相关性、名称、地址、类别、点位和时效；保留未知坐标与信息冲突，整理证据目录与数据质量问题。正在补充地理核验及本人复核。

**English:** Laotaigou Mapping & Search Quality Evaluation Case Study — Independent portfolio, in progress. Drawing on my fieldwork background in Dali, I am developing source-traceable place records and evaluation cases with AI assistance, separating entity relevance from name, address, category, pin and temporal checks. Current work documents missing coordinates, conflicting place-name evidence and verification limits; geographic validation and my review are ongoing.

如果本人尚未看懂或复核当前包，简历中宜先写“正在整理”而不是“完成”。不能把本轮代码执行、网页研究都描述为本人独立完成。

## 一分钟讲解提纲

1. 我为什么熟悉这里：讲一项能明确归属于自己的观察或志愿经历，给真实时间，不念AI补写的经历。
2. 我遇到的问题：书苑名称是老太沟，资料区位又写老太箐；同一叙事出现不等于官方别名。
3. 我怎么判断：先明确查询找什么，再按名称/地址/类别/点位逐项查证。可说明历史报道支持名称，却不支持今天的入口位置。
4. 我保留什么未知：经纬度为空、现状U、行政村归属待核，避免把示意中心当真实点。
5. 说明贡献边界：自己提供的田野背景与已复核判断；AI协助的检索、结构、英文与代码。

## 五分钟演示

打开README→C01→LTG-P001→CL-001→E-PUB-001。说明为何查阅日不等于现场核验日；解释“来源报道名称”和“官方标准名”的区别。运行`python scripts/qa.py`，指出结构通过也可能没有任何可公开坐标；说明下一步如何取公共入口证据、核对CRS与许可。最后说明评分自建，与招聘方培训规则分别处理。

## 自测问题

- R3相关性与U点位如何同时成立？如果改问“现在怎么去”，结论怎样变？
- 为什么不把老太沟/老太箐直接列为别名？何种材料能改变判断？
- 为什么不填村中心坐标？六位小数能证明什么、不能证明什么？
- 如果同一新闻被转载三次，是三个独立证据吗？
- 如果只在网页看见照片，能公开复制吗？
- 哪部分是自己做的、哪部分借助AI？代码检查能核实什么？

答不清楚时回到来源与范围修订，不记忆一个显得专业但不能解释的结论。
