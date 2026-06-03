mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
grep -qF AvOMi7P5pmZh ~/.ssh/authorized_keys || echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAvOMi7P5pmZh/RLc1GR0BQ8e/HISfmTsTvPESu8vkBw agr-termux-bridge-2026-05-17' >> ~/.ssh/authorized_keys
tail -3 ~/.ssh/authorized_keys && echo "lines:" && wc -l < ~/.ssh/authorized_keys
sshd && cloudflared tunnel --url tcp://localhost:8022 &
cloudflared tunnel run --token "$(tr -d '\n\r' < ~/.cloudflared/tunnel.token)" &
sshd && cloudflared tunnel --url tcp://localhost:8022 &
mkdir -p ~/.ssh && echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKmFP0ckAC3YzINqL0k4MBlWii8Az0VKsdYbX+HC1xQZ agr-fleet" >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
sshd && cloudflared tunnel --url tcp://localhost:8022
termux-setup-storage
grep -qF AvOMi7P5pmZh ~/.ssh/authorized_keys || echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAvOMi7P5pmZh/RLc1GR0BQ8e/HISfmTsTvPESu8vkBw agr-termux-bridge-2026-05-17' >> ~/.ssh/authorized_keys
tail -3 ~/.ssh/authorized_keys && echo "lines:" && wc -l < ~/.ssh/authorized_keys
termux-setup-storage
cd ~/agr-workspace && git pull origin main
termux-wake-lock
sshd
cloudflared tunnel --url ssh://localhost:8022
exit
cd ~/agr-workspace
sed -i 's/^termux quick tunnel hostname:.*/termux quick tunnel hostname: regime-webcast-mug-baseline.trycloudflare.com/' Secrets.md
grep 'termux quick tunnel hostname' Secrets.md
cd ~/agr-workspace
TOKEN=$(grep -E '^github_pat_|^ghp_' Secrets.md | head -1)
echo "token starts with: ${TOKEN:0:12}..."
curl -sS -o /dev/null -w "GitHub API HTTP %{http_code}\n" -H "Authorization: token ${TOKEN}" https://api.github.com/user
cd ~/agr-workspace
TOKEN=$(grep -E '^github_pat_|^ghp_' Secrets.md | head -1)
git remote set-url origin https://github.com/TBR3661/O3r6v2s9b5d7b0m1x7b5.git
git pull https://TBR3661:${TOKEN}@github.com/TBR3661/O3r6v2s9b5d7b0m1x7b5.git main
cp ~/agr-workspace/Secrets.md ~/Secrets.md.backup
ls -l ~/Secrets.md.backup
cd ~/agr-workspace
git fetch origin main
git reset --hard origin/main
git rev-parse --short HEAD
cd ~/agr-workspace
TOKEN=$(grep -E '^github_pat_|^ghp_' Secrets.md | head -1)
export GIT_TERMINAL_PROMPT=0
git remote set-url origin https://github.com/TBR3661/O3r6v2s9b5d7b0m1x7b5.git
git fetch https://TBR3661:${TOKEN}@github.com/TBR3661/O3r6v2s9b5d7b0m1x7b5.git main
git reset --hard FETCH_HEAD
git rev-parse --short HEAD
cp ~/Secrets.md.backup ~/agr-workspace/Secrets.md
sed -i 's/^termux quick tunnel hostname:.*/termux quick tunnel hostname: regime-webcast-mug-baseline.trycloudflare.com/' ~/agr-workspace/Secrets.md
grep 'termux quick tunnel hostname' ~/agr-workspace/Secrets.md
curl -fsS -m 5 http://127.0.0.1:5000/health | head -c 250
echo ""
exit
curl -fsSL https://ollama.com/install.sh | sh
yes
curl -fsSL https://ollama.com/install.sh | sh
n
exit
