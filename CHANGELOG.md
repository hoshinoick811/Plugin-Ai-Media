# 更新日志

本文件依据 git tag 历史整理，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。
新提交合入后请在 `## [Unreleased]` 下记录，发布时随版本 tag 归档。

## [4.3.16] - 2026-08-30

- fix(sing): 唱歌/点歌确认回复改同步直发，消除异步投递延迟

## [4.3.15] - 2026-08-18

- fix(sing): 撤回取消任务日志按规范改为英文叙事句式

## [4.3.14] - 2026-08-18

- fix(sing): 撤回点歌/唱歌消息时取消未开始的任务，避免撤回后仍投递歌曲

## [4.3.13] - 2026-08-14

- refactor(log): 唱歌/点歌/语音请求补接单日志，日志按正文/运维约定整改

## [4.3.12] - 2026-08-13

- fix(sing): direct 唱歌与点歌改用 durable work job 提交，避免远程歌曲查询与媒体服务请求阻塞 MessageRuntime 调度。

## [4.3.11] - 2026-08-11

- feat(logging): 统一提交诊断文案并补启动日志

## [4.3.10] - 2026-08-11

- feat(logging): 投递事件分型并按任务区分，统一事件文案

## [4.3.9] - 2026-08-11

- feat(logging): 补充唱歌与语音合成投递完成事件

## [4.3.8] - 2026-08-11

- feat(logging): 补充唱歌 / 语音合成受理与网易云绑定业务事件日志

## [4.3.7] - 2026-08-10

- feat(tts): 「牛牛说」接入 MessageRuntime prefix direct 与 durable work job，保留既有 AI callback 发语音链路
- feat(sing): 接入 MessageRuntime direct 路径，并统一唱歌、随机播放与点歌的异步提交生命周期

## [4.3.6] - 2026-08-03

- fix(sing): 帮助详情将可用音色改为分组列表展示，长音色列表可完整折行

## [4.3.5] - 2026-08-02

- fix(sing): 帮助「可用音色」只展示触发名并按同音色归组，不再暴露 speaker id

## [4.3.4] - 2026-08-02

- fix(sing): 裸「〈音色〉唱歌」随机播放后挡住闲聊，避免 LLM 再派发导致连续投歌；随机 play 仅匹配整句前缀命令

## [4.3.3] - 2026-08-02

- feat(sing): 音频映射变更时同步帮助 usage / menu 触发文案与可用音色；`reload_policy` 设为 metadata

## [4.3.2] - 2026-08-01

- fix(sing): 音频映射（`sing_speakers`）变更时同步展开为 ingress `command_prefixes`，自定义前缀如「一歌唱歌」可被路由命中

## [4.3.1] - 2026-07-30

- fix(tts): 「牛牛说」后须有空格，避免「牛牛说啥呢」误触发
- feat(tts): soft-recall hints 补充「念出来」「把你的话」等

## [4.3.0] - 2026-07-29

- feat(config): 服务地址 / Bearer 改由 AI 配置 · 媒体服务统一管理；唱歌与 TTS 插件页隐藏相关字段，运行时优先读 `AI_SERVER_*` / `TTS_API_TOKEN`
- feat(config): 音色映射、默认合成时长等业务项仍在插件配置（控制台媒体页可嵌入）

## [4.2.1] - 2026-07-28

- fix(tts): `api_token` 经 `field_to_env` 读取 `TTS_API_TOKEN`，修复侧车 `/v1/tts` 401

## [4.2.0] - 2026-07-27

- feat(tts): 新增 `pallas_plugin_tts`（口令「牛牛说」→ 侧车 `/v1/tts`，预留 cloud 通路）

## [4.1.8] - 2026-07-26

- feat(llm_tools): 点歌 hints 补充我想听等口语

## [4.1.7] - 2026-07-26

- fix(sing): 点歌下发后写入 sing_progress，避免「什么歌」读到旧曲目

## [4.1.6] - 2026-07-26

- feat(llm_tools): 点歌 hints 补充放首/来首口语

## [4.1.5] - 2026-07-26

- feat(sing): 闲聊工具声明口语触发说法（如音乐、放首歌），便于 @ 对话唤起点歌/翻唱

## [4.1.4] - 2026-07-26

- feat(config): WebUI 配置字段增加 ui_group 分组与 ui_order 排序


