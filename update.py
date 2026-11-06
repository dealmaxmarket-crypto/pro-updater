import xml.etree.ElementTree as ET
import requests
import datetime

# Усі 11 посилань на прайси постачальників:
SUPPLIER_URLS = [
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
                for offer in root.iter('offer'):
                    # Гнучкий пошук ID товару
                    offer_id = offer.attrib.get('id') or offer.attrib.get('code') or offer.attrib.get('vendorCode')
                    if not offer_id:
                        id_node = offer.find('id') or offer.find('code') or offer.find('vendorCode')
                        if id_node is not None and id_node.text:
                            offer_id = id_node.text.strip()
                    
                    if not offer_id:
                        continue

                    # Гнучкий пошук наявності (available / доступный)
                    available = offer.attrib.get('available') or offer.attrib.get('доступный')
                    if not available:
                        avail_node = offer.find('available') or offer.find('доступный')
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
                    qty_node = offer.find('stock_quantity') or offer.find('quantity') or offer.find('stock')
                    stock_qty = qty_node.text.strip() if qty_node is not None and qty_node.text else '0'

                    supplier_stock[str(offer_id)] = {
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
    
    # Додаємо коментар з поточним часом, щоб файл завжди гарантовано відрізнявся
    comment = ET.Comment(f"Updated at: {datetime.datetime.now()}")
    root.append(comment)

    shop = ET.SubElement(root, "shop")
    offers = ET.SubElement(shop, "offers")

    for item_id, data in supplier_stock.items():
        offer_el = ET.SubElement(offers, "offer", id=item_id, available=data['available'])
        stock_el = ET.SubElement(offer_el, "stock_quantity")
        stock_el.text = str(data['quantity'])

    tree = ET.ElementTree(root)
    tree.write("prom_update_feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"Готово! Загалом об'єднано унікальних товарів у фіді: {len(supplier_stock)}")

if __name__ == "__main__":
    main()
