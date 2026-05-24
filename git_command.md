# Git 常用指令
1. 查看提交记录
git log --oneline

2. 暂存所有修改
git add .

3. 提交备注
git commit -m "备注内容"

4. 推送到远程
git push

5. 回退上一个版本（写崩复原）
git reset --hard HEAD~1

6. 回退到指定版本
git reset --hard 对应commit_id

7. 放弃本地所有修改
git checkout .