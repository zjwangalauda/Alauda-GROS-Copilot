#!/bin/bash
echo "启动内网穿透..."
echo "正在为您生成公网可访问的 HTTPS 链接，请稍候..."
echo "当您看到 'your url is: https://...' 时，把那个链接发给同事即可。"
echo "请注意：同事第一次打开链接时，可能会看到一个 localtunnel 的提醒页面，只需点击 'Click to Continue' 即可进入应用。"
echo "------------------------------------------------------"
npx localtunnel --port 8502
