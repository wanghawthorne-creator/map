# Data dictionary / 字段说明 v0.1

一行/对象对应一个待维护地点实体，不按每次截图新建实体。JSON是当前唯一地点数据源，UTF-8；空值用`null`，列表无已确认项用`[]`，不用0、空串或虚构日期占位。[样例](../data/places.json)不含精确住宅位置或活动路线。

| Field | Type / rule | Meaning |
|---|---|---|
| place_id | unique string | 稳定地点ID；更名不换ID，合并保留重定向记录 |
| record_kind | source_reported_real_place | 真实来源提及，区别模拟；当前只接受这一种 |
| display_name | nonempty string | 工作展示名；不是官方标准名声明 |
| name_status | source_reported | 名称依据等级 |
| aliases_verified | string array | 仅放有独立证据及审核记录的别名；[]是尚未确认 |
| category_provisional | controlled string | 当前允许 community_reading_and_cultural_space / unknown；宽泛功能标签 |
| reported_address | string or null | 忠实保存来源区位，不自动标准化成官方地址 |
| verified_address | string or null | 待可靠证据支持的完整地址；当前null |
| admin_village_verified | string or null | 核实的行政村归属；不能从报道中的“村”直接填写 |
| longitude / latitude | finite number pair or both null | 原始记录坐标，必须关联CRS和来源；不代表已可发布 |
| crs | WGS84 / GCJ-02 / BD-09 / null | null表示未确认；未知不可猜WGS84 |
| coordinate_source_ids | source ID array | 坐标专属证据；有坐标时必须非空 |
| source_ids | nonempty source ID array | 指向 evidence/sources.json，外键必须存在 |
| claim_ids | nonempty claim ID array | 指向 evidence/claims.json，每项主张的范围和证据 |
| source_published_on | YYYY-MM-DD or null | 当前单一主要来源的文章发布日期；未来多源各日期放来源表 |
| source_checked_on | YYYY-MM-DD | 本轮来源读取日期，不等于现场观察 |
| observed_on | YYYY-MM-DD or null | 有原始记录支持的本人观察日；不从发布日期推断 |
| last_verified_on | YYYY-MM-DD or null | 对地点事实进行实质核验的日期；不等于读新闻日 |
| current_operation_status | unable_to_verify / reported_active / reported_closed | 即使来源报告活跃/关闭也保留reported，需逐项日期/证据 |
| verification_status | historically_reported_location_unverified / reviewed_with_evidence | 总体审核阶段；不代替属性判断 |
| location_status | missing_evidence / source_recorded / reviewed | 点位证据阶段 |
| spatial_precision | unknown / approximate / entrance | 精度对象；不声明误差米数 |
| map_release_status | pending_review / approved / withheld | 点位拟公开审批阶段；不表示已部署 |
| privacy_review_status | pending_review / approved / withheld | 独立隐私复核 |
| notes | string | 保留不确定性和不能自动推断的事项 |

`sources.json`每项含source_id、kind、title、URL（可空）、发布日期（可空）、查阅日、实际访问状态、段落定位、自写摘要、限制和再使用范围。`claims.json`含claim_id、place_id、field、判断、范围、source_ids与checked_on。每项判断沿这些ID追溯。

自动检查只实现重要结构约束，不宣称是覆盖所有语义的通用JSON Schema。别名真实性、行政归属、精度、许可和审阅者身份必须人工核对。当前无 GeoJSON 导出，避免将null地点默认为原点；以后导出只接收已复核WGS84、来源齐全且获准公开的几何。
