@bot.event
async def on_ready():
    print(f"🤖 Bot đã chạy ngầm thành công: {bot.user}")
    if not auto_quest_task.is_running():
        auto_quest_task.start()
    
    # Bắt buộc bot phải gửi tin nhắn báo cáo lên kênh ngay khi vừa khởi động
    await asyncio.sleep(3)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🔔 **Bot đã khởi động thành công và đang kết nối hệ thống tự động!**")
        
        # Tiến hành quét và gửi kết quả
        result = await run_auto_quest()
        if isinstance(result, list):
            if len(result) == 0:
                await channel.send("✅ Đã quét xong nhưng tài khoản hiện tại không có nhiệm vụ mới nào.")
            else:
                embed = discord.Embed(
                    title="🎯 BÁO CÁO KHỞI ĐỘNG HỆ THỐNG QUEST",
                    description="Danh sách các Quest đang có trên tài khoản:",
                    color=0x57F287
                )
                for idx, q in enumerate(result, 1):
                    status_text = "✅ Đã xong" if q["completed"] else "⏳ Đang xử lý"
                    embed.add_field(
                        name=f"#{idx}. {q['name']}",
                        value=f"🎮 **Game:** {q['game']}\n📌 **Trạng thái:** {status_text}",
                        inline=False
                    )
                await channel.send(embed=embed)
        else:
            await channel.send(f"⚠️ Kết quả trả về: {result}")
