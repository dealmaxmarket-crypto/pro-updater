import xml.etree.ElementTree as ET
import requests

# Твої 9 посилань на прайси постачальників:
SUPPLIER_URLS = [
    "https://aveon.net.ua/yandex_market.xml?hash_tag=7b71fadcc4a12f03cf26a304da032fba&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&export_lang=ru&group_ids=",
    "https://i-maxi.com.ua/yandex_market.xml?hash_tag=3862084c32af01bfd3be5efc7110b84c&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=1&yandex_cpa=&process_presence_sure=&languages=ru&group_ids=",
    "https://livelyshop.com.ua/products_feed.xml?hash_tag=e0e046a4f54904aacd559e46afd96a8e&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&group_ids=",
    "https://6kilometr.com.ua/yandex_market.xml?hash_tag=a05443bbe29b8152f7f23e09cd8c0fac&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&group_ids=",
    "https://modern.best-time.biz/uk/feed/rozetka?priceua_price=1",
    "https://feed.lugi.com.ua/index.php?route=extension/feed/unixml/prommulti",
    "https://opt-drop.com/storage/xml/opt-drop-29.xml",
    "https://velocompany.com.ua/products_feed.xml?hash_tag=dd9d6354c41b68d6d3d059d15f2dac4d&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=0&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&extra_fields=keywords&group_ids=",
    "https://geo-market.salesdrive.me/export/yml/export.yml?publicKey=g7HidIKJWTjhyiMvbsUQKuztsuqHTR2-gLac21sdTbwAVGX81FQSJ0FnelqaQAni"
]

def main():
    supplier_stock = {}

    print("Починаємо збір даних з прайсів постачальників...")

    # По черзі завантажуємо кожен прайс постачальника
    for url in SUPPLIER_URLS:
        if not url.startswith("http"):
            continue
        try:
            resp = requests.get(url.strip(), timeout=25)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                count = 0
                for offer in root.iter('offer'):
                    offer_id = offer.attrib.get('id')
                    available = offer.attrib.get('available', 'false')
                    stock_qty = offer.findtext('stock_quantity', '0')
                    
                    if offer_id:
                        supplier_stock[str(offer_id)] = {
                            'available': available,
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
    shop = ET.SubElement(root, "shop")
    offers = ET.SubElement(shop, "offers")

    for item_id, data in supplier_stock.items():
        offer_el = ET.SubElement(offers, "offer", id=item_id, available=data['available'])
        stock_el = ET.SubElement(offer_el, "stock_quantity")
        stock_el.text = str(data['quantity'])

    # Зберігаємо у файл
    tree = ET.ElementTree(root)
    tree.write("prom_update_feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"Готово! Загалом об'єднано унікальних товарів у фіді: {len(supplier_stock)}")

if __name__ == "__main__":
    main()
