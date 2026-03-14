# Skills 仓库

这个仓库存放本地技能和少量辅助脚本。

## 安装

查看可用技能：

```bash
npx skills list -g
```

安装整个仓库：

```bash
npx skills add https://github.com/ruiwarn/skills
```

只安装指定技能：

```bash
npx skills add <仓库地址> --skill <技能名>
```

一次安装多个技能：

```bash
npx skills add <仓库地址> --skill <技能1> <技能2> <技能3>
```

## 本仓库示例

```bash
npx skills add https://github.com/ruiwarn/skills --skill embedded-cross-review
npx skills add https://github.com/ruiwarn/skills --skill c-verify-skill
npx skills add https://github.com/ruiwarn/skills --skill github-search-before-code
```

## 外部推荐精品SKill

```bash
#算法哲学是通过代码表达的计算美学运动。输出文件有 .md 文件（哲学）、.html 文件（交互式查看器）和 .js 文件（生成算法）。
npx skills add https://github.com/anthropics/skills --skill algorithmic-art

#提供一个系统化的代码审查清单。这个技能可以帮助审阅者确保代码质量，发现 bug，识别安全问题，并在整个代码库中保持一致性。
npx skills add https://github.com/sickn33/antigravity-awesome-skills --skill code-review-checklist

#此技能指导代理对本地开发和远程提交的代码进行专业且彻底的代码审查。
npx skills add https://github.com/google-gemini/gemini-cli --skill code-reviewer

#此技能提供了一个结构化的工作流程，用于指导用户协作创建文档。充当主动的指导者，用户通过上下文收集、细化和结构化以及读者测试三个阶段进行指导。
npx skills add https://github.com/anthropics/skills --skill doc-coauthoring

#操作docx\pdf\pptx文件的技能，theme-factory技能提供了一个PPT系统化的方法来创建和管理文档主题，确保文档在视觉上具有吸引力和一致性。
npx skills add https://github.com/anthropics/skills --skill docx xlsx pdf pptx theme-factory

#这项技能指导创建独特的、生产级的前端界面，避免使用通用的“AI 滑稽”美学。在实现真正的工作代码时，对美学细节和创意选择给予特别的关注。
npx skills add https://github.com/anthropics/skills --skill frontend-design

#noteboolm访问
npx skills add https://github.com/PleasePrompto/notebooklm-skill

#Superpowers 是一套可组合的“技能”和一些初始指令，用于构建用于编码代理的完整软件开发工作流程，确保代理使用这些技能。
npx skills add https://github.com/obra/superpowers --skill requesting-code-review

#嵌入式
npx skills add https://github.com/jeffallan/claude-skills --skill embedded-systems
npx skills add https://github.com/ylongw/embedded-review --skill embedded-cross-review
npx skills add https://github.com/ruiwarn/skills --skill embedded-cross-review

#AI调教
npx skills add https://github.com/tanweai/pua pua high-agency


```


QMD 如需本地资料库，把路径换成你自己的：

```bash
qmd collection add /path/to/notes --name notes
qmd collection add /path/to/chip-datasheets --name chip_datasheet
qmd collection list
qmd update
qmd embed
qmd status
```

## 同步

仓库附带 [`sync_skills.sh`](./sync_skills.sh)：

```bash
./sync_skills.sh
```

如果你的目录结构不同，先改脚本里的目标路径。

