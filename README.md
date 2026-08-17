# AI Coding Task Evaluator

一个面向 AI Coding 训练任务的轻量级自动评测器。它把“任务要求”转成结构化检查项，执行提交代码的验证命令，并输出可追踪的分项得分与失败原因。

## 为什么做这个项目

AI Coding 任务不仅要判断代码能否运行，还要保证评测规则可复现、权重透明、失败信息可定位。本项目演示了任务专家常见的三类工作：

- 把自然语言验收标准结构化为 JSON 任务规范；
- 对功能、边界条件和回归测试进行加权评分；
- 生成机器可读的 JSON 报告，便于训练数据复核与质量分析。

## 快速开始

```bash
python -m ai_task_evaluator.cli examples/task.json examples/submission
```

也可以在项目根目录直接运行：

```bash
python -m unittest discover -s tests -v
```

## 任务规范

```json
{
  "id": "sum-positive-v1",
  "title": "实现正整数求和",
  "timeout_seconds": 3,
  "checks": [
    {
      "name": "basic_case",
      "command": ["python", "solution.py", "1", "2", "3"],
      "expected_exit_code": 0,
      "stdout_equals": "6",
      "weight": 60
    }
  ]
}
```

每个检查项都保留执行耗时、退出码、标准输出和失败原因。总分按权重归一化到 100 分。

## 安全边界

该项目用于本地、受信任的作品集任务。它会执行任务规范中的命令，不是生产级沙箱；真实平台应增加容器隔离、网络限制、资源配额和恶意代码检测。

## 技术亮点

- Python 标准库实现，无第三方运行时依赖；
- 规范校验、超时控制、输出截断和确定性计分；
- 单元测试覆盖通过、输出不匹配、非零退出和超时场景；
- 清晰区分评测结果与基础设施错误。

## 仓库标签建议

`ai-coding` `evaluation` `benchmark` `python` `training-data` `quality-assurance`

## License

MIT
