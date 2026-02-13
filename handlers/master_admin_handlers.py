from aiogram import Router, types, F
from aiogram.filters import Command
from config import Config
from services.db_service import db, activate_pro_subscription
from core.strings import Buttons

router = Router()

def is_master_admin(user_id: int):
    return user_id in Config.ADMIN_IDS

@router.message(Command("master"))
async def master_admin_menu(message: types.Message):
    if not is_master_admin(message.from_user.id):
        return

    profiles = db.table("profiles").select("*", count="exact").execute()
    products = db.table("products").select("*", count="exact").execute()
    orders = db.table("orders").select("*", count="exact").execute()
    pro_users = db.table("profiles").select("*").eq("is_pro", True).execute()

    stats_text = (
        "👑 **Master-Admin Dashboard**\n\n"
        f"👥 Gesamt-User: `{profiles.count}`\n"
        f"💎 PRO-User: `{len(pro_users.data)}`\n"
        f"📦 Produkte gesamt: `{products.count}`\n"
        f"💳 Bestellungen gesamt: `{orders.count}`\n\n"
        "**Admin-Befehle:**\n"
        "• `/grantpro <ID>` - User auf PRO setzen\n"
        "• `/revokepro <ID>` - PRO-Status entfernen\n"
        "• `/userinfo <ID>` - Details zu einem User"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

@router.message(Command("grantpro"))
async def master_grant_pro(message: types.Message):
    if not is_master_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Nutze: `/grantpro <Telegram_ID>`")
        return

    try:
        target_id = int(args[1])
        await activate_pro_subscription(target_id)
        
        await message.answer(f"✅ User `{target_id}` wurde erfolgreich auf **PRO** gesetzt.")
        
        try:
            await message.bot.send_message(
                target_id, 
                "🎉 Dein Upgrade auf **PRO** wurde vom Admin aktiviert!\n"
                "Du hast nun Zugriff auf alle Funktionen."
            )
        except:
            pass
    except Exception as e:
        await message.answer(f"❌ Fehler: {e}")

@router.message(Command("revokepro"))
async def master_revoke_pro(message: types.Message):
    if not is_master_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Nutze: `/revokepro <Telegram_ID>`")
        return

    try:
        target_id = int(args[1])
        db.table("profiles").update({"is_pro": False}).eq("id", target_id).execute()
        await message.answer(f"🚫 PRO-Status für `{target_id}` entfernt.")
    except Exception as e:
        await message.answer(f"❌ Fehler: {e}")

@router.message(Command("userinfo"))
async def master_user_info(message: types.Message):
    if not is_master_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Nutze: `/userinfo <Telegram_ID>`")
        return

    try:
        target_id = int(args[1])
        res = db.table("profiles").select("*").eq("id", target_id).single().execute()
        
        if res.data:
            u = res.data
            info = (
                f"👤 **User Info: {u.get('username')}**\n"
                f"🆔 ID: `{u.get('id')}`\n"
                f"💎 PRO: `{'Ja' if u.get('is_pro') else 'Nein'}`\n"
                f"🏪 Shop-ID: `{u.get('shop_id')}`\n"
                f"🪙 BTC: `{u.get('wallet_btc') or 'n/a'}`\n"
                f"🪙 LTC: `{u.get('wallet_ltc') or 'n/a'}`"
            )
            await message.answer(info, parse_mode="Markdown")
        else:
            await message.answer("User nicht gefunden.")
    except Exception as e:
        await message.answer(f"❌ Fehler: {e}")