## [4.1.3] - 2026-07-25

- feat: 声明群口令 `llm_tools`，供闲聊 selective 工具调用
## [4.1.2] - 2026-07-25

- feat: PluginMetadata.extra 增加 `help_tag`（帮助图分组）

## [4.1.0] - 2026-07-24

- breaking: 移除 `pallas_plugin_chat`；酒后对话改由本体 `llm_chat` 承接（可选 `CHAT_TTS_ENABLE` 走 AI 仓 TTS）
- docs: 包展示与说明改为「牛牛唱歌」

## [4.0.20] - 2026-07-24

- docs: 说明酒后 `chat` 仍作为旧版 AI 路径保留；与本体 `llm_chat` 并存时由本体让路避免双回复
- docs: 展示与说明改为以「牛牛唱歌」为主能力

## [4.0.19] - 2026-07-18

- fix(sing): 点歌/唱歌收尾文案对 ActionFailed（如 result=120 协议拒发）降级为 warning，避免 worker LogError；点歌失败路径先清理任务再结束，并改用本 matcher

## [4.0.18] - 2026-07-03

- perf(sing): rule 匹配跳过日志改为 DEBUG 且默认关闭（`sing_rule_debug`），避免每条群消息刷 3 条 INFO

## [4.0.17] - 2026-06-27
- docs(readme): 命令权限默认等级改用中文展示

## [4.0.16] - 2026-06-27

- feat(sing): 补齐牛牛唱歌/点歌等命令权限声明，冷却改用统一 command_limits 并显示中文名

## [4.0.15] - 2026-06-27
- docs(readme): 「怎么使用」口令统一加行内代码标记

## [4.0.14] - 2026-06-27
- fix(sing): 恢复 `sing_runtime_mode` 配置与解析函数，修复牛牛连通探活 AttributeError

## [4.0.13] - 2026-06-26
- fix(chat): 醉话走统一 LLM 提交并构建 drunk system prompt，保留 legacy RWKV 回退

## [4.0.12] - 2026-06-25
- feat(metadata): 补充网易云登录/登出命令冷却声明

## [4.0.11] - 2026-06-24
- fix sing callback task key mismatch
- feat(knowledge): 声明 knowledge_sources FAQ 供 LLM 注入

## [4.0.10] - 2026-06-21
- fix(chat): route drunk chat through unified llm submit

## [4.0.9] - 2026-06-21
- fix: align sing play callback request ids

## [4.0.8] - 2026-06-19
- docs(assets): 更新头像资源并改用 PyPI 版本徽章
- fix(sing): 补充媒体请求诊断并提升纯唱歌命中优先级
- chore(assets): 替换品牌头像为透明背景版本
- chore(release): 发布 4.0.8

## [4.0.7] - 2026-06-19
- chore(release): 4.0.2 同步 README 进 PyPI 包
- migrate: src.* → pallas.api.* / pallas.product.* / pallas.core.*
- release: bump to 4.0.3 for pallas import migration
- docs(readme): 更新官方扩展安装命令
- docs(readme): 统一官方插件卡片模板
- fix(ai-media): 修复 4.0 主仓兼容与任务回调问题
- chore(release): 发布 4.0.7

## [4.0.6] - 2026-06-19
- docs(ai-media): 统一文档与元数据
- fix(sing): 修复 AI 媒体插件 task_id 回调断链
- chore(release): 发布 4.0.3
- chore(release): 发布 4.0.6

## [4.0.5] - 2026-06-18
- docs(readme): 统一官方插件卡片模板

## [4.0.4] - 2026-06-18
- docs(readme): 更新官方扩展安装命令

## [4.0.3] - 2026-06-18
- migrate: src.* → pallas.api.* / pallas.product.* / pallas.core.*
- release: bump to 4.0.3 for pallas import migration

## [4.0.2] - 2026-06-18
- fix(sing): 移除 ncm_login 未使用的 PluginMetadata 导入
- chore: ruff format ai-media 插件源码
- docs(readme): 添加 Pallas-Bot hero 图
- chore(release): 4.0.2 同步 README 进 PyPI 包

## [4.0.1] - 2026-06-17
- feat: Pallas-Bot 4.0 官方扩展首包
- fix(build): 修正 hatch wheel 的 src 包路径
- feat(release): PyPI 发版 workflow 与 4.0.1
