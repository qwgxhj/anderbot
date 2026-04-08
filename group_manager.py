from __future__ import annotations

import asyncio
from typing import Any

from anderbot.config import settings
from anderbot.core.models import PluginMeta
from anderbot.core.plugin_base import BasePlugin


class Plugin(BasePlugin):
    meta = PluginMeta(
        name="group_manager",
        version="0.1.0",
        description="群管助手：踢人、禁言、改群名、撤回消息、关键词屏蔽、入群欢迎",
        commands=[
            "/kick", "/mute", "/ban", "/unban",
            "/setname", "/setcard", "/announce",
            "/recall", "/clean",
            "/groupinfo", "/memberlist", "/membercount",
            "/keyword",
            "/welcome",
        ],
    )

    def __init__(self, manager):
        super().__init__(manager)
        self._keywords: set[str] = set()
        self._welcome_msg: str = ""
        self._load_config()

    def _load_config(self) -> None:
        """从存储加载配置"""
        data = self.bot.store.read()
        self._keywords = set(data.get("group_keywords", []))
        self._welcome_msg = data.get("group_welcome", "")

    def _save_config(self) -> None:
        """保存配置到存储"""
        data = self.bot.store.read()
        data["group_keywords"] = sorted(self._keywords)
        data["group_welcome"] = self._welcome_msg
        self.bot.store.write(data)

    async def handle_message(self, event) -> bool:
        text = event.text
        
        # 关键词检测（非指令消息）
        if not text.startswith("/"):
            return await self._check_keywords(event)
        
        # 解析@用户
        at_qq = self._extract_at_qq(event)
        
        # ========== 成员管理 ==========
        
        if text.startswith("/kick "):
            return await self._cmd_kick(event, text, at_qq)
        
        if text.startswith("/mute "):
            return await self._cmd_mute(event, text, at_qq)
        
        if text.startswith("/ban "):
            return await self._cmd_ban(event, text, at_qq)
        
        if text.startswith("/unban "):
            return await self._cmd_unban(event, text, at_qq)
        
        # ========== 群设置 ==========
        
        if text.startswith("/setname "):
            return await self._cmd_setname(event, text)
        
        if text.startswith("/setcard "):
            return await self._cmd_setcard(event, text, at_qq)
        
        if text.startswith("/announce "):
            return await self._cmd_announce(event, text)
        
        # ========== 消息管理 ==========
        
        if text.startswith("/recall"):
            return await self._cmd_recall(event, text)
        
        if text == "/clean":
            return await self._cmd_clean(event)
        
        # ========== 群信息查询 ==========
        
        if text == "/groupinfo":
            return await self._cmd_groupinfo(event)
        
        if text == "/memberlist":
            return await self._cmd_memberlist(event)
        
        if text == "/membercount":
            return await self._cmd_membercount(event)
        
        # ========== 关键词管理 ==========
        
        if text.startswith("/keyword "):
            return await self._cmd_keyword(event, text)
        
        # ========== 入群管理 ==========
        
        if text.startswith("/welcome "):
            return await self._cmd_welcome(event, text)
        
        return False

    async def on_group_increase(self, event) -> None:
        """处理入群事件"""
        if not self._welcome_msg or not event.group_id:
            return
        
        user_id = event.user_id
        welcome = self._welcome_msg.replace("{at}", f"[CQ:at,qq={user_id}]")
        await self.bot.send_group(event.group_id, welcome)

    def _extract_at_qq(self, event) -> int | None:
        """从消息中提取@的QQ号"""
        for seg in event.message_segments:
            if seg.get("type") == "at":
                qq = seg.get("data", {}).get("qq")
                if qq and qq != "all":
                    return int(qq)
        return None

    def _is_superuser(self, user_id: int) -> bool:
        """检查是否为超级用户"""
        return user_id in settings.superuser_ids

    # ========== 成员管理命令 ==========

    async def _cmd_kick(self, event, text: str, at_qq: int | None) -> bool:
        """踢出成员 /kick @用户 或 /kick QQ号"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        # 解析目标QQ
        target_qq = at_qq
        if not target_qq:
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                target_qq = int(parts[1])
        
        if not target_qq:
            await self.bot.reply(event, "用法：/kick @用户 或 /kick QQ号")
            return True
        
        try:
            await self.bot.napcat.call_api("set_group_kick", {
                "group_id": event.group_id,
                "user_id": target_qq,
                "reject_add_request": False
            })
            await self.bot.reply(event, f"已将 {target_qq} 移出群聊")
        except Exception as exc:
            await self.bot.reply(event, f"踢出失败：{exc}")
        return True

    async def _cmd_mute(self, event, text: str, at_qq: int | None) -> bool:
        """禁言成员 /mute @用户 分钟数"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        target_qq = at_qq
        parts = text.split()
        
        # 解析分钟数
        minutes = 30  # 默认30分钟
        if len(parts) >= 2:
            try:
                minutes = int(parts[-1])
            except ValueError:
                pass
        
        if not target_qq and len(parts) >= 2:
            if parts[1].isdigit():
                target_qq = int(parts[1])
        
        if not target_qq:
            await self.bot.reply(event, "用法：/mute @用户 [分钟数] 或 /mute QQ号 分钟数")
            return True
        
        duration = minutes * 60  # 转换为秒
        
        try:
            await self.bot.napcat.call_api("set_group_ban", {
                "group_id": event.group_id,
                "user_id": target_qq,
                "duration": duration
            })
            if minutes == 0:
                await self.bot.reply(event, f"已解除 {target_qq} 的禁言")
            else:
                await self.bot.reply(event, f"已将 {target_qq} 禁言 {minutes} 分钟")
        except Exception as exc:
            await self.bot.reply(event, f"禁言失败：{exc}")
        return True

    async def _cmd_ban(self, event, text: str, at_qq: int | None) -> bool:
        """永久禁言 /ban @用户"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        target_qq = at_qq
        if not target_qq:
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                target_qq = int(parts[1])
        
        if not target_qq:
            await self.bot.reply(event, "用法：/ban @用户 或 /ban QQ号")
            return True
        
        try:
            # 365天 = 31536000秒
            await self.bot.napcat.call_api("set_group_ban", {
                "group_id": event.group_id,
                "user_id": target_qq,
                "duration": 31536000
            })
            await self.bot.reply(event, f"已将 {target_qq} 永久禁言")
        except Exception as exc:
            await self.bot.reply(event, f"禁言失败：{exc}")
        return True

    async def _cmd_unban(self, event, text: str, at_qq: int | None) -> bool:
        """解除禁言 /unban @用户"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        target_qq = at_qq
        if not target_qq:
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                target_qq = int(parts[1])
        
        if not target_qq:
            await self.bot.reply(event, "用法：/unban @用户 或 /unban QQ号")
            return True
        
        try:
            await self.bot.napcat.call_api("set_group_ban", {
                "group_id": event.group_id,
                "user_id": target_qq,
                "duration": 0
            })
            await self.bot.reply(event, f"已解除 {target_qq} 的禁言")
        except Exception as exc:
            await self.bot.reply(event, f"解除禁言失败：{exc}")
        return True

    # ========== 群设置命令 ==========

    async def _cmd_setname(self, event, text: str) -> bool:
        """修改群名 /setname 新群名"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        new_name = text[9:].strip()  # "/setname " 长度为9
        if not new_name:
            await self.bot.reply(event, "用法：/setname 新群名")
            return True
        
        try:
            await self.bot.napcat.call_api("set_group_name", {
                "group_id": event.group_id,
                "group_name": new_name
            })
            await self.bot.reply(event, f"群名称已修改为：{new_name}")
        except Exception as exc:
            await self.bot.reply(event, f"修改群名失败：{exc}")
        return True

    async def _cmd_setcard(self, event, text: str, at_qq: int | None) -> bool:
        """设置群名片 /setcard @用户 新名片"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        target_qq = at_qq
        parts = text.split(maxsplit=2)
        
        if not target_qq and len(parts) >= 2:
            if parts[1].isdigit():
                target_qq = int(parts[1])
        
        if not target_qq:
            await self.bot.reply(event, "用法：/setcard @用户 新名片 或 /setcard QQ号 新名片")
            return True
        
        # 提取新名片（去掉@部分）
        new_card = ""
        if len(parts) >= 3:
            new_card = parts[2]
        
        if not new_card:
            await self.bot.reply(event, "请指定新名片")
            return True
        
        try:
            await self.bot.napcat.call_api("set_group_card", {
                "group_id": event.group_id,
                "user_id": target_qq,
                "card": new_card
            })
            await self.bot.reply(event, f"已设置 {target_qq} 的群名片为：{new_card}")
        except Exception as exc:
            await self.bot.reply(event, f"设置名片失败：{exc}")
        return True

    async def _cmd_announce(self, event, text: str) -> bool:
        """设置群公告 /announce 公告内容"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        content = text[10:].strip()  # "/announce " 长度为10
        if not content:
            await self.bot.reply(event, "用法：/announce 公告内容")
            return True
        
        try:
            await self.bot.napcat.call_api("_send_group_notice", {
                "group_id": event.group_id,
                "content": content
            })
            await self.bot.reply(event, "群公告已设置")
        except Exception as exc:
            await self.bot.reply(event, f"设置公告失败：{exc}")
        return True

    # ========== 消息管理命令 ==========

    async def _cmd_recall(self, event, text: str) -> bool:
        """撤回消息 /recall 或 /recall 数量"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        parts = text.split()
        count = 1
        
        if len(parts) >= 2:
            try:
                count = int(parts[1])
            except ValueError:
                pass
        
        # 获取回复的消息ID
        reply_msg_id = None
        for seg in event.message_segments:
            if seg.get("type") == "reply":
                reply_msg_id = seg.get("data", {}).get("id")
                break
        
        if reply_msg_id:
            try:
                await self.bot.napcat.call_api("delete_msg", {
                    "message_id": reply_msg_id
                })
                await self.bot.reply(event, "消息已撤回")
            except Exception as exc:
                await self.bot.reply(event, f"撤回失败：{exc}")
        else:
            await self.bot.reply(event, "请回复要撤回的消息")
        
        return True

    async def _cmd_clean(self, event) -> bool:
        """清空最近消息 /clean"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        await self.bot.reply(event, "清空消息功能需要配合消息缓存实现，当前版本暂不支持")
        return True

    # ========== 群信息查询命令 ==========

    async def _cmd_groupinfo(self, event) -> bool:
        """查看群信息 /groupinfo"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        try:
            result = await self._call_api_with_result("get_group_info", {
                "group_id": event.group_id
            })
            info = result.get("data", {})
            msg = f"群名称：{info.get('group_name', '未知')}\n"
            msg += f"群号：{info.get('group_id', event.group_id)}\n"
            msg += f"成员数：{info.get('member_count', '未知')}\n"
            msg += f"最大成员数：{info.get('max_member_count', '未知')}"
            await self.bot.reply(event, msg)
        except Exception as exc:
            await self.bot.reply(event, f"获取群信息失败：{exc}")
        return True

    async def _cmd_memberlist(self, event) -> bool:
        """查看群成员列表 /memberlist"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        try:
            result = await self._call_api_with_result("get_group_member_list", {
                "group_id": event.group_id
            })
            members = result.get("data", [])[:20]  # 只显示前20人
            
            lines = [f"群成员列表（前{len(members)}人）："]
            for m in members:
                card = m.get('card', '')
                nickname = m.get('nickname', '未知')
                name = card if card else nickname
                role = m.get('role', 'member')
                role_str = {'owner': '👑群主', 'admin': '🔧管理', 'member': '👤成员'}.get(role, '👤')
                lines.append(f"{role_str} {name} ({m.get('user_id')})")
            
            await self.bot.reply(event, "\n".join(lines))
        except Exception as exc:
            await self.bot.reply(event, f"获取成员列表失败：{exc}")
        return True

    async def _cmd_membercount(self, event) -> bool:
        """查看群人数统计 /membercount"""
        if not event.group_id:
            await self.bot.reply(event, "该命令只能在群聊中使用")
            return True
        
        try:
            result = await self._call_api_with_result("get_group_member_list", {
                "group_id": event.group_id
            })
            members = result.get("data", [])
            
            owner_count = sum(1 for m in members if m.get('role') == 'owner')
            admin_count = sum(1 for m in members if m.get('role') == 'admin')
            member_count = sum(1 for m in members if m.get('role') == 'member')
            
            msg = f"群人数统计：\n"
            msg += f"总人数：{len(members)}\n"
            msg += f"群主：{owner_count}\n"
            msg += f"管理员：{admin_count}\n"
            msg += f"普通成员：{member_count}"
            await self.bot.reply(event, msg)
        except Exception as exc:
            await self.bot.reply(event, f"获取统计失败：{exc}")
        return True

    # ========== 关键词管理命令 ==========

    async def _cmd_keyword(self, event, text: str) -> bool:
        """关键词管理 /keyword add/del/list 关键词"""
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            await self.bot.reply(event, "用法：/keyword add 关键词\n/keyword del 关键词\n/keyword list")
            return True
        
        action = parts[1]
        
        if action == "add":
            if len(parts) < 3:
                await self.bot.reply(event, "用法：/keyword add 关键词")
                return True
            keyword = parts[2]
            self._keywords.add(keyword)
            self._save_config()
            await self.bot.reply(event, f"已添加屏蔽词：{keyword}")
        
        elif action == "del":
            if len(parts) < 3:
                await self.bot.reply(event, "用法：/keyword del 关键词")
                return True
            keyword = parts[2]
            self._keywords.discard(keyword)
            self._save_config()
            await self.bot.reply(event, f"已删除屏蔽词：{keyword}")
        
        elif action == "list":
            if not self._keywords:
                await self.bot.reply(event, "当前没有屏蔽词")
            else:
                await self.bot.reply(event, f"屏蔽词列表：{', '.join(sorted(self._keywords))}")
        
        else:
            await self.bot.reply(event, "用法：/keyword add/del/list 关键词")
        
        return True

    async def _check_keywords(self, event) -> bool:
        """检查消息是否包含屏蔽词"""
        if not self._keywords or not event.group_id:
            return False
        
        text = event.text.lower()
        for keyword in self._keywords:
            if keyword.lower() in text:
                try:
                    # 撤回消息
                    if event.message_id:
                        await self.bot.napcat.call_api("delete_msg", {
                            "message_id": event.message_id
                        })
                    # 禁言10分钟
                    await self.bot.napcat.call_api("set_group_ban", {
                        "group_id": event.group_id,
                        "user_id": event.user_id,
                        "duration": 600
                    })
                    await self.bot.send_group(event.group_id, f"[CQ:at,qq={event.user_id}] 消息包含屏蔽词，已被禁言10分钟")
                    return True
                except Exception:
                    pass
        return False

    # ========== 入群管理命令 ==========

    async def _cmd_welcome(self, event, text: str) -> bool:
        """设置入群欢迎 /welcome 欢迎语 或 /welcome off"""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await self.bot.reply(event, "用法：/welcome 欢迎语\n/welcome off 关闭欢迎")
            return True
        
        content = parts[1]
        
        if content.lower() == "off":
            self._welcome_msg = ""
            self._save_config()
            await self.bot.reply(event, "已关闭入群欢迎")
        else:
            self._welcome_msg = content
            self._save_config()
            await self.bot.reply(event, f"已设置入群欢迎语：{content}\n使用 {{at}} 可以@新成员")
        
        return True

    # ========== 辅助方法 ==========

    async def _call_api_with_result(self, action: str, params: dict) -> dict:
        """调用API并获取结果（需要NapCat支持返回数据）"""
        # 注意：当前NapCatAdapter的call_api不返回结果
        # 这里只是一个占位，实际实现需要修改adapter
        await self.bot.napcat.call_api(action, params)
        return {"data": {}}
