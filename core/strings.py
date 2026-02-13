class Buttons:
    MAIN_MENU = "🏠 Hauptmenü"
    ADMIN_MANAGE = "🛒 Meinen Test-Shop verwalten"
    VIEW_SHOP = "🛍 Eigenen Shop ansehen"
    UPGRADE_PRO = "💎 Upgrade auf Pro (10€/Monat)"
    
    ADD_PRODUCT = "➕ Produkt hinzufügen"
    LIST_PRODUCTS = "📋 Meine Produkte"
    SETTINGS = "⚙️ Shop-Einstellungen / Zahlungsarten"
    
    CONF_BOT = "⚙️ Shop-Bot konfigurieren"
    CHANGE_BTC = "Bitcoin (BTC) ändern"
    CHANGE_LTC = "Litecoin (LTC) ändern"
    CHANGE_ETH = "Ethereum (ETH) ändern"
    CHANGE_SOL = "Solana (SOL) ändern"
    CHANGE_PAYPAL = "PayPal (F&F) ändern"
    OWN_BOT_TOKEN = "🤖 Eigener Bot-Token"
    
    SKIP_STOCK = "⏭ Später auffüllen (Überspringen)"
    REFILL_STOCK = "➕ Lager auffüllen"
    DELETE_PRODUCT = "🗑 Löschen"
    BUY_NOW = "🛒 Jetzt kaufen ({price}€)"
    CONTACT_SELLER = "Nachricht an Verkäufer"
    CONFIRM_PAYMENT = "✅ Zahlung erhalten (Ware senden)"

class Messages:
    WELCOME_BACK = "Willkommen bei **Own1Shop**! 🚀\n\nStatus: {status}\nShop-ID: `{shop_id}`"
    ADMIN_WELCOME = (
        "🛠 **Admin-Bereich**\n\n"
        "🆔 Deine Shop-ID: `{shop_id}`\n"
        "🔗 Kunden-Link: [Hier klicken]({shop_link})\n\n"
        "Verwalte hier deine Produkte, Zahlungsarten und Bestände."
    )
    
    ASK_PRODUCT_NAME = "Wie soll das Produkt heißen?"
    ASK_PRODUCT_DESC = "Gib eine kurze Beschreibung ein:"
    ASK_PRODUCT_PRICE = "Was soll es kosten? (z.B. 12.50)"
    STOCK_REFILL_PROMPT = "📥 Sende nun die neuen Daten (`mail:pass` oder eine pro Zeile):"
    PRODUCT_ADDED = "✅ Produkt **{name}** wurde erstellt!"
    REFILL_SUCCESS = "✅ Erfolgreich `{count}` Einheiten nachgefüllt!"
    LIMIT_REACHED = "⚠️ Limit erreicht! Im Free-Modus max. 2 Produkte. Upgrade auf Pro für unbegrenzt."
    
    SETTINGS_MENU = (
        "⚙️ **Shop-Einstellungen**\n\n"
        "Hier kannst du deine Zahlungsdaten hinterlegen, damit Kunden direkt an dich bezahlen.\n\n"
        "**Hinterlegte Daten:**\n"
        "• BTC: `{btc}`\n"
        "• LTC: `{ltc}`\n"
        "{pro_fields}"
    )
    PRO_SETTINGS_PART = "• ETH: `{eth}`\n• SOL: `{sol}`\n• PayPal: `{paypal}`\n"
    ASK_WALLET_ADDRESS = "Bitte sende mir jetzt deine Adresse/Email für **{method}**:"
    WALLET_SUCCESS = "✅ **Gespeichert!** Deine Zahlungsdaten für dieses Feld wurden aktualisiert."
    TOKEN_PROMPT = "Bitte sende mir jetzt den **API-Token** deines Bots (vom @BotFather):"
    TOKEN_SUCCESS = "✅ **Token erfolgreich gespeichert!** Dein Shop wird nun konfiguriert."
    
    SHOP_WELCOME = "🏪 **Willkommen im Shop von {owner_name}**\n\nHier kannst du die verfügbaren Produkte durchstöbern."
    CATALOG_EMPTY = "📭 Dieser Shop hat aktuell keine Produkte im Angebot."
    PRODUCT_DETAILS = "📦 **{name}**\n\n📝 {desc}\n\n💰 Preis: {price}€\n🔢 Status: {stock}"
    
    ORDER_INITIATED = (
        "✅ **Bestellung eingeleitet!**\n\n"
        "Bitte sende den Betrag an eine der folgenden Adressen des Verkäufers:\n\n"
        "{payment_methods}\n"
        "Sobald der Händler den Zahlungseingang bestätigt, wird dir die Ware automatisch zugestellt."
    )
    
    NEW_ORDER_SELLER = (
        "🔔 **Neue Bestellung!**\n\n"
        "Kunde: @{username} (`{user_id}`)\n"
        "Produkt-ID: `{product_id}`\n"
        "Bestell-ID: `{order_id}`\n\n"
        "Bitte bestätige den Zahlungseingang unten, um die Ware auszuliefern."
    )
    SALE_CONFIRMED_SELLER = "✅ **Verkauf bestätigt!**\nDie Ware wurde automatisch gesendet:\n<code>{content}</code>"
    SALE_CONFIRMED_BUYER = "🎉 **Zahlung bestätigt!**\n\nHier ist deine Ware:\n<code>{content}</code>"
