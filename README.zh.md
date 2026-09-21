> 中文 · **[English](README.md)**

# ratch

人可以守一份团队约定。Agent 没有那种尴尬：写成 prompt 或政策文件，
下一轮仍可能再犯，而 git 的 author 已经不能标明是哪智能体在推进。
ratch 把约定做成每次提交都能复算的事实 —— agent 结对下的极限编程。

## 安装

```bash
pip install ratch
```

仓库根放 `ratch_checks.py`（最小样例见 `examples/ratch_checks.py`）。没有这份文件则什么都不跑。然后：

```bash
python -m ratch check
python -m ratch check --compact
python -m ratch list
python -m ratch describe no-forbidden-literal
```

闸失败则非零退出；空 `patterns=` / `needles=` 为 VACUOUS（退出 2），逼你配针。眼睛只打印，不改退出码。`ratch list` 标 enabled / catalog / meta。

## 插件

**出处** — 提交身份不再是某个人：

- `no-forbidden-literal` — 你传入的字面量；空 `patterns=` 为 VACUOUS
- `no-first-person` — 记录散文去掉第一人称
- `no-ai-signatures` — 归属拖车；`sources=` 可加 tags/files；浅克隆 FAIL

**树里会留下的残渣：**

- `no-conflict-markers` — 没结束的合并标记
- `no-vacuous-assert` — 占位的 `assert True` / `assert False`
- `no-pytest-skip` — skip 掉却显示绿灯的测试；e2e 用 `paths=` 收窄
- `no-hash-named-test` — 文件名带一段随后没人认得的十六进制
- `todo-has-issue-ref` — 没有 issue 引用的欠债标记
- `bdd-test-conventions` — 测试名读成一句话；`prefix=` / `blank_blocks=`
- `no-circular-import` — 只有一种 import 顺序能装上的包
- `no-reassurance-words` — 让读者停止核对的安抚腔
- `loc-cap` — Python 模块超过 1000 行
- `no-external-font-cdn` — 已交付 HTML/CSS/JS 去拉远程字体；没有网页文件则为不适用

**约定也必须套在约定上：**

- `plugin-registry` — 每个插件有植物、夹具和四段标题（meta）
- `manifest-purity` — `ratch_checks.py` 可导入且可重复
- `no-internal-refs` — 你传入的针；空 `needles=` 为 VACUOUS
- `doc-counts-match-ssot` — README 的 `catalog_n` 等于 `discover()`（meta）
- `docs-equal-fresh-render` — 生成区等于现场渲染（meta）
- `tests-repo-root-ssot` — 测试共用一个 ROOT，不自己 walk `__file__` 父目录
- `injected-clock` — 有 Clock 类型时禁止绑定后的 stdlib time/datetime 调用
- `doc-cli-examples-valid` — 文档里的 ratch 命令能被 argparse 解析
- `no-autoclose-keywords-in-commits` — 提交说明不会误关 issue

**眼睛** — 证据，从不让一次运行失败：

- `catalog-size` — `enabled_n` 对 `catalog_n`（轮子入口数，不是欠债）
- `commit-heatmap` — 仍跟踪的文件 × 时间；`--compact` 压成一行

不闸品味、命名、散文和测试是否有意义。本仓用根上 `ratch_checks.py`
自托管。完整英文正文见 [README.md](README.md)。目录现算，不在此手抄数量。

## License

[Apache License 2.0](LICENSE).
