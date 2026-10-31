# W07 提交命令与顺序（Team Odie）

提交辅助脚本已经按要求删除。下面全部使用普通 Git 命令。
当前 W07 已整理为一笔本地提交，并由 `w07-midterm` 标签固定。
MAIE6000C 是课程名称，项目名称是 Model 3 Manual Assistant。

## 1. 在 Windows CMD 中检查检查点

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
git status --short
git log --oneline 085885e..HEAD
git rev-parse HEAD
git rev-parse "w07-midterm^{commit}"
```

应只有一笔 W07 提交，最后两条 SHA 应相同。`tatus --porcelain` 如仍出现为未跟踪
文件，它是命令输出临时文件，不属于作业，不要加入提交。不要再次执行已删除的
`prepare-week07-submission.ps1`。

## 2. 推送当前分支和标签

```cmd
git push -u origin feature/oyd
git push origin refs/tags/w07-midterm
git ls-remote origin refs/heads/feature/oyd "refs/tags/w07-midterm^{}"
```

远程分支与标签解析出的 SHA 应与本地检查点一致。本次合并前两笔 W07 提交均未
推送，因此不需要强制推送。若出现拒绝或远程标签已存在，先检查远程状态，不要
直接覆盖他人的提交或课程标签。

## 3. 复制 Canvas 提交文本

```cmd
type "submissions\week07\CANVAS_SUBMISSION.txt"
type "submissions\week07\CANVAS_SUBMISSION.txt" | clip
```

该文件已同步合并后的真实标签 SHA，并且按设计不纳入 Git，避免自引用。若以后
又修改了检查点，请用第 1 步的 `git rev-parse` 输出更新 Tagged commit SHA 字段。

## 4. 在 Canvas 完成提交

当前作业页：https://canvas.ust.hk/courses/74201/assignments/461342

1. 点击 Start Assignment，在文字输入框粘贴完整的 Canvas 提交文本。
2. 附上 `submissions/week07/Odie_W07_Midterm_Demo.pptx`，检查上传结果。
   主报告及提交文本也包含该 PPT 的仓库标签链接，推送后可访问。
3. 检查组名 Odie、仓库地址、标签与 SHA，然后点击 Submit Assignment。
4. 确认页面显示提交成功及提交时间。

四份必需文档、测试与运行证据都随仓库检查点提交。PPT、文字和
仓库是同一份里程碑材料的不同部分。Git 推送不替代 Canvas 的最终提交。
W07 截止时间为 2026-10-31 17:30 香港时间，开放至 11 月 7 日不代表延期。

## 5. 运行环境

运行与恢复步骤见 `docs/operations.md`、`docs/startup-zh.md`。
AutoDL 的后台网关仍在运行时，只需维持 SSH 隧道，不要启动第二份网关。
若本地尚无 6001 隧道，可在另一个 CMD 窗口执行：

```cmd
ssh -N -p 16814 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:6001:127.0.0.1:6001 root@region-9.autodl.pro
```

按提示输入密码并保持窗口打开。新问答需要 AutoDL GPU 服务，已保存的问答文本
可在本地历史中读取。密码、私有配置、模型权重与数据库文件不在提交材料中。
