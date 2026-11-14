import xml.etree.ElementTree as ET
import requests
import datetime

# Усі посилання на прайси постачальників (нові додано на початок):
SUPPLIER_URLS = [
    "https://api.dropshipping.ua/api/feeds/5491.xml",
    "https://api.dropshipping.ua/api/feeds/5490.xml",
    "https://api.dropshipping.ua/api/feeds/5489.xml",
    "https://api.dropshipping.ua/api/feeds/5488.xml",
    "https://api.dropshipping.ua/api/feeds/5487.xml",
    "https://aveon.net.ua/yandex_market.xml?hash_tag=7b71fadcc4a12f03cf26a304da032fba&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&export_lang=ru&group_ids=",
    "https://i-maxi.com.ua/yandex_market.xml?hash_tag=3862084c32af01bfd3be5efc7110b84c&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=1&yandex_cpa=&process_presence_sure=&languages=ru&group_ids=",
    "https://livelyshop.com.ua/products_feed.xml?hash_tag=e0e046a4f54904aacd559e46afd96a8e&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&group_ids=",
    "https://6kilometr.com.ua/yandex_market.xml?hash_tag=a05443bbe29b8152f7f23e09cd8c0fac&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&group_ids=",
    "https://modern.best-time.biz/uk/feed/rozetka?priceua_price=1",
    "https://feed.lugi.com.ua/index.php?route=extension/feed/unixml/prommulti",
    "https://opt-drop.com/storage/xml/opt-drop-29.xml",
    "https://velocompany.com.ua/products_feed.xml?hash_tag=dd9d6354c41b68d6d3d059d15f2dac4d&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&extra_fields=keywords&group_ids=",
    "https://geo-market.salesdrive.me/export/yml/export.yml?publicKey=g7HidIKJWTjhyiMvbsUQKuztsuqHTR2-gLac21sdTbwAVGX81FQSJ0FnelqaQAni",
    "https://stozhary.net.ua/api/drop/margin-wholesale/DjCE0C_JNLrJiEM8SS1z31cFuc095jr9?price_min=465&incr=2",
    "https://export.buymeua.shop/export-config?config_id=2422"
]

def main():
    supplier_stock = {}

    print("Починаємо збір даних з прайсів постачальників...")

    for url in SUPPLIER_URLS:
        if not url.startswith("http"):
            continue
        try:
            resp = requests.get(url.strip(), timeout=30)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                count = 0
                
                # Визначаємо особливості прайсу
                is_stozhary = "stozhary.net.ua" in url
                is_optdrop = "opt-drop.com" in url
                iter_tag = 'item' if is_stozhary else 'offer'

                for element in root.iter(iter_tag):
                    offer_id = None

                    # Визначаємо артикул товару залежно від постачальника
                    if is_stozhary or is_optdrop:
                        # Стожари та Opt-drop: спочатку беремо vendorCode
                        vc_node = element.find('vendorCode')
                        if vc_node is not None and vc_node.text:
                            offer_id = vc_node.text.strip()
                        # Якщо vendorCode відсутній — використовуємо ID
                        if not offer_id:
                            offer_id = element.attrib.get('id')
                    else:
                        # Інші постачальники (включно з новими з dropshipping.ua) — стандартний гнучкий пошук
                        offer_id = element.attrib.get('id') or element.attrib.get('code') or element.attrib.get('vendorCode')
                        if not offer_id:
                            id_node = element.find('id') or element.find('code') or element.find('vendorCode')
                            if id_node is not None and id_node.text:
                                offer_id = id_node.text.strip()

                    if not offer_id:
                        continue

                    # Ціна товару
                    price_node = element.find('price')
                    price_val = price_node.text.strip() if price_node is not None and price_node.text else '0'

                    # Гнучкий пошук наявності (available / доступный)
                    available = element.attrib.get('available') or element.attrib.get('доступный')
                    if not available:
                        avail_node = element.find('available') or element.find('доступный')
                        if avail_node is not None and avail_node.text:
                            available = avail_node.text.strip()
                        else:
                            available = 'true'

                    # Нормалізуємо значення наявності в 'true' / 'false'
                    avail_str = str(available).lower()
                    if avail_str in ['1', 'true', '+', 'yes', 'так']:
                        available_val = 'true'
                    else:
                        available_val = 'false'

                    # Гнучкий пошук кількості на складі
                    if is_stozhary:
                        qty_node = element.find('quantity_in_stock') or element.find('stock_quantity') or element.find('quantity') or element.find('stock')
                    else:
                        qty_node = element.find('stock_quantity') or element.find('quantity') or element.find('stock')
                        
                    stock_qty = qty_node.text.strip() if qty_node is not None and qty_node.text else '0'

                    supplier_stock[str(offer_id)] = {
                        'price': price_val,
                        'available': available_val,
                        'quantity': stock_qty
                    }
                    count += 1

                print(f"Успішно опрацьовано прайс: {url[:40]}... (знайдено товарів: {count})")
            else:
                print(f"Помилка завантаження (статус {resp.status_code}): {url[:40]}...")
        except Exception as e:
            print(f"Помилка для {url[:40]}...: {e}")

    # Створюємо єдиний XML-фід для Prom.ua
    root = ET.Element("yml_catalog")
    
    # Додаємо коментар з поточним часом
    comment = ET.Comment(f"Updated at: {datetime.datetime.now()}")
    root.append(comment)

    shop = ET.SubElement(root, "shop")
    offers = ET.SubElement(shop, "offers")

    for item_id, data in supplier_stock.items():
        offer_el = ET.SubElement(offers, "offer", id=item_id, available=data['available'])
        
        price_el = ET.SubElement(offer_el, "price")
        price_el.text = str(data['price'])

        stock_el = ET.SubElement(offer_el, "stock_quantity")
        stock_el.text = str(data['quantity'])

    tree = ET.ElementTree(root)
    tree.write("prom_update_feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"\nГотово! Загалом об'єднано унікальних товарів у єдиному фіді: {len(supplier_stock)}")

if __name__ == "__main__":
    main()
