import xml.etree.ElementTree as ET
import requests
import datetime

# Тільки ці 5 нових посилань від dropshipping.ua:
DROPSHIPPING_URLS = [
    "https://api.dropshipping.ua/api/feeds/5491.xml",
    "https://api.dropshipping.ua/api/feeds/5490.xml",
    "https://api.dropshipping.ua/api/feeds/5489.xml",
    "https://api.dropshipping.ua/api/feeds/5488.xml",
    "https://api.dropshipping.ua/api/feeds/5487.xml"
]

def main():
    supplier_stock = {}

    print("Починаємо збір даних з нових прайсів dropshipping.ua...")

    for url in DROPSHIPPING_URLS:
        if not url.startswith("http"):
            continue
        try:
            resp = requests.get(url.strip(), timeout=30)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                count = 0

                for element in root.iter('offer'):
                    # Стандартний пошук артикула/ID для цих фідів
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

                    # Наявність
                    available = element.attrib.get('available') or element.attrib.get('доступный')
                    if not available:
                        avail_node = element.find('available') or element.find('доступный')
                        if avail_node is not None and avail_node.text:
                            available = avail_node.text.strip()
                        else:
                            available = 'true'

                    avail_str = str(available).lower()
                    if avail_str in ['1', 'true', '+', 'yes', 'так']:
                        available_val = 'true'
                    else:
                        available_val = 'false'

                    # Кількість
                    qty_node = element.find('stock_quantity') or element.find('quantity') or element.find('stock')
                    stock_qty = qty_node.text.strip() if qty_node is not None and qty_node.text else '0'

                    supplier_stock[str(offer_id)] = {
                        'price': price_val,
                        'available': available_val,
                        'quantity': stock_qty
                    }
                    count += 1

                print(f"Успішно опрацьовано прайс: {url} (знайдено товарів: {count})")
            else:
                print(f"Помилка завантаження (статус {resp.status_code}): {url}")
        except Exception as e:
            print(f"Помилка для {url}: {e}")

    # Створюємо окремий XML-фід для цих 5 постачальників
    root = ET.Element("yml_catalog")
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
    # Зберігаємо в окремий файл
    tree.write("dropshipping_feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"\nГотово! Загалом об'єднано унікальних товарів у новому фіді: {len(supplier_stock)}")

if __name__ == "__main__":
    main()
