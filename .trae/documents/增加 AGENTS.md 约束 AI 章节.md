我将为 `AI_ONE_PERSON_TEAM_GUIDE.md` 增加一个新的章节，专门讲解如何利用 `AGENTS.md` 和 `.rules` 文件来“驯服”AI，使其产出符合团队规范的高质量代码。

### 更新计划

1.  **新增“3.5 进阶：利用 AGENTS.md 建立 AI 协作协议”章节**：
    *   **核心理念**：AI 不仅需要“指令 (Prompt)”，更需要“宪法 (Constitution)”。`AGENTS.md` 就是项目级的 AI 宪法。
    *   **实施方法**：
        *   **显式声明**：在项目根目录创建 `AGENTS.md` 或 `CLAUDE.md`，明确告知 AI 项目的架构模式（如六边形架构）、关键文件路径和编码规范。
        *   **规则引用**：引用 `domain_driven_design_hexagonal_arhictecture_python_rules.md` 等详细规则文件，作为 AI 编程的“最高指示”。
        *   **上下文预设**：在文件中定义 `Repository Overview` 和 `Architecture Principles`，让 AI 在进入项目的第一秒就理解“我是谁，我在哪，我要做什么”。
    *   **实战价值**：
        *   减少重复提示：无需每次对话都重复“请使用六边形架构”。
        *   保持一致性：确保不同 AI Session 生成的代码风格统一。

2.  **调整目录结构**：
    *   将该章节插入到“Trae 研发方法论”中，作为提升 AI 协作质量的关键一环。

3.  **最终效果**：
    *   文档将包含从“工具选择”到“工作流定义”再到“规则约束”的完整 AI 协作体系。

确认计划后，我将立即执行修改。