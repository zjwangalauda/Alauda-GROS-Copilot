#!/bin/bash
echo "=========================================================="
echo "正在启动企业级 Cloudflare 穿透隧道..."
echo "不需要申请域名，也不需要填写烦人的 IP 密码验证！"
echo ""
echo "请在下方输出的信息中，寻找类似这样的链接："
echo "👉  https://some-random-words.trycloudflare.com  👈"
echo ""
echo "把它发给你的同事，他们点开就能直接无缝使用系统！"
echo "=========================================================="
/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8502
